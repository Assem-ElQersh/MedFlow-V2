## ============================================================================
## WAVELET-ENHANCED FREQFORMER - DUAL FREQUENCY PROCESSING FOR MEDICAL SR
## Combines Frequency-Aware Transformer + Wavelet Transform
## Addresses the "disappearing edges" problem with dual frequency processing
## ============================================================================

# Installation
!pip install einops -q
!pip install torchxrayvision -q

# Core imports
import os
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torchvision.models import vgg19
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
import glob
import cv2
from tqdm import tqdm
import pandas as pd
from PIL import Image
import seaborn as sns
import torchxrayvision as xrv
from scipy import ndimage
from einops import rearrange
from einops.layers.torch import Rearrange
import math

# Set random seeds for reproducibility
np.random.seed(42)
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)

# ============================================================================
# CONFIGURATION - FreqFormer Parameters
# ============================================================================

IMAGE_SIZE = 128          # High-resolution image size
UPSCALE_FACTOR = 4        # Super-resolution factor (4x)
LR_SIZE = IMAGE_SIZE // UPSCALE_FACTOR  # Low-resolution size (32x32)

BATCH_SIZE = 8            # Can be larger than GAN training
EPOCHS = 100              # More epochs for convergence
LR = 2e-4                 # Learning rate for transformer
BETA1 = 0.9
BETA2 = 0.999

# FreqFormer specific parameters
EMBED_DIM = 64            # Embedding dimension
DEPTHS = [6, 6, 6, 6]     # Number of transformer blocks per stage
NUM_HEADS = [2, 2, 2, 2]  # Number of attention heads per stage
WINDOW_SIZE = 8           # Window size for local attention
MLP_RATIO = 2.0           # MLP expansion ratio

# Dataset path
DATASET_PATH = "/kaggle/input/chest-x-ray-dataset/chest_xray"

# Wavelet Parameters (NEW)
USE_WAVELET = True          # Enable wavelet-enhanced architecture
WAVELET_TYPE = 'db1'        # Daubechies 1 (Haar) wavelet

# Enhanced Loss Weights for Medical Imaging
LAMBDA_CONTENT = 1.0        # Pixel-level accuracy (L1 loss)
LAMBDA_PERCEPTUAL = 0.01    # VGG perceptual features
LAMBDA_EDGE = 1.5           # Edge preservation (CRITICAL)
LAMBDA_TEXTURE = 0.3        # Texture correlation
LAMBDA_FREQUENCY = 1.0      # Frequency domain preservation (HIGH for FreqFormer)
LAMBDA_WAVELET = 0.5        # Wavelet coefficient loss (NEW - frequency domain complement)
LAMBDA_SSIM = 0.2           # Structural similarity

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {DEVICE}")
print(f"Configuration: {IMAGE_SIZE}x{IMAGE_SIZE} -> {LR_SIZE}x{LR_SIZE} -> {IMAGE_SIZE}x{IMAGE_SIZE} ({UPSCALE_FACTOR}x SR)")
print(f"FreqFormer: {len(DEPTHS)} stages, embed_dim={EMBED_DIM}, window_size={WINDOW_SIZE}")

# ============================================================================
# ENHANCED LOSS FUNCTIONS (Same as before - Medical Specific)
# ============================================================================

class EdgePreservingLoss(nn.Module):
    """Multi-scale edge preserving loss for medical images"""
    
    def __init__(self):
        super(EdgePreservingLoss, self).__init__()
        
        # Sobel operators
        self.register_buffer('sobel_x', torch.tensor([
            [-1, 0, 1], [-2, 0, 2], [-1, 0, 1]
        ], dtype=torch.float32).view(1, 1, 3, 3))
        
        self.register_buffer('sobel_y', torch.tensor([
            [-1, -2, -1], [0, 0, 0], [1, 2, 1]
        ], dtype=torch.float32).view(1, 1, 3, 3))
        
        # Laplacian operator
        self.register_buffer('laplacian', torch.tensor([
            [0, -1, 0], [-1, 4, -1], [0, -1, 0]
        ], dtype=torch.float32).view(1, 1, 3, 3))
    
    def rgb_to_grayscale(self, x):
        """Convert RGB to grayscale"""
        return 0.299 * x[:, 0:1, :, :] + 0.587 * x[:, 1:2, :, :] + 0.114 * x[:, 2:3, :, :]
    
    def gradient_loss(self, sr_img, hr_img):
        """Calculate gradient-based edge loss"""
        sr_gray = self.rgb_to_grayscale(sr_img)
        hr_gray = self.rgb_to_grayscale(hr_img)
        
        sr_grad_x = F.conv2d(sr_gray, self.sobel_x, padding=1)
        sr_grad_y = F.conv2d(sr_gray, self.sobel_y, padding=1)
        hr_grad_x = F.conv2d(hr_gray, self.sobel_x, padding=1)
        hr_grad_y = F.conv2d(hr_gray, self.sobel_y, padding=1)
        
        return F.l1_loss(sr_grad_x, hr_grad_x) + F.l1_loss(sr_grad_y, hr_grad_y)
    
    def laplacian_loss(self, sr_img, hr_img):
        """Calculate Laplacian-based edge loss"""
        sr_gray = self.rgb_to_grayscale(sr_img)
        hr_gray = self.rgb_to_grayscale(hr_img)
        
        sr_lap = F.conv2d(sr_gray, self.laplacian, padding=1)
        hr_lap = F.conv2d(hr_gray, self.laplacian, padding=1)
        
        return F.l1_loss(sr_lap, hr_lap)
    
    def multi_scale_edge_loss(self, sr_img, hr_img):
        """Calculate edge loss at multiple scales"""
        total_loss = 0
        scales = [1.0, 0.5, 0.25]
        weights = [1.0, 0.5, 0.25]
        
        for scale, weight in zip(scales, weights):
            if scale != 1.0:
                sr_scaled = F.interpolate(sr_img, scale_factor=scale, mode='bilinear', align_corners=False)
                hr_scaled = F.interpolate(hr_img, scale_factor=scale, mode='bilinear', align_corners=False)
            else:
                sr_scaled, hr_scaled = sr_img, hr_img
            
            total_loss += weight * self.gradient_loss(sr_scaled, hr_scaled)
        
        return total_loss / sum(weights)
    
    def forward(self, sr_img, hr_img):
        """Calculate combined edge loss"""
        grad_loss = self.gradient_loss(sr_img, hr_img)
        lap_loss = self.laplacian_loss(sr_img, hr_img)
        multi_scale = self.multi_scale_edge_loss(sr_img, hr_img)
        
        return 1.0 * grad_loss + 0.5 * lap_loss + 0.7 * multi_scale


class TexturePreservingLoss(nn.Module):
    """Texture correlation loss for medical image patterns"""
    
    def __init__(self):
        super(TexturePreservingLoss, self).__init__()
    
    def forward(self, sr_img, hr_img):
        """Calculate texture correlation loss"""
        kernel_size = 5
        kernel = torch.ones(1, 1, kernel_size, kernel_size, device=sr_img.device) / (kernel_size ** 2)
        
        # Convert to grayscale
        sr_gray = 0.299 * sr_img[:, 0:1] + 0.587 * sr_img[:, 1:2] + 0.114 * sr_img[:, 2:3]
        hr_gray = 0.299 * hr_img[:, 0:1] + 0.587 * hr_img[:, 1:2] + 0.114 * hr_img[:, 2:3]
        
        padding = kernel_size // 2
        
        # Calculate local variances
        sr_mean = F.conv2d(sr_gray, kernel, padding=padding)
        hr_mean = F.conv2d(hr_gray, kernel, padding=padding)
        
        sr_var = F.conv2d((sr_gray - sr_mean) ** 2, kernel, padding=padding)
        hr_var = F.conv2d((hr_gray - hr_mean) ** 2, kernel, padding=padding)
        
        return F.mse_loss(sr_var, hr_var)


