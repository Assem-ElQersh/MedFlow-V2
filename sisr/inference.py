"""
SISR (Single Image Super-Resolution) inference for CXR enhancement.
Loads images from jpg, jpeg, png, or DICOM and runs Wavelet-HAT to produce enhanced 4x upscaled output.
"""

import os
import numpy as np
import torch
from PIL import Image

# Import Wavelet-HAT model
from wavelet_hat_model import WaveletHATGenerator, INPUT_SIZE, IMAGE_SIZE

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Accepted image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".dcm", ".dicom"}

# Model configuration (must match training)
NUM_RHAG = 6
NUM_HAB = 6
EMBED_DIM = 180
NUM_HEADS = 6
WINDOW_SIZE = 16
MLP_RATIO = 2
UPSCALE = 4
USE_WAVELET = True


def load_dicom(path: str) -> np.ndarray:
    """Load DICOM file and return grayscale image as uint8 numpy array (H, W)."""
    try:
        import pydicom
    except ImportError:
        raise ImportError("DICOM support requires pydicom: pip install pydicom")
    dcm = pydicom.dcmread(path)
    arr = dcm.pixel_array.astype(np.float32)
    # Apply rescale slope/intercept if present
    if hasattr(dcm, "RescaleSlope") and hasattr(dcm, "RescaleIntercept"):
        arr = arr * float(dcm.RescaleSlope) + float(dcm.RescaleIntercept)
    # Normalize to 0-255 for display/consistency
    arr = np.clip(arr, arr.min(), arr.max())
    if arr.max() > arr.min():
        arr = (arr - arr.min()) / (arr.max() - arr.min()) * 255.0
    return arr.astype(np.uint8)


def load_image(path: str) -> np.ndarray:
    """
    Load image from path. Supports jpg, jpeg, png, bmp, tif, tiff, and DICOM (.dcm, .dicom).
    Returns RGB numpy array (H, W, 3) in [0, 255] uint8.
    """
    path = str(path)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".dcm", ".dicom"):
        gray = load_dicom(path)
        # Stack to RGB (CXR is grayscale)
        rgb = np.stack([gray, gray, gray], axis=-1)
        return rgb
    # Standard image
    img = Image.open(path)
    img = np.array(img)
    if img.ndim == 2:
        rgb = np.stack([img, img, img], axis=-1)
    elif img.ndim == 3 and img.shape[2] == 4:
        rgb = img[:, :, :3]
    else:
        rgb = img[:, :, :3] if img.ndim == 3 else np.stack([img, img, img], axis=-1)
    return np.ascontiguousarray(rgb.astype(np.uint8))


def preprocess_for_model(rgb: np.ndarray) -> torch.Tensor:
    """
    Preprocess image for model (Normalize only).
    Degradation is handled externally in enhance_cxr to support dynamic sizes.
    """
    # Convert to float [0, 1]
    arr = rgb.astype(np.float32) / 255.0
    # Normalize to [-1, 1] like dataset (mean=0.5, std=0.5)
    arr = (arr - 0.5) / 0.5
    # To Tensor [C, H, W]
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).float()
    return tensor


def tensor_to_display(sr_tensor: torch.Tensor) -> np.ndarray:
    """Convert model output (1, 3, H, W) in [-1, 1] range to RGB numpy [0,255] for display."""
    x = sr_tensor.squeeze(0).cpu().numpy().transpose(1, 2, 0)
    # Model output is in [-1, 1] due to tanh, denormalize to [0, 1]
    x = (x + 1) / 2
    x = np.clip(x, 0, 1)
    return (x * 255).astype(np.uint8)


def load_model(checkpoint_path: str | None = None, img_size: int = 32) -> torch.nn.Module:
    """Load Wavelet-HAT and weights dynamically for specific image size."""
    print(f"Loading Wavelet-HAT model...")
    print(f"  Configuration: Dynamic LR Input ({img_size}x{img_size}) -> 4x Output")
    print(f"  Architecture: HAT (Hybrid Attention Transformer)")
    
    # Initialize model with specific image size to match the LR input
    model = WaveletHATGenerator(
        img_size=img_size,
        in_chans=3,
        embed_dim=EMBED_DIM,
        depths=[NUM_HAB] * NUM_RHAG,
        num_heads=[NUM_HEADS] * NUM_RHAG,
        window_size=WINDOW_SIZE,
        mlp_ratio=MLP_RATIO,
        upscale=UPSCALE,
        use_wavelet=USE_WAVELET
    )
    
    if checkpoint_path and os.path.isfile(checkpoint_path):
        print(f"  Loading weights from: {checkpoint_path}")
        try:
            ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        except TypeError:
            ckpt = torch.load(checkpoint_path, map_location="cpu")
        
        # Handle different checkpoint formats
        if 'model_state_dict' in ckpt:
            state = ckpt['model_state_dict']
        elif 'generator_state_dict' in ckpt:
            state = ckpt['generator_state_dict']
        else:
            state = ckpt
        
        # Filter out attention masks which depend on input size
        # This prevents "size mismatch" errors when loading weights for a different resolution
        filtered_state = {k: v for k, v in state.items() if 'attn_mask' not in k}
        
        if len(filtered_state) < len(state):
            print(f"  ℹ Skipped {len(state) - len(filtered_state)} attention mask buffers (dynamic size)")
        
        # Load weights with strict=False (required since we removed masks)
        model.load_state_dict(filtered_state, strict=False)
        print(f"  ✓ Weights loaded successfully (strict=False)")
    else:
        print(f"  ⚠ No checkpoint found, using random weights")
    
    model.to(DEVICE)
    model.eval()
    print(f"  ✓ Model ready on {DEVICE}")
    return model


