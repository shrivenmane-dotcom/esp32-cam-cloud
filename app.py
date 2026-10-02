from flask import Flask, Response, request
import threading
import time

app = Flask(__name__)

ACCESS_KEY = "esp32cam123"

latest_frame = None
frame_lock = threading.Lock()


@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ESP32-CAM Remote Live</title>

    <style>
        body {
            background: #222;
            color: white;
            text-align: center;
            font-family: Arial;
            margin: 0;
            padding: 20px;
        }

        img {
            width: 100%;
            max-width: 640px;
            height: auto;
            border: 2px solid white;
        }
    </style>
</head>

<body>

<h1>ESP32-CAM LIVE</h1>

<img src="/stream?key=esp32cam123">

<p>Remote camera stream</p>

</body>
</html>
"""


@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame

    key = request.args.get("key")

    if key != ACCESS_KEY:
        return "Unauthorized", 401

    data = request.get_data()

    if not data:
        return "No image received", 400

    with frame_lock:
        latest_frame = data

    return "OK", 200


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

            if frame is not None and frame != last_frame:
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

            time.sleep(0.03)

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/health")
def health():
    return "ESP32-CAM cloud server is running!"


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
