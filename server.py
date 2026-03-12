import os
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)
ytt = YouTubeTranscriptApi()


@app.route("/api/transcript", methods=["POST", "OPTIONS"])
def transcript():
    if request.method == "OPTIONS":
        return "", 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

    try:
        body = request.get_json(silent=True) or {}
        video_id = body.get("videoId", "")

        if not video_id:
            return jsonify({"error": "Missing videoId"}), 400

        fetched = ytt.fetch(video_id)
        text = " ".join(item.text for item in fetched)

        if not text or len(text) < 50:
            return jsonify({"error": "Transcript too short or empty"}), 404

        return jsonify({"transcript": text}), 200, {
            "Access-Control-Allow-Origin": "*",
        }

    except Exception as e:
        return jsonify({"error": str(e)}), 500, {
            "Access-Control-Allow-Origin": "*",
        }


@app.route("/api/transcript", methods=["GET"])
def health():
    import subprocess
    warp_status = "unknown"
    try:
        result = subprocess.run(
            ["warp-cli", "--accept-tos", "status"],
            capture_output=True, text=True, timeout=5
        )
        warp_status = result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        warp_status = str(e)

    proxy = os.environ.get("ALL_PROXY", "not set")
    return jsonify({"status": "ok", "warp": warp_status, "proxy": proxy}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
