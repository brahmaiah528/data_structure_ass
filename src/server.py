"""
Embedded Localhost Web Server & REST API for the University Course Prerequisite Management System.
Uses Python standard library http.server (Zero external dependencies).

Runs on http://localhost:8000 / http://127.0.0.1:8000
Provides an interactive web dashboard with dynamic graph visualizers, live step simulators,
cycle analysis, and academic test case reporting.
"""

import http.server
import json
import socketserver
import urllib.parse
from typing import Optional

from src.course_graph import CourseGraph
from src.topological_sort import TopologicalSort
from src.cycle_detector import CycleDetector
from src.validator import OrderValidator
from src.test_suite import TestSuite

PORT = 8000
SHARED_GRAPH = CourseGraph()
SHARED_GRAPH.load_sample_dataset()


class PrerequisiteAPIHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler providing REST API and Interactive Dashboard."""

    def log_message(self, format, *args):
        # Suppress noisy logging in console
        pass

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._serve_html_dashboard()
        elif path == "/api/graph":
            self._send_json(SHARED_GRAPH.to_dict())
        elif path == "/api/bfs":
            res = TopologicalSort.kahn_sort(SHARED_GRAPH)
            data = res.to_dict()
            data["report"] = res.format_report(SHARED_GRAPH)
            self._send_json(data)
        elif path == "/api/dfs":
            res = TopologicalSort.dfs_sort(SHARED_GRAPH)
            data = res.to_dict()
            data["report"] = res.format_report(SHARED_GRAPH)
            self._send_json(data)
        elif path == "/api/cycle":
            bfs_rep = CycleDetector.detect_cycle_bfs(SHARED_GRAPH)
            dfs_rep = CycleDetector.detect_cycle_dfs(SHARED_GRAPH)
            self._send_json({
                "bfs": {
                    "detected": bfs_rep.cycle_detected,
                    "path": bfs_rep.cycle_path,
                    "affected": bfs_rep.involved_courses,
                    "report": bfs_rep.format_report()
                },
                "dfs": {
                    "detected": dfs_rep.cycle_detected,
                    "path": dfs_rep.cycle_path,
                    "affected": dfs_rep.involved_courses,
                    "report": dfs_rep.format_report()
                }
            })
        elif path == "/api/validate":
            res_kahn = TopologicalSort.kahn_sort(SHARED_GRAPH)
            if res_kahn.success:
                val = OrderValidator.validate(SHARED_GRAPH, res_kahn.order)
                self._send_json({
                    "passed": val.passed,
                    "order": res_kahn.order,
                    "report": val.format_report()
                })
            else:
                self._send_json({
                    "passed": False,
                    "order": [],
                    "report": "Topological sort failed due to circular dependencies; cannot validate order."
                })
        elif path == "/api/tests":
            results = TestSuite.run_all_tests()
            self._send_json({
                "summary": TestSuite.format_summary_report(results),
                "test_cases": [r.to_dict() for r in results]
            })
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/load-sample":
            SHARED_GRAPH.load_sample_dataset()
            self._send_json({"message": "Sample 12-course DAG dataset loaded successfully."})
        elif path == "/api/load-cyclic":
            SHARED_GRAPH.load_cyclic_dataset()
            self._send_json({"message": "Cyclic prerequisite dataset loaded successfully."})
        elif path == "/api/clear":
            SHARED_GRAPH.clear()
            self._send_json({"message": "Curriculum graph cleared."})
        elif path == "/api/course":
            code = payload.get("code", "")
            title = payload.get("title", "")
            credits = payload.get("credits", 3)
            try:
                c = SHARED_GRAPH.add_course(code, title, credits)
                self._send_json({"success": True, "course": c.to_dict()})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
        elif path == "/api/prerequisite":
            prereq = payload.get("prereq", "")
            target = payload.get("target", "")
            try:
                SHARED_GRAPH.add_prerequisite(prereq, target)
                self._send_json({"success": True, "edge": [prereq.upper(), target.upper()]})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
        else:
            self.send_error(404, "POST endpoint not found")

    def _serve_html_dashboard(self):
        """Generates and serves the rich interactive HTML/CSS/JS dashboard."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>University Course Prerequisite Management System</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-primary: #0f172a;
      --bg-secondary: #1e293b;
      --bg-card: rgba(30, 41, 59, 0.85);
      --border-card: rgba(255, 255, 255, 0.08);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent-blue: #38bdf8;
      --accent-indigo: #6366f1;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-red: #ef4444;
      --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font-sans);
      background: radial-gradient(circle at 10% 20%, #1e1b4b 0%, #0f172a 90%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-card);
      padding: 1.25rem 2rem;
      position: sticky;
      top: 0;
      z-index: 100;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header-title h1 {
      font-size: 1.35rem;
      font-weight: 700;
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.02em;
    }
    .header-title p {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 0.2rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--accent-blue);
      padding: 0.3rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .badge.sdg {
      background: rgba(16, 185, 129, 0.12);
      border-color: rgba(16, 185, 129, 0.3);
      color: var(--accent-green);
    }
    .container {
      max-width: 1440px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem 2rem;
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 1.5rem;
      flex: 1;
    }
    @media (max-width: 1024px) {
      .container { grid-template-columns: 1fr; }
    }
    .sidebar { display: flex; flex-direction: column; gap: 1.25rem; }
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-card);
      border-radius: 12px;
      padding: 1.25rem;
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.36);
      backdrop-filter: blur(8px);
    }
    .card-title {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 0.85rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border-card);
      padding-bottom: 0.5rem;
    }
    .form-group { margin-bottom: 0.75rem; }
    label {
      display: block;
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--text-muted);
      margin-bottom: 0.3rem;
    }
    input, select {
      width: 100%;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 6px;
      color: #fff;
      padding: 0.55rem 0.75rem;
      font-size: 0.85rem;
      font-family: inherit;
      outline: none;
      transition: border-color 0.2s;
    }
    input:focus { border-color: var(--accent-blue); }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      padding: 0.6rem 1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      gap: 0.4rem;
    }
    .btn-primary {
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: #fff;
    }
    .btn-primary:hover { background: linear-gradient(135deg, #0369a1, #075985); }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: var(--text-main);
      margin-top: 0.4rem;
    }
    .btn-secondary:hover { background: rgba(255, 255, 255, 0.14); }
    .btn-algo {
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.4);
      color: #c7d2fe;
      margin-bottom: 0.5rem;
    }
    .btn-algo:hover { background: rgba(99, 102, 241, 0.3); color: #fff; }
    .btn-danger {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fca5a5;
    }
    .btn-danger:hover { background: rgba(239, 68, 68, 0.3); color: #fff; }
    .content-area {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .tabs {
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid var(--border-card);
      padding-bottom: 0.5rem;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.88rem;
      font-weight: 500;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent-blue);
      font-weight: 600;
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .canvas-container {
      position: relative;
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--border-card);
      border-radius: 10px;
      height: 480px;
      overflow: hidden;
    }
    canvas {
      width: 100%;
      height: 100%;
      display: block;
    }
    .console-box {
      background: #090d16;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      padding: 1rem;
      font-family: var(--font-mono);
      font-size: 0.82rem;
      color: #e2e8f0;
      max-height: 450px;
      overflow-y: auto;
      white-space: pre-wrap;
      line-height: 1.5;
    }
    .order-pill-box {
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
      margin-top: 1rem;
      padding: 0.75rem;
      background: rgba(15, 23, 42, 0.6);
      border-radius: 8px;
    }
    .order-pill {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(99, 102, 241, 0.2));
      border: 1px solid rgba(56, 189, 248, 0.4);
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      font-size: 0.82rem;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    .order-pill span.num {
      background: var(--accent-blue);
      color: #0f172a;
      border-radius: 50%;
      width: 18px;
      height: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.7rem;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
      margin-bottom: 1.25rem;
    }
    .stat-card {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border-card);
      border-radius: 8px;
      padding: 0.85rem;
      text-align: center;
    }
    .stat-value {
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--accent-blue);
    }
    .stat-label {
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 0.2rem;
    }
    table.test-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
      margin-top: 0.5rem;
    }
    table.test-table th {
      background: rgba(255, 255, 255, 0.05);
      text-align: left;
      padding: 0.6rem;
      border-bottom: 1px solid var(--border-card);
      color: var(--text-muted);
    }
    table.test-table td {
      padding: 0.6rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .status-badge {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.72rem;
      font-weight: 700;
    }
    .status-passed { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .status-failed { background: rgba(239, 68, 68, 0.2); color: #f87171; }
  </style>
</head>
<body>
  <header>
    <div class="header-title">
      <h1>University Course Prerequisite Management System</h1>
      <p>Course: CSA03 – Data Structures (Slot D) | Outcome: CO5 (Robust Graph-Based Solutions)</p>
    </div>
    <div style="display:flex; gap:0.5rem;">
      <span class="badge sdg">SDG 4: Quality Education</span>
      <span class="badge sdg">SDG 9: Industry & Infrastructure</span>
      <span class="badge">Kahn BFS & 3-State DFS</span>
    </div>
  </header>

  <div class="container">
    <!-- LEFT SIDEBAR -->
    <div class="sidebar">
      <!-- 1. Stats Card -->
      <div class="card">
        <div class="card-title">Curriculum Metrics</div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value" id="stat-courses">0</div>
            <div class="stat-label">Courses</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="stat-prereqs">0</div>
            <div class="stat-label">Prereqs</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="stat-entry">0</div>
            <div class="stat-label">Deg 0</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" id="stat-credits">0</div>
            <div class="stat-label">Credits</div>
          </div>
        </div>
        <button class="btn btn-secondary" onclick="loadSampleData()">Load Sample DAG (12 Courses)</button>
        <button class="btn btn-secondary" onclick="loadCyclicData()">Load Cyclic Demo Dataset</button>
        <button class="btn btn-danger" style="margin-top:0.4rem;" onclick="clearGraph()">Clear Graph</button>
      </div>

      <!-- 2. Algorithm Triggers -->
      <div class="card">
        <div class="card-title">Algorithm Suite</div>
        <button class="btn btn-algo" onclick="runBFS()">1. BFS / Kahn's Topological Sort</button>
        <button class="btn btn-algo" onclick="runDFS()">2. DFS Topological Sort (3-State)</button>
        <button class="btn btn-algo" onclick="detectCycles()">3. Detect Cycle (Dual Engine)</button>
        <button class="btn btn-algo" onclick="validateOrder()">4. Validate Precedence [pos(A)&lt;pos(B)]</button>
        <button class="btn btn-algo" onclick="runAllTests()">5. Execute All 6 Test Cases</button>
      </div>

      <!-- 3. Add Course & Prerequisite -->
      <div class="card">
        <div class="card-title">Add Course / Edge</div>
        <div class="form-group">
          <label>Course Code & Credits</label>
          <div style="display:flex; gap:0.4rem;">
            <input type="text" id="inp-code" placeholder="e.g. CS401" style="flex:2;">
            <input type="number" id="inp-cred" value="3" min="1" max="6" style="flex:1;">
          </div>
        </div>
        <div class="form-group">
          <label>Course Name</label>
          <input type="text" id="inp-title" placeholder="e.g. Cloud Computing">
        </div>
        <button class="btn btn-primary" onclick="addCourse()">+ Add Course Vertex</button>

        <div style="margin-top:1rem; border-top:1px solid var(--border-card); padding-top:0.8rem;">
          <label>Add Dependency Edge: Prereq (A) &rarr; Target (B)</label>
          <div style="display:flex; gap:0.4rem;">
            <input type="text" id="inp-prereq" placeholder="Prereq (A)">
            <input type="text" id="inp-target" placeholder="Target (B)">
          </div>
          <button class="btn btn-secondary" style="margin-top:0.5rem;" onclick="addPrerequisite()">+ Add Prerequisite Edge</button>
        </div>
      </div>
    </div>

    <!-- MAIN CONTENT AREA -->
    <div class="content-area">
      <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('tab-graph')">Graph Visualizer</button>
        <button class="tab-btn" onclick="switchTab('tab-order')">Topological Order</button>
        <button class="tab-btn" onclick="switchTab('tab-console')">Execution Diagnostics</button>
        <button class="tab-btn" onclick="switchTab('tab-tests')">Academic Test Suite</button>
      </div>

      <!-- TAB 1: GRAPH VISUALIZER -->
      <div id="tab-graph" class="tab-content active">
        <div class="card">
          <div class="card-title">
            Interactive Prerequisite Dependency Directed Graph
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">
              Green: Entry (Deg 0) | Blue: Intermediate | Red: In Cycle
            </span>
          </div>
          <div class="canvas-container">
            <canvas id="graphCanvas"></canvas>
          </div>
        </div>
      </div>

      <!-- TAB 2: TOPOLOGICAL ORDER -->
      <div id="tab-order" class="tab-content">
        <div class="card">
          <div class="card-title" id="order-title">Valid Course-Taking Order</div>
          <p style="font-size:0.82rem; color:var(--text-muted); margin-bottom:0.8rem;">
            Courses ordered sequentially such that every prerequisite course is completed before any dependent course.
          </p>
          <div id="order-container" class="order-pill-box">
            <div style="color:var(--text-muted); font-size:0.85rem;">Click "Run BFS" or "Run DFS" to compute the sequence.</div>
          </div>
        </div>
      </div>

      <!-- TAB 3: CONSOLE OUTPUT -->
      <div id="tab-console" class="tab-content">
        <div class="card">
          <div class="card-title">Diagnostic & Execution Log</div>
          <div class="console-box" id="console-output">Ready. Click any algorithm button on the left to start execution.</div>
        </div>
      </div>

      <!-- TAB 4: TEST CASES -->
      <div id="tab-tests" class="tab-content">
        <div class="card">
          <div class="card-title">Automated Academic Test Cases (TC-01 to TC-06)</div>
          <div style="overflow-x:auto;">
            <table class="test-table" id="test-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Test Case Name</th>
                  <th>Input Specification</th>
                  <th>Expected Result</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody id="test-body">
                <tr><td colspan="5" style="text-align:center; color:var(--text-muted);">Click "Execute All 6 Test Cases" to run verification.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let graphData = null;
    let nodePositions = {};
    let cycleNodes = new Set();

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById(tabId).classList.add('active');
      if (tabId === 'tab-graph') {
        renderGraph();
      }
    }

    async function fetchGraph() {
      try {
        const res = await fetch('/api/graph');
        graphData = await res.json();
        updateMetrics();
        calculateLayout();
        renderGraph();
      } catch (e) {
        console.error("Failed to load graph:", e);
      }
    }

    function updateMetrics() {
      if (!graphData) return;
      document.getElementById('stat-courses').innerText = graphData.num_vertices;
      document.getElementById('stat-prereqs').innerText = graphData.num_edges;
      const deg0 = Object.values(graphData.indegrees).filter(d => d === 0).length;
      document.getElementById('stat-entry').innerText = deg0;
      const credits = graphData.courses.reduce((sum, c) => sum + c.credits, 0);
      document.getElementById('stat-credits').innerText = credits;
    }

    function calculateLayout() {
      if (!graphData || !graphData.courses) return;
      const canvas = document.getElementById('graphCanvas');
      const rect = canvas.getBoundingClientRect();
      const W = canvas.width = canvas.parentElement.clientWidth;
      const H = canvas.height = canvas.parentElement.clientHeight;

      nodePositions = {};
      const courses = graphData.courses;
      const total = courses.length;
      if (total === 0) return;

      // Group nodes by in-degree levels or simple circle/grid
      const centerX = W / 2;
      const centerY = H / 2;
      const radius = Math.min(W, H) * 0.38;

      courses.forEach((c, idx) => {
        const angle = (idx / total) * 2 * Math.PI - Math.PI / 2;
        nodePositions[c.code] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
          code: c.code,
          title: c.title,
          indegree: graphData.indegrees[c.code] || 0
        };
      });
    }

    function renderGraph() {
      const canvas = document.getElementById('graphCanvas');
      if (!canvas || !graphData) return;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 1. Draw Directed Edges
      for (const u in graphData.adj_list) {
        const neighbors = graphData.adj_list[u];
        const p1 = nodePositions[u];
        if (!p1) continue;

        neighbors.forEach(v => {
          const p2 = nodePositions[v];
          if (!p2) continue;

          const isCycleEdge = cycleNodes.has(u) && cycleNodes.has(v);

          ctx.beginPath();
          ctx.strokeStyle = isCycleEdge ? '#ef4444' : 'rgba(56, 189, 248, 0.4)';
          ctx.lineWidth = isCycleEdge ? 2.5 : 1.5;

          // Arrow from p1 to p2
          const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
          const nodeR = 24;
          const startX = p1.x + nodeR * Math.cos(angle);
          const startY = p1.y + nodeR * Math.sin(angle);
          const endX = p2.x - nodeR * Math.cos(angle);
          const endY = p2.y - nodeR * Math.sin(angle);

          ctx.moveTo(startX, startY);
          ctx.lineTo(endX, endY);
          ctx.stroke();

          // Arrowhead
          const headLen = 9;
          ctx.beginPath();
          ctx.fillStyle = isCycleEdge ? '#ef4444' : '#38bdf8';
          ctx.moveTo(endX, endY);
          ctx.lineTo(endX - headLen * Math.cos(angle - Math.PI / 6), endY - headLen * Math.sin(angle - Math.PI / 6));
          ctx.lineTo(endX - headLen * Math.cos(angle + Math.PI / 6), endY - headLen * Math.sin(angle + Math.PI / 6));
          ctx.closePath();
          ctx.fill();
        });
      }

      // 2. Draw Nodes
      for (const code in nodePositions) {
        const p = nodePositions[code];
        const isCycle = cycleNodes.has(code);
        const isEntry = p.indegree === 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, 22, 0, 2 * Math.PI);
        if (isCycle) {
          ctx.fillStyle = 'rgba(239, 68, 68, 0.85)';
          ctx.strokeStyle = '#fca5a5';
        } else if (isEntry) {
          ctx.fillStyle = 'rgba(16, 185, 129, 0.85)';
          ctx.strokeStyle = '#6ee7b7';
        } else {
          ctx.fillStyle = 'rgba(30, 58, 138, 0.9)';
          ctx.strokeStyle = '#38bdf8';
        }
        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();

        // Node label
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(code, p.x, p.y);

        // In-degree badge
        ctx.beginPath();
        ctx.arc(p.x + 16, p.y - 14, 8, 0, 2 * Math.PI);
        ctx.fillStyle = '#0f172a';
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.4)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = isCycle ? '#ef4444' : '#38bdf8';
        ctx.font = '9px monospace';
        ctx.fillText(p.indegree, p.x + 16, p.y - 14);
      }
    }

    async function runBFS() {
      const res = await fetch('/api/bfs');
      const data = await res.json();
      document.getElementById('console-output').innerText = data.report;
      switchTabCustom('tab-console');
      renderOrder(data.order, data.has_cycle, "BFS / Kahn's Topological Order");
    }

    async function runDFS() {
      const res = await fetch('/api/dfs');
      const data = await res.json();
      document.getElementById('console-output').innerText = data.report;
      switchTabCustom('tab-console');
      renderOrder(data.order, data.has_cycle, "DFS Topological Order");
    }

    async function detectCycles() {
      const res = await fetch('/api/cycle');
      const data = await res.json();
      let text = "======================================================================\\n";
      text += "DUAL-ENGINE CYCLE DETECTION REPORT (BFS & DFS)\\n";
      text += "======================================================================\\n\\n";
      text += data.bfs.report + "\\n\\n" + data.dfs.report;
      document.getElementById('console-output').innerText = text;

      cycleNodes.clear();
      if (data.dfs.detected && data.dfs.affected) {
        data.dfs.affected.forEach(c => cycleNodes.add(c));
      }
      renderGraph();
      switchTabCustom('tab-console');
    }

    async function validateOrder() {
      const res = await fetch('/api/validate');
      const data = await res.json();
      document.getElementById('console-output').innerText = data.report;
      switchTabCustom('tab-console');
    }

    async function runAllTests() {
      const res = await fetch('/api/tests');
      const data = await res.json();
      document.getElementById('console-output').innerText = data.summary;

      const tbody = document.getElementById('test-body');
      tbody.innerHTML = '';
      data.test_cases.forEach(tc => {
        const tr = document.createElement('tr');
        const badgeClass = tc.status === 'PASSED' ? 'status-passed' : 'status-failed';
        tr.innerHTML = `
          <td><strong>${tc.test_id}</strong></td>
          <td>${tc.name}</td>
          <td style="color:var(--text-muted);">${tc.input_desc}</td>
          <td>${tc.expected}</td>
          <td><span class="status-badge ${badgeClass}">${tc.status}</span></td>
        `;
        tbody.appendChild(tr);
      });
      switchTabCustom('tab-tests');
    }

    function renderOrder(order, hasCycle, title) {
      const box = document.getElementById('order-container');
      document.getElementById('order-title').innerText = title;
      box.innerHTML = '';

      if (hasCycle || !order || order.length === 0) {
        box.innerHTML = '<div style="color:#ef4444; font-weight:600;">Cycle detected! Topological ordering cannot be generated.</div>';
        return;
      }

      order.forEach((code, idx) => {
        const course = graphData.courses.find(c => c.code === code);
        const name = course ? course.title : '';
        const pill = document.createElement('div');
        pill.className = 'order-pill';
        pill.innerHTML = `<span class="num">${idx + 1}</span><strong>${code}</strong> <span>${name}</span>`;
        box.appendChild(pill);
      });
    }

    function switchTabCustom(id) {
      document.querySelectorAll('.tab-btn').forEach(b => {
        if (b.getAttribute('onclick').includes(id)) b.classList.add('active');
        else b.classList.remove('active');
      });
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      document.getElementById(id).classList.add('active');
    }

    async function loadSampleData() {
      await fetch('/api/load-sample', { method: 'POST' });
      cycleNodes.clear();
      await fetchGraph();
      document.getElementById('console-output').innerText = "Loaded realistic sample university dataset (12 courses, DAG).";
    }

    async function loadCyclicData() {
      await fetch('/api/load-cyclic', { method: 'POST' });
      await fetchGraph();
      await detectCycles();
    }

    async function clearGraph() {
      await fetch('/api/clear', { method: 'POST' });
      cycleNodes.clear();
      await fetchGraph();
      document.getElementById('console-output').innerText = "Graph cleared. 0 courses registered.";
    }

    async function addCourse() {
      const code = document.getElementById('inp-code').value.trim();
      const title = document.getElementById('inp-title').value.trim();
      const credits = parseInt(document.getElementById('inp-cred').value) || 3;
      if (!code || !title) return alert("Please specify both Course Code and Title.");

      const res = await fetch('/api/course', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, title, credits })
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('inp-code').value = '';
        document.getElementById('inp-title').value = '';
        fetchGraph();
      } else {
        alert("Error: " + data.error);
      }
    }

    async function addPrerequisite() {
      const prereq = document.getElementById('inp-prereq').value.trim();
      const target = document.getElementById('inp-target').value.trim();
      if (!prereq || !target) return alert("Please specify Prerequisite (A) and Target (B).");

      const res = await fetch('/api/prerequisite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prereq, target })
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('inp-prereq').value = '';
        document.getElementById('inp-target').value = '';
        fetchGraph();
      } else {
        alert("Error: " + data.error);
      }
    }

    window.addEventListener('resize', () => {
      calculateLayout();
      renderGraph();
    });

    window.addEventListener('DOMContentLoaded', () => {
      fetchGraph();
    });
  </script>
</body>
</html>
"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))


def run_server(port: int = PORT) -> socketserver.TCPServer:
    """Starts the embedded localhost web server."""
    handler = PrerequisiteAPIHandler
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("0.0.0.0", port), handler)
    print(f"Localhost web application running at: http://localhost:{port}/")
    return httpd


if __name__ == "__main__":
    server = run_server(PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
        server.server_close()
