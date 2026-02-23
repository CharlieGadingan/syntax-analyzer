# repo_analyzer.py
import os
import re
import json
import shutil
import tempfile
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from git import Repo, GitCommandError
from github import Github, GithubException
import gitlab

# Remove the import from app - we'll pass analyzers as parameter instead
# from app import analyzers  # <-- REMOVE THIS LINE

class RepositoryAnalyzer:
    """Analyzes code repositories for syntax errors"""
    
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.java': 'java',
        '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.hpp': 'cpp', '.h': 'cpp',
        '.js': 'javascript', '.jsx': 'javascript',
        '.ts': 'typescript', '.tsx': 'typescript',
        '.html': 'html', '.htm': 'html',
        '.css': 'css', '.scss': 'scss', '.sass': 'sass',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin', '.kts': 'kotlin',
        '.cs': 'csharp',
        '.json': 'json',
        '.yaml': 'yaml', '.yml': 'yaml',
        '.md': 'markdown',
        '.sql': 'sql',
        '.sh': 'bash',
        '.ps1': 'powershell'
    }
    
    def __init__(self, analyzers_dict=None, base_path: str = "data/repos"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.gitlab_token = os.getenv('GITLAB_TOKEN')
        self.analyzers = analyzers_dict or {}  # Store analyzers as instance variable
    
    def analyze_file(self, file_path: Path, analyzers=None) -> Dict[str, Any]:
        """Analyze a single file"""
        language = self.SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), 'unknown')
        analyzers_to_use = analyzers or self.analyzers
        
        if language == 'unknown':
            return {
                'file': str(file_path.relative_to(self.base_path)),
                'language': 'unknown',
                'errors': [],
                'warnings': [f"Unknown file type: {file_path.suffix}"],
                'status': 'skipped'
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except (UnicodeDecodeError, IOError):
            return {
                'file': str(file_path.relative_to(self.base_path)),
                'language': language,
                'errors': [f"Cannot read file (binary or encoding issue)"],
                'warnings': [],
                'status': 'error'
            }
        
        # Get analyzer
        analyzer = analyzers_to_use.get(language)
        if not analyzer:
            return {
                'file': str(file_path.relative_to(self.base_path)),
                'language': language,
                'errors': [],
                'warnings': [f"No analyzer for {language}"],
                'status': 'skipped'
            }
        
        # Analyze
        result = analyzer.analyze(code)
        
        return {
            'file': str(file_path.relative_to(self.base_path)),
            'language': language,
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'status': 'analyzed',
            'size': len(code)
        }
    
    def clone_repository(self, repo_url: str, branch: str = None, depth: int = 1):
        """Clone a git repository"""
        # Create a unique folder name
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:10]
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = self.base_path / f"{repo_name}_{repo_hash}"
        
        if repo_path.exists():
            shutil.rmtree(repo_path)
        
        print(f"📦 Cloning {repo_url} to {repo_path}")
        
        try:
            # Clone with specific options
            clone_kwargs = {
                'url': repo_url,
                'to_path': repo_path,
                'depth': depth,
                'no_single_branch': True
            }
            
            if branch:
                clone_kwargs['branch'] = branch
            
            repo = Repo.clone_from(**clone_kwargs)
            
            # Get repository info
            info = {
                'path': str(repo_path),
                'branch': repo.active_branch.name,
                'commit': repo.head.commit.hexsha,
                'last_commit': repo.head.commit.committed_datetime.isoformat()
            }
            
            return repo_path, info
            
        except GitCommandError as e:
            raise Exception(f"Git clone failed: {e}")
    
    def analyze_repository(self, repo_path: Path, max_files: int = 10000) -> Dict[str, Any]:
        """Analyze all files in repository"""
        start_time = time.time()
        
        results = {
            'repository': str(repo_path),
            'total_files': 0,
            'analyzed_files': 0,
            'skipped_files': 0,
            'files_with_errors': 0,
            'files_with_warnings': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'files': [],
            'languages': {},
            'error_types': {},
            'analysis_time': 0
        }
        
        # Find all supported files
        all_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            all_files.extend(repo_path.rglob(f"*{ext}"))
        
        # Limit files
        if len(all_files) > max_files:
            all_files = all_files[:max_files]
            results['truncated'] = True
        
        results['total_files'] = len(all_files)
        
        # Analyze in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_file = {executor.submit(self.analyze_file, f): f for f in all_files}
            
            for future in as_completed(future_to_file):
                file_result = future.result()
                results['files'].append(file_result)
                
                # Update counters
                if file_result['status'] == 'analyzed':
                    results['analyzed_files'] += 1
                elif file_result['status'] == 'skipped':
                    results['skipped_files'] += 1
                
                # Count errors/warnings
                errors = file_result.get('errors', [])
                warnings = file_result.get('warnings', [])
                
                if errors:
                    results['files_with_errors'] += 1
                    results['total_errors'] += len(errors)
                    
                    # Track error types
                    for error in errors:
                        error_type = error.get('type', 'unknown')
                        results['error_types'][error_type] = results['error_types'].get(error_type, 0) + 1
                
                if warnings:
                    results['files_with_warnings'] += 1
                    results['total_warnings'] += len(warnings)
                
                # Track languages
                lang = file_result['language']
                if lang != 'unknown':
                    results['languages'][lang] = results['languages'].get(lang, 0) + 1
        
        results['analysis_time'] = time.time() - start_time
        
        return results
    
    def generate_report(self, results: Dict[str, Any], format: str = 'json') -> str:
        """Generate analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path("data/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            report_path = report_dir / f"report_{timestamp}.json"
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif format == 'html':
            report_path = report_dir / f"report_{timestamp}.html"
            self._generate_html_report(results, report_path)
        
        return str(report_path)
    
    def _generate_html_report(self, results: Dict[str, Any], output_path: Path):
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Repository Analysis Report</title>
    <style>
        body {{ font-family: Arial; margin: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .stat-card {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Repository Analysis Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Total Files</h3>
            <p>{results['total_files']}</p>
        </div>
        <div class="stat-card">
            <h3>Files with Errors</h3>
            <p class="error">{results['files_with_errors']}</p>
        </div>
        <div class="stat-card">
            <h3>Files with Warnings</h3>
            <p class="warning">{results['files_with_warnings']}</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)