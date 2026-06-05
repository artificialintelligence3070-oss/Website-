from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-video', methods=['POST'])
def get_video():
    url = request.json.get('url')
    # Using Cobalt API which is very stable
    api_url = "https://api.cobalt.tools/api/json"
    payload = {"url": url, "vCodec": "h264"}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        data = response.json()
        if "url" in data:
            return jsonify({"success": True, "url": data["url"]})
        else:
            return jsonify({"success": False, "error": "Could not fetch video"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run()