class FrequencyDomainLoss(nn.Module):
    """
    Enhanced Frequency domain loss - CRITICAL for FreqFormer
    Preserves high-frequency information (edges and details)
    """
    
    def __init__(self):
        super(FrequencyDomainLoss, self).__init__()
    
    def create_frequency_masks(self, h, w, device):
        """Create low, mid, and high-pass filter masks"""
        center_h, center_w = h // 2, w // 2
        
        y, x = torch.meshgrid(
            torch.arange(h, device=device), 
            torch.arange(w, device=device),
            indexing='ij'
        )
        dist = torch.sqrt((y - center_h).float()**2 + (x - center_w).float()**2)
        
        # Define frequency bands
        low_radius = min(h, w) // 8
        mid_radius = min(h, w) // 4
        
        # Create masks
        low_mask = (dist <= low_radius).float()
        mid_mask = ((dist > low_radius) & (dist <= mid_radius)).float()
        high_mask = (dist > mid_radius).float()
        
        return low_mask, mid_mask, high_mask
    
    def forward(self, sr_img, hr_img):
        """Calculate frequency domain loss with emphasis on high frequencies"""
        # Convert to grayscale
        sr_gray = 0.299 * sr_img[:, 0:1] + 0.587 * sr_img[:, 1:2] + 0.114 * sr_img[:, 2:3]
        hr_gray = 0.299 * hr_img[:, 0:1] + 0.587 * hr_img[:, 1:2] + 0.114 * hr_img[:, 2:3]
        
        # FFT
        sr_freq = torch.fft.fft2(sr_gray)
        hr_freq = torch.fft.fft2(hr_gray)
        
        # Shift zero frequency to center
        sr_freq_shifted = torch.fft.fftshift(sr_freq)
        hr_freq_shifted = torch.fft.fftshift(hr_freq)
        
        # Get frequency masks
        h, w = sr_gray.shape[-2:]
        low_mask, mid_mask, high_mask = self.create_frequency_masks(h, w, sr_img.device)
        
        # Calculate loss for each frequency band
        sr_mag = torch.abs(sr_freq_shifted)
        hr_mag = torch.abs(hr_freq_shifted)
        
        # Higher weight on high frequencies (edges)
        low_loss = F.l1_loss(sr_mag * low_mask, hr_mag * low_mask)
        mid_loss = F.l1_loss(sr_mag * mid_mask, hr_mag * mid_mask)
        high_loss = F.l1_loss(sr_mag * high_mask, hr_mag * high_mask)
        
        # Weighted combination (emphasize high frequencies)
        return 0.2 * low_loss + 0.3 * mid_loss + 0.5 * high_loss


