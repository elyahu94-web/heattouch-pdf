"""
HeatTouch Quote PDF Server
מקבל JSON עם נתוני לקוח, ממלא את הצעת המחיר, מחזיר PDF base64
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, base64, traceback
from fill_pdf import fill_quote_pdf

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "heattouch-quote"})

@app.route('/fill', methods=['POST'])
def fill():
    try:
        data = request.get_json()
        pdf_bytes = fill_quote_pdf(data)
        return jsonify({"pdf": base64.b64encode(pdf_bytes).decode()})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/fields', methods=['GET'])
def get_fields():
    """מחזיר את הגדרת השדות לממשק הגרירה"""
    with open('fields_template.json', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/save-fields', methods=['POST'])
def save_fields():
    """שומר עדכון לשדות מממשק הגרירה"""
    try:
        data = request.get_json()
        with open('fields_template.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

@app.route('/editor', methods=['GET'])
def editor():
    with open(os.path.join(BASE_DIR, 'editor.html'), encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
