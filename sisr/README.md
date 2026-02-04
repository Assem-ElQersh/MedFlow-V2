# SISR - Wavelet-HAT for Chest X-Ray Enhancement

This directory contains a **Wavelet-Enhanced Hybrid Attention Transformer (HAT)** model for 4× super-resolution of chest X-ray images (32×32 → 128×128).

## Model Architecture

**Wavelet-HAT** combines:
- **Wavelet Decomposition** (Haar/db1) for frequency-domain structural priors
- **Hybrid Attention Transformer (HAT)** backbone
- **Window Video-Style Attention** for local feature extraction
- **Channel Attention (CAB)** for feature recalibration
- **Overlapping Cross-Attention (OCAB)** for inter-window information interaction

### Key Features
- **Inference Input:** 32×32 low-resolution CXR
- **Inference Output:** 128×128 super-resolved CXR
- **Upscale Factor:** 4×
- **Architecture Depth:** 6 Residual Hybrid Attention Groups (RHAGs)
- **Attention Mechanisms:** Window Attention + Channel Attention + Cross Attention

## Files

- `app.py` - Gradio web interface (Updated for HAT)
- `inference.py` - Inference pipeline (Updated for HAT)
- `wavelet_hat_model.py` - Model architecture for inference
- `requirements-app.txt` - Python dependencies
- `wavelet_hat_best_model.pth` - Trained model weights (275 MB)

## Setup

### Option 1: Using Conda
```bash
conda env create -f environment.yml
conda activate sisr
python app.py
```

### Option 2: Using Pip
```bash
pip install -r requirements-app.txt
python app.py
```

## Usage

1. **Start the app:**
   ```bash
   python app.py
   ```

2. **Open in browser:**
   The URL will be shown in the terminal, usually `http://localhost:7860`.

3. **Upload an image:**
   - Supported formats: JPG, JPEG, PNG, BMP, TIF, TIFF, DICOM (.dcm)
   - Click "Enhance CXR"

## Model Weights

The weights file `wavelet_hat_best_model.pth` should be in this directory.
It contains the trained parameters for the Wavelet-HAT generator.

## Performance

Wavelet-HAT typically outperforms standard CNN-based SR methods (like SRGAN) on medical images by leveraging:
1. **Long-range dependencies** via Transformers
2. **Frequency awareness** via Wavelet integration
3. **Structured edge recovery** via specialized loss functions during training

## Architecture Diagram

```
Input (32×32)
    ↓
Wavelet Decomposition (LL, LH, HL, HH)
    ↓
Feature Fusion
    ↓
Shallow Feature Extraction
    ↓
Deep Feature Extraction (6 RHAGs)
    ↓
    ├── Window Attention
    ├── Channel Attention
    └── Overlapping Cross-Attention
    ↓
Global Residual
    ↓
Upsampling (PixelShuffle)
    ↓
Output (128×128)
```
