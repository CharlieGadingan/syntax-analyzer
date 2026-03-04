// simple-server.js - A minimal HTTP server
const http = require('http');
const url = require('url');

const server = http.createServer((req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Parse URL
  const parsedUrl = url.parse(req.url, true);
  
  // Route handling
  if (parsedUrl.pathname === '/test' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: true, message: 'Server is running!' }));
  }
  
  else if (parsedUrl.pathname === '/clone-repo' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const sessionId = Date.now().toString();
        const files = [
          { name: 'main.js', path: 'main.js', language: 'javascript' },
          { name: 'index.html', path: 'index.html', language: 'html' },
          { name: 'style.css', path: 'style.css', language: 'css' },
          { name: 'app.py', path: 'app.py', language: 'python' },
          { name: 'Main.java', path: 'Main.java', language: 'java' },
          { name: 'main.cpp', path: 'main.cpp', language: 'cpp' },
        ];
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, session_id: sessionId, files }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: error.message }));
      }
    });
  }
  
  else if (parsedUrl.pathname === '/file-content' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const { file_path } = data;
        let content = '';
        
        if (file_path.includes('.js')) {
          content = `function hello() {
  console.log("Hello")
  let x = 10
  return x
}`;
        } else if (file_path.includes('.html')) {
          content = `<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>`;
        } else if (file_path.includes('.py')) {
          content = `def hello():
    print("Hello")`;
        } else if (file_path.includes('.java')) {
          content = `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello")
    }
}`;
        } else if (file_path.includes('.cpp')) {
          content = `#include <iostream>
using namespace std;

int main() {
    cout << "Hello World" << endl;
    return 0;
}`;
        } else {
          content = `// Sample code for ${file_path}`;
        }
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, content }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: error.message }));
      }
    });
  }
  
  else if (parsedUrl.pathname === '/analyze-file-content' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const { content, language } = data;
        const errors = [];
        const warnings = [];
        
        const lines = content.split('\n');
        lines.forEach((line, i) => {
          if (language === 'javascript' && line.includes('=') && !line.includes(';') && !line.includes('{')) {
            warnings.push({ line: i + 1, message: 'Missing semicolon' });
          }
          if (language === 'python' && line.includes('print') && !line.includes('(')) {
            errors.push({ line: i + 1, message: 'print needs parentheses' });
          }
          if (language === 'java' && line.includes('System.out.println') && !line.includes(';')) {
            errors.push({ line: i + 1, message: 'Missing semicolon' });
          }
        });
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, errors, warnings }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, error: error.message }));
      }
    });
  }
  
  else if (parsedUrl.pathname === '/save-feedback' && req.method === 'POST') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: true, message: 'Feedback saved' }));
  }
  
  else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not found' }));
  }
});

const PORT = 5500;
server.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});