def pad_to_square(img: np.ndarray):
    """Pad image to be square."""
    h, w = img.shape[:2]
    max_dim = max(h, w)
    pad_h = max_dim - h
    pad_w = max_dim - w
    padded = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode='edge')
    return padded, max_dim


def pad_to_multiple_of(img: np.ndarray, multiple: int):
    """Pad spatial dimensions to a multiple of `multiple` (e.g. 16 for HAT window)."""
    h, w = img.shape[:2]
    h_pad = (multiple - h % multiple) % multiple
    w_pad = (multiple - w % multiple) % multiple
    if h_pad == 0 and w_pad == 0:
        return img, h, w
    padded = np.pad(img, ((0, h_pad), (0, w_pad), (0, 0)), mode='edge')
    return padded, padded.shape[0], padded.shape[1]


def enhance_cxr(image_path: str, model: torch.nn.Module | None = None, checkpoint_path: str | None = None, return_degraded: bool = False):
    """
    Dynamic Size Degradation & Restoration Loop:
    1. Load Original Image (HR).
    2. Crop to multiple of 4 (HR).
    3. DEGRADATION: Downscale 4x with BICUBIC -> LR (this is the only input the model sees).
    4. Pad LR to square, then to multiple of WINDOW_SIZE (16).
    5. Model restores LR -> HR' (super-resolution).
    6. Crop back to original HR size.

    Returns:
        original_display: the HR image you uploaded (ground truth).
        enhanced_display: model output (restored from the degraded LR).
        If return_degraded=True: also returns degraded_upscaled = LR upscaled 4x with BICUBIC
          (no model) so you can compare: Original | Degraded (BICUBIC) | Restored (Model).
    """
    rgb = load_image(image_path)

    # 1. Ensure dimensions are multiples of 4 (for clean 4x downscale)
    h, w = rgb.shape[:2]
    h_trim = (h // 4) * 4
    w_trim = (w // 4) * 4
    if h != h_trim or w != w_trim:
        rgb = rgb[:h_trim, :w_trim, :]
        print(f"  Trimmed input to {h_trim}x{w_trim} for 4x compatibility")

    original_display = rgb  # HR ground truth (what we show as "Original")

    # 2. DEGRADATION: 4x BICUBIC downscale -> LR (model input is only this)
    lr_h, lr_w = h_trim // 4, w_trim // 4
    pil_hr = Image.fromarray(rgb)
    pil_lr = pil_hr.resize((lr_w, lr_h), Image.BICUBIC)
    lr_rgb = np.array(pil_lr)

    # Optional: LR upscaled back to HR with BICUBIC (no model) for comparison
    degraded_upscaled = None
    if return_degraded:
        degraded_upscaled = np.array(pil_lr.resize((w_trim, h_trim), Image.BICUBIC))

    # 3. Pad LR to square (HAT expects square), then to multiple of WINDOW_SIZE (16)
    padded_lr, square_size = pad_to_square(lr_rgb)
    padded_lr, model_h, model_w = pad_to_multiple_of(padded_lr, WINDOW_SIZE)
    model_size = model_h

    # 4. Initialize Model for this LR size (must be multiple of 16)
    model = load_model(checkpoint_path, img_size=model_size)

    # 5. Run Inference (model sees only the degraded LR image)
    x = preprocess_for_model(padded_lr).to(DEVICE)
    with torch.no_grad():
        sr = model(x)

    # 6. Post-process
    enhanced_padded = tensor_to_display(sr)

    # 7. Crop back to expected HR size
    expected_h, expected_w = h_trim, w_trim
    enhanced_display = enhanced_padded[:expected_h, :expected_w, :]

    if return_degraded:
        return original_display, enhanced_display, degraded_upscaled
    return original_display, enhanced_display