class SSIMLoss(nn.Module):
    """Structural Similarity Index Loss"""
    
    def __init__(self, window_size=11, size_average=True):
        super(SSIMLoss, self).__init__()
        self.window_size = window_size
        self.size_average = size_average
        self.channel = 1
        self.window = self.create_window(window_size, self.channel)
    
    def gaussian(self, window_size, sigma):
        gauss = torch.Tensor([math.exp(-(x - window_size//2)**2/float(2*sigma**2)) for x in range(window_size)])
        return gauss/gauss.sum()
    
    def create_window(self, window_size, channel):
        _1D_window = self.gaussian(window_size, 1.5).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        window = _2D_window.expand(channel, 1, window_size, window_size).contiguous()
        return window
    
    def forward(self, img1, img2):
        # Convert to grayscale
        img1_gray = 0.299 * img1[:, 0:1] + 0.587 * img1[:, 1:2] + 0.114 * img1[:, 2:3]
        img2_gray = 0.299 * img2[:, 0:1] + 0.587 * img2[:, 1:2] + 0.114 * img2[:, 2:3]
        
        if self.window.data.type() != img1_gray.data.type():
            self.window = self.window.to(img1_gray.device).type_as(img1_gray)
        
        return self._ssim(img1_gray, img2_gray, self.window, self.window_size, self.size_average)
    
    def _ssim(self, img1, img2, window, window_size, size_average=True):
        mu1 = F.conv2d(img1, window, padding=window_size//2, groups=1)
        mu2 = F.conv2d(img2, window, padding=window_size//2, groups=1)
        
        mu1_sq = mu1.pow(2)
        mu2_sq = mu2.pow(2)
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = F.conv2d(img1*img1, window, padding=window_size//2, groups=1) - mu1_sq
        sigma2_sq = F.conv2d(img2*img2, window, padding=window_size//2, groups=1) - mu2_sq
        sigma12 = F.conv2d(img1*img2, window, padding=window_size//2, groups=1) - mu1_mu2
        
        C1 = 0.01**2
        C2 = 0.03**2
        
        ssim_map = ((2*mu1_mu2 + C1)*(2*sigma12 + C2))/((mu1_sq + mu2_sq + C1)*(sigma1_sq + sigma2_sq + C2))
        
        if size_average:
            return 1 - ssim_map.mean()
        else:
            return 1 - ssim_map.mean(1).mean(1).mean(1)


# ============================================================================
# WAVELET TRANSFORM MODULE (NEW)
# ============================================================================

class FastWaveletTransform2D(nn.Module):
    """
    Fast Stationary Wavelet Transform (SWT) for FreqFormer
    Complements the frequency-aware attention with explicit wavelet decomposition
    """
    
    def __init__(self, wavelet='db1'):
        super(FastWaveletTransform2D, self).__init__()
        self.wavelet = wavelet
        
        # Haar wavelet filters (db1)
        if wavelet == 'db1':
            h0 = torch.tensor([0.7071067811865476, 0.7071067811865476])
            h1 = torch.tensor([-0.7071067811865476, 0.7071067811865476])
        else:
            h0 = torch.tensor([0.7071067811865476, 0.7071067811865476])
            h1 = torch.tensor([-0.7071067811865476, 0.7071067811865476])
        
        # Create 2D filters
        self.register_buffer('h0', h0.view(1, 1, -1, 1))
        self.register_buffer('h1', h1.view(1, 1, -1, 1))
    
    def forward(self, x):
        """
        Perform 2D SWT decomposition
        Returns: dict with LL, LH, HL, HH coefficients
        """
        batch, channels, height, width = x.shape
        
        # Process each channel separately
        coeffs = {'LL': [], 'LH': [], 'HL': [], 'HH': []}
        
        for c in range(channels):
            x_c = x[:, c:c+1, :, :]
            
            # Row-wise convolution
            x_L = F.conv2d(x_c, self.h0.repeat(1, 1, 1, 1), padding=(1, 0))[:, :, :-1, :]
            x_H = F.conv2d(x_c, self.h1.repeat(1, 1, 1, 1), padding=(1, 0))[:, :, :-1, :]
            
            # Column-wise convolution
            LL = F.conv2d(x_L, self.h0.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            LH = F.conv2d(x_L, self.h1.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            HL = F.conv2d(x_H, self.h0.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            HH = F.conv2d(x_H, self.h1.transpose(2, 3), padding=(0, 1))[:, :, :, :-1]
            
            coeffs['LL'].append(LL)
            coeffs['LH'].append(LH)
            coeffs['HL'].append(HL)
            coeffs['HH'].append(HH)
        
        # Concatenate channels
        return {
            'LL': torch.cat(coeffs['LL'], dim=1),
            'LH': torch.cat(coeffs['LH'], dim=1),
            'HL': torch.cat(coeffs['HL'], dim=1),
            'HH': torch.cat(coeffs['HH'], dim=1)
        }


class WaveletCoefficientLoss(nn.Module):
    """
    Wavelet coefficient loss for explicit edge preservation
    Complements FreqFormer's frequency-aware attention
    """
    
    def __init__(self, wavelet='db1'):
        super(WaveletCoefficientLoss, self).__init__()
        self.swt = FastWaveletTransform2D(wavelet=wavelet)
        self.l1_loss = nn.L1Loss()
        
    def forward(self, sr_img, hr_img):
        sr_coeffs = self.swt(sr_img)
        hr_coeffs = self.swt(hr_img)
        
        # Weighted combination (emphasize high-frequency details)
        wavelet_loss = (
            0.3 * self.l1_loss(sr_coeffs['LL'], hr_coeffs['LL']) +  # Lower weight on approximation
            0.25 * self.l1_loss(sr_coeffs['LH'], hr_coeffs['LH']) +  # High weight on edges
            0.25 * self.l1_loss(sr_coeffs['HL'], hr_coeffs['HL']) +
            0.2 * self.l1_loss(sr_coeffs['HH'], hr_coeffs['HH'])
        )
        
        return wavelet_loss


# ============================================================================
# FREQFORMER ARCHITECTURE COMPONENTS
# ============================================================================

class FrequencyAwareAttention(nn.Module):
    """
    Frequency-Aware Self-Attention Module
    Key innovation: Decomposes features into frequency components before attention
    """
    
    def __init__(self, dim, num_heads=8, window_size=8, qkv_bias=True):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.window_size = window_size
        head_dim = dim // num_heads
        self.scale = head_dim ** -0.5
        
        # QKV projection
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.proj = nn.Linear(dim, dim)
        
        # Frequency decomposition parameters
        self.freq_ratio = 0.5  # Ratio for high-frequency focus
        
        # Learnable temperature for frequency attention
        self.temperature = nn.Parameter(torch.ones(num_heads, 1, 1))
    
    def frequency_decomposition(self, x):
        """
        Decompose input into low and high frequency components
        Input: (B, N, C)
        """
        B, N, C = x.shape
        H = W = int(math.sqrt(N))
        
        # Reshape to spatial
        x_spatial = x.reshape(B, H, W, C).permute(0, 3, 1, 2)
        
        # FFT
        x_freq = torch.fft.fft2(x_spatial, dim=(-2, -1))
        x_freq = torch.fft.fftshift(x_freq, dim=(-2, -1))
        
        # Create frequency mask
        center_h, center_w = H // 2, W // 2
        radius = int(min(H, W) * self.freq_ratio / 2)
        
        y, x_coords = torch.meshgrid(
            torch.arange(H, device=x.device),
            torch.arange(W, device=x.device),
            indexing='ij'
        )
        dist = torch.sqrt((y - center_h).float()**2 + (x_coords - center_w).float()**2)
        
        # Masks
        low_mask = (dist <= radius).float().unsqueeze(0).unsqueeze(0)
        high_mask = (dist > radius).float().unsqueeze(0).unsqueeze(0)
        
        # Separate frequency components
        x_freq_low = x_freq * low_mask
        x_freq_high = x_freq * high_mask
        
        # Inverse FFT
        x_low = torch.fft.ifftshift(x_freq_low, dim=(-2, -1))
        x_low = torch.fft.ifft2(x_low, dim=(-2, -1)).real
        
        x_high = torch.fft.ifftshift(x_freq_high, dim=(-2, -1))
        x_high = torch.fft.ifft2(x_high, dim=(-2, -1)).real
        
        # Reshape back
        x_low = x_low.permute(0, 2, 3, 1).reshape(B, N, C)
        x_high = x_high.permute(0, 2, 3, 1).reshape(B, N, C)
        
        return x_low, x_high
    
    def forward(self, x):
        """
        Input: (B, N, C) where N = H * W
        """
        B, N, C = x.shape
        
        # Frequency decomposition
        x_low, x_high = self.frequency_decomposition(x)
        
        # QKV for high-frequency (more important for edges)
        qkv_high = self.qkv(x_high).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q_high, k_high, v_high = qkv_high[0], qkv_high[1], qkv_high[2]
        
        # Attention with temperature scaling
        attn_high = (q_high @ k_high.transpose(-2, -1)) * self.scale * self.temperature
        attn_high = attn_high.softmax(dim=-1)
        
        # Apply attention
        x_high_out = (attn_high @ v_high).transpose(1, 2).reshape(B, N, C)
        
        # QKV for low-frequency
        qkv_low = self.qkv(x_low).reshape(B, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q_low, k_low, v_low = qkv_low[0], qkv_low[1], qkv_low[2]
        
        attn_low = (q_low @ k_low.transpose(-2, -1)) * self.scale
        attn_low = attn_low.softmax(dim=-1)
        
        x_low_out = (attn_low @ v_low).transpose(1, 2).reshape(B, N, C)
        
        # Combine frequency components (emphasize high-frequency for edges)
        x_out = 0.4 * x_low_out + 0.6 * x_high_out
        
        # Final projection
        x_out = self.proj(x_out)
        
        return x_out


class WindowAttention(nn.Module):
    """
    Window-based Multi-head Self-Attention with relative position bias
    """
    
    def __init__(self, dim, window_size, num_heads, qkv_bias=True):
        super().__init__()
        self.dim = dim
        self.window_size = window_size
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** -0.5
        
        # Relative position bias
        self.relative_position_bias_table = nn.Parameter(
            torch.zeros((2 * window_size - 1) * (2 * window_size - 1), num_heads)
        )
        
        # Get pair-wise relative position index
        coords_h = torch.arange(self.window_size)
        coords_w = torch.arange(self.window_size)
        coords = torch.stack(torch.meshgrid([coords_h, coords_w], indexing='ij'))
        coords_flatten = torch.flatten(coords, 1)
        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
        relative_coords = relative_coords.permute(1, 2, 0).contiguous()
        relative_coords[:, :, 0] += self.window_size - 1
        relative_coords[:, :, 1] += self.window_size - 1
        relative_coords[:, :, 0] *= 2 * self.window_size - 1
        relative_position_index = relative_coords.sum(-1)
        self.register_buffer("relative_position_index", relative_position_index)
        
        self.qkv = nn.Linear(dim, dim * 3, bias=qkv_bias)
        self.proj = nn.Linear(dim, dim)
        
        nn.init.trunc_normal_(self.relative_position_bias_table, std=.02)
    
    def forward(self, x):
        B_, N, C = x.shape
        qkv = self.qkv(x).reshape(B_, N, 3, self.num_heads, C // self.num_heads).permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        q = q * self.scale
        attn = (q @ k.transpose(-2, -1))
        
        relative_position_bias = self.relative_position_bias_table[self.relative_position_index.view(-1)].view(
            self.window_size * self.window_size, self.window_size * self.window_size, -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous()
        attn = attn + relative_position_bias.unsqueeze(0)
        
        attn = attn.softmax(dim=-1)
        
        x = (attn @ v).transpose(1, 2).reshape(B_, N, C)
        x = self.proj(x)
        return x


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


class FreqFormerBlock(nn.Module):
    """
    FreqFormer Transformer Block
    Combines frequency-aware attention with window-based attention
    """
    
    def __init__(self, dim, num_heads, window_size=8, mlp_ratio=2.0, drop=0.):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.window_size = window_size
        self.mlp_ratio = mlp_ratio
        
        # Layer norm
        self.norm1 = nn.LayerNorm(dim)
        
        # Frequency-aware attention
        self.freq_attn = FrequencyAwareAttention(dim, num_heads, window_size)
        
        # Window attention
        self.window_attn = WindowAttention(dim, window_size, num_heads)
        
        # MLP
        self.norm2 = nn.LayerNorm(dim)
        mlp_hidden_dim = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_hidden_dim),
            nn.GELU(),
            nn.Dropout(drop),
            nn.Linear(mlp_hidden_dim, dim),
            nn.Dropout(drop)
        )
        
        # Learnable mixing weight
        self.alpha = nn.Parameter(torch.ones(1) * 0.5)
    
    def forward(self, x):
        """
        Input: (B, C, H, W)
        """
        B, C, H, W = x.shape
        
        # Reshape for attention
        x = x.flatten(2).transpose(1, 2)  # (B, H*W, C)
        
        # Residual connection
        shortcut = x
        x = self.norm1(x)
        
        # Frequency-aware attention on full resolution
        x_freq = self.freq_attn(x)
        
        # Window-based attention
        x_spatial = x.reshape(B, H, W, C)
        
        # Partition windows
        x_windows = window_partition(x_spatial, self.window_size)  # (B*num_windows, window_size, window_size, C)
        x_windows = x_windows.view(-1, self.window_size * self.window_size, C)  # (B*num_windows, window_size*window_size, C)
        
        # Window attention
        x_windows = self.window_attn(x_windows)
        
        # Reverse windows
        x_windows = x_windows.view(-1, self.window_size, self.window_size, C)
        x_win = window_reverse(x_windows, self.window_size, H, W)  # (B, H, W, C)
        x_win = x_win.view(B, H * W, C)
        
        # Mix frequency and spatial attention
        x = self.alpha * x_freq + (1 - self.alpha) * x_win
        x = shortcut + x
        
        # MLP
        x = x + self.mlp(self.norm2(x))
        
        # Reshape back
        x = x.transpose(1, 2).reshape(B, C, H, W)
        
        return x


class PatchEmbed(nn.Module):
    """Image to Patch Embedding"""
    
    def __init__(self, img_size=32, patch_size=1, in_chans=3, embed_dim=64):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.num_patches = (img_size // patch_size) ** 2
        
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)
    
    def forward(self, x):
        B, C, H, W = x.shape
        x = self.proj(x)
        return x


class PatchUnEmbed(nn.Module):
    """Patch Embedding to Image"""
    
    def __init__(self, img_size=32, patch_size=1, embed_dim=64, out_chans=3):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        
        self.proj = nn.Conv2d(embed_dim, out_chans, kernel_size=1)
    
    def forward(self, x):
        return self.proj(x)


class FreqFormer(nn.Module):
    """
    FreqFormer: Frequency-aware Transformer for Image Super-Resolution
    
    Key features:
    - Frequency-aware attention for edge preservation
    - Window-based attention for efficiency
    - Multi-stage architecture with skip connections
    - Pixel shuffle upsampling
    """
    
    def __init__(
        self,
        img_size=32,
        patch_size=1,
        in_chans=3,
        embed_dim=64,
        depths=[6, 6, 6, 6],
        num_heads=[2, 2, 2, 2],
        window_size=8,
        mlp_ratio=2.0,
        upscale=4,
        img_range=1.0,
        upsampler='pixelshuffle'
    ):
        super(FreqFormer, self).__init__()
        
        self.img_range = img_range
        self.mean = torch.Tensor([0.5, 0.5, 0.5]).view(1, 3, 1, 1)
        self.upscale = upscale
        self.window_size = window_size
        
        # Shallow feature extraction
        self.conv_first = nn.Conv2d(in_chans, embed_dim, 3, 1, 1)
        
        # Patch embedding
        self.patch_embed = PatchEmbed(
            img_size=img_size, 
            patch_size=patch_size, 
            in_chans=embed_dim, 
            embed_dim=embed_dim
        )
        
        # Transformer stages
        self.stages = nn.ModuleList()
        for i_stage in range(len(depths)):
            stage = nn.Sequential(*[
                FreqFormerBlock(
                    dim=embed_dim,
                    num_heads=num_heads[i_stage],
                    window_size=window_size,
                    mlp_ratio=mlp_ratio
                ) for _ in range(depths[i_stage])
            ])
            self.stages.append(stage)
        
        # Feature fusion
        self.conv_after_body = nn.Conv2d(embed_dim, embed_dim, 3, 1, 1)
        
        # Upsampling
        if upsampler == 'pixelshuffle':
            self.upsampler = nn.Sequential(
                nn.Conv2d(embed_dim, embed_dim * 4, 3, 1, 1),
                nn.PixelShuffle(2),
                nn.PReLU(),
                nn.Conv2d(embed_dim, embed_dim * 4, 3, 1, 1),
                nn.PixelShuffle(2),
                nn.PReLU()
            )
        
        # Final reconstruction
        self.conv_last = nn.Conv2d(embed_dim, in_chans, 3, 1, 1)
        
        self.apply(self._init_weights)
    
    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.trunc_normal_(m.weight, std=.02)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.Conv2d):
            nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)
    
    def forward_features(self, x):
        """Forward through transformer blocks"""
        for stage in self.stages:
            x = stage(x)
        return x
    
    def forward(self, x):
        """
        Input: (B, 3, 32, 32) LR image
        Output: (B, 3, 128, 128) SR image
        """
        # Normalize
        self.mean = self.mean.type_as(x)
        x = (x - self.mean) * self.img_range
        
        # Shallow feature extraction
        x = self.conv_first(x)
        x_residual = x
        
        # Deep feature extraction with transformers
        x = self.forward_features(x)
        
        # Feature fusion with residual
        x = self.conv_after_body(x) + x_residual
        
        # Upsampling
        x = self.upsampler(x)
        
        # Reconstruction
        x = self.conv_last(x)
        
        # Denormalize
        x = x / self.img_range + self.mean
        
        return x


# ============================================================================
# FEATURE EXTRACTOR (VGG-based) - Same as before
# ============================================================================

class FeatureExtractor(nn.Module):
    """VGG-based feature extractor for perceptual loss"""
    
    def __init__(self):
        super(FeatureExtractor, self).__init__()
        vgg = vgg19(pretrained=True)
        
        self.feature_extractor_shallow = nn.Sequential(*list(vgg.features.children())[:9])
        self.feature_extractor_mid = nn.Sequential(*list(vgg.features.children())[:18])
        self.feature_extractor_deep = nn.Sequential(*list(vgg.features.children())[:27])
        
        for param in self.parameters():
            param.requires_grad = False
    
    def forward(self, x):
        shallow = self.feature_extractor_shallow(x)
        mid = self.feature_extractor_mid(x)
        deep = self.feature_extractor_deep(x)
        return shallow, mid, deep


# ============================================================================
# DATASET CLASS (Same as before)
# ============================================================================

class MedicalSRDataset(Dataset):
    """Enhanced dataset class for medical super-resolution"""
    
    def __init__(self, hr_dir, hr_size=IMAGE_SIZE, lr_size=LR_SIZE, augment=True):
        self.hr_dir = hr_dir
        self.hr_size = hr_size
        self.lr_size = lr_size
        self.augment = augment
        
        self.image_files = [
            f for f in os.listdir(hr_dir) 
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]
        
        print(f"Found {len(self.image_files)} images in {hr_dir}")
        
        if augment:
            self.augment_transform = transforms.Compose([
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=5),
                transforms.ColorJitter(brightness=0.1, contrast=0.1),
            ])
        
        self.hr_transform = transforms.Compose([
            transforms.Resize((hr_size, hr_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        
        self.lr_transform = transforms.Compose([
            transforms.Resize((lr_size, lr_size), interpolation=Image.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        img_path = os.path.join(self.hr_dir, self.image_files[idx])
        hr_img = Image.open(img_path).convert('RGB')
        
        if self.augment and hasattr(self, 'augment_transform'):
            hr_img = self.augment_transform(hr_img)
        
        lr_img = hr_img.resize((self.lr_size, self.lr_size), Image.BICUBIC)
        
        hr_img = self.hr_transform(hr_img)
        lr_img = self.lr_transform(lr_img)
        
        return lr_img, hr_img


# ============================================================================
# EDGE QUALITY METRICS (Same as before)
# ============================================================================

class EdgeQualityMetrics:
    """Comprehensive edge quality metrics for evaluating super-resolution"""
    
    @staticmethod
    def denormalize_image(img_tensor):
        return (img_tensor + 1) / 2
    
    @staticmethod
    def tensor_to_numpy(img_tensor):
        img = EdgeQualityMetrics.denormalize_image(img_tensor)
        img = img.cpu().numpy().transpose(1, 2, 0)
        img = (img * 255).astype(np.uint8)
        
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        return img
    
    @staticmethod
    def edge_preservation_index(sr_img, hr_img):
        sr_np = EdgeQualityMetrics.tensor_to_numpy(sr_img)
        hr_np = EdgeQualityMetrics.tensor_to_numpy(hr_img)
        
        sr_edges = cv2.Canny(sr_np, 100, 200)
        hr_edges = cv2.Canny(hr_np, 100, 200)
        
        intersection = np.logical_and(sr_edges, hr_edges).sum()
        union = np.logical_or(sr_edges, hr_edges).sum()
        
        if union == 0:
            return 1.0
        
        return intersection / union
    
    @staticmethod
    def gradient_magnitude_similarity(sr_img, hr_img):
        sr_np = EdgeQualityMetrics.tensor_to_numpy(sr_img)
        hr_np = EdgeQualityMetrics.tensor_to_numpy(hr_img)
        
        sr_gx = cv2.Sobel(sr_np, cv2.CV_64F, 1, 0, ksize=3)
        sr_gy = cv2.Sobel(sr_np, cv2.CV_64F, 0, 1, ksize=3)
        sr_grad = np.sqrt(sr_gx**2 + sr_gy**2)
        
        hr_gx = cv2.Sobel(hr_np, cv2.CV_64F, 1, 0, ksize=3)
        hr_gy = cv2.Sobel(hr_np, cv2.CV_64F, 0, 1, ksize=3)
        hr_grad = np.sqrt(hr_gx**2 + hr_gy**2)
        
        C = 170
        gms = (2 * sr_grad * hr_grad + C) / (sr_grad**2 + hr_grad**2 + C)
        gmsd = np.std(gms)
        
        return gmsd
    
    @staticmethod
    def edge_sharpness_measure(img_tensor):
        img_np = EdgeQualityMetrics.tensor_to_numpy(img_tensor)
        laplacian = cv2.Laplacian(img_np, cv2.CV_64F)
        return laplacian.var()
    
    @staticmethod
    def calculate_all_metrics(sr_img, hr_img):
        epi = EdgeQualityMetrics.edge_preservation_index(sr_img, hr_img)
        gmsd = EdgeQualityMetrics.gradient_magnitude_similarity(sr_img, hr_img)
        sr_sharpness = EdgeQualityMetrics.edge_sharpness_measure(sr_img)
        hr_sharpness = EdgeQualityMetrics.edge_sharpness_measure(hr_img)
        sharpness_ratio = sr_sharpness / (hr_sharpness + 1e-8)
        
        return {
            'epi': epi,
            'gmsd': gmsd,
            'sr_sharpness': sr_sharpness,
            'hr_sharpness': hr_sharpness,
            'sharpness_ratio': sharpness_ratio
        }


# ============================================================================
# DATA PREPARATION
# ============================================================================

def prepare_medical_data(dataset_path, hr_size=IMAGE_SIZE, lr_size=LR_SIZE, batch_size=BATCH_SIZE):
    """Prepare data loaders for medical imaging"""
    
    hr_train_dir = os.path.join(dataset_path, 'train', 'NORMAL')
    
    if not os.path.exists(hr_train_dir):
        raise ValueError(f"Dataset path not found: {hr_train_dir}")
    
    full_dataset = MedicalSRDataset(
        hr_dir=hr_train_dir, 
        hr_size=hr_size,
        lr_size=lr_size,
        augment=True
    )
    
    train_size = int(0.85 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, 
        [train_size, val_size], 
        generator=torch.Generator().manual_seed(42)
    )
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=2, 
        pin_memory=True, 
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=2, 
        pin_memory=True
    )
    
    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    
    return train_loader, val_loader


# ============================================================================
# TRAINING FUNCTION
# ============================================================================

def train_freqformer(model, feature_extractor, train_loader, val_loader, num_epochs=EPOCHS):
    """
    Train FreqFormer model with comprehensive loss functions
    """
    
    model.to(DEVICE)
    feature_extractor.to(DEVICE)
    
    print(f"\n{'='*60}")
    print(f"Starting FreqFormer Training")
    print(f"{'='*60}")
    print(f"Device: {DEVICE}")
    print(f"Epochs: {num_epochs}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Learning rate: {LR}")
    print(f"{'='*60}\n")
    
    # Loss functions
    content_criterion = nn.L1Loss().to(DEVICE)
    edge_loss = EdgePreservingLoss().to(DEVICE)
    texture_loss = TexturePreservingLoss().to(DEVICE)
    frequency_loss = FrequencyDomainLoss().to(DEVICE)
    wavelet_loss_fn = WaveletCoefficientLoss(wavelet=WAVELET_TYPE).to(DEVICE)  # NEW
    ssim_loss = SSIMLoss().to(DEVICE)
    
    # Optimizer
    optimizer = optim.AdamW(model.parameters(), lr=LR, betas=(BETA1, BETA2), weight_decay=1e-4)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=1e-6)
    
    # Training history
    history = {
        'losses': [], 'content_losses': [], 'perceptual_losses': [],
        'edge_losses': [], 'texture_losses': [], 'frequency_losses': [], 
        'wavelet_losses': [],  # NEW
        'ssim_losses': [],
        'val_psnr': [], 'val_ssim': [], 'val_epi': [], 'val_gmsd': []
    }
    
    best_psnr = 0
    best_epi = 0
    patience = 0
    max_patience = 20
    
    for epoch in range(num_epochs):
        model.train()
        
        running_loss = 0.0
        running_content = 0.0
        running_perceptual = 0.0
        running_edge = 0.0
        running_texture = 0.0
        running_frequency = 0.0
        running_wavelet = 0.0  # NEW
        running_ssim = 0.0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs}")
        
        for lr_imgs, hr_imgs in pbar:
            lr_imgs, hr_imgs = lr_imgs.to(DEVICE), hr_imgs.to(DEVICE)
            
            optimizer.zero_grad()
            
            # Forward pass
            sr_imgs = model(lr_imgs)
            
            # 1. Content loss (L1)
            loss_content = content_criterion(sr_imgs, hr_imgs)
            
            # 2. Perceptual loss
            shallow_sr, mid_sr, deep_sr = feature_extractor(sr_imgs)
            shallow_hr, mid_hr, deep_hr = feature_extractor(hr_imgs)
            
            loss_perceptual = (
                content_criterion(shallow_sr, shallow_hr) + 
                content_criterion(mid_sr, mid_hr) + 
                content_criterion(deep_sr, deep_hr)
            ) / 3
            
            # 3. Edge preservation loss
            loss_edge = edge_loss(sr_imgs, hr_imgs)
            
            # 4. Texture loss
            loss_texture = texture_loss(sr_imgs, hr_imgs)
            
            # 5. Frequency domain loss
            loss_frequency = frequency_loss(sr_imgs, hr_imgs)
            
            # 6. Wavelet coefficient loss (NEW - complement to frequency loss)
            loss_wavelet = wavelet_loss_fn(sr_imgs, hr_imgs)
            
            # 7. SSIM loss
            loss_ssim = ssim_loss(sr_imgs, hr_imgs)
            
            # Total loss
            total_loss = (
                LAMBDA_CONTENT * loss_content + 
                LAMBDA_PERCEPTUAL * loss_perceptual + 
                LAMBDA_EDGE * loss_edge + 
                LAMBDA_TEXTURE * loss_texture +
                LAMBDA_FREQUENCY * loss_frequency +
                LAMBDA_WAVELET * loss_wavelet +  # NEW
                LAMBDA_SSIM * loss_ssim
            )
            
            total_loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            # Update running losses
            running_loss += total_loss.item()
            running_content += loss_content.item()
            running_perceptual += loss_perceptual.item()
            running_edge += loss_edge.item()
            running_texture += loss_texture.item()
            running_frequency += loss_frequency.item()
            running_wavelet += loss_wavelet.item()  # NEW
            running_ssim += loss_ssim.item()
            
            pbar.set_postfix({
                'Loss': f"{total_loss.item():.4f}",
                'Edge': f"{loss_edge.item():.4f}",
                'Freq': f"{loss_frequency.item():.4f}",
                'Wav': f"{loss_wavelet.item():.4f}"  # NEW
            })
        
        scheduler.step()
        
        # Epoch averages
        epoch_loss = running_loss / len(train_loader)
        epoch_content = running_content / len(train_loader)
        epoch_perceptual = running_perceptual / len(train_loader)
        epoch_edge = running_edge / len(train_loader)
        epoch_texture = running_texture / len(train_loader)
        epoch_frequency = running_frequency / len(train_loader)
        epoch_wavelet = running_wavelet / len(train_loader)  # NEW
        epoch_ssim = running_ssim / len(train_loader)
        
        history['losses'].append(epoch_loss)
        history['content_losses'].append(epoch_content)
        history['perceptual_losses'].append(epoch_perceptual)
        history['edge_losses'].append(epoch_edge)
        history['texture_losses'].append(epoch_texture)
        history['frequency_losses'].append(epoch_frequency)
        history['wavelet_losses'].append(epoch_wavelet)  # NEW
        history['ssim_losses'].append(epoch_ssim)
        
        # Validation
        val_metrics = evaluate_enhanced_metrics(model, val_loader)
        
        history['val_psnr'].append(val_metrics['psnr'])
        history['val_ssim'].append(val_metrics['ssim'])
        history['val_epi'].append(val_metrics['epi'])
        history['val_gmsd'].append(val_metrics['gmsd'])
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Epoch {epoch+1}/{num_epochs} Summary")
        print(f"{'='*60}")
        print(f"Total Loss:        {epoch_loss:.4f}")
        print(f"  - Content:       {epoch_content:.4f}")
        print(f"  - Perceptual:    {epoch_perceptual:.4f}")
        print(f"  - Edge:          {epoch_edge:.4f}")
        print(f"  - Texture:       {epoch_texture:.4f}")
        print(f"  - Frequency:     {epoch_frequency:.4f}")
        print(f"  - Wavelet:       {epoch_wavelet:.4f}  (NEW)")
        print(f"  - SSIM:          {epoch_ssim:.4f}")
        print(f"Validation:")
        print(f"  - PSNR:          {val_metrics['psnr']:.2f} dB")
        print(f"  - SSIM:          {val_metrics['ssim']:.4f}")
        print(f"  - EPI:           {val_metrics['epi']:.4f}")
        print(f"  - GMSD:          {val_metrics['gmsd']:.4f}")
        print(f"{'='*60}\n")
        
        # Save best model
        combined_score = val_metrics['psnr'] + val_metrics['epi'] * 10
        best_combined = best_psnr + best_epi * 10
        
        if combined_score > best_combined:
            best_psnr = val_metrics['psnr']
            best_epi = val_metrics['epi']
            patience = 0
            
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'psnr': val_metrics['psnr'],
                'ssim': val_metrics['ssim'],
                'epi': val_metrics['epi'],
                'gmsd': val_metrics['gmsd'],
                'history': history
            }
            
            torch.save(checkpoint, 'wavelet_freqformer_best_model.pth')
            print(f"✅ Saved best model! PSNR: {best_psnr:.2f} dB | EPI: {best_epi:.4f}\n")
        else:
            patience += 1
            print(f"Patience: {patience}/{max_patience}\n")
        
        if patience >= max_patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
        
        if (epoch + 1) % 10 == 0:
            visualize_training_progress(model, val_loader, epoch+1)
    
    return history


def evaluate_enhanced_metrics(model, dataloader, max_batches=10):
    """Enhanced evaluation with edge metrics"""
    model.eval()
    
    psnr_values = []
    ssim_values = []
    epi_values = []
    gmsd_values = []
    
    with torch.no_grad():
        for batch_idx, (lr_imgs, hr_imgs) in enumerate(dataloader):
            if batch_idx >= max_batches:
                break
                
            lr_imgs, hr_imgs = lr_imgs.to(DEVICE), hr_imgs.to(DEVICE)
            sr_imgs = model(lr_imgs)
            
            for i in range(sr_imgs.size(0)):
                sr = sr_imgs[i]
                hr = hr_imgs[i]
                
                sr_np = (sr.cpu().numpy().transpose(1, 2, 0) + 1) / 2
                hr_np = (hr.cpu().numpy().transpose(1, 2, 0) + 1) / 2
                
                sr_np = np.clip(sr_np, 0, 1)
                hr_np = np.clip(hr_np, 0, 1)
                
                psnr_value = psnr(hr_np, sr_np, data_range=1.0)
                ssim_value = ssim(hr_np, sr_np, data_range=1.0, win_size=3, channel_axis=2)
                
                edge_metrics = EdgeQualityMetrics.calculate_all_metrics(sr, hr)
                
                psnr_values.append(psnr_value)
                ssim_values.append(ssim_value)
                epi_values.append(edge_metrics['epi'])
                gmsd_values.append(edge_metrics['gmsd'])
    
    return {
        'psnr': np.mean(psnr_values),
        'ssim': np.mean(ssim_values),
        'epi': np.mean(epi_values),
        'gmsd': np.mean(gmsd_values)
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def visualize_training_progress(model, dataloader, epoch):
    """Visualize training progress"""
    model.eval()
    
    with torch.no_grad():
        lr_imgs, hr_imgs = next(iter(dataloader))
        lr_imgs, hr_imgs = lr_imgs.to(DEVICE), hr_imgs.to(DEVICE)
        sr_imgs = model(lr_imgs)
        
        num_samples = min(4, lr_imgs.size(0))
        
        fig, axes = plt.subplots(num_samples, 5, figsize=(20, num_samples * 4))
        
        for i in range(num_samples):
            lr = (lr_imgs[i].cpu().numpy().transpose(1, 2, 0) + 1) / 2
            sr = (sr_imgs[i].cpu().numpy().transpose(1, 2, 0) + 1) / 2
            hr = (hr_imgs[i].cpu().numpy().transpose(1, 2, 0) + 1) / 2
            
            lr = np.clip(lr, 0, 1)
            sr = np.clip(sr, 0, 1)
            hr = np.clip(hr, 0, 1)
            
            sr_uint8 = (sr * 255).astype(np.uint8)
            hr_uint8 = (hr * 255).astype(np.uint8)
            
            sr_gray = cv2.cvtColor(sr_uint8, cv2.COLOR_RGB2GRAY)
            hr_gray = cv2.cvtColor(hr_uint8, cv2.COLOR_RGB2GRAY)
            sr_edges = cv2.Canny(sr_gray, 100, 200)
            hr_edges = cv2.Canny(hr_gray, 100, 200)
            
            axes[i, 0].imshow(lr)
            axes[i, 0].set_title(f'LR Input ({LR_SIZE}x{LR_SIZE})')
            axes[i, 0].axis('off')
            
            axes[i, 1].imshow(sr)
            axes[i, 1].set_title('FreqFormer Output')
            axes[i, 1].axis('off')
            
            axes[i, 2].imshow(hr)
            axes[i, 2].set_title('HR Ground Truth')
            axes[i, 2].axis('off')
            
            axes[i, 3].imshow(sr_edges, cmap='gray')
            axes[i, 3].set_title('SR Edges')
            axes[i, 3].axis('off')
            
            axes[i, 4].imshow(hr_edges, cmap='gray')
            axes[i, 4].set_title('Target Edges')
            axes[i, 4].axis('off')
        
        plt.tight_layout()
        plt.savefig(f'wavelet_freqformer_progress_epoch_{epoch}.png', dpi=150, bbox_inches='tight')
        plt.close()


def plot_training_history(history):
    """Plot comprehensive training history for Wavelet-Enhanced FreqFormer"""
    
    fig, axes = plt.subplots(2, 4, figsize=(24, 12))
    
    epochs = range(1, len(history['losses']) + 1)
    
    # Total loss
    axes[0, 0].plot(epochs, history['losses'], 'b-', linewidth=2)
    axes[0, 0].set_title('Total Training Loss', fontweight='bold')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Component losses (main)
    axes[0, 1].plot(epochs, history['edge_losses'], label='Edge', linewidth=2)
    axes[0, 1].plot(epochs, history['frequency_losses'], label='Frequency (FFT)', linewidth=2)
    axes[0, 1].plot(epochs, history['wavelet_losses'], label='Wavelet (NEW)', linewidth=2, linestyle='--')
    axes[0, 1].plot(epochs, history['content_losses'], label='Content', linewidth=2)
    axes[0, 1].set_title('Component Losses', fontweight='bold')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Loss')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Frequency domain losses (zoomed)
    axes[0, 2].plot(epochs, history['frequency_losses'], label='FFT-based', linewidth=2, color='blue')
    axes[0, 2].plot(epochs, history['wavelet_losses'], label='Wavelet-based', linewidth=2, color='purple')
    axes[0, 2].set_title('Dual Frequency Processing (NEW)', fontweight='bold')
    axes[0, 2].set_xlabel('Epoch')
    axes[0, 2].set_ylabel('Loss')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)
    
    # PSNR
    axes[0, 3].plot(epochs, history['val_psnr'], 'g-', linewidth=2, marker='o', markersize=3)
    axes[0, 3].set_title('Validation PSNR', fontweight='bold')
    axes[0, 3].set_xlabel('Epoch')
    axes[0, 3].set_ylabel('PSNR (dB)')
    axes[0, 3].grid(True, alpha=0.3)
    
    # SSIM
    axes[1, 0].plot(epochs, history['val_ssim'], 'm-', linewidth=2, marker='s', markersize=3)
    axes[1, 0].set_title('Validation SSIM', fontweight='bold')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('SSIM')
    axes[1, 0].grid(True, alpha=0.3)
    
    # EPI
    axes[1, 1].plot(epochs, history['val_epi'], 'c-', linewidth=2, marker='^', markersize=3)
    axes[1, 1].set_title('Edge Preservation Index', fontweight='bold')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('EPI')
    axes[1, 1].grid(True, alpha=0.3)
    
    # GMSD
    axes[1, 2].plot(epochs, history['val_gmsd'], 'orange', linewidth=2, marker='d', markersize=3)
    axes[1, 2].set_title('Gradient Magnitude Similarity', fontweight='bold')
    axes[1, 2].set_xlabel('Epoch')
    axes[1, 2].set_ylabel('GMSD (Lower=Better)')
    axes[1, 2].grid(True, alpha=0.3)
    
    # Summary text
    axes[1, 3].axis('off')
    best_psnr = max(history['val_psnr'])
    best_ssim = max(history['val_ssim'])
    best_epi = max(history['val_epi'])
    summary_text = f"""
    WAVELET-ENHANCED FREQFORMER
    
    Best Validation Metrics:
    • PSNR: {best_psnr:.2f} dB
    • SSIM: {best_ssim:.4f}
    • EPI: {best_epi:.4f}
    
    Total Epochs: {len(epochs)}
    
    Key Features:
    ✓ Frequency-Aware Attention
    ✓ FFT-based Frequency Loss
    ✓ Wavelet Coefficient Loss
    ✓ Dual Frequency Processing
    ✓ Multi-scale Edge Detection
    ✓ Window-based Transformers
    """
    axes[1, 3].text(0.1, 0.9, summary_text, transform=axes[1, 3].transAxes,
                    fontsize=11, verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.suptitle('Wavelet-Enhanced FreqFormer Training History', fontsize=18, fontweight='bold')
    plt.tight_layout()
    plt.savefig('wavelet_freqformer_training_history.png', dpi=300, bbox_inches='tight')
    plt.show()


# ============================================================================
# PATHOLOGICAL INVARIANCE VALIDATOR (Same structure as before)
# ============================================================================

class PathologicalInvarianceValidator:
    """Tests pathological invariance using TorchXRayVision"""
    
    def __init__(self, sr_model, device):
        self.sr_model = sr_model
        self.device = device
        
        print("Loading TorchXRayVision classifier...")
        self.classifier = xrv.models.DenseNet(weights="densenet121-res224-all")
        self.classifier.to(device)
        self.classifier.eval()
        
        self.pathologies = self.classifier.pathologies
        print(f"Loaded classifier for pathologies: {self.pathologies}")
    
    def preprocess_for_classifier(self, image_tensor):
        """Preprocess for XRV classifier"""
        # Convert from [-1, 1] to [0, 255] with clipping
        image = (image_tensor + 1) * 127.5
        image = torch.clamp(image, 0, 255)  # ADD THIS LINE - clip to valid range
        
        if image.shape[1] == 3:
            image = 0.299 * image[:, 0:1] + 0.587 * image[:, 1:2] + 0.114 * image[:, 2:3]
        
        processed_images = []
        for i in range(image.shape[0]):
            img = image[i].cpu().numpy().astype(np.float32)
            
            img_processed = xrv.datasets.XRayCenterCrop()(img)
            img_processed = xrv.datasets.XRayResizer(224)(img_processed)
            img_processed = xrv.datasets.normalize(img_processed, maxval=255, reshape=False)
            
            processed_images.append(torch.from_numpy(img_processed))
        
        return torch.stack(processed_images).float().to(self.device)
        
    def get_predictions(self, images):
        """Get classifier predictions"""
        with torch.no_grad():
            processed_images = self.preprocess_for_classifier(images)
            outputs = self.classifier(processed_images)
            predictions = torch.sigmoid(outputs)
        return predictions
    
    def test_pathological_invariance(self, test_loader, pneumonia_threshold=0.5, max_batches=None):
        """Test pathological invariance on test dataset"""
        print("\n" + "="*60)
        print("TESTING PATHOLOGICAL INVARIANCE")
        print("="*60)
        
        self.sr_model.eval()
        
        original_predictions = []
        sr_predictions = []
        all_original_probs = []
        all_sr_probs = []
        batch_count = 0
        
        with torch.no_grad():
            for lr_imgs, hr_imgs in tqdm(test_loader, desc="Processing batches"):
                if max_batches and batch_count >= max_batches:
                    break
                
                lr_imgs = lr_imgs.to(self.device)
                hr_imgs = hr_imgs.to(self.device)
                
                sr_imgs = self.sr_model(lr_imgs)
                
                original_preds = self.get_predictions(hr_imgs)
                sr_preds = self.get_predictions(sr_imgs)
                
                pneumonia_idx = self.pathologies.index('Pneumonia')
                
                orig_pneumonia_probs = original_preds[:, pneumonia_idx].cpu().numpy()
                sr_pneumonia_probs = sr_preds[:, pneumonia_idx].cpu().numpy()
                
                all_original_probs.extend(orig_pneumonia_probs)
                all_sr_probs.extend(sr_pneumonia_probs)
                
                orig_binary = (orig_pneumonia_probs > pneumonia_threshold).astype(int)
                sr_binary = (sr_pneumonia_probs > pneumonia_threshold).astype(int)
                
                original_predictions.extend(orig_binary)
                sr_predictions.extend(sr_binary)
                
                batch_count += 1
        
        original_predictions = np.array(original_predictions)
        sr_predictions = np.array(sr_predictions)
        all_original_probs = np.array(all_original_probs)
        all_sr_probs = np.array(all_sr_probs)
        
        # Calculate metrics
        agreement = accuracy_score(original_predictions, sr_predictions)
        prob_correlation = np.corrcoef(all_original_probs, all_sr_probs)[0, 1]
        
        print(f"\nAgreement Rate: {agreement:.1%}")
        print(f"Probability Correlation: {prob_correlation:.4f}")
        
        if agreement > 0.90:
            print("✅ EXCELLENT pathological invariance!")
        elif agreement > 0.85:
            print("✅ GOOD pathological invariance")
        else:
            print("⚠️  MODERATE pathological invariance")
        
        print("="*60 + "\n")
        
        return {
            'agreement_rate': agreement,
            'probability_correlation': prob_correlation
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    print("\n" + "="*60)
    print("WAVELET-ENHANCED FREQFORMER")
    print("Dual Frequency Processing for Medical Chest X-Ray SR")
    print("="*60)
    print(f"Device: {DEVICE}")
    print(f"Configuration: {LR_SIZE}x{LR_SIZE} -> {IMAGE_SIZE}x{IMAGE_SIZE} ({UPSCALE_FACTOR}x)")
    print(f"Wavelet: {USE_WAVELET} ({WAVELET_TYPE})")
    print("="*60 + "\n")
    
    # Initialize models
    print("Initializing Wavelet-Enhanced FreqFormer...")
    model = FreqFormer(
        img_size=LR_SIZE,
        patch_size=1,
        in_chans=3,
        embed_dim=EMBED_DIM,
        depths=DEPTHS,
        num_heads=NUM_HEADS,
        window_size=WINDOW_SIZE,
        mlp_ratio=MLP_RATIO,
        upscale=UPSCALE_FACTOR
    )
    
    feature_extractor = FeatureExtractor()
    
    params = sum(p.numel() for p in model.parameters())
    print(f"FreqFormer parameters: {params:,}")
    print(f"Architecture: {len(DEPTHS)} stages, {sum(DEPTHS)} transformer blocks")
    print(f"Embed dim: {EMBED_DIM}, Window size: {WINDOW_SIZE}")
    print(f"Wavelet loss enabled: {USE_WAVELET}\n")
    
    # Prepare data
    print("Preparing data...")
    train_loader, val_loader = prepare_medical_data(DATASET_PATH)
    
    # Train
    print("\nStarting training...")
    history = train_freqformer(
        model, 
        feature_extractor, 
        train_loader, 
        val_loader, 
        num_epochs=EPOCHS
    )
    
    # Plot history
    print("\nPlotting training history...")
    plot_training_history(history)
    
    # Load best model
    print("\nLoading best Wavelet-Enhanced FreqFormer model...")
    checkpoint = torch.load('wavelet_freqformer_best_model.pth', weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(DEVICE)
    model.eval()
    
    print(f"Best model metrics:")
    print(f"  PSNR: {checkpoint['psnr']:.2f} dB")
    print(f"  SSIM: {checkpoint['ssim']:.4f}")
    print(f"  EPI: {checkpoint['epi']:.4f}")
    print(f"  GMSD: {checkpoint['gmsd']:.4f}")
    
    # Pathological invariance test
    print("\nRunning pathological invariance test...")
    validator = PathologicalInvarianceValidator(model, DEVICE)
    results = validator.test_pathological_invariance(val_loader, max_batches=20)
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print("\nKey Features:")
    print("  ✅ Frequency-aware attention mechanism")
    print("  ✅ Wavelet coefficient loss (NEW)")
    print("  ✅ Dual frequency processing (FFT + Wavelet)")
    print("  ✅ Multi-scale edge preservation")
    print("  ✅ Window-based transformer efficiency")
    print("  ✅ Enhanced frequency domain loss")
    print("  ✅ Comprehensive edge quality metrics")
    print("  ✅ Pathological invariance validation")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()