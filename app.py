# app.py - Modified version that works without Celery
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import threading

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import analyzers
try:
    from analyzers.python_analyzer import PythonAnalyzer
    from analyzers.java_analyzer import JavaAnalyzer
    from analyzers.cpp_analyzer import CPPAnalyzer
    from analyzers.javascript_analyzer import JavaScriptAnalyzer
    from analyzers.html_analyzer import HTMLAnalyzer
    from analyzers.generic_analyzer import GenericAnalyzer
    from utils.language_detector import detect_language
    from repo_analyzer import RepositoryAnalyzer
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

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

# Initialize repository analyzer
repo_analyzer = RepositoryAnalyzer()

# Store task status in memory (replace with Redis in production)
task_status = {}

def run_repo_analysis(task_id, repo_url, branch, options):
    """Run repository analysis in background thread"""
    try:
        task_status[task_id] = {'state': 'PROGRESS', 'progress': 10, 'stage': 'cloning'}
        
        # Clone repository
        repo_path, repo_info = repo_analyzer.clone_repository(repo_url, branch)
        
        task_status[task_id] = {'state': 'PROGRESS', 'progress': 30, 'stage': 'analyzing'}
        
        # Analyze repository
        results = repo_analyzer.analyze_repository(repo_path)
        results['repo_info'] = repo_info
        results['task_id'] = task_id
        
        task_status[task_id] = {'state': 'PROGRESS', 'progress': 80, 'stage': 'generating_report'}
        
        # Generate reports
        html_report = repo_analyzer.generate_report(results, format='html')
        json_report = repo_analyzer.generate_report(results, format='json')
        
        # Clean up if not keeping files
        if not options.get('keep_files'):
            import shutil
            shutil.rmtree(repo_path)
        
        task_status[task_id] = {
            'state': 'SUCCESS',
            'progress': 100,
            'results': results,
            'reports': {
                'html': html_report,
                'json': json_report
            }
        }
        
    except Exception as e:
        task_status[task_id] = {
            'state': 'FAILURE',
            'error': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'analyzers': list(analyzers.keys()),
        'version': '2.0.0'
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze code snippet"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data'}), 400
        
        code = data.get('code', '')
        language = data.get('language', 'auto')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Detect language if auto
        if language == 'auto':
            language = detect_language(code)
        
        # Get analyzer
        analyzer = analyzers.get(language, analyzers['generic'])
        
        # Analyze
        result = analyzer.analyze(code)
        
        return jsonify({
            'success': True,
            'language': language,
            'errors': result['errors'],
            'warnings': result['warnings'],
            'summary': result['summary']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-file', methods=['POST'])
def analyze_file():
    """Analyze uploaded file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Read file
        code = file.read().decode('utf-8')
        
        # Detect language
        ext = os.path.splitext(filename)[1].lower()
        language = detect_language(code, ext)
        
        # Analyze
        analyzer = analyzers.get(language, analyzers['generic'])
        result = analyzer.analyze(code)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'language': language,
            'code': code[:500] + ('...' if len(code) > 500 else ''),
            'errors': result['errors'],
            'warnings': result['warnings'],
            'summary': result['summary']
        })
        
    except UnicodeDecodeError:
        return jsonify({'error': 'File must be text/plain or code'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-repo', methods=['POST'])
def analyze_repo():
    """Start repository analysis"""
    try:
        data = request.get_json()
        
        repo_url = data.get('url')
        branch = data.get('branch')
        options = {
            'deep_scan': data.get('deep_scan', False),
            'max_files': data.get('max_files', 10000),
            'keep_files': data.get('keep_files', False)
        }
        
        if not repo_url:
            return jsonify({'error': 'No repository URL provided'}), 400
        
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Start background thread
        thread = threading.Thread(
            target=run_repo_analysis,
            args=(task_id, repo_url, branch, options)
        )
        thread.daemon = True
        thread.start()
        
        # Initialize status
        task_status[task_id] = {'state': 'PENDING', 'progress': 0}
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Repository analysis started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/task-status/<task_id>', methods=['GET'])
def task_status_endpoint(task_id):
    """Get task status"""
    try:
        status = task_status.get(task_id, {'state': 'NOT_FOUND'})
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-report/<path:report_path>', methods=['GET'])
def download_report(report_path):
    """Download analysis report"""
    try:
        report_file = os.path.join('data/reports', secure_filename(report_path))
        if os.path.exists(report_file):
            return send_file(report_file, as_attachment=True)
        return jsonify({'error': 'Report not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/supported-languages', methods=['GET'])
def supported_languages():
    """Get supported languages"""
    return jsonify({
        'languages': list(analyzers.keys()),
        'extensions': repo_analyzer.SUPPORTED_EXTENSIONS
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SYNTAX ANALYZER WITH REPOSITORY SUPPORT")
    print("="*60)
    print(f"📊 Analyzers: {', '.join(analyzers.keys())}")
    print(f"📁 Templates: {app.template_folder}")
    print(f"🌐 URL: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)