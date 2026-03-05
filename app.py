import io
import os
from threading import Lock

import soundfile as sf
from flask import Flask, jsonify, request, send_file
from f5_tts.api import F5TTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_REF = os.path.join(BASE_DIR, "voice.wav")
VOICE_REF_TEXT_FILE = os.path.join(BASE_DIR, "voice_ref.txt")
PORT = int(os.getenv("F5TTS_PORT", "5002"))
AUTH_TOKEN = os.getenv("F5TTS_AUTH_TOKEN", "").strip()

ref_text = ""
if os.path.isfile(VOICE_REF_TEXT_FILE):
    with open(VOICE_REF_TEXT_FILE, "r", encoding="utf-8") as f:
        ref_text = f.read().strip()

print(f"Using ref text: {(ref_text[:80] + '...') if ref_text else '[auto-transcribe]'}")
print("Loading F5-TTS on GPU...")
tts = F5TTS()
print("Model ready.")

app = Flask(__name__)
lock = Lock()


VOICE_ID = os.getenv("F5TTS_VOICE_ID", "pMsXgVXv3BLzUgSXRplE")
VOICE_NAME = os.getenv("F5TTS_VOICE_NAME", "F5 Custom Voice")


def _auth_ok(req) -> bool:
    if not AUTH_TOKEN:
        return True
    token = req.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return token == AUTH_TOKEN


def synth_wav_bytes(text: str) -> io.BytesIO:
    wav, sr, _ = tts.infer(
        ref_file=VOICE_REF,
        ref_text=ref_text,
        gen_text=text,
        show_info=lambda _: None,
    )
    out = io.BytesIO()
    sf.write(out, wav, sr, format="WAV")
    out.seek(0)
    return out


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "voice_ref_found": os.path.isfile(VOICE_REF),
            "voice_ref_text_found": os.path.isfile(VOICE_REF_TEXT_FILE),
            "voice_id": VOICE_ID,
            "port": PORT,
        }
    )


@app.route("/api/tts", methods=["GET", "POST"])
def api_tts():
    if not _auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    text = request.values.get("text") or data.get("text", "")
    if not text:
        return jsonify({"error": "missing 'text' parameter"}), 400
    if not os.path.isfile(VOICE_REF):
        return jsonify({"error": f"voice reference not found: {VOICE_REF}"}), 500

    with lock:
        out = synth_wav_bytes(text)
    return send_file(out, mimetype="audio/wav")


@app.route("/v1/voices", methods=["GET"])
def elevenlabs_voices():
    if not _auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401

    return jsonify(
        {
            "voices": [
                {
                    "voice_id": VOICE_ID,
                    "name": VOICE_NAME,
                    "labels": {"source": "f5-tts"},
                }
            ]
        }
    )


@app.route("/v1/text-to-speech/<voice_id>", methods=["POST"])
@app.route("/v1/text-to-speech/<voice_id>/stream", methods=["POST"])
def elevenlabs_tts(voice_id):
    if not _auth_ok(request):
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "missing 'text' field"}), 400
    if not os.path.isfile(VOICE_REF):
        return jsonify({"error": f"voice reference not found: {VOICE_REF}"}), 500
    if voice_id != VOICE_ID:
        return jsonify({"error": f"unknown voice_id '{voice_id}'"}), 404

    with lock:
        out = synth_wav_bytes(text)
    return send_file(out, mimetype="audio/wav")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
