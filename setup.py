# setup.py
import subprocess
import sys

packages = [
    'Flask==2.3.3',
    'Flask-CORS==4.0.0',
    'Werkzeug==2.3.7',
    'pyflakes==3.1.0',
    'pycodestyle==2.11.1',
    'GitPython==3.1.40',
    'PyGithub==2.1.1',
    'python-gitlab==4.0.0',
    'requests==2.31.0',
    'celery==5.3.4',
    'redis==5.0.1',
    'python-dotenv==1.0.0'
]

print("📦 Installing packages...")
for package in packages:
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

print("✅ All packages installed successfully!")