# analyzers/python_analyzer.py
import ast
from .base_analyzer import BaseAnalyzer

class PythonAnalyzer(BaseAnalyzer):
    def analyze(self, code):
        errors = []
        warnings = []
        
        # Use base class helper methods
        bracket_errors = self.check_brackets(code)
        errors.extend(bracket_errors)
        
        quote_errors = self.check_quotes(code)
        errors.extend(quote_errors)
        
        line_length_warnings = self.check_line_length(code)
        warnings.extend(line_length_warnings)
        
        # Python-specific syntax checking
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(self.create_error(
                str(e),
                e.lineno or 1,
                e.offset or 0
            ))
        
        # Return formatted result using base class method
        return self.format_result(errors, warnings)