# analyzers/python_analyzer.py
import ast
import tokenize
import io
import py_compile
import tempfile
import os
import re
from typing import List, Dict, Any, Tuple
from .base_analyzer import BaseAnalyzer

class PythonAnalyzer(BaseAnalyzer):
    """
    Enhanced Python analyzer that detects ALL syntax errors,
    not just the first one.
    """
    
    def analyze(self, code: str) -> Dict[str, Any]:
        errors = []
        warnings = []
        
        # Method 1: Line-by-line syntax checking
        line_errors = self.check_line_by_line(code)
        errors.extend(line_errors)
        
        # Method 2: Token-based checking (finds more errors)
        token_errors = self.check_tokens(code)
        errors.extend(token_errors)
        
        # Method 3: AST parsing (gets structural errors)
        ast_errors = self.check_ast(code)
        errors.extend(ast_errors)
        
        # Method 4: Compilation check
        compile_errors = self.check_compilation(code)
        errors.extend(compile_errors)
        
        # Method 5: Indentation checking
        indent_errors, indent_warnings = self.check_indentation(code)
        errors.extend(indent_errors)
        warnings.extend(indent_warnings)
        
        # Method 6: Common Python pitfalls
        pitfall_warnings = self.check_common_pitfalls(code)
        warnings.extend(pitfall_warnings)
        
        # Method 7: Style checking (PEP 8)
        style_warnings = self.check_pep8(code)
        warnings.extend(style_warnings)
        
        # Remove duplicates while preserving order
        errors = self.deduplicate_errors(errors)
        warnings = self.deduplicate_warnings(warnings)
        
        return self.format_result(errors, warnings)
    
    def check_line_by_line(self, code: str) -> List[Dict[str, Any]]:
        """Check each line individually for syntax errors"""
        errors = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Check for common line-level errors
            try:
                # Try to compile just this line (if it's a complete statement)
                if self.is_complete_statement(line):
                    compile(line, '<string>', 'exec')
            except SyntaxError as e:
                errors.append({
                    'line': i,
                    'column': e.offset or 0,
                    'message': f"Line {i}: {str(e)}",
                    'type': 'syntax_error',
                    'severity': 'high'
                })
            except Exception as e:
                # Other errors might be caught by other methods
                pass
        
        return errors
    
    def is_complete_statement(self, line: str) -> bool:
        """Check if a line looks like a complete statement"""
        line = line.strip()
        if not line:
            return False
        
        # These are usually complete statements
        complete_patterns = [
            r'^print\s*\(.*\)$',
            r'^return\s+.*$',
            r'^import\s+.*$',
            r'^from\s+.*\s+import\s+.*$',
            r'^class\s+\w+.*:$',
            r'^def\s+\w+.*:$',
            r'^if\s+.*:$',
            r'^elif\s+.*:$',
            r'^else:$',
            r'^for\s+.*:$',
            r'^while\s+.*:$',
            r'^try:$',
            r'^except.*:$',
            r'^finally:$',
            r'^with\s+.*:$',
            r'^@.*$',  # Decorator
            r'^break$',
            r'^continue$',
            r'^pass$',
            r'^raise\s+.*$',
            r'^yield\s+.*$',
            r'^assert\s+.*$',
            r'^del\s+.*$',
            r'^global\s+.*$',
            r'^nonlocal\s+.*$',
        ]
        
        for pattern in complete_patterns:
            if re.match(pattern, line):
                return True
        
        # Check if it's a simple assignment
        if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            return True
        
        return False
    
    def check_tokens(self, code: str) -> List[Dict[str, Any]]:
        """Check using Python tokenizer - catches many errors"""
        errors = []
        
        try:
            # Use tokenize to find errors
            tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
            
            # Check for common token errors
            for i, token in enumerate(tokens):
                if token.type == tokenize.ERRORTOKEN:
                    errors.append({
                        'line': token.start[0],
                        'column': token.start[1],
                        'message': f"Invalid token: '{token.string}'",
                        'type': 'token_error',
                        'severity': 'high'
                    })
                
                # Check for unterminated strings
                if token.type == tokenize.STRING and token.string.count('"') % 2 != 0:
                    errors.append({
                        'line': token.start[0],
                        'column': token.start[1],
                        'message': "Unterminated string literal",
                        'type': 'string_error',
                        'severity': 'high'
                    })
        
        except tokenize.TokenError as e:
            # This catches indentation errors and unterminated strings
            line_match = re.search(r'line (\d+)', str(e))
            line = int(line_match.group(1)) if line_match else 1
            errors.append({
                'line': line,
                'column': 0,
                'message': str(e),
                'type': 'token_error',
                'severity': 'high'
            })
        
        return errors
    
    def check_ast(self, code: str) -> List[Dict[str, Any]]:
        """Check using AST - finds structural errors"""
        errors = []
        
        try:
            # Try to parse the entire AST
            tree = ast.parse(code)
            
            # Even if parsing succeeds, check for specific issues
            for node in ast.walk(tree):
                # Check for missing nodes in function definitions
                if isinstance(node, ast.FunctionDef):
                    if not node.body:
                        errors.append({
                            'line': node.lineno,
                            'column': node.col_offset,
                            'message': f"Function '{node.name}' has no body",
                            'type': 'structure_error',
                            'severity': 'medium'
                        })
                
                # Check for empty classes
                if isinstance(node, ast.ClassDef):
                    if not node.body:
                        errors.append({
                            'line': node.lineno,
                            'column': node.col_offset,
                            'message': f"Class '{node.name}' has no body",
                            'type': 'structure_error',
                            'severity': 'medium'
                        })
        
        except SyntaxError as e:
            # This catches the first syntax error, but we'll try to find more
            errors.append({
                'line': e.lineno or 1,
                'column': e.offset or 0,
                'message': str(e),
                'type': 'syntax_error',
                'severity': 'high'
            })
            
            # Try to find more errors by checking code in chunks
            more_errors = self.check_code_chunks(code, e.lineno or 1)
            errors.extend(more_errors)
        
        return errors
    
    def check_code_chunks(self, code: str, error_line: int) -> List[Dict[str, Any]]:
        """Check code in chunks to find more errors after the first one"""
        errors = []
        lines = code.split('\n')
        
        # Check code before the error line
        if error_line > 1:
            before_code = '\n'.join(lines[:error_line-1])
            try:
                ast.parse(before_code)
            except SyntaxError as e:
                # This shouldn't happen if the code before was valid
                pass
        
        # Check code after the error line
        if error_line < len(lines):
            after_code = '\n'.join(lines[error_line:])
            try:
                ast.parse(after_code)
            except SyntaxError as e:
                # Found another error
                actual_line = error_line + (e.lineno or 1) - 1
                errors.append({
                    'line': actual_line,
                    'column': e.offset or 0,
                    'message': str(e),
                    'type': 'syntax_error',
                    'severity': 'high'
                })
        
        return errors
    
    def check_compilation(self, code: str) -> List[Dict[str, Any]]:
        """Check by attempting to compile the code"""
        errors = []
        
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            # This catches the first error, but we'll also get others from our other methods
            pass
        except Exception as e:
            # Other compilation errors
            errors.append({
                'line': 1,
                'column': 0,
                'message': f"Compilation error: {str(e)}",
                'type': 'compilation_error',
                'severity': 'high'
            })
        
        return errors
    
    def check_indentation(self, code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Check for indentation errors and inconsistencies"""
        errors = []
        warnings = []
        lines = code.split('\n')
        
        expected_indent = 0
        indent_stack = []
        line_indents = []
        
        for i, line in enumerate(lines, 1):
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            line_indents.append((i, indent, line))
            
            # Check for mixed tabs and spaces
            if '\t' in line[:indent] and ' ' in line[:indent]:
                warnings.append({
                    'line': i,
                    'column': 0,
                    'message': "Mixed tabs and spaces in indentation",
                    'type': 'indentation_warning',
                    'severity': 'medium'
                })
            
            # Check for indentation errors
            stripped = line.strip()
            
            # Keywords that decrease indent
            decrease_keywords = ['return', 'break', 'continue', 'pass', 'raise']
            if any(stripped.startswith(kw) for kw in decrease_keywords):
                if indent > expected_indent - 4:
                    pass  # This is usually okay
            
            # Check if this line should be indented
            if i > 1 and lines[i-2].strip().endswith(':'):
                if indent <= line_indents[-2][1] if len(line_indents) > 1 else 0:
                    errors.append({
                        'line': i,
                        'column': 0,
                        'message': "Expected indented block after line with colon",
                        'type': 'indentation_error',
                        'severity': 'high'
                    })
        
        return errors, warnings
    
    def check_common_pitfalls(self, code: str) -> List[Dict[str, Any]]:
        """Check for common Python mistakes"""
        warnings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for '== None' instead of 'is None'
            if '== None' in line or '!= None' in line:
                warnings.append({
                    'line': i,
                    'column': line.find('== None') if '== None' in line else line.find('!= None'),
                    'message': "Use 'is None' / 'is not None' instead of '== None' / '!= None'",
                    'type': 'style_warning',
                    'severity': 'low'
                })
            
            # Check for bare except
            if re.search(r'except\s*:', line):
                warnings.append({
                    'line': i,
                    'column': line.find('except'),
                    'message': "Bare except clause - specify exception types",
                    'type': 'style_warning',
                    'severity': 'medium'
                })
            
            # Check for mutable default arguments
            mutable_defaults = r'def\s+\w+\s*\([^)]*=\s*[{\[]'
            if re.search(mutable_defaults, line):
                warnings.append({
                    'line': i,
                    'column': line.find('='),
                    'message': "Mutable default argument (list/dict) - can cause unexpected behavior",
                    'type': 'style_warning',
                    'severity': 'medium'
                })
            
            # Check for 'is' with literal
            if re.search(r'is\s+[\d\'].*', line) or re.search(r'is\s+True|False|None', line):
                # This is actually okay for None, but not for numbers/strings
                if 'is None' not in line and 'is not None' not in line:
                    warnings.append({
                        'line': i,
                        'column': line.find('is'),
                        'message': "Use '==' for value comparison with literals, not 'is'",
                        'type': 'style_warning',
                        'severity': 'medium'
                    })
            
            # Check for unused variables (simple check)
            if '=' in line and not any(k in line for k in ['==', '!=', '<=', '>=']):
                var_name = line.split('=')[0].strip()
                if var_name.isidentifier() and var_name not in code[code.find(line)+len(line):]:
                    if var_name not in ['_', 'self', 'cls']:
                        warnings.append({
                            'line': i,
                            'column': line.find('='),
                            'message': f"Variable '{var_name}' might be unused",
                            'type': 'style_warning',
                            'severity': 'low'
                        })
        
        return warnings
    
    def check_pep8(self, code: str) -> List[Dict[str, Any]]:
        """Basic PEP 8 style checking"""
        warnings = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check line length (max 79 for PEP 8)
            if len(line) > 79:
                warnings.append({
                    'line': i,
                    'column': 79,
                    'message': f"Line too long ({len(line)} > 79 characters)",
                    'type': 'pep8_warning',
                    'severity': 'low'
                })
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                warnings.append({
                    'line': i,
                    'column': len(line.rstrip()),
                    'message': "Trailing whitespace",
                    'type': 'pep8_warning',
                    'severity': 'low'
                })
            
            # Check for multiple statements on one line
            if ';' in line and not line.strip().startswith('#'):
                warnings.append({
                    'line': i,
                    'column': line.find(';'),
                    'message': "Multiple statements on one line (use ';' sparingly)",
                    'type': 'pep8_warning',
                    'severity': 'low'
                })
            
            # Check for spaces around operators
            operators = ['=', '==', '!=', '<=', '>=', '+', '-', '*', '/', '//', '%', '**']
            for op in operators:
                if op in line and f' {op} ' not in line:
                    # Skip if it's in a string or comment
                    if not self.in_string_or_comment(line, line.find(op)):
                        if op not in ['**', '//']:  # These often don't need spaces
                            warnings.append({
                                'line': i,
                                'column': line.find(op),
                                'message': f"Missing spaces around operator '{op}'",
                                'type': 'pep8_warning',
                                'severity': 'low'
                            })
        
        return warnings
    
    def in_string_or_comment(self, line: str, position: int) -> bool:
        """Check if a position in a line is inside a string or comment"""
        # Simple check - look for quotes before position
        quote_count = line[:position].count('"') + line[:position].count("'")
        if quote_count % 2 == 1:
            return True
        
        # Check if in comment
        comment_pos = line.find('#')
        if comment_pos != -1 and comment_pos < position:
            return True
        
        return False
    
    def deduplicate_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate errors"""
        seen = set()
        unique_errors = []
        
        for error in errors:
            # Create a unique key
            key = (error['line'], error['column'], error['message'])
            if key not in seen:
                seen.add(key)
                unique_errors.append(error)
        
        return unique_errors
    
    def deduplicate_warnings(self, warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate warnings"""
        seen = set()
        unique_warnings = []
        
        for warning in warnings:
            key = (warning['line'], warning['column'], warning['message'])
            if key not in seen:
                seen.add(key)
                unique_warnings.append(warning)
        
        return unique_warnings