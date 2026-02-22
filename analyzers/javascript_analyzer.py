import subprocess
import tempfile
import os
import json
from analyzers.base_analyzer import BaseAnalyzer

class JavaScriptAnalyzer(BaseAnalyzer):
    def analyze(self, code):
        errors = []
        warnings = []
        
        # Try using ESLint if available
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Try ESLint
            result = subprocess.run(
                ['eslint', '--format', 'json', temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout:
                try:
                    eslint_output = json.loads(result.stdout)
                    if eslint_output and len(eslint_output) > 0:
                        for message in eslint_output[0].get('messages', []):
                            error_item = {
                                'line': message.get('line', 1),
                                'column': message.get('column', 0),
                                'message': message.get('message', 'Unknown error'),
                                'type': 'eslint_' + message.get('severity', 1)
                            }
                            if message.get('severity', 1) == 2:  # Error
                                errors.append(error_item)
                            else:  # Warning
                                warnings.append(error_item)
                except json.JSONDecodeError:
                    pass
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to basic syntax checking
            self._basic_js_check(code, errors, warnings)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
        return self.format_result(errors, warnings)
    
    def _basic_js_check(self, code, errors, warnings):
        """Basic JavaScript syntax checking without ESLint"""
        
        # Check for basic syntax errors
        lines = code.split('\n')
        bracket_count = 0
        paren_count = 0
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Count brackets
            bracket_count += line.count('{') - line.count('}')
            paren_count += line.count('(') - line.count(')')
            
            # Check for common errors
            if '===' in line and '!==' not in line:
                if '===' in line and 'if' in line:
                    # This is fine, it's strict equality
                    pass
            elif '==' in line and '===' not in line and '!=' in line:
                warnings.append({
                    'line': line_num,
                    'column': line.find('=='),
                    'message': 'Consider using strict equality (===) instead of (==)',
                    'type': 'style_warning'
                })
            
            # Check for missing semicolons (basic)
            if line.strip() and not line.strip().endswith(';') and not line.strip().endswith('{') and not line.strip().endswith('}') and not line.strip().startswith('//'):
                if not any(keyword in line for keyword in ['if', 'else', 'for', 'while', 'function']):
                    warnings.append({
                        'line': line_num,
                        'column': len(line),
                        'message': 'Missing semicolon',
                        'type': 'style_warning'
                    })
        
        # Check for unmatched brackets
        if bracket_count != 0:
            errors.append({
                'line': 1,
                'column': 0,
                'message': f'Unmatched curly braces: {bracket_count}',
                'type': 'syntax_error'
            })
        
        if paren_count != 0:
            errors.append({
                'line': 1,
                'column': 0,
                'message': f'Unmatched parentheses: {paren_count}',
                'type': 'syntax_error'
            })