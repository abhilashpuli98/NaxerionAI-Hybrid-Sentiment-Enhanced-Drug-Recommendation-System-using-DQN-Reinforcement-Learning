import os
# Fix: clear broken SSL_CERT_FILE env var that causes ollama import to crash
os.environ.pop("SSL_CERT_FILE", None)
os.environ.pop("SSL_CERT_DIR", None)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ollama import chat
import ollama as ollama_lib
import traceback
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prioritized model list: gemma4:e4b first, then fallbacks
MODELS_PRIORITY = ["gemma4:e4b", "llama3.2:1b", "gemma3:1b", "gemma:2b"]


def get_available_model():
    """Try each model in priority order and return the first available one."""
    try:
        model_list = ollama_lib.list()
        # Build set of available model names (full "name:tag" strings)
        available = set()
        models_data = model_list.get("models", []) if isinstance(model_list, dict) else getattr(model_list, 'models', [])
        for m in models_data:
            # Support both dict and object access
            name = m.get("name", "") if isinstance(m, dict) else getattr(m, 'name', '') or getattr(m, 'model', '')
            model_field = m.get("model", "") if isinstance(m, dict) else getattr(m, 'model', '')
            if name:
                available.add(name)
            if model_field:
                available.add(model_field)

        for model in MODELS_PRIORITY:
            # Exact match or substring match
            if model in available or any(model in a for a in available):
                return model
    except Exception as e:
        print(f"[get_available_model] Error listing models: {e}")
    # Default to gemma4:e4b even if we can't check — let ollama error naturally
    return "gemma4:e4b"


class ChatRequest(BaseModel):
    message: str
    history: list
    tone: str
    mode: str
    config: dict = {}


def _extract_response(response):
    """Safely extract content and thinking from ollama ChatResponse.
    Works with both dict-like and attribute-based access (ollama 0.4.x - 0.6.x)."""
    content = ""
    thinking = ""
    try:
        # Try attribute access first (ollama >= 0.5.x returns ChatResponse objects)
        msg = getattr(response, 'message', None)
        if msg is not None:
            content = getattr(msg, 'content', '') or ''
            thinking = getattr(msg, 'thinking', '') or ''
        else:
            # Fallback to dict access
            msg = response.get("message", {}) if isinstance(response, dict) else {}
            content = msg.get("content", "") or ""
            thinking = msg.get("thinking", "") or ""
    except Exception:
        # Last resort: try dict-style subscript
        try:
            content = response["message"]["content"]
        except Exception:
            pass
    return content, thinking


@app.get("/health")
def health():
    model = get_available_model()
    return {"status": "ok", "model": model}


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """Chat endpoint with gemma4:e4b thinking support.
    Returns thinking text and final answer separately."""
    try:
        model = get_available_model()
        messages = []

        # Build system prompt
        system_prompt = req.tone or "You are a helpful AI assistant."
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history (last 6 turns)
        for m in req.history[-6:]:
            role = m.get("role", "user")
            if role == "bot":
                role = "assistant"
            content = m.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": req.message})

        # Use think=True for gemma4 models (ollama handles the thinking natively)
        use_thinking = "gemma4" in model

        print(f"[chat] Using model: {model}, thinking: {use_thinking}")

        if use_thinking:
            response = chat(
                model=model,
                messages=messages,
                think=True
            )
            answer_text, thinking_text = _extract_response(response)
            print(f"[chat] Thinking length: {len(thinking_text)}, Answer length: {len(answer_text)}")

            return {
                "text": answer_text,
                "thinking": thinking_text,
                "model": model,
                "type": "text"
            }
        else:
            response = chat(
                model=model,
                messages=messages
            )
            answer_text, _ = _extract_response(response)
            return {
                "text": answer_text,
                "thinking": "",
                "model": model,
                "type": "text"
            }

    except Exception as e:
        traceback.print_exc()
        return {
            "text": f"Backend error: {str(e)}",
            "thinking": "",
            "model": "error",
            "type": "text"
        }


@app.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Streaming chat endpoint — streams thinking + answer as SSE events."""
    try:
        model = get_available_model()
        messages = []

        system_prompt = req.tone or "You are a helpful AI assistant."
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for m in req.history[-6:]:
            role = m.get("role", "user")
            if role == "bot":
                role = "assistant"
            content = m.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": req.message})

        use_thinking = "gemma4" in model

        def generate():
            try:
                stream = chat(
                    model=model,
                    messages=messages,
                    stream=True,
                    think=use_thinking
                )

                for chunk in stream:
                    # Extract from each streaming chunk
                    content, thinking = _extract_response(chunk)

                    if thinking:
                        yield f"data: {json.dumps({'type': 'thinking', 'text': thinking})}\n\n"
                    if content:
                        yield f"data: {json.dumps({'type': 'content', 'text': content})}\n\n"

                yield f"data: {json.dumps({'type': 'done', 'model': model})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
