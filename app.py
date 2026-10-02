from flask import Flask, Response, request
import threading
import time

app = Flask(__name__)

ACCESS_KEY = "esp32cam123"

latest_frame = None
frame_lock = threading.Lock()

flash_state = False


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():

    return """
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>ESP32-CAM Remote Camera</title>

<style>

body {
    background: #222;
    color: white;
    text-align: center;
    font-family: Arial;
    margin: 0;
    padding: 15px;
}

h1 {
    margin: 10px;
}

img {
    width: 100%;
    max-width: 640px;
    height: auto;
    border: 2px solid white;
}

button {
    padding: 12px 25px;
    margin: 8px;
    font-size: 18px;
    border-radius: 8px;
    border: none;
}

</style>

</head>

<body>

<h1>ESP32-CAM LIVE</h1>

<img src="/stream?key=esp32cam123">

<br>

<button onclick="flashOn()">
FLASH ON
</button>

<button onclick="flashOff()">
FLASH OFF
</button>

<script>

function flashOn()
{
    fetch("/flash/on?key=esp32cam123");
}

function flashOff()
{
    fetch("/flash/off?key=esp32cam123");
}

</script>

</body>

</html>
"""


# =====================================================
# RECEIVE CONTINUOUS MJPEG STREAM FROM ESP32
# =====================================================

@app.route("/upload_stream", methods=["POST"])
def upload_stream():

    key = request.args.get("key")

    if key != ACCESS_KEY:
        return "Unauthorized", 401

    stream = request.stream

    try:

        while True:

            # Read until multipart boundary
            line = stream.readline()

            if not line:
                break

            if b"Content-Length:" not in line:
                continue

            # Content-Length line
            content_length = int(
                line.split(b":")[1].strip()
            )

            # Read remaining multipart headers
            while True:

                line = stream.readline()

                if not line:
                    break

                if line in (b"\r\n", b"\n"):
                    break

            # Read JPEG
            frame = stream.read(content_length)

            if not frame:
                break

            with frame_lock:
                global latest_frame
                latest_frame = frame

            # Consume trailing CRLF
            stream.read(2)

    except Exception as e:

        print("ESP32 stream disconnected:", e)

    return "Stream ended", 200


# =====================================================
# VIEW LIVE STREAM
# =====================================================

@app.route("/stream")
def stream():

    key = request.args.get("key")

    if key != ACCESS_KEY:
        return "Unauthorized", 401

    def generate():

        last_frame = None

        while True:

            with frame_lock:
                frame = latest_frame

            if frame is not None and frame is not last_frame:

                last_frame = frame

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: "
                    + str(len(frame)).encode()
                    + b"\r\n\r\n"
                    + frame
                    + b"\r\n"
                )

            time.sleep(0.02)

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# =====================================================
# FLASH
# =====================================================

@app.route("/flash/on")
def flash_on():

    global flash_state

    key = request.args.get("key")

    if key != ACCESS_KEY:
        return "Unauthorized", 401

    flash_state = True

    return "FLASH_ON"


@app.route("/flash/off")
def flash_off():

    global flash_state

    key = request.args.get("key")

    if key != ACCESS_KEY:
        return "Unauthorized", 401

    flash_state = False

    return "FLASH_OFF"


@app.route("/flash")
def flash():

    key = request.args.get("key")

    if key != ACCESS_KEY:
        return "Unauthorized", 401

    if flash_state:
        return "ON"

    return "OFF"


# =====================================================
# HEALTH
# =====================================================

@app.route("/health")
def health():

    return "ESP32-CAM cloud server is running!"


# =====================================================
# START
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
