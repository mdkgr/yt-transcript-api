import json
import traceback
from http.server import BaseHTTPRequestHandler

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    ytt = YouTubeTranscriptApi()
    IMPORT_OK = True
    IMPORT_ERR = None
except Exception as e:
    IMPORT_OK = False
    IMPORT_ERR = str(e)
    ytt = None


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not IMPORT_OK:
                return self._json(500, {"error": f"Import failed: {IMPORT_ERR}"})

            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            video_id = body.get("videoId", "")

            if not video_id:
                return self._json(400, {"error": "Missing videoId"})

            fetched = ytt.fetch(video_id)

            # Try attribute access first, then dict access
            parts = []
            for item in fetched:
                if hasattr(item, "text"):
                    parts.append(item.text)
                elif isinstance(item, dict):
                    parts.append(item.get("text", ""))
                else:
                    parts.append(str(item))

            text = " ".join(parts)

            if not text or len(text) < 50:
                return self._json(404, {"error": "Transcript too short or empty"})

            return self._json(200, {"transcript": text})

        except Exception as e:
            return self._json(500, {"error": str(e), "trace": traceback.format_exc()})

    def do_GET(self):
        return self._json(200, {
            "status": "ok",
            "import_ok": IMPORT_OK,
            "import_err": IMPORT_ERR,
        })

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _json(self, status, data):
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
