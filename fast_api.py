from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai
import os, uuid, re
from gtts import gTTS
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Load env vars
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=GEMINI_API_KEY)

# Init FastAPI app
app = FastAPI(title="HealthBot API", description="Endpoints for HealthBot", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic models ---
class MessageRequest(BaseModel):
    message: str

# --- Helper function to clean AI text for TTS ---
def clean_text(text: str) -> str:
    text = re.sub(r"[*_#`]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# --- Root endpoint ---
@app.get("/")
def root():
    return {"message": "✅ HealthBot FastAPI is running!"}

# --- 1. Chat Endpoint ---
@app.post("/chat_with_healthbot/")
async def chat_with_healthbot(request: MessageRequest):
    user_message = request.message

    if not user_message.strip():
        return JSONResponse({"reply": "Please type a message."})

    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
    You are HealthBot, a friendly virtual healthcare assistant. 
    Only answer healthcare-related questions (diet, exercise, symptoms, medications, etc.).
    If asked something unrelated, reply: "Sorry, I cannot answer that. I only provide healthcare-related guidance."
    Keep responses concise and professional.
    User said: {user_message}
    """
    response = model.generate_content(prompt)
    bot_reply = response.text if response and hasattr(response, "text") else "Sorry, I didn't understand."

    bot_reply_clean = clean_text(bot_reply)

    audio_filename = f"bot_{uuid.uuid4().hex}.mp3"
    audio_path = os.path.join("media", audio_filename)
    os.makedirs("media", exist_ok=True)
    gTTS(bot_reply_clean, lang="en").save(audio_path)

    return JSONResponse({
        "reply": bot_reply,
        "audio_url": f"/media/{audio_filename}"
    })

# --- 2. AI Call Endpoint ---
@app.post("/ai_call/")
async def ai_call(request: MessageRequest):
    user_message = request.message

    if not user_message.strip():
        return JSONResponse({"error": "No input detected"})

    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
    You are HealthBot. Answer only healthcare-related questions naturally like a human. 
    If unrelated, say: "Sorry, I cannot answer that. I only provide healthcare-related guidance.
    Keep responses concise and professional"
    User said: {user_message}
    """
    response = model.generate_content(prompt)
    bot_reply = response.text if response and hasattr(response, "text") else "Sorry, I didn't understand."

    bot_reply_clean = clean_text(bot_reply)

    audio_filename = f"ai_call_{uuid.uuid4().hex}.mp3"
    audio_path = os.path.join("media", audio_filename)
    os.makedirs("media", exist_ok=True)
    gTTS(bot_reply_clean, lang="en").save(audio_path)

    return JSONResponse({
        "reply": bot_reply_clean,
        "audio_url": f"/media/{audio_filename}"})

# Serve the media folder
app.mount("/media", StaticFiles(directory="media"), name="media")
