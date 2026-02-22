from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys

# Add the current directory to path so Python can find your modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your analyzers
try:
    from analyzers.python_analyzer import PythonAnalyzer
    from analyzers.java_analyzer import JavaAnalyzer
    from analyzers.cpp_analyzer import CPPAnalyzer
    from analyzers.javascript_analyzer import JavaScriptAnalyzer
    from analyzers.html_analyzer import HTMLAnalyzer
    from analyzers.generic_analyzer import GenericAnalyzer
    from utils.language_detector import detect_language
    print("✅ Successfully imported analyzers")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all analyzer files exist in the analyzers/ folder")

app = Flask(__name__)
CORS(app)

# Initialize analyzers
analyzers = {
    'python': PythonAnalyzer(),
    'java': JavaAnalyzer(),
    'cpp': CPPAnalyzer(),
    'javascript': JavaScriptAnalyzer(),
    'html': HTMLAnalyzer(),
    'generic': GenericAnalyzer()
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        code = data.get('code', '')
        language = data.get('language', 'auto')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        print(f"📝 Analyzing code: {len(code)} chars, language: {language}")
        
        # Detect language if auto
        if language == 'auto':
            language = detect_language(code)
            print(f"🔍 Auto-detected language: {language}")
        
        # Get the appropriate analyzer
        analyzer = analyzers.get(language, analyzers['generic'])
        
        # Analyze the code
        result = analyzer.analyze(code)
        
        print(f"✅ Analysis complete: {len(result['errors'])} errors, {len(result['warnings'])} warnings")
        
        # Return the results
        return jsonify({
            'success': True,
            'language': language,
            'errors': result['errors'],
            'warnings': result['warnings'],
            'summary': result['summary']
        })
        
    except Exception as e:
        print(f"❌ Error in analyze: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-file', methods=['POST'])
def analyze_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content
        code = file.read().decode('utf-8')
        
        # Detect language from file extension
        extension = os.path.splitext(file.filename)[1].lower()
        language = detect_language(code, extension)
        
        # Get the appropriate analyzer
        analyzer = analyzers.get(language, analyzers['generic'])
        
        # Analyze the code
        result = analyzer.analyze(code)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'language': language,
            'code': code[:500] + ('...' if len(code) > 500 else ''),
            'errors': result['errors'],
            'warnings': result['warnings'],
            'summary': result['summary']
        })
        
    except Exception as e:
        print(f"❌ Error in analyze-file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'analyzers': list(analyzers.keys())
    })

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Flask server on http://127.0.0.1:5000")
    print("="*50)
    print(f"📊 Available analyzers: {', '.join(analyzers.keys())}")
    print("📁 Templates folder:", app.template_folder)
    print("="*50 + "\n")
    app.run(debug=True, port=5000)