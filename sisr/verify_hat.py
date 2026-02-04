"""
Verify Wavelet-HAT model loading and inference
"""

import torch
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wavelet_hat_model import WaveletHATGenerator, INPUT_SIZE, IMAGE_SIZE

checkpoint_path = "wavelet_hat_best_model.pth"

print("="*60)
print("Verifying Wavelet-HAT Integration")
print("="*60)

# 1. Check weights file
print("\n1. Checking weights file...")
if os.path.exists(checkpoint_path):
    size_mb = os.path.getsize(checkpoint_path) / (1024*1024)
    print(f"   [SUCCESS] Found {checkpoint_path} ({size_mb:.2f} MB)")
else:
    print(f"   [ERROR] File not found: {checkpoint_path}")
    print("   Please ensure the weights file is in this directory.")
    sys.exit(1)

# 2. Initialize Model
print("\n2. Initializing Wavelet-HAT model...")
try:
    model = WaveletHATGenerator(
        img_size=INPUT_SIZE,
        upscale=4,
        use_wavelet=True
    )
    print("   [SUCCESS] Model initialized")
except Exception as e:
    print(f"   [ERROR] Model initialization failed: {e}")
    sys.exit(1)

# 3. Load Weights
print("\n3. Loading weights...")
try:
    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    
    # Handle different checkpoint structures
    if 'model_state_dict' in ckpt:
        state_dict = ckpt['model_state_dict']
        print("   Key 'model_state_dict' found")
    elif 'generator_state_dict' in ckpt:
        state_dict = ckpt['generator_state_dict']
        print("   Key 'generator_state_dict' found")
    else:
        state_dict = ckpt
        print("   Using dictionary directly")
        
    model.load_state_dict(state_dict, strict=True)
    print("   [SUCCESS] Weights loaded (strict=True)")
except Exception as e:
    print(f"   [ERROR] Loading weights failed: {e}")
    # Try listing keys to help debug
    if 'state_dict' in locals():
        print(f"   Model keys: {list(model.state_dict().keys())[:3]}")
        print(f"   Checkpoint keys: {list(state_dict.keys())[:3]}")

# 4. Test Inference
print("\n4. Testing forward pass...")
try:
    model.eval()
    dummy_input = torch.randn(1, 3, 32, 32)
    with torch.no_grad():
        output = model(dummy_input)
    
    print(f"   Input shape: {dummy_input.shape}")
    print(f"   Output shape: {output.shape}")
    
    if output.shape == (1, 3, 128, 128):
        print("   [SUCCESS] Output shape is correct (128x128)")
    else:
        print(f"   [ERROR] Unexpected output shape: {output.shape}")
except Exception as e:
    print(f"   [ERROR] Inference failed: {e}")

print("\n" + "="*60)
print("Verification Complete")
print("="*60)
