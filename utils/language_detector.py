# utils/language_detector.py
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
    
    # Detect by content patterns - ENHANCED for better Python detection
    patterns = {
        'python': [
            r'^\s*def\s+\w+\s*\(.*\)\s*:',
            r'^\s*class\s+\w+\s*:',
            r'^\s*import\s+\w+',
            r'^\s*from\s+\w+\s+import',
            r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:',
            r'print\s*\(',  # Python print with parentheses
            r'^\s*for\s+\w+\s+in\s+',  # Python for loop
            r'^\s*while\s+.*:',
            r'^\s*if\s+.*:',  # Python if statement
            r'^\s*elif\s+.*:',
            r'^\s*else\s*:',
            r'^\s*try\s*:',
            r'^\s*except\s+.*:',
            r'^\s*final\s*:',
            r'^\s*with\s+.*:',
            r'^\s*@',  # Decorator
            r'#.*$',  # Python comments
        ],
        'java': [
            r'public\s+class\s+\w+',
            r'public\s+static\s+void\s+main',
            r'System\.out\.println',
            r'import\s+java\.',
            r'@Override',
            r'private\s+\w+\s+\w+',
            r'protected\s+\w+\s+\w+',
            r'new\s+[A-Z]\w+\s*\('
        ],
        'javascript': [
            r'function\s+\w+\s*\(.*\)\s*{',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'document\.getElementById',
            r'console\.log',
            r'=>\s*{',
            r'for\s*\(.*;.*;.*\)\s*{',
            r'if\s*\(.*\)\s*{'
        ],
        'html': [
            r'<!DOCTYPE\s+html>',
            r'<html>',
            r'<body>',
            r'<div\s+class=',
            r'<script>',
            r'<style>',
            r'<h[1-6]>',
            r'<p>'
        ],
        'cpp': [
            r'#include\s*<[^>]+>',
            r'using\s+namespace\s+std;',
            r'int\s+main\s*\(.*\)\s*{',
            r'std::cout',
            r'class\s+\w+\s*{',
            r'cout\s*<<',
            r'cin\s*>>'
        ]
    }
    
    # Add more weight to Python-specific patterns
    scores = {}
    lines = code.split('\n')
    
    for lang, lang_patterns in patterns.items():
        score = 0
        for pattern in lang_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            score += len(matches) * 2  # Give more weight to each match
            
            # Check line by line for certain patterns
            for line in lines[:10]:  # Check first 10 lines
                if re.search(pattern, line):
                    score += 1
        
        scores[lang] = score
    
    # Also check for Python-specific syntax even with errors
    if 'print' in code and '(' in code and ')' in code:
        scores['python'] = scores.get('python', 0) + 2
    
    if 'if' in code and ':' in code:
        scores['python'] = scores.get('python', 0) + 2
    
    if '#' in code and not '//' in code:  # Python comments vs JS/C++ comments
        scores['python'] = scores.get('python', 0) + 3
    
    # Get language with highest score
    if max(scores.values()) > 0:
        detected = max(scores, key=scores.get)
        return detected
    
    # Default fallback based on common patterns
    if 'def ' in code or 'print(' in code or 'if ' in code and ':' in code:
        return 'python'
    
    return 'generic'