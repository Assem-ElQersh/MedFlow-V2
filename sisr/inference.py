"""
SISR (Single Image Super-Resolution) inference for CXR enhancement.
Loads images from jpg, jpeg, png, or DICOM and runs FreqFormer to produce enhanced 4x upscaled output.
"""

import os
import numpy as np
import torch
from PIL import Image

# Import model and config from freqformer (avoid heavy deps at import)
from freqformer import FreqFormer, LR_SIZE, IMAGE_SIZE, EMBED_DIM, DEPTHS, NUM_HEADS, WINDOW_SIZE, MLP_RATIO, UPSCALE_FACTOR

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Accepted image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".dcm", ".dicom"}


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
    Match training degradation: resize to HR scale (128x128), then BICUBIC downscale to LR (32x32).
    Same as MedicalSRDataset: lr_img = hr_img.resize((lr_size, lr_size), Image.BICUBIC), then normalize.
    """
    pil = Image.fromarray(rgb)
    # Step 1: resize to HR scale (128) like training
    pil_hr = pil.resize((IMAGE_SIZE, IMAGE_SIZE), Image.BICUBIC)
    # Step 2: degrade to LR with BICUBIC downscale (same as training)
    pil_lr = pil_hr.resize((LR_SIZE, LR_SIZE), Image.BICUBIC)
    arr = np.array(pil_lr).astype(np.float32) / 255.0  # [0,1]
    # Normalize to [-1, 1] like dataset (mean=0.5, std=0.5)
    arr = (arr - 0.5) / 0.5
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).float()
    return tensor


def tensor_to_display(sr_tensor: torch.Tensor) -> np.ndarray:
    """Convert model output (1, 3, H, W) in model's range to RGB numpy [0,255] for display."""
    x = sr_tensor.squeeze(0).cpu().numpy().transpose(1, 2, 0)
    # Model output is denormalized to ~[0,1] in forward
    x = np.clip(x, 0, 1)
    return (x * 255).astype(np.uint8)


def load_model(checkpoint_path: str | None = None) -> torch.nn.Module:
    """Load FreqFormer and weights. Tries freqformer_best_model.pth then wavelet_freqformer_best_model.pth."""
    model = FreqFormer(
        img_size=LR_SIZE,
        patch_size=1,
        in_chans=3,
        embed_dim=EMBED_DIM,
        depths=DEPTHS,
        num_heads=NUM_HEADS,
        window_size=WINDOW_SIZE,
        mlp_ratio=MLP_RATIO,
        upscale=UPSCALE_FACTOR,
    )
    if checkpoint_path and os.path.isfile(checkpoint_path):
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        state = ckpt.get("model_state_dict", ckpt)
        model.load_state_dict(state, strict=True)
    model.to(DEVICE)
    model.eval()
    return model


def enhance_cxr(image_path: str, model: torch.nn.Module | None = None, checkpoint_path: str | None = None):
    """
    Load image from path, degrade like training (128 -> 32 BICUBIC), run SISR, return (original_display, enhanced_display).
    original_display = image at HR scale (128) before degradation; enhanced_display = model output.
    """
    if model is None:
        model = load_model(checkpoint_path)
    rgb = load_image(image_path)
    # Original at HR scale (128) - same as training; we degrade this to 32 then enhance back
    pil_hr = Image.fromarray(rgb).resize((IMAGE_SIZE, IMAGE_SIZE), Image.BICUBIC)
    original_display = np.array(pil_hr)
    x = preprocess_for_model(rgb).to(DEVICE)
    with torch.no_grad():
        sr = model(x)
    enhanced_display = tensor_to_display(sr)
    return original_display, enhanced_display
