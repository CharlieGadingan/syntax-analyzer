import subprocess
import tempfile
import os
import re
from analyzers.base_analyzer import BaseAnalyzer  # Fixed import

class CPPAnalyzer(BaseAnalyzer):
    def analyze(self, code):
        errors = []
        warnings = []
        
        # Create temporary C++ file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Try to compile with g++
            result = subprocess.run(
                ['g++', '-fsyntax-only', '-Wall', temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse compiler output
            for line in result.stderr.split('\n'):
                if line.strip():
                    error_match = re.search(r'([^:]+):(\d+):(\d+):\s*(error|warning):\s*(.+)', line)
                    if error_match:
                        line_num = int(error_match.group(2))
                        message = error_match.group(5)
                        error_type = error_match.group(4)
                        
                        if error_type == 'error':
                            errors.append(self.create_error(message, line_num, int(error_match.group(3))))
                        else:
                            warnings.append(self.create_warning(message, line_num, int(error_match.group(3))))
                    else:
                        warnings.append(self.create_warning(line, 1, 0))
            
        except subprocess.TimeoutExpired:
            errors.append(self.create_error('Compilation timed out', 1, 0))
        except FileNotFoundError:
            errors.append(self.create_error('G++ compiler not found. Please install GCC.', 1, 0))
        finally:
            os.unlink(temp_file)
        
        return self.format_result(errors, warnings)