"""
Simple Gradio interface for CXR SISR: upload image (jpg, jpeg, png, DICOM) and enhance with one button.
"""

import os
import gradio as gr
from inference import load_model, load_image, enhance_cxr, IMAGE_EXTENSIONS, DEVICE

# Resolve checkpoint: prefer project checkpoint names
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_PATHS = [
    os.path.join(SCRIPT_DIR, "wavelet_hat_best_model.pth"),
]
CHECKPOINT_PATH = next((p for p in CHECKPOINT_PATHS if os.path.isfile(p)), None)


def run_enhance(file):
    if file is None:
        return None, None, None, "Please upload an image first."
    path = file if isinstance(file, (str, bytes)) else getattr(file, "name", file)
    if path is None:
        return None, None, None, "Please upload an image first."
    path = str(path)
    ext = os.path.splitext(path)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return None, None, None, f"Unsupported format: {ext}. Use: {', '.join(sorted(IMAGE_EXTENSIONS))}"
    try:
        # return_degraded=True so we show: Original | Degraded (what model saw, upscaled) | Restored
        original, enhanced, degraded = enhance_cxr(path, model=None, checkpoint_path=CHECKPOINT_PATH, return_degraded=True)
        msg = f"Pipeline: **Original (HR)** → **Degraded (4× down, then BICUBIC up for display)** → **Restored (model)**. Running on {DEVICE}."
        return original, degraded, enhanced, msg
    except Exception as e:
        return None, None, None, f"Error: {e}"


# Accepted file types for upload
ACCEPTED_FILES = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".dcm", ".dicom"]

with gr.Blocks(title="CXR SISR – Wavelet-HAT") as demo:
    gr.Markdown("# Chest X-Ray SISR Enhancer (Wavelet-HAT)")
    gr.Markdown("Upload a CXR image and click **Enhance**. The app **degrades** it (4× BICUBIC downscale), then the model **restores** it. Compare: Original → Degraded (blurry) → Restored (model).")
    with gr.Row():
        upload = gr.File(
            label="Upload image",
            file_types=ACCEPTED_FILES,
            type="filepath",
        )
    btn = gr.Button("Enhance CXR", variant="primary")
    status = gr.Markdown("")
    with gr.Row():
        out_original = gr.Image(label="1. Original (HR)", type="numpy")
        out_degraded = gr.Image(label="2. Degraded (4× down then BICUBIC up – what the model sees)", type="numpy")
        out_enhanced = gr.Image(label="3. Restored (Model Output)", type="numpy")

    btn.click(
        fn=run_enhance,
        inputs=[upload],
        outputs=[out_original, out_degraded, out_enhanced, status],
    )

if __name__ == "__main__":
    # Use None for server_port to auto-select an available port
    # Theme moved to launch() for Gradio 6.0 compatibility
    demo.launch(server_name="127.0.0.1", server_port=None, theme=gr.themes.Soft())
