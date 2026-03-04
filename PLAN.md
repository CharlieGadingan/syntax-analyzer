# Plan: CodeTracker with Syntax Analyzer Integration

## Information Gathered

### Current Project Structure:
- **Backend (app.py)**: Flask server with syntax analyzers for Python, Java, C++, JavaScript, HTML
- **Repository Analyzer (repo_analyzer.py)**: Clones and analyzes GitHub repositories
- **Analyzers**: PythonAnalyzer, JavaAnalyzer, CPPAnalyzer, JavaScriptAnalyzer, HTMLAnalyzer, GenericAnalyzer
- **Current Template (templates/index.html)**: Basic code input with syntax checking

### User Requirements:
1. Add full syntax analyzer to CodeTracker dashboard
2. Remove timeline navigation and activity heatmap
3. Assignment cards should open syntax analyzer popup when clicked
4. Syntax analyzer should:
   - Check repository code (Java, Python, HTML, C++, C, etc.)
   - Show code in VSCode-like line view
   - Display syntax errors for each file
   - Show professor feedback section with text input and Done button
5. After "Done Checking", update assignment card with:
   - Syntax errors found
   - Professor feedback
   - "Done Checking" status
6. Each file should be separate for easy modification

## Plan

### Step 1: Update templates/index.html
- Remove timeline tab from dashboard tabs
- Remove activity heatmap section from overview tab
- Redesign assignments tab with cards that trigger syntax analyzer popup
- Add VSCode-like syntax analyzer modal/popup with:
  - File selector (list of files from repository)
  - Code viewer with line numbers
  - Syntax errors display
  - Professor feedback textarea
  - Done button
- Add inline assignment status update after checking

### Step 2: Update app.py
- Add endpoint to fetch repository files (/repo-files)
- Add endpoint to analyze specific file (/analyze-file-content)
- Add endpoint to save professor feedback (/save-feedback)
- Update analyze-repo to store results properly

### Step 3: Create supporting files
- Keep all analyzers as separate files (already done)
- Store feedback in JSON file for persistence

## Implementation Order
1. First update app.py with new endpoints
2. Then update templates/index.html with full dashboard and syntax analyzer
3. Test the integration
