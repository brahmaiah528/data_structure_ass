"""
University Student Course Enrollment Portal - Localhost Multi-Threaded Web Application.
Zero external framework dependencies - uses Python 3 standard library http.server, sqlite3, json.
Runs on http://localhost:8000/
"""

import http.server
import json
import os
import sqlite3
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional

import database
from graph import CourseGraph
from prerequisites import check_prerequisites, get_course_status, get_recommended_courses
from enrollment import enroll_student_in_course, drop_course_enrollment
from models import CourseStatus

PORT = 8000
DB_PATH = database.DB_PATH


class PortalAPIHandler(http.server.SimpleHTTPRequestHandler):
    """Handles REST API calls and serves the interactive SPA on localhost."""

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        return json.loads(body)

    # =========================================================================
    # GET REQUEST ROUTER
    # =========================================================================
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Main SPA Single-Page Application
        if path == "/" or path == "/index.html":
            self._set_headers(200, "text/html")
            self.wfile.write(HTML_PORTAL.encode("utf-8"))
            return

        # 2. Student Dashboard Stats & Details
        elif path == "/api/student/dashboard":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            student = database.get_student_by_id(stu_id, DB_PATH)
            if not student:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Student not found"}).encode("utf-8"))
                return

            dept = student["department"]
            dept_courses = database.get_courses_by_department(dept, include_common=True, db_path=DB_PATH)
            completed = database.get_student_completed_courses(stu_id, DB_PATH)
            enrollments = database.get_student_enrollments(stu_id, DB_PATH)

            completed_ids = {c["course_id"] for c in completed}
            enrolled_ids = {e["course_id"] for e in enrollments}

            available_count = 0
            blocked_count = 0
            for c in dept_courses:
                c_id = c["course_id"]
                if c_id not in completed_ids and c_id not in enrolled_ids:
                    st = get_course_status(stu_id, c_id, DB_PATH)
                    if st in (CourseStatus.AVAILABLE, CourseStatus.ELIGIBLE):
                        available_count += 1
                    elif st == CourseStatus.BLOCKED:
                        blocked_count += 1

            data = {
                "student": student,
                "metrics": {
                    "total_courses": len(dept_courses),
                    "completed_courses": len(completed),
                    "active_enrollments": len(enrollments),
                    "available_courses": available_count,
                    "blocked_courses": blocked_count,
                    "total_credits_earned": sum(c["credits"] for c in completed)
                },
                "active_enrollments": enrollments
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 3. Courses Filtered by Department and Semester
        elif path == "/api/courses":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            dept = query.get("department", ["CSE"])[0]
            sem = query.get("semester", ["All"])[0]
            search = query.get("search", [""])[0].lower()

            if dept == "All":
                courses = database.get_all_courses(DB_PATH)
            else:
                courses = database.get_courses_by_department(dept, include_common=True, db_path=DB_PATH)

            if sem != "All":
                courses = [c for c in courses if str(c["semester"]) == sem]

            if search:
                courses = [c for c in courses if search in c["course_code"].lower() or search in c["course_name"].lower()]

            results = []
            for c in courses:
                c_id = c["course_id"]
                c_status = get_course_status(stu_id, c_id, DB_PATH)
                prereqs = database.get_prerequisites_for_course(c_id, DB_PATH)
                prereq_str = ", ".join(p["course_code"] for p in prereqs) if prereqs else "None"
                item = dict(c)
                item["status"] = c_status.value
                item["prerequisites_str"] = prereq_str
                item["prerequisites_count"] = len(prereqs)
                results.append(item)

            self._set_headers(200)
            self.wfile.write(json.dumps(results).encode("utf-8"))
            return

        # 4. Check Prerequisites for Course
        elif path == "/api/prerequisites/check":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            course_id = int(query.get("course_id", [0])[0])
            check = check_prerequisites(stu_id, course_id, DB_PATH)
            course = database.get_course_by_id(course_id, DB_PATH)
            status = get_course_status(stu_id, course_id, DB_PATH)
            res = {
                "course": course,
                "status": status.value,
                "check": check
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 5. Completed Courses
        elif path == "/api/completed":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            completed = database.get_student_completed_courses(stu_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(completed).encode("utf-8"))
            return

        # 6. Recommended Courses
        elif path == "/api/recommended":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            recommended = get_recommended_courses(stu_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(recommended).encode("utf-8"))
            return

        # 7. Graph Topology API
        elif path == "/api/graph":
            dept = query.get("department", [None])[0]
            if dept == "All":
                dept = None
            g = CourseGraph.load_from_database(DB_PATH, department=dept)
            indegrees = g.calculate_indegrees()
            courses = []
            for code in g.get_all_courses():
                courses.append({
                    "code": code,
                    "name": g.course_names.get(code, code),
                    "department": g.departments.get(code, ""),
                    "credits": g.credits.get(code, 3),
                    "semester": g.semesters.get(code, 1),
                    "indegree": indegrees.get(code, 0)
                })

            data = {
                "courses": courses,
                "adj_list": g.adj_list,
                "indegrees": indegrees,
                "total_vertices": len(g.adj_list),
                "total_edges": sum(len(v) for v in g.adj_list.values())
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 8. Graph BFS Kahn Sort
        elif path == "/api/graph/bfs":
            dept = query.get("department", [None])[0]
            if dept == "All":
                dept = None
            g = CourseGraph.load_from_database(DB_PATH, department=dept)
            success, order, logs, cycle_nodes = g.bfs_topological_sort()
            is_valid, violations = g.validate_topological_order(order) if success else (False, [])
            res = {
                "success": success,
                "order": order,
                "logs": logs,
                "cycle_nodes": cycle_nodes,
                "is_valid": is_valid,
                "violations": violations
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 9. Graph DFS 3-State Sort
        elif path == "/api/graph/dfs":
            dept = query.get("department", [None])[0]
            if dept == "All":
                dept = None
            g = CourseGraph.load_from_database(DB_PATH, department=dept)
            success, order, logs, cycle_path = g.dfs_topological_sort()
            is_valid, violations = g.validate_topological_order(order) if success else (False, [])
            res = {
                "success": success,
                "order": order,
                "logs": logs,
                "cycle_path": cycle_path,
                "is_valid": is_valid,
                "violations": violations
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 10. Graph Cycle Audit
        elif path == "/api/graph/cycle-audit":
            dept = query.get("department", [None])[0]
            if dept == "All":
                dept = None
            g = CourseGraph.load_from_database(DB_PATH, department=dept)
            c_bfs, nodes, expl_bfs = g.detect_cycle_bfs()
            c_dfs, path_dfs, expl_dfs = g.detect_cycle_dfs()
            res = {
                "bfs": {"has_cycle": c_bfs, "nodes": nodes, "explanation": expl_bfs},
                "dfs": {"has_cycle": c_dfs, "path": path_dfs, "explanation": expl_dfs}
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 11. Cycle Injection Demonstration
        elif path == "/api/graph/cycle-demo":
            demo = CourseGraph.create_demo_cycle_graph()
            c_bfs, nodes, expl_b = demo.detect_cycle_bfs()
            c_dfs, path, expl_d = demo.detect_cycle_dfs()
            res = {
                "bfs": {"has_cycle": c_bfs, "nodes": nodes, "explanation": expl_b},
                "dfs": {"has_cycle": c_dfs, "path": path, "explanation": expl_d},
                "cycle_string": " -> ".join(path) if path else "CS101 -> CS102 -> CS104 -> CS201 -> CS101"
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 12. Admin Stats & Students
        elif path == "/api/admin/stats":
            stats = database.get_system_stats(DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            return

        elif path == "/api/admin/students":
            students = database.get_all_students(DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(students).encode("utf-8"))
            return

        elif path == "/api/admin/enrollments":
            enrollments = database.get_all_enrollments(DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(enrollments).encode("utf-8"))
            return

        elif path == "/api/admin/prerequisites":
            prereqs = database.get_all_prerequisites(DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(prereqs).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(b"Endpoint Not Found")

    # =========================================================================
    # POST REQUEST ROUTER
    # =========================================================================
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # 1. Authentication
        if path == "/api/login":
            username = body.get("username", "").strip().upper()
            password = body.get("password", "").strip()

            if username == "ADMIN" and password == "admin123":
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "role": "admin",
                    "user_id": "admin",
                    "name": "Portal Administrator"
                }).encode("utf-8"))
                return

            student = database.get_student_by_id(username, DB_PATH)
            if student and student["password"] == password:
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "role": "student",
                    "user_id": student["student_id"],
                    "student": dict(student)
                }).encode("utf-8"))
            else:
                self._set_headers(401)
                self.wfile.write(json.dumps({"success": False, "error": "Invalid Student ID or Password."}).encode("utf-8"))
            return

        # 2. Student Course Enrollment (Strict Backend Validation)
        elif path == "/api/enroll":
            stu_id = body.get("student_id", "").strip().upper()
            course_id = int(body.get("course_id", 0))
            semester = body.get("semester", None)

            success, message = enroll_student_in_course(stu_id, course_id, semester, DB_PATH)
            self._set_headers(200 if success else 400)
            self.wfile.write(json.dumps({"success": success, "message": message}).encode("utf-8"))
            return

        # 3. Drop Course Enrollment
        elif path == "/api/drop":
            enrollment_id = int(body.get("enrollment_id", 0))
            stu_id = body.get("student_id", "").strip().upper()
            success, message = drop_course_enrollment(enrollment_id, stu_id, DB_PATH)
            self._set_headers(200 if success else 400)
            self.wfile.write(json.dumps({"success": success, "message": message}).encode("utf-8"))
            return

        # 4. Admin Add Course
        elif path == "/api/admin/courses":
            try:
                c_id = database.add_course(
                    course_code=body["course_code"],
                    course_name=body["course_name"],
                    department=body["department"],
                    credits=int(body["credits"]),
                    semester=int(body["semester"]),
                    description=body.get("description", ""),
                    db_path=DB_PATH
                )
                self._set_headers(200)
                self.wfile.write(json.dumps({"success": True, "course_id": c_id}).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # 5. Admin Add Prerequisite
        elif path == "/api/admin/prerequisites":
            try:
                database.add_prerequisite(int(body["course_id"]), int(body["prereq_course_id"]), DB_PATH)
                self._set_headers(200)
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # 6. Admin Add Student
        elif path == "/api/admin/students":
            try:
                database.add_student(
                    student_id=body["student_id"],
                    name=body["name"],
                    email=body["email"],
                    password=body.get("password", "student123"),
                    department=body["department"],
                    semester=int(body.get("semester", 1)),
                    year=int(body.get("year", 1)),
                    phone=body.get("phone", ""),
                    db_path=DB_PATH
                )
                self._set_headers(200)
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(b"POST Endpoint Not Found")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/admin/students":
            stu_id = query.get("student_id", [""])[0]
            database.delete_student(stu_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        elif path == "/api/admin/prerequisites":
            c_id = int(query.get("course_id", [0])[0])
            p_id = int(query.get("prereq_course_id", [0])[0])
            database.remove_prerequisite(c_id, p_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(b"DELETE Endpoint Not Found")


# =============================================================================
# SINGLE-PAGE WEB APPLICATION HTML5 / CSS3 / JAVASCRIPT
# =============================================================================
HTML_PORTAL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>University Student Course Enrollment Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --bg: #0b1329;
      --surface: #111e38;
      --surface-card: #182849;
      --border: #233863;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --cyan: #38bdf8;
      --purple: #a855f7;
    }
    * { margin:0; padding:0; box-sizing:border-box; font-family:'Inter', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; display:flex; flex-direction:column; }
    
    header {
      background: rgba(17, 30, 56, 0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 0.85rem 2rem;
      display:flex;
      justify-content: space-between;
      align-items:center;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .brand { display:flex; align-items:center; gap: 0.75rem; }
    .brand-logo { font-size: 1.8rem; }
    .brand-title { font-size: 1.15rem; font-weight: 700; color: #fff; }
    .brand-sub { font-size: 0.75rem; color: var(--cyan); }
    .user-pill {
      display:flex;
      align-items:center;
      gap: 0.8rem;
      background: var(--surface-card);
      border: 1px solid var(--border);
      padding: 0.4rem 1rem;
      border-radius: 9999px;
      font-size: 0.85rem;
    }
    .user-pill .name { font-weight: 600; color: #fff; }
    .user-pill .badge { background: #1e3a8a; color: #60a5fa; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; }
    
    .btn {
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-secondary { background: var(--surface-card); color: #cbd5e1; border: 1px solid var(--border); }
    .btn-secondary:hover { background: #1e335a; color:#fff; }
    .btn-danger { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }
    .btn-danger:hover { background: #ef4444; color: #fff; }
    .btn-success { background: #10b981; color: #fff; }
    .btn-success:hover { background: #059669; }

    /* LAYOUT CONTAINER */
    .app-container { display:flex; flex:1; }
    .sidebar {
      width: 260px;
      background: var(--surface);
      border-right: 1px solid var(--border);
      padding: 1.25rem 0.75rem;
      display:flex;
      flex-direction:column;
      gap: 0.4rem;
    }
    .nav-item {
      display:flex;
      align-items:center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      color: var(--text-muted);
      cursor: pointer;
      font-weight: 500;
      font-size: 0.9rem;
      transition: all 0.2s;
    }
    .nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
    .nav-item.active { background: var(--primary); color: #fff; font-weight: 600; }
    .main-view { flex:1; padding: 2rem; overflow-y:auto; }

    /* CARDS & METRICS */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .card-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; display:flex; justify-content:space-between; align-items:center; }
    .metrics-row { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
    .stat-card {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.2rem;
      text-align: center;
    }
    .stat-val { font-size: 2rem; font-weight: 800; color: #fff; margin-bottom: 0.2rem; }
    .stat-lbl { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }

    /* TABLES */
    .table-container { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th { text-align: left; padding: 0.75rem 1rem; background: var(--surface-card); color: var(--text-muted); border-bottom: 1px solid var(--border); }
    td { padding: 0.75rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.05); color: #e2e8f0; }
    tr:hover td { background: rgba(255,255,255,0.02); }

    /* BADGES */
    .status-badge {
      display: inline-block;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.4px;
    }
    .b-available { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid #10b981; }
    .b-eligible { background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid #38bdf8; }
    .b-blocked { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }
    .b-completed { background: rgba(168, 85, 247, 0.2); color: #d8b4fe; border: 1px solid #a855f7; }
    .b-enrolled { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid #f59e0b; }

    /* FORMS & INPUTS */
    .form-group { margin-bottom: 1rem; }
    .form-group label { display:block; font-size: 0.8rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.35rem; }
    input, select, textarea {
      width: 100%;
      background: var(--surface-card);
      border: 1px solid var(--border);
      color: #fff;
      padding: 0.6rem 0.85rem;
      border-radius: 6px;
      font-size: 0.85rem;
      outline: none;
    }
    input:focus, select:focus, textarea:focus { border-color: var(--primary); }

    /* AUTH MODAL OVERLAY */
    .auth-overlay {
      position: fixed;
      top:0; left:0; width:100%; height:100%;
      background: rgba(11, 19, 41, 0.9);
      backdrop-filter: blur(8px);
      display:flex;
      align-items:center;
      justify-content:center;
      z-index: 1000;
    }
    .auth-box {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      width: 100%;
      max-width: 480px;
      padding: 2.2rem;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
    }

    /* CODE & CONSOLE */
    .code-console {
      background: #060b18;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      color: #38bdf8;
      max-height: 380px;
      overflow-y: auto;
      white-space: pre-wrap;
    }
    .check-item { display:flex; align-items:center; gap:0.5rem; padding: 0.4rem 0; font-size: 0.85rem; }
  </style>
</head>
<body>

  <!-- HEADER -->
  <header>
    <div class="brand">
      <div class="brand-logo">🎓</div>
      <div>
        <div class="brand-title">University Student Course Enrollment Portal</div>
        <div class="brand-sub">Directed Graph Prerequisites • Kahn's BFS • DFS 3-State Topological Sort</div>
      </div>
    </div>
    <div id="header-user" style="display:none;">
      <div class="user-pill">
        <span id="u-name" class="name">Student</span>
        <span id="u-badge" class="badge">CSE</span>
        <button class="btn btn-secondary" style="padding: 0.25rem 0.6rem; font-size:0.75rem;" onclick="logout()">Logout</button>
      </div>
    </div>
  </header>

  <!-- AUTHENTICATION OVERLAY -->
  <div id="auth-modal" class="auth-overlay">
    <div class="auth-box">
      <div style="text-align:center; margin-bottom:1.5rem;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🏛️</div>
        <h2 style="font-size:1.4rem; font-weight:700;">University Portal Login</h2>
        <p style="font-size:0.8rem; color:var(--text-muted); margin-top:0.3rem;">
          Sign in with your Student ID or Administrative Account
        </p>
      </div>

      <div class="form-group">
        <label>Student ID / Username</label>
        <input type="text" id="login-user" placeholder="e.g. STU001 or admin">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" id="login-pwd" placeholder="Enter password">
      </div>
      <button class="btn btn-primary" style="width:100%; justify-content:center; padding:0.7rem;" onclick="handleLogin()">
        🔑 Sign In to Portal
      </button>

      <div style="margin-top:1.5rem; border-top:1px solid var(--border); padding-top:1rem;">
        <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.6rem; text-align:center;">
          ⚡ Quick 1-Click Demo Accounts
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem;">
          <button class="btn btn-secondary" onclick="quickLogin('STU001', 'student123')">
            👤 Rahul Kumar (CSE)
          </button>
          <button class="btn btn-secondary" onclick="quickLogin('STU002', 'student123')">
            👤 Priya Sharma (AI&DS)
          </button>
          <button class="btn btn-secondary" onclick="quickLogin('STU003', 'student123')">
            👤 Arun Kumar (ECE)
          </button>
          <button class="btn btn-secondary" onclick="quickLogin('admin', 'admin123')">
            🛡️ Administrator
          </button>
        </div>
      </div>
      <div id="login-err" style="color:var(--danger); font-size:0.8rem; margin-top:0.8rem; text-align:center;"></div>
    </div>
  </div>

  <!-- APPLICATION BODY -->
  <div class="app-container" id="app-main" style="display:none;">
    <!-- SIDEBAR -->
    <div class="sidebar">
      <div class="nav-item active" id="btn-view-dashboard" onclick="switchNav('view-dashboard')">📊 Dashboard</div>
      <div class="nav-item" id="btn-view-courses" onclick="switchNav('view-courses')">📚 Courses Catalogue</div>
      <div class="nav-item" id="btn-view-enrollment" onclick="switchNav('view-enrollment')">✍️ Course Enrollment</div>
      <div class="nav-item" id="btn-view-completed" onclick="switchNav('view-completed')">🎓 Completed Courses</div>
      <div class="nav-item" id="btn-view-recommended" onclick="switchNav('view-recommended')">💡 Recommended Sequences</div>
      <div class="nav-item" id="btn-view-graph" onclick="switchNav('view-graph')">📈 Prerequisite Graph</div>
      <div class="nav-item" id="btn-view-admin" style="display:none;" onclick="switchNav('view-admin')">🛡️ Admin Management</div>
    </div>

    <!-- MAIN VIEW -->
    <div class="main-view">

      <!-- 1. DASHBOARD TAB -->
      <div id="view-dashboard">
        <div class="card">
          <div class="card-title">
            <div>
              <span id="dash-greeting" style="font-size:1.4rem;">Welcome!</span>
              <div id="dash-sub" style="font-size:0.85rem; color:var(--text-muted); font-weight:normal; margin-top:0.2rem;"></div>
            </div>
            <span class="status-badge b-eligible">Active Student</span>
          </div>

          <div class="metrics-row">
            <div class="stat-card">
              <div class="stat-val" id="m-dept-courses">0</div>
              <div class="stat-lbl">Department Courses</div>
            </div>
            <div class="stat-card">
              <div class="stat-val" id="m-completed" style="color:#a855f7;">0</div>
              <div class="stat-lbl">Completed Courses</div>
            </div>
            <div class="stat-card">
              <div class="stat-val" id="m-enrolled" style="color:#f59e0b;">0</div>
              <div class="stat-lbl">Current Enrollments</div>
            </div>
            <div class="stat-card">
              <div class="stat-val" id="m-available" style="color:#10b981;">0</div>
              <div class="stat-lbl">Eligible Courses</div>
            </div>
            <div class="stat-card">
              <div class="stat-val" id="m-blocked" style="color:#ef4444;">0</div>
              <div class="stat-lbl">Blocked Prereqs</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">Active Semester Course Registrations</div>
          <div class="table-container">
            <table id="dash-enr-table">
              <thead>
                <tr>
                  <th>Course Code</th>
                  <th>Course Title</th>
                  <th>Credits</th>
                  <th>Enrollment Date</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody id="dash-enr-body">
                <tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No active enrollments.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 2. COURSES CATALOGUE TAB -->
      <div id="view-courses" style="display:none;">
        <div class="card">
          <div class="card-title">
            Department Course Catalogue & Prerequisite Status
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">Auto-filtered to student department + university common subjects</span>
          </div>

          <div style="display:grid; grid-template-columns: 2fr 1fr 2fr; gap:1rem; margin-bottom:1rem;">
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Department Filter</label>
              <select id="course-filter-dept" onchange="loadCourses()">
                <option value="CSE">Computer Science and Engineering (CSE)</option>
                <option value="AI&DS">Artificial Intelligence & Data Science (AI&DS)</option>
                <option value="Information Technology">Information Technology (IT)</option>
                <option value="Cyber Security">Cyber Security</option>
                <option value="ECE">Electronics and Communication (ECE)</option>
                <option value="EEE">Electrical and Electronics (EEE)</option>
                <option value="MECH">Mechanical Engineering (MECH)</option>
                <option value="Civil Engineering">Civil Engineering</option>
                <option value="Computer Applications">Computer Applications (MCA)</option>
                <option value="All">All University Courses (112 Courses)</option>
              </select>
            </div>
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Semester</label>
              <select id="course-filter-sem" onchange="loadCourses()">
                <option value="All">All Semesters</option>
                <option value="1">Semester 1</option>
                <option value="2">Semester 2</option>
                <option value="3">Semester 3</option>
                <option value="4">Semester 4</option>
                <option value="5">Semester 5</option>
                <option value="6">Semester 6</option>
                <option value="7">Semester 7</option>
                <option value="8">Semester 8</option>
              </select>
            </div>
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Search Code or Title</label>
              <input type="text" id="course-search" placeholder="e.g. CS104 or Algorithms" oninput="loadCourses()">
            </div>
          </div>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Course Name</th>
                  <th>Department</th>
                  <th>Credits</th>
                  <th>Semester</th>
                  <th>Required Prerequisites</th>
                  <th>Eligibility Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody id="courses-table-body">
                <tr><td colspan="8" style="text-align:center;">Loading courses...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Course Prerequisite Inspection Box -->
        <div class="card" id="course-detail-box" style="display:none;">
          <div class="card-title" id="det-title">Course Inspection</div>
          <div id="det-body" style="font-size:0.9rem;"></div>
        </div>
      </div>

      <!-- 3. COURSE ENROLLMENT TAB -->
      <div id="view-enrollment" style="display:none;">
        <div class="card">
          <div class="card-title">
            Academic Course Enrollment & Prerequisite Verification
          </div>
          <div style="background:rgba(37,99,235,0.1); border:1px solid rgba(37,99,235,0.3); padding:1rem; border-radius:8px; margin-bottom:1.5rem; font-size:0.85rem;">
            <strong>Mandatory University Academic Policy:</strong><br>
            A student is strictly prohibited from enrolling in any course unless <strong>ALL</strong> mandatory prerequisite dependencies have been completed and verified against official academic records.
          </div>

          <div class="form-group">
            <label>Select Course to Enroll:</label>
            <select id="enroll-course-select" onchange="onEnrollCourseSelected()">
              <option value="">-- Choose an Available Course --</option>
            </select>
          </div>

          <div id="enroll-verify-panel" style="display:none; background:var(--surface-card); border:1px solid var(--border); border-radius:10px; padding:1.25rem; margin-top:1rem;">
            <div id="enroll-course-header" style="font-weight:700; font-size:1.1rem; color:#fff; margin-bottom:0.5rem;"></div>
            <div id="enroll-course-meta" style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;"></div>

            <div style="font-weight:600; font-size:0.9rem; margin-bottom:0.5rem; color:var(--cyan);">Prerequisite Verification Checklist:</div>
            <div id="enroll-checklist"></div>

            <div id="enroll-decision-box" style="margin-top:1.25rem; padding:1rem; border-radius:8px;"></div>
          </div>
        </div>
      </div>

      <!-- 4. COMPLETED COURSES TAB -->
      <div id="view-completed" style="display:none;">
        <div class="card">
          <div class="card-title">Official Completed Coursework & Academic Transcript</div>
          <div class="metrics-row" style="margin-bottom:1rem;">
            <div class="stat-card">
              <div class="stat-val" id="trans-count" style="color:#a855f7;">0</div>
              <div class="stat-lbl">Courses Passed</div>
            </div>
            <div class="stat-card">
              <div class="stat-val" id="trans-credits" style="color:#10b981;">0</div>
              <div class="stat-lbl">Credits Earned</div>
            </div>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Course Title</th>
                  <th>Department</th>
                  <th>Credits</th>
                  <th>Semester</th>
                  <th>Grade</th>
                  <th>Date Completed</th>
                </tr>
              </thead>
              <tbody id="completed-table-body">
                <tr><td colspan="7" style="text-align:center;">Loading completed courses...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 5. RECOMMENDED SEQUENCES TAB -->
      <div id="view-recommended" style="display:none;">
        <div class="card">
          <div class="card-title">Topologically Sequenced Course Recommendations</div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.5rem;">
            These recommendations are computed based on your current completed courses, department curriculum, and courses that unlock the highest number of downstream specializations.
          </p>
          <div id="rec-list"></div>
        </div>
      </div>

      <!-- 6. PREREQUISITE GRAPH TAB -->
      <div id="view-graph" style="display:none;">
        <div class="card">
          <div class="card-title">
            Directed Prerequisite Graph & Algorithm Engine
            <div style="display:flex; gap:0.5rem;">
              <button class="btn btn-secondary" onclick="runGraphBFS()">1. Run Kahn's BFS</button>
              <button class="btn btn-secondary" onclick="runGraphDFS()">2. Run DFS 3-State</button>
              <button class="btn btn-secondary" onclick="runCycleAudit()">3. Dual Cycle Audit</button>
              <button class="btn btn-danger" onclick="runDemoCycle()">🚨 Test Injected Cycle</button>
            </div>
          </div>

          <div class="metrics-row">
            <div class="stat-card">
              <div class="stat-val" id="g-v">0</div>
              <div class="stat-lbl">Vertices (|V|)</div>
            </div>
            <div class="stat-card">
              <div class="stat-val" id="g-e">0</div>
              <div class="stat-lbl">Directed Edges (|E|)</div>
            </div>
            <div class="stat-card">
              <div class="stat-val" id="g-entry" style="color:#10b981;">0</div>
              <div class="stat-lbl">In-Degree 0 (Entry)</div>
            </div>
          </div>

          <div style="margin-bottom:1.5rem;">
            <div style="font-size:0.85rem; font-weight:600; margin-bottom:0.4rem; color:var(--cyan);">Interactive Graph Canvas (Adjacency Matrix / List Projection)</div>
            <canvas id="canvas-graph" width="950" height="420" style="background:#070d1d; border:1px solid var(--border); border-radius:10px; width:100%;"></canvas>
          </div>

          <div style="font-size:0.9rem; font-weight:700; margin-bottom:0.5rem; color:#fff;">Execution Diagnostic Console Output:</div>
          <div class="code-console" id="graph-console">Click an algorithm button above to execute Kahn's BFS, DFS 3-State sort, or Cycle Detection.</div>
        </div>
      </div>

      <!-- 7. ADMIN TAB -->
      <div id="view-admin" style="display:none;">
        <div class="card">
          <div class="card-title">Administrator System Management</div>
          <div class="metrics-row">
            <div class="stat-card"><div class="stat-val" id="adm-courses">0</div><div class="stat-lbl">Courses</div></div>
            <div class="stat-card"><div class="stat-val" id="adm-prereqs">0</div><div class="stat-lbl">Prerequisites</div></div>
            <div class="stat-card"><div class="stat-val" id="adm-students">0</div><div class="stat-lbl">Students</div></div>
            <div class="stat-card"><div class="stat-val" id="adm-enrollments">0</div><div class="stat-lbl">Active Enrollments</div></div>
          </div>

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.5rem;">
            <!-- Register Student -->
            <div style="background:var(--surface-card); padding:1rem; border-radius:8px; border:1px solid var(--border);">
              <h4 style="margin-bottom:0.8rem; color:#38bdf8;">➕ Register New Student</h4>
              <div class="form-group"><label>Student ID</label><input type="text" id="adm-stu-id" placeholder="STU016"></div>
              <div class="form-group"><label>Full Name</label><input type="text" id="adm-stu-name" placeholder="John Doe"></div>
              <div class="form-group"><label>Email</label><input type="text" id="adm-stu-email" placeholder="john.doe@university.edu"></div>
              <div class="form-group">
                <label>Department</label>
                <select id="adm-stu-dept">
                  <option value="CSE">CSE</option>
                  <option value="AI&DS">AI&DS</option>
                  <option value="Information Technology">Information Technology</option>
                  <option value="Cyber Security">Cyber Security</option>
                  <option value="ECE">ECE</option>
                  <option value="EEE">EEE</option>
                  <option value="MECH">MECH</option>
                  <option value="Civil Engineering">Civil Engineering</option>
                </select>
              </div>
              <button class="btn btn-primary" onclick="adminAddStudent()">Register Student</button>
            </div>

            <!-- Add Prerequisite -->
            <div style="background:var(--surface-card); padding:1rem; border-radius:8px; border:1px solid var(--border);">
              <h4 style="margin-bottom:0.8rem; color:#38bdf8;">🔗 Add Prerequisite Dependency (A → B)</h4>
              <div class="form-group">
                <label>Prerequisite Course (A):</label>
                <select id="adm-prereq-a"></select>
              </div>
              <div class="form-group">
                <label>Target Course (B):</label>
                <select id="adm-prereq-b"></select>
              </div>
              <button class="btn btn-primary" onclick="adminAddPrereq()">Establish Dependency</button>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>

  <script>
    let CURRENT_USER = null;
    let CURRENT_COURSES = [];
    let GRAPH_DATA = null;

    // Login logic
    async function handleLogin() {
      const user = document.getElementById('login-user').value.trim();
      const pwd = document.getElementById('login-pwd').value.trim();
      if (!user || !pwd) {
        document.getElementById('login-err').innerText = 'Please enter both User ID and Password.';
        return;
      }
      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ username: user, password: pwd })
        });
        const data = await res.json();
        if (data.success) {
          setupSession(data);
        } else {
          document.getElementById('login-err').innerText = data.error || 'Login failed.';
        }
      } catch (e) {
        document.getElementById('login-err').innerText = 'Connection error.';
      }
    }

    function quickLogin(user, pwd) {
      document.getElementById('login-user').value = user;
      document.getElementById('login-pwd').value = pwd;
      handleLogin();
    }

    function setupSession(data) {
      CURRENT_USER = data;
      document.getElementById('auth-modal').style.display = 'none';
      document.getElementById('app-main').style.display = 'flex';
      document.getElementById('header-user').style.display = 'block';

      if (data.role === 'admin') {
        document.getElementById('u-name').innerText = 'Administrator';
        document.getElementById('u-badge').innerText = 'GLOBAL ADMIN';
        const adminBtn = document.getElementById('btn-view-admin');
        if (adminBtn) adminBtn.style.display = 'flex';
        switchNav('view-admin');
        loadAdminData();
      } else {
        document.getElementById('u-name').innerText = data.student.name;
        document.getElementById('u-badge').innerText = data.student.department;
        document.getElementById('course-filter-dept').value = data.student.department;
        const adminBtn = document.getElementById('btn-view-admin');
        if (adminBtn) adminBtn.style.display = 'none';
        switchNav('view-dashboard');
      }
    }

    function logout() {
      CURRENT_USER = null;
      document.getElementById('auth-modal').style.display = 'flex';
      document.getElementById('app-main').style.display = 'none';
      document.getElementById('header-user').style.display = 'none';
    }

    function switchNav(viewId) {
      document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
      const btn = document.getElementById('btn-' + viewId);
      if (btn) btn.classList.add('active');

      const views = ['view-dashboard', 'view-courses', 'view-enrollment', 'view-completed', 'view-recommended', 'view-graph', 'view-admin'];
      views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.style.display = (v === viewId) ? 'block' : 'none';
      });

      if (viewId === 'view-dashboard') loadDashboard();
      else if (viewId === 'view-courses') loadCourses();
      else if (viewId === 'view-enrollment') loadEnrollmentOptions();
      else if (viewId === 'view-completed') loadCompleted();
      else if (viewId === 'view-recommended') loadRecommended();
      else if (viewId === 'view-graph') loadGraph();
      else if (viewId === 'view-admin') loadAdminData();
    }

    // Dashboard loader
    async function loadDashboard() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/student/dashboard?student_id=' + stuId);
      const data = await res.json();

      document.getElementById('dash-greeting').innerText = `Welcome, ${data.student.name}! 👋`;
      document.getElementById('dash-sub').innerText = `${data.student.department} | Semester ${data.student.semester} | Academic Year ${data.student.year}`;

      document.getElementById('m-dept-courses').innerText = data.metrics.total_courses;
      document.getElementById('m-completed').innerText = data.metrics.completed_courses;
      document.getElementById('m-enrolled').innerText = data.metrics.active_enrollments;
      document.getElementById('m-available').innerText = data.metrics.available_courses;
      document.getElementById('m-blocked').innerText = data.metrics.blocked_courses;

      const tbody = document.getElementById('dash-enr-body');
      tbody.innerHTML = '';
      if (data.active_enrollments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No active enrollments for this semester.</td></tr>';
      } else {
        data.active_enrollments.forEach(enr => {
          tbody.innerHTML += `
            <tr>
              <td><strong>${enr.course_code}</strong></td>
              <td>${enr.course_name}</td>
              <td>${enr.credits}</td>
              <td>${enr.enrollment_date}</td>
              <td><span class="status-badge b-enrolled">${enr.status}</span></td>
              <td><button class="btn btn-danger" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="dropCourse(${enr.enrollment_id})">Drop</button></td>
            </tr>
          `;
        });
      }
    }

    // Courses loader
    async function loadCourses() {
      const stuId = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.student_id : 'STU001';
      const dept = document.getElementById('course-filter-dept').value;
      const sem = document.getElementById('course-filter-sem').value;
      const search = document.getElementById('course-search').value.trim();

      const res = await fetch(`/api/courses?student_id=${stuId}&department=${encodeURIComponent(dept)}&semester=${sem}&search=${encodeURIComponent(search)}`);
      CURRENT_COURSES = await res.json();

      const tbody = document.getElementById('courses-table-body');
      tbody.innerHTML = '';
      if (CURRENT_COURSES.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No courses found matching criteria.</td></tr>';
        return;
      }

      CURRENT_COURSES.forEach(c => {
        let badgeClass = 'b-available';
        if (c.status === 'ELIGIBLE') badgeClass = 'b-eligible';
        else if (c.status === 'BLOCKED') badgeClass = 'b-blocked';
        else if (c.status === 'COMPLETED') badgeClass = 'b-completed';
        else if (c.status === 'ENROLLED') badgeClass = 'b-enrolled';

        tbody.innerHTML += `
          <tr>
            <td><strong>${c.course_code}</strong></td>
            <td>${c.course_name}</td>
            <td>${c.department}</td>
            <td>${c.credits}</td>
            <td>Sem ${c.semester}</td>
            <td style="font-size:0.75rem; color:var(--text-muted);">${c.prerequisites_str}</td>
            <td><span class="status-badge ${badgeClass}">${c.status}</span></td>
            <td><button class="btn btn-secondary" style="padding:0.25rem 0.5rem; font-size:0.75rem;" onclick="inspectCourse(${c.course_id})">Inspect</button></td>
          </tr>
        `;
      });
    }

    // Inspect single course
    async function inspectCourse(cId) {
      const stuId = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.student_id : 'STU001';
      const res = await fetch(`/api/prerequisites/check?student_id=${stuId}&course_id=${cId}`);
      const data = await res.json();

      const box = document.getElementById('course-detail-box');
      box.style.display = 'block';
      document.getElementById('det-title').innerText = `${data.course.course_code} – ${data.course.course_name} (${data.course.credits} Credits)`;

      let prereqHtml = '';
      if (data.check.required_prereqs.length === 0) {
        prereqHtml = '<div style="color:var(--success);">✓ No prerequisites required. Directly available for enrollment.</div>';
      } else {
        data.check.required_prereqs.forEach(p => {
          const isDone = data.check.completed_prereqs.some(cp => cp.course_id === p.course_id);
          prereqHtml += `
            <div class="check-item" style="color: ${isDone ? 'var(--success)' : 'var(--danger)'}">
              ${isDone ? '✅' : '❌'} <strong>${p.course_code} - ${p.course_name}</strong> (${isDone ? 'Completed' : 'Missing / Incomplete'})
            </div>
          `;
        });
      }

      document.getElementById('det-body').innerHTML = `
        <div style="margin-bottom:0.6rem; color:var(--text-muted);">${data.course.description}</div>
        <div style="margin-bottom:0.6rem;"><strong>Department:</strong> ${data.course.department} | <strong>Semester:</strong> ${data.course.semester}</div>
        <div style="margin-top:0.8rem;"><strong>Prerequisite Breakdown:</strong></div>
        ${prereqHtml}
      `;
      box.scrollIntoView({ behavior: 'smooth' });
    }

    // Enrollment options loader
    async function loadEnrollmentOptions() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stuId = CURRENT_USER.student.student_id;
      const dept = CURRENT_USER.student.department;
      const res = await fetch(`/api/courses?student_id=${stuId}&department=${encodeURIComponent(dept)}&semester=All`);
      const courses = await res.json();

      const sel = document.getElementById('enroll-course-select');
      sel.innerHTML = '<option value="">-- Choose an Available Course --</option>';

      courses.forEach(c => {
        if (c.status !== 'COMPLETED' && c.status !== 'ENROLLED') {
          sel.innerHTML += `<option value="${c.course_id}">[${c.status}] ${c.course_code} - ${c.course_name} (Sem ${c.semester}, ${c.credits} Cr)</option>`;
        }
      });
      document.getElementById('enroll-verify-panel').style.display = 'none';
    }

    // On Course Selected for Enrollment
    async function onEnrollCourseSelected() {
      const cId = document.getElementById('enroll-course-select').value;
      if (!cId) {
        document.getElementById('enroll-verify-panel').style.display = 'none';
        return;
      }
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch(`/api/prerequisites/check?student_id=${stuId}&course_id=${cId}`);
      const data = await res.json();

      const panel = document.getElementById('enroll-verify-panel');
      panel.style.display = 'block';

      document.getElementById('enroll-course-header').innerText = `${data.course.course_code} – ${data.course.course_name}`;
      document.getElementById('enroll-course-meta').innerText = `Department: ${data.course.department} | Credits: ${data.course.credits} | Semester: ${data.course.semester}`;

      const checkList = document.getElementById('enroll-checklist');
      checkList.innerHTML = '';
      if (data.check.required_prereqs.length === 0) {
        checkList.innerHTML = '<div style="color:var(--success);">✓ Type 1 Course: No prerequisites required for enrollment.</div>';
      } else {
        data.check.required_prereqs.forEach(p => {
          const isDone = data.check.completed_prereqs.some(cp => cp.course_id === p.course_id);
          checkList.innerHTML += `
            <div class="check-item" style="color: ${isDone ? 'var(--success)' : 'var(--danger)'}">
              ${isDone ? '✅' : '❌'} <strong>${p.course_code} - ${p.course_name}</strong> (${isDone ? 'Completed' : 'Missing / Incomplete'})
            </div>
          `;
        });
      }

      const decBox = document.getElementById('enroll-decision-box');
      if (data.check.eligible) {
        decBox.style.background = 'rgba(16, 185, 129, 0.15)';
        decBox.style.border = '1px solid #10b981';
        decBox.innerHTML = `
          <div style="color:#6ee7b7; font-weight:700; margin-bottom:0.6rem;">🎉 ALL PREREQUISITES COMPLETED! Eligible for registration.</div>
          <button class="btn btn-success" style="width:100%; justify-content:center; padding:0.75rem;" onclick="confirmEnroll(${data.course.course_id})">
            🚀 ENROLL NOW IN THIS COURSE
          </button>
        `;
      } else {
        decBox.style.background = 'rgba(239, 68, 68, 0.15)';
        decBox.style.border = '1px solid #ef4444';
        const missing = data.check.missing_prereqs.map(m => m.course_code).join(', ');
        decBox.innerHTML = `
          <div style="color:#fca5a5; font-weight:700; margin-bottom:0.4rem;">❌ ENROLLMENT BLOCKED!</div>
          <div style="font-size:0.85rem; color:#fca5a5; margin-bottom:0.8rem;">You cannot enroll in this course because the following required prerequisite(s) are incomplete: <strong>${missing}</strong></div>
          <button class="btn btn-secondary" style="width:100%; justify-content:center; opacity:0.5; cursor:not-allowed;" disabled>
            🚫 ENROLLMENT BLOCKED (Complete Prerequisites First)
          </button>
        `;
      }
    }

    // Confirm Enrollment
    async function confirmEnroll(cId) {
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/enroll', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ student_id: stuId, course_id: cId })
      });
      const data = await res.json();
      if (data.success) {
        alert(data.message);
        loadEnrollmentOptions();
      } else {
        alert("Enrollment Failed: " + data.message);
      }
    }

    // Drop Course
    async function dropCourse(enrId) {
      if (!confirm("Are you sure you want to drop this course?")) return;
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/drop', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ enrollment_id: enrId, student_id: stuId })
      });
      const data = await res.json();
      alert(data.message);
      loadDashboard();
    }

    // Completed courses loader
    async function loadCompleted() {
      const stuId = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.student_id : 'STU001';
      const res = await fetch('/api/completed?student_id=' + stuId);
      const data = await res.json();

      document.getElementById('trans-count').innerText = data.length;
      document.getElementById('trans-credits').innerText = data.reduce((acc, c) => acc + c.credits, 0);

      const tbody = document.getElementById('completed-table-body');
      tbody.innerHTML = '';
      if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">No completed courses on record.</td></tr>';
        return;
      }
      data.forEach(c => {
        tbody.innerHTML += `
          <tr>
            <td><strong>${c.course_code}</strong></td>
            <td>${c.course_name}</td>
            <td>${c.department}</td>
            <td>${c.credits}</td>
            <td>Sem ${c.semester}</td>
            <td><span class="status-badge b-completed">${c.grade}</span></td>
            <td>${c.completed_on}</td>
          </tr>
        `;
      });
    }

    // Recommended sequences loader
    async function loadRecommended() {
      const stuId = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.student_id : 'STU001';
      const res = await fetch('/api/recommended?student_id=' + stuId);
      const data = await res.json();

      const list = document.getElementById('rec-list');
      list.innerHTML = '';
      if (data.length === 0) {
        list.innerHTML = '<div style="color:var(--success); text-align:center; padding:2rem;">🎉 All departmental courses completed or enrolled!</div>';
        return;
      }

      data.forEach((rec, idx) => {
        list.innerHTML += `
          <div style="background:var(--surface-card); border:1px solid var(--border); border-radius:10px; padding:1.2rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div>
                <span style="font-weight:700; font-size:1.1rem; color:#fff;">#${idx + 1} ${rec.course_code} – ${rec.course_name}</span>
                <span class="status-badge ${rec.status === 'ELIGIBLE' ? 'b-eligible' : 'b-available'}" style="margin-left:0.5rem;">${rec.status}</span>
              </div>
              <button class="btn btn-primary" style="padding:0.35rem 0.8rem; font-size:0.8rem;" onclick="confirmEnroll(${rec.course_id})">Enroll Now</button>
            </div>
            <div style="font-size:0.85rem; color:var(--text-muted); margin-top:0.4rem;">${rec.description}</div>
            <div style="margin-top:0.6rem; font-size:0.8rem; color:var(--cyan);">
              ★ Clears prerequisites for: <strong>${rec.unlocked_courses.length > 0 ? rec.unlocked_courses.join(', ') : 'Terminal Elective'}</strong>
            </div>
          </div>
        `;
      });
    }

    // Graph loader & canvas visualization
    async function loadGraph() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.department : 'All';
      const res = await fetch('/api/graph?department=' + encodeURIComponent(dept));
      GRAPH_DATA = await res.json();

      document.getElementById('g-v').innerText = GRAPH_DATA.total_vertices;
      document.getElementById('g-e').innerText = GRAPH_DATA.total_edges;
      const entryCount = Object.values(GRAPH_DATA.indegrees).filter(d => d === 0).length;
      document.getElementById('g-entry').innerText = entryCount;

      renderCanvasGraph();
    }

    function renderCanvasGraph() {
      const canvas = document.getElementById('canvas-graph');
      if (!canvas || !GRAPH_DATA) return;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const courses = GRAPH_DATA.courses.slice(0, 24); // Render top 24 courses for clean canvas layout
      const total = courses.length;
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const radius = 160;

      const positions = {};
      courses.forEach((c, idx) => {
        const angle = (idx / total) * 2 * Math.PI - Math.PI / 2;
        positions[c.code] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
          indegree: c.indegree
        };
      });

      // Draw directed edges
      Object.keys(GRAPH_DATA.adj_list).forEach(u => {
        const p1 = positions[u];
        if (!p1) return;
        const targets = GRAPH_DATA.adj_list[u];
        targets.forEach(v => {
          const p2 = positions[v];
          if (!p2) return;

          ctx.beginPath();
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
          ctx.lineWidth = 1.5;
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();

          // Arrow head
          const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
          ctx.beginPath();
          ctx.fillStyle = '#38bdf8';
          ctx.arc(p2.x - 18 * Math.cos(angle), p2.y - 18 * Math.sin(angle), 3, 0, 2 * Math.PI);
          ctx.fill();
        });
      });

      // Draw course nodes
      Object.keys(positions).forEach(code => {
        const p = positions[code];
        ctx.beginPath();
        ctx.arc(p.x, p.y, 18, 0, 2 * Math.PI);
        ctx.fillStyle = p.indegree === 0 ? 'rgba(16, 185, 129, 0.85)' : 'rgba(30, 58, 138, 0.9)';
        ctx.fill();
        ctx.strokeStyle = p.indegree === 0 ? '#6ee7b7' : '#38bdf8';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = '#fff';
        ctx.font = 'bold 9px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(code, p.x, p.y);
      });
    }

    async function runGraphBFS() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.department : 'All';
      const res = await fetch('/api/graph/bfs?department=' + encodeURIComponent(dept));
      const data = await res.json();
      let out = "=== BFS / KAHN'S TOPOLOGICAL SORT EXECUTION TRACE ===\\n";
      out += `Total Ordered: ${data.order.length} Courses\\n`;
      out += `Topological Sequence Validated [pos(u) < pos(v)]: ${data.is_valid}\\n\\n`;
      out += data.logs.join('\\n');
      document.getElementById('graph-console').innerText = out;
    }

    async function runGraphDFS() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.department : 'All';
      const res = await fetch('/api/graph/dfs?department=' + encodeURIComponent(dept));
      const data = await res.json();
      let out = "=== DFS 3-STATE TOPOLOGICAL SORT EXECUTION TRACE ===\\n";
      out += `Total Ordered: ${data.order.length} Courses\\n`;
      out += `Topological Sequence Validated: ${data.is_valid}\\n\\n`;
      out += data.logs.join('\\n');
      document.getElementById('graph-console').innerText = out;
    }

    async function runCycleAudit() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.department : 'All';
      const res = await fetch('/api/graph/cycle-audit?department=' + encodeURIComponent(dept));
      const data = await res.json();
      let out = "=== DUAL-ENGINE PREREQUISITE CYCLE AUDIT ===\\n";
      out += `1. BFS Kahn Starvation Check: Has Cycle? ${data.bfs.has_cycle ? 'YES ❌' : 'NO ✓'}\\n   ${data.bfs.explanation}\\n\\n`;
      out += `2. DFS Back-Edge Check: Has Cycle? ${data.dfs.has_cycle ? 'YES ❌' : 'NO ✓'}\\n   ${data.dfs.explanation}\\n`;
      document.getElementById('graph-console').innerText = out;
    }

    async function runDemoCycle() {
      const res = await fetch('/api/graph/cycle-demo');
      const data = await res.json();
      let out = "=== ARTIFICIAL PREREQUISITE DEADLOCK DEMONSTRATION ===\\n";
      out += `Circular Path Injected: ${data.cycle_string}\\n\\n`;
      out += `[Engine 1 - BFS Kahn's Algorithm]: Cycle Detected = ${data.bfs.has_cycle}\\n${data.bfs.explanation}\\n\\n`;
      out += `[Engine 2 - DFS Back-Edge Search]: Cycle Detected = ${data.dfs.has_cycle}\\n${data.dfs.explanation}\\n\\n`;
      out += "Real-World Interpretation: Prerequisite cycles completely block degree progression because every course in the loop requires another incomplete course in the loop!";
      document.getElementById('graph-console').innerText = out;
    }

    // Admin loaders
    async function loadAdminData() {
      const res = await fetch('/api/admin/stats');
      const stats = await res.json();
      document.getElementById('adm-courses').innerText = stats.total_courses;
      document.getElementById('adm-prereqs').innerText = stats.total_prerequisites;
      document.getElementById('adm-students').innerText = stats.total_students;
      document.getElementById('adm-enrollments').innerText = stats.active_enrollments;

      // Populate Prereq dropdowns
      const cRes = await fetch('/api/courses?department=All');
      const courses = await cRes.json();
      const sA = document.getElementById('adm-prereq-a');
      const sB = document.getElementById('adm-prereq-b');
      sA.innerHTML = '';
      sB.innerHTML = '';
      courses.forEach(c => {
        const opt = `<option value="${c.course_id}">${c.course_code} - ${c.course_name}</option>`;
        sA.innerHTML += opt;
        sB.innerHTML += opt;
      });
    }

    async function adminAddStudent() {
      const id = document.getElementById('adm-stu-id').value.trim().toUpperCase();
      const name = document.getElementById('adm-stu-name').value.trim();
      const email = document.getElementById('adm-stu-email').value.trim();
      const dept = document.getElementById('adm-stu-dept').value;

      if (!id || !name || !email) {
        alert("Please fill all required student fields.");
        return;
      }
      const res = await fetch('/api/admin/students', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ student_id: id, name: name, email: email, department: dept })
      });
      const data = await res.json();
      if (data.success) {
        alert("Student registered successfully!");
        loadAdminData();
      } else {
        alert("Error: " + data.error);
      }
    }

    async function adminAddPrereq() {
      const a = document.getElementById('adm-prereq-a').value;
      const b = document.getElementById('adm-prereq-b').value;
      if (a === b) {
        alert("A course cannot be a prerequisite of itself!");
        return;
      }
      const res = await fetch('/api/admin/prerequisites', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ course_id: b, prereq_course_id: a })
      });
      const data = await res.json();
      if (data.success) {
        alert("Prerequisite relationship established!");
        loadAdminData();
      } else {
        alert("Error: " + data.error);
      }
    }
  </script>
</body>
</html>
"""


def run_portal_server(port: int = PORT) -> http.server.ThreadingHTTPServer:
    """Starts the multi-threaded pure Python HTTP server on localhost."""
    database.init_database()
    handler = PortalAPIHandler
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"University Student Course Enrollment Portal is live at: http://localhost:{port}/")
    return server


if __name__ == "__main__":
    httpd = run_portal_server(PORT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nPortal Server shutting down.")
        httpd.server_close()
