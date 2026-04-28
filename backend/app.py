from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from rag.chatbot import get_response

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/static")


@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    answer = get_response(question)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
