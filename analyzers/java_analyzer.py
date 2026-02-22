import subprocess
import tempfile
import os
import re
from analyzers.base_analyzer import BaseAnalyzer
class JavaAnalyzer(BaseAnalyzer):
    def analyze(self, code):
        errors = []
        warnings = []
        
        # Create temporary Java file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            # Extract class name or use default
            class_match = re.search(r'class\s+(\w+)', code)
            class_name = class_match.group(1) if class_match else 'Main'
            
            # If class name doesn't match filename, create appropriate content
            if class_match and class_match.group(1) != 'Main':
                f.write(code)
            else:
                # Wrap code in a class if needed
                if 'class' not in code:
                    code = f'public class Main {{\n{code}\n}}'
                f.write(code)
            
            temp_file = f.name
        
        try:
            # Try to compile the Java code
            result = subprocess.run(
                ['javac', temp_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse compilation errors
            if result.returncode != 0:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        # Parse Java compiler error format
                        error_match = re.search(r'([^:]+):(\d+):\s*error:\s*(.+)', line)
                        if error_match:
                            errors.append({
                                'line': int(error_match.group(2)),
                                'column': 0,
                                'message': error_match.group(3),
                                'type': 'compilation_error'
                            })
                        else:
                            warnings.append({
                                'line': 1,
                                'column': 0,
                                'message': line,
                                'type': 'compiler_output'
                            })
            
            # Check for common Java issues
            if 'System.out.println' in code and 'public static void main' not in code:
                warnings.append({
                    'line': 1,
                    'column': 0,
                    'message': 'Print statements without main method',
                    'type': 'logic_warning'
                })
                
        except subprocess.TimeoutExpired:
            errors.append({
                'line': 1,
                'column': 0,
                'message': 'Compilation timed out',
                'type': 'timeout_error'
            })
        except FileNotFoundError:
            errors.append({
                'line': 1,
                'column': 0,
                'message': 'Java compiler not found. Please install JDK.',
                'type': 'environment_error'
            })
        finally:
            # Clean up
            os.unlink(temp_file)
            class_file = temp_file.replace('.java', '.class')
            if os.path.exists(class_file):
                os.unlink(class_file)
        
        return self.format_result(errors, warnings)