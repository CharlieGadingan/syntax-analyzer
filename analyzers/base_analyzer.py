"""
Base Analyzer Module

This module defines the abstract base class for all language analyzers.
All specific language analyzers (Python, Java, C++, etc.) should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAnalyzer(ABC):
    """
    Abstract base class for all code analyzers.
    
    This class defines the interface that all language-specific analyzers must implement.
    It provides common functionality for formatting results and handling errors.
    """
    
    @abstractmethod
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyze code and return errors and warnings.
        
        This method must be implemented by all subclasses.
        
        Args:
            code (str): The source code to analyze
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - errors: List of error objects
                - warnings: List of warning objects
                - summary: Summary statistics
        """
        pass
    
    def format_result(self, errors: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format the analysis result into a standardized structure.
        
        Args:
            errors: List of error objects found during analysis
            warnings: List of warning objects found during analysis
            
        Returns:
            Dict[str, Any]: Formatted result with errors, warnings, and summary
        """
        return {
            'errors': errors,
            'warnings': warnings,
            'summary': {
                'error_count': len(errors),
                'warning_count': len(warnings),
                'has_errors': len(errors) > 0,
                'has_warnings': len(warnings) > 0,
                'is_valid': len(errors) == 0
            }
        }
    
    def validate_line(self, line: str, line_number: int) -> List[Dict[str, Any]]:
        """
        Basic line validation that can be used by all analyzers.
        
        Args:
            line: The line of code to validate
            line_number: The line number
            
        Returns:
            List of warnings/errors for this line
        """
        issues = []
        
        # Check for trailing whitespace
        if line.rstrip() != line:
            issues.append({
                'line': line_number,
                'column': len(line.rstrip()),
                'message': 'Trailing whitespace detected',
                'type': 'style_warning',
                'severity': 'low'
            })
        
        # Check for tabs (if you prefer spaces)
        if '\t' in line:
            issues.append({
                'line': line_number,
                'column': line.find('\t'),
                'message': 'Tabs detected. Consider using spaces for indentation.',
                'type': 'style_warning',
                'severity': 'low'
            })
        
        return issues
    
    def create_error(self, message: str, line: int = 1, column: int = 0, 
                    error_type: str = 'syntax_error', severity: str = 'high') -> Dict[str, Any]:
        """
        Helper method to create a standardized error object.
        
        Args:
            message: Error message
            line: Line number where error occurred
            column: Column number where error occurred
            error_type: Type of error (syntax_error, compilation_error, etc.)
            severity: Error severity (high, medium, low)
            
        Returns:
            Dict[str, Any]: Formatted error object
        """
        return {
            'line': line,
            'column': column,
            'message': message,
            'type': error_type,
            'severity': severity
        }
    
    def create_warning(self, message: str, line: int = 1, column: int = 0,
                      warning_type: str = 'style_warning', severity: str = 'medium') -> Dict[str, Any]:
        """
        Helper method to create a standardized warning object.
        
        Args:
            message: Warning message
            line: Line number where warning occurred
            column: Column number where warning occurred
            warning_type: Type of warning
            severity: Warning severity
            
        Returns:
            Dict[str, Any]: Formatted warning object
        """
        return {
            'line': line,
            'column': column,
            'message': message,
            'type': warning_type,
            'severity': severity,
            'is_warning': True
        }
    
    def check_brackets(self, code: str) -> List[Dict[str, Any]]:
        """
        Check for balanced brackets, parentheses, and braces.
        
        Args:
            code: The source code to check
            
        Returns:
            List of errors found
        """
        errors = []
        stack = []
        bracket_pairs = {
            '(': ')',
            '[': ']',
            '{': '}'
        }
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for col_num, char in enumerate(line, 1):
                if char in bracket_pairs.keys():
                    stack.append((char, line_num, col_num))
                elif char in bracket_pairs.values():
                    if not stack:
                        errors.append(self.create_error(
                            f"Unexpected closing bracket '{char}'",
                            line_num, col_num
                        ))
                    else:
                        last_open, open_line, open_col = stack.pop()
                        if bracket_pairs[last_open] != char:
                            errors.append(self.create_error(
                                f"Mismatched bracket: expected '{bracket_pairs[last_open]}' but found '{char}'",
                                line_num, col_num
                            ))
        
        # Check for unclosed brackets
        for bracket, line_num, col_num in stack:
            errors.append(self.create_error(
                f"Unclosed bracket '{bracket}'",
                line_num, col_num
            ))
        
        return errors
    
    def check_quotes(self, code: str) -> List[Dict[str, Any]]:
        """
        Check for balanced quotes in the code.
        
        Args:
            code: The source code to check
            
        Returns:
            List of errors found
        """
        errors = []
        lines = code.split('\n')
        
        in_single_quote = False
        in_double_quote = False
        escape_next = False
        
        for line_num, line in enumerate(lines, 1):
            for col_num, char in enumerate(line, 1):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
            
            # Check for unfinished quotes at end of line
            if in_single_quote:
                errors.append(self.create_error(
                    "Unclosed single quote at end of line",
                    line_num, len(line)
                ))
                in_single_quote = False
            
            if in_double_quote:
                errors.append(self.create_error(
                    "Unclosed double quote at end of line",
                    line_num, len(line)
                ))
                in_double_quote = False
        
        return errors
    
    def check_line_length(self, code: str, max_length: int = 120) -> List[Dict[str, Any]]:
        """
        Check for lines that exceed maximum length.
        
        Args:
            code: The source code to check
            max_length: Maximum allowed line length
            
        Returns:
            List of warnings for long lines
        """
        warnings = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if len(line) > max_length:
                warnings.append(self.create_warning(
                    f"Line exceeds maximum length ({len(line)} > {max_length})",
                    line_num, max_length,
                    'style_warning', 'low'
                ))
        
        return warnings

# Optional: Add a factory method if needed
def create_analyzer(language: str) -> Optional[BaseAnalyzer]:
    """
    Factory function to create the appropriate analyzer for a language.
    
    Args:
        language: The programming language name
        
    Returns:
        An instance of the appropriate analyzer, or None if not found
    """
    analyzers = {
        'python': 'PythonAnalyzer',
        'java': 'JavaAnalyzer',
        'cpp': 'CPPAnalyzer',
        'javascript': 'JavaScriptAnalyzer',
        'html': 'HTMLAnalyzer',
        'generic': 'GenericAnalyzer'
    }
    
    if language in analyzers:
        module_name = f"analyzers.{language}_analyzer"
        class_name = analyzers[language]
        
        try:
            module = __import__(module_name, fromlist=[class_name])
            analyzer_class = getattr(module, class_name)
            return analyzer_class()
        except (ImportError, AttributeError) as e:
            print(f"Error creating analyzer for {language}: {e}")
            return None
    
    return None