from flask import Flask, Response, request
import time

app = Flask(__name__)

# Simple access key for testing
ACCESS_KEY = "esp32cam123"

latest_frame = None


@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ESP32-CAM Remote Camera</title>
        <style>
            body {
                background: #222;
                color: white;
                text-align: center;
                font-family: Arial;
                padding: 20px;
            }

            img {
                width: 100%;
                max-width: 640px;
                border: 2px solid white;
            }
        </style>
    </head>

    <body>

        <h1>ESP32-CAM Remote Camera</h1>

        <img src="/stream?key=esp32cam123">

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

    latest_frame = data

    return "OK", 200


@app.route("/stream")
def stream():
    key = request.args.get("key")

    if key != ACCESS_KEY:
        return "Unauthorized", 401

    def generate():
        global latest_frame

        while True:

            if latest_frame is not None:

                frame = latest_frame

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: "
                    + str(len(frame)).encode()
                    + b"\r\n\r\n"
                    + frame
                    + b"\r\n"
                )

            time.sleep(0.05)

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
