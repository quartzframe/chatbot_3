import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import MODEL_NAME, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    if client is None:
        return jsonify({"error": "Gemini API key is not configured."}), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a study question."}), 400

    contents = []
    for item in history[-12:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "model"} and content:
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=content)],
                )
            )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=message)],
        )
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                thinking_level="minimal",
            ),
        )
        answer = (response.text or "").strip()
        if not answer:
            answer = "I couldn't generate a response. Please try your study question again."
        return jsonify({"answer": answer})
    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify(
            {"error": "Something went wrong while contacting Gemini. Please try again."}
        ), 500


if __name__ == "__main__":
    app.run()
