import json
from http.server import BaseHTTPRequestHandler
from youtube_transcript_api import YouTubeTranscriptApi


ytt = YouTubeTranscriptApi()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            video_id = body.get("videoId", "")

            if not video_id:
                return self._json(400, {"error": "Missing videoId"})

            transcript_list = ytt.list_transcripts(video_id)

            # Try to find a transcript: prefer manual, then generated, any language
            transcript = None
            try:
                transcript = transcript_list.find_manually_created_transcript(
                    ["en", "el", "de", "fr", "es", "it", "pt", "ru", "ja", "ko", "zh-Hans"]
                )
            except Exception:
                try:
                    transcript = transcript_list.find_generated_transcript(
                        ["en", "el", "de", "fr", "es", "it", "pt", "ru", "ja", "ko", "zh-Hans"]
                    )
                except Exception:
                    # Grab whatever is available
                    for t in transcript_list:
                        transcript = t
                        break

            if not transcript:
                return self._json(404, {"error": "No transcript available"})

            snippets = transcript.fetch()
            text = " ".join(s.text for s in snippets)

            return self._json(200, {"transcript": text, "language": transcript.language})

        except Exception as e:
            return self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self._cors_headers()
        self.send_response(204)
        self.end_headers()

    def _json(self, status, data):
        self._cors_headers()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
