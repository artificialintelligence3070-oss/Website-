import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-video', methods=['POST'])
def get_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"success": False, "error": "No URL provided"})

    # Cobalt API is very reliable for these requests
    try:
        response = requests.post(
            "https://api.cobalt.tools/api/json",
            json={"url": url, "vCodec": "h264"},
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
        data = response.json()
        
        if response.status_code == 200 and "url" in data:
            return jsonify({"success": True, "url": data["url"]})
        else:
            return jsonify({"success": False, "error": "API failed to process link"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Use the port Render assigns, or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
