from html.parser import HTMLParser
import re
from analyzers.base_analyzer import BaseAnalyzer

class HTMLSyntaxChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
        self.warnings = []
        self.tag_stack = []
        self.line_numbers = {}
        
    def handle_starttag(self, tag, attrs):
        self.tag_stack.append((tag, self.getpos()[0]))
        
    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1][0] == tag:
            self.tag_stack.pop()
        else:
            # Check if it's a self-closing tag
            if tag not in ['br', 'hr', 'img', 'input', 'link', 'meta']:
                self.errors.append({
                    'line': self.getpos()[0],
                    'column': self.getpos()[1],
                    'message': f'Unexpected closing tag: {tag}',
                    'type': 'html_error'
                })
    
    def handle_startendtag(self, tag, attrs):
        # Self-closing tag, ignore
        pass
    
    def error(self, message):
        self.errors.append({
            'line': self.getpos()[0],
            'column': self.getpos()[1],
            'message': message,
            'type': 'html_error'
        })

class HTMLAnalyzer(BaseAnalyzer):
    def analyze(self, code):
        errors = []
        warnings = []
        
        # Basic HTML structure check
        if '<!DOCTYPE html>' not in code.upper():
            warnings.append({
                'line': 1,
                'column': 0,
                'message': 'Missing DOCTYPE declaration',
                'type': 'html_warning'
            })
        
        # Check for required tags
        if '<html' not in code:
            warnings.append({
                'line': 1,
                'column': 0,
                'message': 'Missing <html> tag',
                'type': 'html_warning'
            })
        
        if '<head>' not in code and '<head ' not in code:
            warnings.append({
                'line': 1,
                'column': 0,
                'message': 'Missing <head> section',
                'type': 'html_warning'
            })
        
        if '<body>' not in code and '<body ' not in code:
            warnings.append({
                'line': 1,
                'column': 0,
                'message': 'Missing <body> tag',
                'type': 'html_warning'
            })
        
        # Use HTML parser for syntax checking
        parser = HTMLSyntaxChecker()
        try:
            parser.feed(code)
            errors.extend(parser.errors)
            
            # Check for unclosed tags
            for tag, line in parser.tag_stack:
                errors.append({
                    'line': line,
                    'column': 0,
                    'message': f'Unclosed tag: <{tag}>',
                    'type': 'html_error'
                })
                
        except Exception as e:
            errors.append({
                'line': 1,
                'column': 0,
                'message': f'HTML parsing error: {str(e)}',
                'type': 'parsing_error'
            })
        
        # Check for common HTML issues
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Check for unquoted attributes
            attr_pattern = r'<[^>]+\s+(\w+)=[^"\'\s>][^>\s]*'
            unquoted = re.findall(attr_pattern, line)
            if unquoted:
                warnings.append({
                    'line': i + 1,
                    'column': 0,
                    'message': f'Unquoted attribute values found',
                    'type': 'html_warning'
                })
        
        return self.format_result(errors, warnings)