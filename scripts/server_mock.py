from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/publish", methods=["POST"])
def mock_publish():
    data = request.json
    if "mac_address" in data:
        return (
            jsonify({"status": "success", "device_name": "TEST_NAME"}),
            200,
        )
    else:
        return jsonify({"status": "error", "message": "Missing MAC address"}), 400


if __name__ == "__main__":
    app.run(port=5000)
