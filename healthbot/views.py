from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from gtts import gTTS
import uuid
import google.generativeai as genai
from django.conf import settings
from dotenv import load_dotenv

# Load .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=GEMINI_API_KEY)

def home(request):
    return render(request, "home.html")

@csrf_exempt
def chat_with_healthbot(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request method."})

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        if not user_message.strip():
            return JsonResponse({"reply": "Please type a message."})

        # Call Gemini AI with short, concise instructions
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Answer the user's health question concisely and precisely in short text. Avoid long explanations. User asked: {user_message}"
        response = model.generate_content(prompt)
        bot_reply = response.text if response and hasattr(response, "text") else "Sorry, I didn't understand."

        # Generate TTS
        audio_filename = f"bot_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(settings.MEDIA_ROOT, audio_filename)
        tts = gTTS(bot_reply, lang="en")
        tts.save(audio_path)

        return JsonResponse({
            "reply": bot_reply,
            "audio_url": f"/media/{audio_filename}"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"reply": f"Error contacting AI: {e}"})

# AI Call endpoint (voice only, no text)
@csrf_exempt
def ai_call(request):
    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request method."})

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        if not user_message.strip():
            return JsonResponse({"error": "No input detected"})

        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"Answer user voice input naturally like a human, concise and understandable. Only voice output, no text formatting. User said: {user_message}"
        response = model.generate_content(prompt)
        bot_reply = response.text if response and hasattr(response, "text") else "Sorry, I didn't understand."

        # Generate TTS
        audio_filename = f"ai_call_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(settings.MEDIA_ROOT, audio_filename)
        tts = gTTS(bot_reply, lang="en")
        tts.save(audio_path)

        # Return only audio URL (AI Call is voice-only)
        return JsonResponse({"audio_url": f"/media/{audio_filename}"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Error contacting AI: {e}"})
