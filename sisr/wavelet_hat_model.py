"""
Wavelet-HAT Model Architecture
HAT: Hybrid Attention Transformer for Image Super-Resolution
Extracted for inference use only
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# Configuration
IMAGE_SIZE = 128
INPUT_SIZE = 32
UPSCALE = 4

# HAT Architecture Parameters
NUM_RHAG = 6
NUM_HAB = 6
EMBED_DIM = 180
NUM_HEADS = 6
WINDOW_SIZE = 16
MLP_RATIO = 2
QKV_BIAS = True
QK_SCALE = None
DROP_RATE = 0.0
ATTN_DROP_RATE = 0.0
DROP_PATH_RATE = 0.1
IMG_RANGE = 1.0
RESI_CONNECTION = '1conv'
CAB_SQUEEZE_FACTOR = 3
CAB_WEIGHT = 0.01
OVERLAP_RATIO = 0.5
WAVELET_TYPE = 'db1'


class FastWaveletTransform2D(nn.Module):
    """Haar wavelet decomposition"""
    def __init__(self, wavelet='db1'):
        super(FastWaveletTransform2D, self).__init__()
        h0 = torch.tensor([0.7071067811865476, 0.7071067811865476])
        h1 = torch.tensor([-0.7071067811865476, 0.7071067811865476])
        self.register_buffer('h0', h0.view(1, 1, -1, 1))
        self.register_buffer('h1', h1.view(1, 1, -1, 1))
    
    def forward(self, x):
        batch, channels, height, width = x.shape
        coeffs = {'LL': [], 'LH': [], 'HL': [], 'HH': []}
        for c in range(channels):
            x_c = x[:, c:c+1, :, :]
            x_L = F.conv2d(x_c, self.h0.repeat(1, 1, 1, 1), padding=(1, 0))[:, :, :-1, :]
            x_H = F.conv2d(x_c, self.h1.repeat(1, 1, 1, 1), padding=(1, 0))[:, :, :-1, :]
            LL = F.conv2d(x_L, self.h0.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            LH = F.conv2d(x_L, self.h1.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            HL = F.conv2d(x_H, self.h0.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            HH = F.conv2d(x_H, self.h1.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            coeffs['LL'].append(LL); coeffs['LH'].append(LH)
            coeffs['HL'].append(HL); coeffs['HH'].append(HH)
        return {k: torch.cat(v, dim=1) for k, v in coeffs.items()}


def window_partition(x, window_size):
    """Partition into non-overlapping windows"""
    B, H, W, C = x.shape
    x = x.view(B, H // window_size, window_size, W // window_size, window_size, C)
    windows = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(-1, window_size, window_size, C)
    return windows


def window_reverse(windows, window_size, H, W):
    """Reverse window partition"""
    B = int(windows.shape[0] / (H * W / window_size / window_size))
    x = windows.view(B, H // window_size, W // window_size, window_size, window_size, -1)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous().view(B, H, W, -1)
    return x


class Mlp(nn.Module):
    """MLP with GELU activation"""
    def __init__(self, in_features, hidden_features=None, out_features=None, 
                 act_layer=nn.GELU, drop=0.):
        super().__init__()
        out_features = out_features or in_features
        hidden_features = hidden_features or in_features
        self.fc1 = nn.Linear(in_features, hidden_features)
        self.act = act_layer()
        self.fc2 = nn.Linear(hidden_features, out_features)
        self.drop = nn.Dropout(drop)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.drop(x)
        x = self.fc2(x)
        x = self.drop(x)
        return x


class WindowAttention(nn.Module):
    """Window based multi-head self attention"""
    
    def __init__(self, dim, window_size, num_heads, qkv_bias=True, qk_scale=None, 
                 attn_drop=0., proj_drop=0.):
        super().__init__()
        self.dim = dim
        self.window_size = window_size
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** -0.5

        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2 * window_size[0] - 1) * (2 * window_size[1] - 1), num_heads))

        coords_h = torch.arange(self.window_size[0])
        coords_w = torch.arange(self.window_size[1])
        coords = torch.stack(torch.meshgrid([coords_h, coords_w], indexing='ij'))
        coords_flatten = torch.flatten(coords, 1)
        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
        relative_coords = relative_coords.permute(1, 2, 0).contiguous()
        relative_coords[:, :, 0] += self.window_size[0] - 1
        relative_coords[:, :, 1] += self.window_size[1] - 1
        relative_coords[:, :, 0] *= 2 * self.window_size[1] - 1
        relative_position_index = relative_coords.sum(-1)
        self.register_buffer("relative_position_index", relative_position_index)

        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)

        nn.init.trunc_normal_(self.relative_position_bias_table, std=.02)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x, mask=None):
        B_, N, C = x.shape
        qkv = self.qkv(x).reshape(B_, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        q = q * self.scale
        attn = (q @ k.transpose(-2, -1))

        relative_position_bias = self.relative_position_bias_table[self.relative_position_index.view(-1)].view(
            self.window_size[0] * self.window_size[1], self.window_size[0] * self.window_size[1], -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous()
        attn = attn + relative_position_bias.unsqueeze(0)

        if mask is not None:
            nW = mask.shape[0]
            attn = attn.view(B_ // nW, nW, self.num_heads, N, N) + mask.unsqueeze(1).unsqueeze(0)
            attn = attn.view(-1, self.num_heads, N, N)
            attn = self.softmax(attn)
        else:
            attn = self.softmax(attn)

        attn = self.attn_drop(attn)

        x = (attn @ v).transpose(1, 2).reshape(B_, N, C)
        x = self.proj(x)
        x = self.proj_drop(x)
        return x


class ChannelAttention(nn.Module):
    """Channel Attention Module"""
    def __init__(self, num_feat, squeeze_factor=16):
        super(ChannelAttention, self).__init__()
        self.attention = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(num_feat, num_feat // squeeze_factor, 1, padding=0),
            nn.ReLU(inplace=True),
            nn.Conv2d(num_feat // squeeze_factor, num_feat, 1, padding=0),
            nn.Sigmoid()
        )

    def forward(self, x):
        y = self.attention(x)
        return x * y


class CAB(nn.Module):
    """Channel Attention Block"""
    def __init__(self, num_feat, compress_ratio=3, squeeze_factor=16):
        super(CAB, self).__init__()
        self.cab = nn.Sequential(
            nn.Conv2d(num_feat, num_feat // compress_ratio, 3, 1, 1),
            nn.GELU(),
            nn.Conv2d(num_feat // compress_ratio, num_feat, 3, 1, 1),
            ChannelAttention(num_feat, squeeze_factor)
        )

    def forward(self, x):
        return self.cab(x)


class HAB(nn.Module):
    """Hybrid Attention Block"""
    
    def __init__(self, dim, input_resolution, num_heads, window_size=7, shift_size=0,
                 mlp_ratio=4., qkv_bias=True, qk_scale=None, drop=0., attn_drop=0.,
                 drop_path=0., act_layer=nn.GELU, norm_layer=nn.LayerNorm,
                 compress_ratio=3, squeeze_factor=16, cab_weight=0.01):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.num_heads = num_heads
        self.window_size = window_size
        self.shift_size = shift_size
        self.mlp_ratio = mlp_ratio
        self.cab_weight = cab_weight
        
        if min(self.input_resolution) <= self.window_size:
            self.shift_size = 0
            self.window_size = min(self.input_resolution)
        assert 0 <= self.shift_size < self.window_size

        self.norm1 = norm_layer(dim)
        self.attn = WindowAttention(
            dim, window_size=(self.window_size, self.window_size), num_heads=num_heads,
            qkv_bias=qkv_bias, qk_scale=qk_scale, attn_drop=attn_drop, proj_drop=drop)

        self.conv_block = CAB(num_feat=dim, compress_ratio=compress_ratio, squeeze_factor=squeeze_factor)

        self.drop_path = nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=act_layer, drop=drop)

        if self.shift_size > 0:
            H, W = self.input_resolution
            img_mask = torch.zeros((1, H, W, 1))
            h_slices = (slice(0, -self.window_size),
                       slice(-self.window_size, -self.shift_size),
                       slice(-self.shift_size, None))
            w_slices = (slice(0, -self.window_size),
                       slice(-self.window_size, -self.shift_size),
                       slice(-self.shift_size, None))
            cnt = 0
            for h in h_slices:
                for w in w_slices:
                    img_mask[:, h, w, :] = cnt
                    cnt += 1

            mask_windows = window_partition(img_mask, self.window_size)
            mask_windows = mask_windows.view(-1, self.window_size * self.window_size)
            attn_mask = mask_windows.unsqueeze(1) - mask_windows.unsqueeze(2)
            attn_mask = attn_mask.masked_fill(attn_mask != 0, float(-100.0)).masked_fill(attn_mask == 0, float(0.0))
        else:
            attn_mask = None

        self.register_buffer("attn_mask", attn_mask)

    def forward(self, x):
        H, W = self.input_resolution
        B, L, C = x.shape
        assert L == H * W

        shortcut = x
        x = self.norm1(x)
        x = x.view(B, H, W, C)

        if self.shift_size > 0:
            shifted_x = torch.roll(x, shifts=(-self.shift_size, -self.shift_size), dims=(1, 2))
        else:
            shifted_x = x

        x_windows = window_partition(shifted_x, self.window_size)
        x_windows = x_windows.view(-1, self.window_size * self.window_size, C)

        attn_windows = self.attn(x_windows, mask=self.attn_mask)

        attn_windows = attn_windows.view(-1, self.window_size, self.window_size, C)
        shifted_x = window_reverse(attn_windows, self.window_size, H, W)

        if self.shift_size > 0:
            attn_x = torch.roll(shifted_x, shifts=(self.shift_size, self.shift_size), dims=(1, 2))
        else:
            attn_x = shifted_x
        attn_x = attn_x.view(B, H * W, C)

        conv_x = self.conv_block(x.permute(0, 3, 1, 2))
        conv_x = conv_x.permute(0, 2, 3, 1).view(B, H * W, C)

        x = shortcut + attn_x + self.cab_weight * conv_x
        x = x + self.drop_path(self.mlp(self.norm2(x)))

        return x


class OverlapCrossAttention(nn.Module):
    """Overlapping Cross-Attention Module"""
    
    def __init__(self, dim, input_resolution, window_size, overlap_ratio, num_heads,
                 qkv_bias=True, qk_scale=None, attn_drop=0., proj_drop=0.):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.window_size = window_size
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = qk_scale or head_dim ** -0.5
        self.overlap_win_size = int(window_size * (1 + overlap_ratio))

        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        H, W = self.input_resolution
        B, L, C = x.shape
        assert L == H * W
        
        x = x.view(B, H, W, C)
        qkv = self.qkv(x).reshape(B, H, W, 3, C).permute(3, 0, 1, 2, 4)
        q = qkv[0].permute(0, 3, 1, 2)
        
        attn_out = q.permute(0, 2, 3, 1).reshape(B, L, C)
        attn_out = self.proj(attn_out)
        attn_out = self.proj_drop(attn_out)
        
        return attn_out


class OCAB(nn.Module):
    """Overlapping Cross-Attention Block"""
    
    def __init__(self, dim, input_resolution, window_size, overlap_ratio, num_heads, mlp_ratio=2.,
                 qkv_bias=True, qk_scale=None, drop=0., attn_drop=0.,
                 drop_path=0., norm_layer=nn.LayerNorm):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution
        self.num_heads = num_heads
        self.window_size = window_size
        self.mlp_ratio = mlp_ratio

        self.norm1 = norm_layer(dim)
        self.attn = OverlapCrossAttention(
            dim, input_resolution=input_resolution, window_size=window_size, overlap_ratio=overlap_ratio,
            num_heads=num_heads, qkv_bias=qkv_bias, qk_scale=qk_scale,
            attn_drop=attn_drop, proj_drop=drop)

        self.drop_path = nn.Identity()
        self.norm2 = norm_layer(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = Mlp(in_features=dim, hidden_features=mlp_hidden_dim, act_layer=nn.GELU, drop=drop)

    def forward(self, x):
        shortcut = x
        x = self.norm1(x)
        x = self.attn(x)
        x = shortcut + self.drop_path(x)
        x = x + self.drop_path(self.mlp(self.norm2(x)))
        return x


class RHAG(nn.Module):
    """Residual Hybrid Attention Group"""
    
    def __init__(self, dim, input_resolution, depth, num_heads, window_size,
                 mlp_ratio=2., qkv_bias=True, qk_scale=None, drop=0., attn_drop=0.,
                 drop_path=0., norm_layer=nn.LayerNorm, compress_ratio=3, 
                 squeeze_factor=16, cab_weight=0.01, overlap_ratio=0.5):
        super().__init__()
        self.dim = dim
        self.input_resolution = input_resolution

        self.hab_blocks = nn.ModuleList([
            HAB(dim=dim, input_resolution=input_resolution,
                num_heads=num_heads, window_size=window_size,
                shift_size=0 if (i % 2 == 0) else window_size // 2,
                mlp_ratio=mlp_ratio,
                qkv_bias=qkv_bias, qk_scale=qk_scale,
                drop=drop, attn_drop=attn_drop,
                drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path,
                norm_layer=norm_layer,
                compress_ratio=compress_ratio,
                squeeze_factor=squeeze_factor,
                cab_weight=cab_weight)
            for i in range(depth)])

        self.ocab = OCAB(dim=dim, input_resolution=input_resolution,
                        window_size=window_size, overlap_ratio=overlap_ratio,
                        num_heads=num_heads, mlp_ratio=mlp_ratio,
                        qkv_bias=qkv_bias, qk_scale=qk_scale,
                        drop=drop, attn_drop=attn_drop)

        self.conv = nn.Conv2d(dim, dim, 3, 1, 1)

    def forward(self, x):
        H, W = self.input_resolution
        B, L, C = x.shape
        
        shortcut = x
        
        for hab in self.hab_blocks:
            x = hab(x)
        
        x = self.ocab(x)
        
        x = x.view(B, H, W, C).permute(0, 3, 1, 2)
        x = self.conv(x)
        x = x.permute(0, 2, 3, 1).view(B, L, C)
        
        x = x + shortcut
        
        return x


class Upsample(nn.Sequential):
    """Upsample module using PixelShuffle"""
    
    def __init__(self, scale, num_feat):
        m = []
        if (scale & (scale - 1)) == 0:  # scale = 2^n
            for _ in range(int(np.log2(scale))):
                m.append(nn.Conv2d(num_feat, 4 * num_feat, 3, 1, 1))
                m.append(nn.PixelShuffle(2))
        elif scale == 3:
            m.append(nn.Conv2d(num_feat, 9 * num_feat, 3, 1, 1))
            m.append(nn.PixelShuffle(3))
        else:
            raise ValueError(f'scale {scale} is not supported')
        super(Upsample, self).__init__(*m)


class WaveletHATGenerator(nn.Module):
    """
    HAT Generator for Super-Resolution
    Input: (B, 3, 32, 32) -> Output: (B, 3, 128, 128)
    """
    
    def __init__(self, img_size=INPUT_SIZE, in_chans=3, embed_dim=EMBED_DIM,
                 depths=[NUM_HAB]*NUM_RHAG, num_heads=[NUM_HEADS]*NUM_RHAG,
                 window_size=WINDOW_SIZE, mlp_ratio=MLP_RATIO, qkv_bias=QKV_BIAS, qk_scale=QK_SCALE,
                 drop_rate=DROP_RATE, attn_drop_rate=ATTN_DROP_RATE, drop_path_rate=DROP_PATH_RATE,
                 norm_layer=nn.LayerNorm, compress_ratio=CAB_SQUEEZE_FACTOR,
                 squeeze_factor=16, cab_weight=CAB_WEIGHT, overlap_ratio=OVERLAP_RATIO,
                 img_range=IMG_RANGE, upscale=UPSCALE, resi_connection=RESI_CONNECTION, 
                 use_wavelet=True, wavelet='db1'):
        super(WaveletHATGenerator, self).__init__()
        self.use_wavelet = use_wavelet
        
        num_in_ch = in_chans
        num_out_ch = in_chans
        num_feat = 64
        self.img_range = img_range
        self.upscale = upscale
        self.window_size = window_size

        # Shallow feature extraction
        if use_wavelet:
            self.swt = FastWaveletTransform2D(wavelet=wavelet)
            ll_ch = int(embed_dim * 0.4)
            lh_ch = int(embed_dim * 0.2)
            hl_ch = int(embed_dim * 0.2)
            hh_ch = embed_dim - ll_ch - lh_ch - hl_ch
            self.conv_LL = nn.Conv2d(3, ll_ch, 3, 1, 1)
            self.conv_LH = nn.Conv2d(3, lh_ch, 3, 1, 1)
            self.conv_HL = nn.Conv2d(3, hl_ch, 3, 1, 1)
            self.conv_HH = nn.Conv2d(3, hh_ch, 3, 1, 1)
            self.fusion = nn.Conv2d(embed_dim, embed_dim, 1)
        else:
            self.conv_first = nn.Conv2d(num_in_ch, embed_dim, 3, 1, 1)

        # Deep feature extraction
        self.num_layers = len(depths)
        self.embed_dim = embed_dim
        self.num_features = embed_dim
        self.mlp_ratio = mlp_ratio

        self.patch_embed = nn.Identity()
        
        patches_resolution = [img_size, img_size]
        self.patches_resolution = patches_resolution

        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]

        # Build RHAG layers
        self.layers = nn.ModuleList()
        for i_layer in range(self.num_layers):
            layer = RHAG(dim=embed_dim,
                        input_resolution=(patches_resolution[0], patches_resolution[1]),
                        depth=depths[i_layer],
                        num_heads=num_heads[i_layer],
                        window_size=window_size,
                        mlp_ratio=self.mlp_ratio,
                        qkv_bias=qkv_bias, qk_scale=qk_scale,
                        drop=drop_rate, attn_drop=attn_drop_rate,
                        drop_path=dpr[sum(depths[:i_layer]):sum(depths[:i_layer + 1])],
                        norm_layer=norm_layer,
                        compress_ratio=compress_ratio,
                        squeeze_factor=squeeze_factor,
                        cab_weight=cab_weight,
                        overlap_ratio=overlap_ratio)
            self.layers.append(layer)
        
        self.norm = norm_layer(self.num_features)

        if resi_connection == '1conv':
            self.conv_after_body = nn.Conv2d(embed_dim, embed_dim, 3, 1, 1)
        
        # Upsampling
        self.conv_before_upsample = nn.Sequential(
            nn.Conv2d(embed_dim, num_feat, 3, 1, 1),
            nn.LeakyReLU(inplace=True))
        self.upsample = Upsample(upscale, num_feat)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)

        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.trunc_normal_(m.weight, std=.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)

    def forward_features(self, x):
        x_size = (x.shape[2], x.shape[3])
        x = x.flatten(2).transpose(1, 2)
        for layer in self.layers:
            x = layer(x)
        x = self.norm(x)
        x = x.transpose(1, 2).view(-1, self.embed_dim, x_size[0], x_size[1])
        return x

    def forward(self, x):
        H, W = x.shape[2:]
        x = self.check_image_size(x)

        # Shallow feature extraction
        if self.use_wavelet:
            c = self.swt(x)
            f = torch.cat([
                self.conv_LL(c['LL']),
                self.conv_LH(c['LH']),
                self.conv_HL(c['HL']),
                self.conv_HH(c['HH'])
            ], dim=1)
            x = self.fusion(f)
        else:
            x = self.conv_first(x)
        
        # Deep feature extraction
        res = self.conv_after_body(self.forward_features(x))
        res += x

        # Upsampling
        x = self.conv_before_upsample(res)
        x = self.conv_last(self.upsample(x))

        return torch.tanh(x[:, :, :H*self.upscale, :W*self.upscale])

    def check_image_size(self, x):
        _, _, h, w = x.size()
        mod_pad_h = (self.window_size - h % self.window_size) % self.window_size
        mod_pad_w = (self.window_size - w % self.window_size) % self.window_size
        x = F.pad(x, (0, mod_pad_w, 0, mod_pad_h), 'reflect')
        return x
