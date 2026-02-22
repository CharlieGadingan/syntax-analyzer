import re

def detect_language(code, extension=None):
    """Detect programming language from code content and file extension"""
    
    # Check by file extension first
    if extension:
        ext_map = {
            '.py': 'python',
            '.java': 'java',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.h': 'cpp',
            '.js': 'javascript',
            '.html': 'html', '.htm': 'html',
            '.css': 'css',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.ts': 'typescript'
        }
        if extension in ext_map:
            return ext_map[extension]
    
    # Detect by content patterns
    patterns = {
        'python': [
            r'^\s*def\s+\w+\s*\(.*\)\s*:',
            r'^\s*class\s+\w+\s*:',
            r'^\s*import\s+\w+',
            r'^\s*from\s+\w+\s+import',
            r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:'
        ],
        'java': [
            r'public\s+class\s+\w+',
            r'public\s+static\s+void\s+main',
            r'System\.out\.println',
            r'import\s+java\.',
            r'@Override'
        ],
        'javascript': [
            r'function\s+\w+\s*\(.*\)\s*{',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'document\.getElementById',
            r'console\.log',
            r'=>\s*{'
        ],
        'html': [
            r'<!DOCTYPE\s+html>',
            r'<html>',
            r'<body>',
            r'<div\s+class=',
            r'<script>',
            r'<style>'
        ],
        'cpp': [
            r'#include\s*<[^>]+>',
            r'using\s+namespace\s+std;',
            r'int\s+main\s*\(.*\)\s*{',
            r'std::cout',
            r'class\s+\w+\s*{'
        ]
    }
    
    scores = {}
    for lang, lang_patterns in patterns.items():
        score = 0
        for pattern in lang_patterns:
            if re.search(pattern, code, re.MULTILINE):
                score += 1
        scores[lang] = score
    
    # Get language with highest score
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    
    return 'generic'