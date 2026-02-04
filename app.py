import os
import base64
import tempfile
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from moviepy.editor import VideoFileClip
from PIL import Image

app = Flask(__name__)
CORS(app)

# ===============================
# 🔹 ENV VARIABLES
# ===============================
API_KEYS = os.environ.get("API_KEYS", "").split(",")
APP_TOKEN = os.environ.get("APP_TOKEN")

# ===============================
# 🔐 SECURITY
# ===============================
@app.before_request
def secure():
    if request.headers.get("x-app-token") != APP_TOKEN:
        return jsonify({"error": "Forbidden"}), 403

# ===============================
# 🧠 ASK AI (TEXT)
# ===============================
def ask_text(key, prompt):
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# ===============================
# 🖼️ ASK AI (IMAGE)
# ===============================
def ask_image(key, img64):
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Sobanura iyi foto neza"},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img64}"}
                ]
            }]
        }
    )
    return r.json()["choices"][0]["message"]["content"]

# ===============================
# 📝 TEXT ENDPOINT
# ===============================
@app.route("/api/text", methods=["POST"])
def text_api():
    prompt = request.json.get("prompt")
    results = []

    for key in API_KEYS:
        try:
            results.append(ask_text(key, prompt))
        except:
            results.append("❌ API key failed")

    return jsonify({
        "answer": "\n\n---\n\n".join(results)
    })

# ===============================
# 🖼️ IMAGE ENDPOINT
# ===============================
@app.route("/api/image", methods=["POST"])
def image_api():
    image = request.files["image"]
    img64 = base64.b64encode(image.read()).decode()
    results = []

    for key in API_KEYS:
        try:
            results.append(ask_image(key, img64))
        except:
            results.append("❌ API key failed")

    return jsonify({
        "answer": "\n\n---\n\n".join(results)
    })

# ===============================
# 🎥 VIDEO ENDPOINT
# ===============================
@app.route("/api/video", methods=["POST"])
def video_api():
    video = request.files["video"]
    tmp = tempfile.NamedTemporaryFile(delete=False)
    video.save(tmp.name)

    clip = VideoFileClip(tmp.name)
    results = []

    for frame in clip.iter_frames(fps=1):
        img = Image.fromarray(frame)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
            img.save(f.name)
            img64 = base64.b64encode(open(f.name, "rb").read()).decode()
            for key in API_KEYS:
                try:
                    results.append(ask_image(key, img64))
                except:
                    results.append("❌ API key failed")

    clip.close()

    return jsonify({
        "answer": "\n\n---\n\n".join(results)
    })

# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
