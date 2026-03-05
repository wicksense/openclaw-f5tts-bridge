# OpenClaw F5-TTS Bridge (ElevenLabs-Compatible)

Use your self-hosted F5-TTS voice as an OpenClaw TTS provider by exposing an ElevenLabs-compatible API.

## What this does

This bridge provides endpoints that OpenClaw's `messages.tts.provider = "elevenlabs"` can call:

- `GET /v1/voices`
- `POST /v1/text-to-speech/<voice_id>`
- `POST /v1/text-to-speech/<voice_id>/stream`

It also exposes:

- `GET /health`
- `GET|POST /api/tts` (simple direct endpoint)

## Quick start

> Recommended: **Conda** (matches F5-TTS guidance and avoids many CUDA/PyTorch conflicts).

### Option A (recommended) — Conda

```bash
conda create -n f5bridge python=3.10 -y
conda activate f5bridge

# Install PyTorch for your CUDA version first (example for CUDA 12.1)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install F5-TTS + bridge deps
pip install f5-tts flask soundfile
```

### Option B — venv (works, but may need more manual CUDA/PyTorch troubleshooting)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Add your voice assets

Put these in the repo directory:

- `voice.wav` (required)
- `voice_ref.txt` (optional, transcript of `voice.wav` for faster/better startup)

### 3) Run the bridge

```bash
python app.py
```

Default port: `5002`

### 4) Verify endpoints

```bash
curl http://127.0.0.1:5002/health
curl http://127.0.0.1:5002/v1/voices
curl -X POST http://127.0.0.1:5002/v1/text-to-speech/pMsXgVXv3BLzUgSXRplE \
  -H 'Content-Type: application/json' \
  -d '{"text":"Hello from F5-TTS bridge"}' --output test.wav
```

## OpenClaw config

Add to `openclaw.json`:

```json
{
  "messages": {
    "tts": {
      "provider": "elevenlabs",
      "auto": "tagged",
      "elevenlabs": {
        "baseUrl": "http://<YOUR_HOST>:5002",
        "apiKey": "dummy",
        "voiceId": "pMsXgVXv3BLzUgSXRplE"
      }
    }
  }
}
```

Then restart:

```bash
openclaw gateway restart
```

In chat:

- `/tts status`
- `/tts audio this is a bridge test`

## Configuration

Environment variables:

- `F5TTS_PORT` (default `5002`)
- `F5TTS_AUTH_TOKEN` (optional bearer token)
- `F5TTS_VOICE_ID` (default `pMsXgVXv3BLzUgSXRplE`)
- `F5TTS_VOICE_NAME` (default `F5 Custom Voice`)

## Security notes

- Do not commit `voice.wav` / `voice_ref.txt`.
- If exposed beyond localhost/LAN, set `F5TTS_AUTH_TOKEN` and place behind a firewall/reverse proxy.

## Troubleshooting

### OpenClaw says `Invalid voiceId format`
Use a valid ElevenLabs-style `voiceId` string (the default in this repo works).

### No requests hit bridge
- Confirm `messages.tts.provider` is `elevenlabs`
- Confirm `messages.tts.elevenlabs.baseUrl` points to this server
- Restart OpenClaw after config change

### Wrong voice heard
OpenClaw may be falling back. Check `/tts status` and verify `baseUrl` + `voiceId`.

## License

MIT
