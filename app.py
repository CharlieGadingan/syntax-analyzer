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

# Store assignment feedback (in production, use a database)
assignment_feedback = {}

# Store cloned repo paths for file access
repo_paths = {}

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

@app.route('/clone-repo', methods=['POST'])
def clone_repo():
    """Clone a repository and return file list"""
    try:
        data = request.get_json()
        repo_url = data.get('url')
        branch = data.get('branch', 'main')
        
        if not repo_url:
            return jsonify({'error': 'No repository URL provided'}), 400
        
        # Create unique ID for this repo session
        session_id = str(uuid.uuid4())[:8]
        
        # Clone repository
        repo_path, repo_info = repo_analyzer.clone_repository(repo_url, branch)
        
        # Store the path for this session
        repo_paths[session_id] = {
            'path': str(repo_path),
            'url': repo_url,
            'info': repo_info
        }
        
        # Get list of files
        files = []
        for ext in repo_analyzer.SUPPORTED_EXTENSIONS:
            for file_path in repo_path.rglob(f"*{ext}"):
                rel_path = str(file_path.relative_to(repo_path))
                files.append({
                    'path': rel_path,
                    'name': file_path.name,
                    'language': repo_analyzer.SUPPORTED_EXTENSIONS[ext],
                    'size': file_path.stat().st_size
                })
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'repo_info': repo_info,
            'files': files,
            'total_files': len(files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/repo-files/<session_id>', methods=['GET'])
def get_repo_files(session_id):
    """Get list of files in a cloned repository"""
    try:
        if session_id not in repo_paths:
            return jsonify({'error': 'Session not found. Please clone the repository first.'}), 404
        
        repo_data = repo_paths[session_id]
        repo_path = Path(repo_data['path'])
        
        files = []
        for ext in repo_analyzer.SUPPORTED_EXTENSIONS:
            for file_path in repo_path.rglob(f"*{ext}"):
                rel_path = str(file_path.relative_to(repo_path))
                files.append({
                    'path': rel_path,
                    'name': file_path.name,
                    'language': repo_analyzer.SUPPORTED_EXTENSIONS[ext],
                    'size': file_path.stat().st_size
                })
        
        return jsonify({
            'success': True,
            'files': files,
            'total_files': len(files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/file-content', methods=['POST'])
def get_file_content():
    """Get content of a specific file from cloned repository"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        file_path = data.get('file_path')
        
        if not session_id or not file_path:
            return jsonify({'error': 'Session ID and file path required'}), 400
        
        if session_id not in repo_paths:
            return jsonify({'error': 'Session not found'}), 404
        
        repo_path = Path(repo_paths[session_id]['path'])
        full_path = repo_path / file_path
        
        if not full_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Read file content
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Detect language
        ext = Path(file_path).suffix.lower()
        language = repo_analyzer.SUPPORTED_EXTENSIONS.get(ext, 'unknown')
        
        return jsonify({
            'success': True,
            'content': content,
            'language': language,
            'file_path': file_path
        })
        
    except UnicodeDecodeError:
        return jsonify({'error': 'Cannot read binary file'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-file-content', methods=['POST'])
def analyze_file_content():
    """Analyze content of a specific file"""
    try:
        data = request.get_json()
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

@app.route('/save-feedback', methods=['POST'])
def save_feedback():
    """Save professor feedback for an assignment"""
    try:
        data = request.get_json()
        
        assignment_id = data.get('assignment_id')
        feedback = data.get('feedback')
        file_path = data.get('file_path')
        errors = data.get('errors', [])
        warnings = data.get('warnings', [])
        
        if not assignment_id:
            return jsonify({'error': 'Assignment ID required'}), 400
        
        # Store feedback
        if assignment_id not in assignment_feedback:
            assignment_feedback[assignment_id] = {}
        
        assignment_feedback[assignment_id][file_path] = {
            'feedback': feedback,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if all files have feedback
        session_id = data.get('session_id')
        if session_id and session_id in repo_paths:
            repo_path = Path(repo_paths[session_id]['path'])
            total_files = len(list(repo_path.rglob('*.*')))
            checked_files = len(assignment_feedback[assignment_id])
            
            return jsonify({
                'success': True,
                'message': 'Feedback saved',
                'progress': f'{checked_files}/{total_files} files checked',
                'all_checked': checked_files >= total_files
            })
        
        return jsonify({
            'success': True,
            'message': 'Feedback saved'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-feedback/<assignment_id>', methods=['GET'])
def get_feedback(assignment_id):
    """Get feedback for an assignment"""
    try:
        feedback = assignment_feedback.get(assignment_id, {})
        return jsonify({
            'success': True,
            'feedback': feedback
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cleanup-repo/<session_id>', methods=['POST'])
def cleanup_repo(session_id):
    """Clean up a cloned repository"""
    try:
        if session_id in repo_paths:
            repo_path = Path(repo_paths[session_id]['path'])
            if repo_path.exists():
                import shutil
                shutil.rmtree(repo_path)
            del repo_paths[session_id]
        
        return jsonify({
            'success': True,
            'message': 'Repository cleaned up'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add Path import
from pathlib import Path

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SYNTAX ANALYZER WITH REPOSITORY SUPPORT")
    print("="*60)
    print(f"📊 Analyzers: {', '.join(analyzers.keys())}")
    print(f"📁 Templates: {app.template_folder}")
    print(f"🌐 URL: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)