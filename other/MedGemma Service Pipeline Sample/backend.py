from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
import uvicorn
import base64
import traceback

# Fixed: removed trailing slash
REMOTE_MODEL_URL = "https://marquetta-bottommost-designedly.ngrok-free.dev/"

app = FastAPI(title="MedGemma Local Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str
    max_new_tokens: Optional[int] = 512

@app.get("/")
async def root():
    return {"status": "MedGemma backend is running"}

@app.get("/health")
async def health_check():
    try:
        response = requests.get(f"{REMOTE_MODEL_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"local": "healthy", "remote": "connected", "model": data.get("model")}
        return {"local": "healthy", "remote": "disconnected"}
    except Exception as e:
        print(f"Health check error: {e}")
        return {"local": "healthy", "remote": "disconnected"}

@app.post("/analyze_text")
async def analyze_text(input_data: TextInput):
    try:
        print(f"[TEXT] Sending request to {REMOTE_MODEL_URL}/predict_text")
        response = requests.post(
            f"{REMOTE_MODEL_URL}/predict_text",
            json={
                "text": input_data.text,
                "max_new_tokens": input_data.max_new_tokens
            },
            timeout=60
        )
        print(f"[TEXT] Response status: {response.status_code}")
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        print("[TEXT] ERROR: Timeout")
        raise HTTPException(status_code=504, detail="Model service timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"[TEXT] ERROR: Connection failed - {e}")
        raise HTTPException(status_code=503, detail="Cannot connect to model service")
    except Exception as e:
        print(f"[TEXT] ERROR: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_image")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: Optional[str] = Form("Describe this medical image in detail."),
    max_new_tokens: Optional[int] = Form(512)
):
    try:
        print(f"[IMAGE] Received image: {image.filename}, prompt: {prompt}")
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        print(f"[IMAGE] Image encoded, size: {len(image_base64)} chars")
        print(f"[IMAGE] Sending request to {REMOTE_MODEL_URL}/predict_image")
        
        response = requests.post(
            f"{REMOTE_MODEL_URL}/predict_image",
            json={
                "image_base64": image_base64,
                "prompt": prompt,
                "max_new_tokens": max_new_tokens
            },
            timeout=60
        )
        print(f"[IMAGE] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[IMAGE] Response body: {response.text}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        print("[IMAGE] ERROR: Timeout")
        raise HTTPException(status_code=504, detail="Model service timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"[IMAGE] ERROR: Connection failed - {e}")
        raise HTTPException(status_code=503, detail="Cannot connect to model service")
    except requests.exceptions.HTTPError as e:
        print(f"[IMAGE] ERROR: HTTP {e.response.status_code}")
        print(f"[IMAGE] Response: {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Remote service error: {e.response.text}")
    except Exception as e:
        print(f"[IMAGE] ERROR: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_multimodal")
async def analyze_multimodal(
    text: str = Form(...),
    image: UploadFile = File(...),
    max_new_tokens: Optional[int] = Form(512)
):
    try:
        print(f"[MULTIMODAL] Received image: {image.filename}, text: {text[:50]}...")
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        print(f"[MULTIMODAL] Image encoded, size: {len(image_base64)} chars")
        print(f"[MULTIMODAL] Sending request to {REMOTE_MODEL_URL}/predict_multimodal")
        
        response = requests.post(
            f"{REMOTE_MODEL_URL}/predict_multimodal",
            json={
                "text": text,
                "image_base64": image_base64,
                "max_new_tokens": max_new_tokens
            },
            timeout=60
        )
        print(f"[MULTIMODAL] Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[MULTIMODAL] Response body: {response.text}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        print("[MULTIMODAL] ERROR: Timeout")
        raise HTTPException(status_code=504, detail="Model service timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"[MULTIMODAL] ERROR: Connection failed - {e}")
        raise HTTPException(status_code=503, detail="Cannot connect to model service")
    except requests.exceptions.HTTPError as e:
        print(f"[MULTIMODAL] ERROR: HTTP {e.response.status_code}")
        print(f"[MULTIMODAL] Response: {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Remote service error: {e.response.text}")
    except Exception as e:
        print(f"[MULTIMODAL] ERROR: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting MedGemma backend on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)