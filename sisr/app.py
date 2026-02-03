"""
Simple Gradio interface for CXR SISR: upload image (jpg, jpeg, png, DICOM) and enhance with one button.
"""

import os
import gradio as gr
from inference import load_model, load_image, enhance_cxr, IMAGE_EXTENSIONS, DEVICE

# Resolve checkpoint: prefer project checkpoint names
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_PATHS = [
    os.path.join(SCRIPT_DIR, "freqformer_best_model.pth"),
    os.path.join(SCRIPT_DIR, "wavelet_freqformer_best_model.pth"),
]
CHECKPOINT_PATH = next((p for p in CHECKPOINT_PATHS if os.path.isfile(p)), None)

# Load model once at startup
_model = None


def get_model():
    global _model
    if _model is None:
        if CHECKPOINT_PATH is None:
            raise FileNotFoundError(
                "No checkpoint found. Place freqformer_best_model.pth or wavelet_freqformer_best_model.pth in this directory."
            )
        _model = load_model(CHECKPOINT_PATH)
    return _model


def run_enhance(file):
    if file is None:
        return None, None, "Please upload an image first."
    path = file if isinstance(file, (str, bytes)) else getattr(file, "name", file)
    if path is None:
        return None, None, "Please upload an image first."
    path = str(path)
    ext = os.path.splitext(path)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return None, None, f"Unsupported format: {ext}. Use: {', '.join(sorted(IMAGE_EXTENSIONS))}"
    try:
        model = get_model()
        original, enhanced = enhance_cxr(path, model=model)
        return original, enhanced, f"Enhanced on {DEVICE}. Original → Enhanced (4× super-resolution)."
    except Exception as e:
        return None, None, f"Error: {e}"


# Accepted file types for upload
ACCEPTED_FILES = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".dcm", ".dicom"]

with gr.Blocks(title="CXR SISR – Enhance", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Chest X-Ray SISR Enhancer")
    gr.Markdown("Upload a CXR image (JPG, JPEG, PNG, or DICOM) and click **Enhance** to run 4× super-resolution.")
    with gr.Row():
        upload = gr.File(
            label="Upload image",
            file_types=ACCEPTED_FILES,
            type="filepath",
        )
    btn = gr.Button("Enhance CXR", variant="primary")
    status = gr.Markdown("")
    with gr.Row():
        out_original = gr.Image(label="Original (resized for comparison)", type="numpy")
        out_enhanced = gr.Image(label="Enhanced (4× SR)", type="numpy")

    btn.click(
        fn=run_enhance,
        inputs=[upload],
        outputs=[out_original, out_enhanced, status],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
