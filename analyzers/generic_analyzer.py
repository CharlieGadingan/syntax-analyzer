import re
from analyzers.base_analyzer import BaseAnalyzer  # Fixed import

class GenericAnalyzer(BaseAnalyzer):
    def analyze(self, code):
        errors = []
        warnings = []
        
        # Use base class methods
        bracket_errors = self.check_brackets(code)
        errors.extend(bracket_errors)
        
        quote_errors = self.check_quotes(code)
        errors.extend(quote_errors)
        
        line_length_warnings = self.check_line_length(code)
        warnings.extend(line_length_warnings)
        
        # Basic syntax checks
        lines = code.split('\n')
        for i, line in enumerate(lines):
            line_num = i + 1
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                warnings.append(self.create_warning('Trailing whitespace', line_num, len(line.rstrip())))
        
        return self.format_result(errors, warnings)