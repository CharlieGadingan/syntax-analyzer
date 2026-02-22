"""
System Test Script for Code Syntax Analyzer
Run this to verify your analyzer is working correctly
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 5

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🔍 {text}")
    print("="*60)

def print_result(test_name, success, message=""):
    """Print test result with emoji"""
    if success:
        print(f"✅ {test_name}: PASSED")
    else:
        print(f"❌ {test_name}: FAILED")
    if message:
        print(f"   📝 {message}")

def test_server_connection():
    """Test if Flask server is running"""
    print_header("Testing Server Connection")
    
    try:
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        print_result("Server Connection", True, f"Status Code: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print_result("Server Connection", False, 
                    f"Cannot connect to {BASE_URL}\n   Make sure Flask is running with 'python app.py'")
        return False
    except Exception as e:
        print_result("Server Connection", False, str(e))
        return False

def test_analyze_endpoint():
    """Test the /analyze endpoint with various code samples"""
    print_header("Testing /analyze Endpoint")
    
    test_cases = [
        {
            "name": "Python - Simple code",
            "code": "print('Hello, World!')",
            "language": "python",
            "expected_success": True
        },
        {
            "name": "Python - Code with error",
            "code": "def test(\n    print('missing colon')",
            "language": "python",
            "expected_success": True  # API should still return success even with errors
        },
        {
            "name": "Java - Simple code",
            "code": "public class Test { public static void main(String[] args) { System.out.println('Hello'); } }",
            "language": "java",
            "expected_success": True
        },
        {
            "name": "Auto-detect language",
            "code": "function hello() { console.log('Hello'); }",
            "language": "auto",
            "expected_success": True
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        try:
            print(f"\n📋 Testing: {test['name']}")
            print(f"   Language: {test['language']}")
            print(f"   Code: {test['code'][:50]}..." if len(test['code']) > 50 else f"   Code: {test['code']}")
            
            payload = {
                "code": test['code'],
                "language": test['language']
            }
            
            response = requests.post(
                f"{BASE_URL}/analyze", 
                json=payload,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') == test['expected_success']:
                    print_result(test['name'], True, 
                                f"Errors: {len(data.get('errors', []))}, "
                                f"Warnings: {len(data.get('warnings', []))}")
                else:
                    print_result(test['name'], False, 
                                f"Expected success={test['expected_success']}, got {data.get('success')}")
                    all_passed = False
            else:
                print_result(test['name'], False, f"HTTP {response.status_code}")
                all_passed = False
                
        except requests.exceptions.Timeout:
            print_result(test['name'], False, "Request timed out")
            all_passed = False
        except Exception as e:
            print_result(test['name'], False, str(e))
            all_passed = False
    
    return all_passed

def test_file_upload():
    """Test file upload functionality"""
    print_header("Testing File Upload Endpoint")
    
    # Create a temporary test file
    test_files = [
        {
            "name": "test.py",
            "content": "def hello():\n    print('Hello, World!')\n\nhello()",
            "language": "python"
        },
        {
            "name": "test.js", 
            "content": "function hello() {\n    console.log('Hello');\n}\nhello();",
            "language": "javascript"
        }
    ]
    
    all_passed = True
    
    for test_file in test_files:
        try:
            print(f"\n📋 Testing file: {test_file['name']}")
            
            # Create temporary file
            with open(test_file['name'], 'w') as f:
                f.write(test_file['content'])
            
            # Upload file
            with open(test_file['name'], 'rb') as f:
                files = {'file': (test_file['name'], f, 'text/plain')}
                response = requests.post(
                    f"{BASE_URL}/analyze-file",
                    files=files,
                    timeout=TIMEOUT
                )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print_result(f"Upload {test_file['name']}", True,
                               f"Detected: {data.get('language', 'unknown')}")
                else:
                    print_result(f"Upload {test_file['name']}", False,
                               f"API Error: {data.get('error', 'Unknown')}")
                    all_passed = False
            else:
                print_result(f"Upload {test_file['name']}", False,
                           f"HTTP {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print_result(f"Upload {test_file['name']}", False, str(e))
            all_passed = False
        finally:
            # Clean up temp file
            import os
            if os.path.exists(test_file['name']):
                os.remove(test_file['name'])
    
    return all_passed

def test_error_handling():
    """Test error handling"""
    print_header("Testing Error Handling")
    
    test_cases = [
        {
            "name": "Empty code",
            "payload": {"code": "", "language": "python"},
            "expected_status": 400
        },
        {
            "name": "Missing code field",
            "payload": {"language": "python"},
            "expected_status": 400
        },
        {
            "name": "Invalid JSON",
            "payload": "not json",
            "expected_status": 400
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        try:
            print(f"\n📋 Testing: {test['name']}")
            
            if isinstance(test['payload'], dict):
                response = requests.post(
                    f"{BASE_URL}/analyze",
                    json=test['payload'],
                    timeout=TIMEOUT
                )
            else:
                response = requests.post(
                    f"{BASE_URL}/analyze",
                    data=test['payload'],
                    headers={'Content-Type': 'application/json'},
                    timeout=TIMEOUT
                )
            
            if response.status_code == test['expected_status']:
                print_result(test['name'], True, f"Got expected {response.status_code}")
            else:
                print_result(test['name'], False, 
                           f"Expected {test['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print_result(test['name'], False, str(e))
            all_passed = False
    
    return all_passed

def test_performance():
    """Basic performance test"""
    print_header("Testing Performance")
    
    try:
        start_time = time.time()
        
        # Send a simple request
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={"code": "print('test')", "language": "python"},
            timeout=TIMEOUT
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            print_result("Response Time", True, f"{response_time:.2f}ms")
            return True
        else:
            print_result("Performance", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Performance", False, str(e))
        return False

def run_all_tests():
    """Run all system tests"""
    print("\n🌟" + "="*56 + "🌟")
    print("   CODE SYNTAX ANALYZER - SYSTEM TEST SUITE")
    print("🌟" + "="*56 + "🌟\n")
    
    # First check if server is running
    if not test_server_connection():
        print("\n❌ Cannot proceed with tests. Make sure Flask is running!")
        print("\nTo start Flask:")
        print("1. Open a terminal")
        print("2. Run: python app.py")
        print("3. Keep it running and run this test in another terminal")
        return False
    
    # Run all tests
    tests = [
        ("Analyze Endpoint", test_analyze_endpoint),
        ("File Upload", test_file_upload),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n⏳ Running {test_name} tests...")
        results[test_name] = test_func()
        time.sleep(1)  # Small delay between tests
    
    # Print summary
    print_header("TEST SUMMARY")
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        if passed:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Your system is working correctly!")
        print("\nYou can now:")
        print("  • Open http://127.0.0.1:5000 in your browser")
        print("  • Paste code to analyze")
        print("  • Upload files for analysis")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\nCommon issues:")
        print("  • Flask server not running? Run 'python app.py'")
        print("  • Wrong port? Make sure Flask is on port 5000")
        print("  • Missing analyzers? Check your project structure")
    print("="*60)
    
    return all_passed

def quick_test():
    """Quick single test to verify basic functionality"""
    print_header("QUICK TEST")
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json={
                "code": "print('Quick test')",
                "language": "python"
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Quick test PASSED")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Quick test FAILED: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Quick test FAILED: Cannot connect to Flask server")
        print("\nMake sure Flask is running:")
        print("1. Open a terminal")
        print("2. Run: python app.py")
        print("3. Keep it running and run this test again")
        return False
    except Exception as e:
        print(f"❌ Quick test FAILED: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Syntax Analyzer System')
    parser.add_argument('--quick', action='store_true', 
                       help='Run only quick test')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port number (default: 5000)')
    
    args = parser.parse_args()
    
    # Update port if specified
    if args.port != 5000:
        BASE_URL = f"http://127.0.0.1:{args.port}"
    
    if args.quick:
        quick_test()
    else:
        run_all_tests()