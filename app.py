from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        return jsonify({
            'success': True,
            'language': data.get('language', 'auto'),
            'errors': [],
            'warnings': [],
            'summary': {
                'error_count': 0,
                'warning_count': 0,
                'has_errors': False
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Flask server on http://127.0.0.1:5000")
    print("Press CTRL+C to stop")
    app.run(debug=True, port=5000)