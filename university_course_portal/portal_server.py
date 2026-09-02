"""
University Student Course Enrollment Portal - Localhost Multi-Threaded Web Application.
Features:
- Fixed Student Department & Semester-Locked Enrollment Access
- Teacher / Faculty Approval Workflow for Course Registrations
- "My Courses" Category (Now Running Courses + Completed Courses with Grade & Month)
- "Attendance" Category for Running Courses with Percentage & Exam Eligibility
- "Backlogs" Category for Uncleared/Arrear Courses with Supplementary Exam Registration
- "Student Profile" Category with Academic Standing and Mentor Information
- Admin University Notifications & Announcements Board (Exams, Holidays, Deadlines)
- Interactive Directed Prerequisite Graph with BFS Kahn, DFS 3-State, and Cycle Injection
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

        # 2. Student Dashboard Stats, Details, and Admin Notifications
        elif path == "/api/student/dashboard":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            student = database.get_student_by_id(stu_id, DB_PATH)
            if not student:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Student not found"}).encode("utf-8"))
                return

            dept = student["department"]
            sem = student["semester"]
            dept_courses = database.get_courses_by_department(dept, include_common=True, db_path=DB_PATH)
            completed = database.get_student_completed_courses(stu_id, DB_PATH)
            running_courses = database.get_running_courses(stu_id, DB_PATH)
            pending_enrollments = [e for e in database.get_student_enrollments(stu_id, DB_PATH) if e["approval_status"] == "Pending Teacher Approval"]
            backlogs = database.get_student_backlogs(stu_id, DB_PATH)
            notifications = database.get_all_notifications(DB_PATH)

            completed_ids = {c["course_id"] for c in completed}
            enrolled_ids = {e["course_id"] for e in database.get_student_enrollments(stu_id, DB_PATH)}

            # Accessible courses for current semester
            current_sem_courses = [c for c in dept_courses if c["semester"] == sem and c["course_id"] not in completed_ids and c["course_id"] not in enrolled_ids]
            available_count = 0
            blocked_count = 0
            for c in current_sem_courses:
                st = get_course_status(stu_id, c["course_id"], DB_PATH)
                if st in (CourseStatus.AVAILABLE, CourseStatus.ELIGIBLE):
                    available_count += 1
                elif st == CourseStatus.BLOCKED:
                    blocked_count += 1

            data = {
                "student": student,
                "metrics": {
                    "department": dept,
                    "year": student["year"],
                    "semester": sem,
                    "total_dept_courses": len(dept_courses),
                    "completed_courses": len(completed),
                    "running_courses": len(running_courses),
                    "pending_approvals": len(pending_enrollments),
                    "available_current_sem": available_count,
                    "blocked_prereqs": blocked_count,
                    "active_backlogs": len([b for b in backlogs if b["status"] == "Active Backlog"]),
                    "total_credits_earned": sum(c["credits"] for c in completed)
                },
                "running_courses": running_courses,
                "pending_enrollments": pending_enrollments,
                "backlogs": backlogs,
                "notifications": notifications
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 3. Courses Filtered by Fixed Student Department & Semester Access Locking
        elif path == "/api/courses":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            student = database.get_student_by_id(stu_id, DB_PATH)
            student_dept = student["department"] if student else "CSE"
            student_sem = student["semester"] if student else 4

            # Fixed department policy: show only student's department + approved common courses
            courses = database.get_courses_by_department(student_dept, include_common=True, db_path=DB_PATH)

            sem_filter = query.get("semester", ["All"])[0]
            if sem_filter != "All":
                courses = [c for c in courses if str(c["semester"]) == sem_filter]

            search = query.get("search", [""])[0].lower()
            if search:
                courses = [c for c in courses if search in c["course_code"].lower() or search in c["course_name"].lower()]

            results = []
            for c in courses:
                c_id = c["course_id"]
                c_status = get_course_status(stu_id, c_id, DB_PATH)
                prereqs = database.get_prerequisites_for_course(c_id, DB_PATH)
                prereq_str = ", ".join(p["course_code"] for p in prereqs) if prereqs else "None"
                
                # Semester Access Rule:
                # Student can ONLY enroll in courses matching their current academic semester!
                is_current_semester = (c["semester"] == student_sem)
                is_locked_by_semester = (c["semester"] > student_sem)

                item = dict(c)
                item["status"] = c_status.value
                item["prerequisites_str"] = prereq_str
                item["prerequisites_count"] = len(prereqs)
                item["is_current_semester"] = is_current_semester
                item["is_locked_by_semester"] = is_locked_by_semester
                results.append(item)

            self._set_headers(200)
            self.wfile.write(json.dumps(results).encode("utf-8"))
            return

        # 4. My Courses API (Running Courses + Completed with Month & Grade)
        elif path == "/api/student/mycourses":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            running = database.get_running_courses(stu_id, DB_PATH)
            pending = [e for e in database.get_student_enrollments(stu_id, DB_PATH) if e["approval_status"] == "Pending Teacher Approval"]
            completed = database.get_student_completed_courses(stu_id, DB_PATH)

            res = {
                "running_courses": running,
                "pending_approvals": pending,
                "completed_courses": completed
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 5. Student Attendance Tracker API
        elif path == "/api/student/attendance":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            attendance_records = database.get_student_attendance(stu_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(attendance_records).encode("utf-8"))
            return

        # 6. Student Backlogs / Arrears API
        elif path == "/api/student/backlogs":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            backlogs = database.get_student_backlogs(stu_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(backlogs).encode("utf-8"))
            return

        # 7. Check Prerequisites for Specific Course
        elif path == "/api/prerequisites/check":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            course_id = int(query.get("course_id", [0])[0])
            check = check_prerequisites(stu_id, course_id, DB_PATH)
            course = database.get_course_by_id(course_id, DB_PATH)
            status = get_course_status(stu_id, course_id, DB_PATH)
            student = database.get_student_by_id(stu_id, DB_PATH)

            is_sem_allowed = True
            if student and course:
                is_sem_allowed = (course["semester"] <= student["semester"])

            res = {
                "course": course,
                "status": status.value,
                "check": check,
                "is_sem_allowed": is_sem_allowed,
                "student_sem": student["semester"] if student else 1
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        # 8. Notifications API
        elif path == "/api/notifications":
            notifications = database.get_all_notifications(DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(notifications).encode("utf-8"))
            return

        # 9. Teacher / Faculty Pending Approvals
        elif path == "/api/teacher/pending":
            dept = query.get("department", [None])[0]
            pending = database.get_pending_approvals(department=dept, db_path=DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(pending).encode("utf-8"))
            return

        # 10. Recommended Courses
        elif path == "/api/recommended":
            stu_id = query.get("student_id", ["STU001"])[0].upper()
            recommended = get_recommended_courses(stu_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(recommended).encode("utf-8"))
            return

        # 11. Graph Topology API
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

        # 12. Graph BFS & DFS Algorithms
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

        elif path == "/api/admin/stats":
            stats = database.get_system_stats(DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps(stats).encode("utf-8"))
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

        # 1. Authentication (Student, Teacher, Admin)
        if path == "/api/login":
            username = body.get("username", "").strip().upper()
            password = body.get("password", "").strip()

            if username == "ADMIN" and password == "admin123":
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "role": "admin",
                    "user_id": "admin",
                    "name": "Academic Administrator"
                }).encode("utf-8"))
                return

            if (username == "TEACHER" or username == "FAC001") and (password == "teacher123" or password == "admin123"):
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "role": "teacher",
                    "user_id": "FAC001",
                    "name": "Dr. K. Raman (Faculty Advisor)",
                    "department": "CSE"
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

        # 2. Student Course Enrollment (Submits for Teacher Approval)
        elif path == "/api/enroll":
            stu_id = body.get("student_id", "").strip().upper()
            course_id = int(body.get("course_id", 0))
            student = database.get_student_by_id(stu_id, DB_PATH)
            course = database.get_course_by_id(course_id, DB_PATH)

            if not student or not course:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "message": "Invalid student or course."}).encode("utf-8"))
                return

            # Semester Access Rule:
            # Student can only enroll in courses for their specific year and semester!
            if course["semester"] > student["semester"]:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": f"Semester Access Restricted: As a Semester {student['semester']} student, you can only enroll in Semester {student['semester']} courses. {course['course_code']} belongs to Semester {course['semester']}."
                }).encode("utf-8"))
                return

            # Check Prerequisites
            check = check_prerequisites(stu_id, course_id, DB_PATH)
            if not check["eligible"]:
                missing_str = ", ".join(f"{m['course_code']}" for m in check["missing_prereqs"])
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": f"Enrollment Blocked: Missing mandatory prerequisite(s): {missing_str}"
                }).encode("utf-8"))
                return

            # Submit for Teacher Approval
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            try:
                database.add_enrollment(
                    student_id=stu_id,
                    course_id=course_id,
                    semester=student["semester"],
                    enrollment_date=now_str,
                    status="Pending Teacher Approval",
                    approval_status="Pending Teacher Approval",
                    faculty_name="Dr. K. Raman (Faculty Advisor)",
                    faculty_remarks="Submitted by student. Awaiting faculty approval.",
                    db_path=DB_PATH
                )
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": f"✓ Enrollment Request Submitted! Your registration for {course['course_code']} ({course['course_name']}) has been forwarded to your Department Faculty Advisor (Dr. K. Raman) for academic approval."
                }).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "message": f"Already enrolled or pending approval for this course."}).encode("utf-8"))
            return

        # 3. Teacher / Faculty Approval or Rejection Action
        elif path == "/api/teacher/approval":
            enrollment_id = int(body.get("enrollment_id", 0))
            action = body.get("action", "").strip()  # "Approve" or "Reject"
            remarks = body.get("remarks", "Reviewed and processed by Faculty Advisor.")

            new_status = "Approved" if action == "Approve" else "Rejected"
            try:
                database.update_enrollment_approval(enrollment_id, new_status, remarks, DB_PATH)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": f"Course enrollment request has been successfully {new_status}."
                }).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode("utf-8"))
            return

        # 4. Post New Notification (Admin)
        elif path == "/api/notifications":
            title = body.get("title", "").strip()
            category = body.get("category", "General").strip()
            message = body.get("message", "").strip()
            priority = body.get("priority", "Normal").strip()
            posted_by = body.get("posted_by", "Office of Academic Affairs").strip()

            if not title or not message:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "message": "Title and Message are required."}).encode("utf-8"))
                return

            n_id = database.add_notification(title, category, message, posted_by, priority, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "notification_id": n_id}).encode("utf-8"))
            return

        # 5. Pay Backlog Exam Fee
        elif path == "/api/student/backlogs/pay":
            backlog_id = int(body.get("backlog_id", 0))
            database.pay_backlog_exam_fee(backlog_id, DB_PATH)
            self._set_headers(200)
            self.wfile.write(json.dumps({"success": True, "message": "Supplementary Examination Fee Paid successfully! Registered for next exam session."}).encode("utf-8"))
            return

        # 6. Drop Course
        elif path == "/api/drop":
            enrollment_id = int(body.get("enrollment_id", 0))
            stu_id = body.get("student_id", "").strip().upper()
            success, message = drop_course_enrollment(enrollment_id, stu_id, DB_PATH)
            self._set_headers(200 if success else 400)
            self.wfile.write(json.dumps({"success": success, "message": message}).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(b"POST Endpoint Not Found")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/notifications":
            n_id = int(query.get("id", [0])[0])
            database.delete_notification(n_id, DB_PATH)
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
      --bg: #070d1e;
      --surface: #0f1a36;
      --surface-card: #152449;
      --border: #203565;
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
      background: rgba(15, 26, 54, 0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 0.8rem 2rem;
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
      padding: 0.35rem 0.9rem;
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
    .btn-secondary:hover { background: #1c2e5a; color:#fff; }
    .btn-danger { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }
    .btn-danger:hover { background: #ef4444; color: #fff; }
    .btn-success { background: #10b981; color: #fff; }
    .btn-success:hover { background: #059669; }

    /* LAYOUT CONTAINER */
    .app-container { display:flex; flex:1; }
    .sidebar {
      width: 270px;
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
      font-size: 0.88rem;
      transition: all 0.2s;
    }
    .nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
    .nav-item.active { background: var(--primary); color: #fff; font-weight: 600; }
    .main-view { flex:1; padding: 1.8rem 2.2rem; overflow-y:auto; }

    /* CARDS & METRICS */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .card-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; display:flex; justify-content:space-between; align-items:center; }
    .metrics-row { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
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
    .b-pending { background: rgba(234, 179, 8, 0.2); color: #fef08a; border: 1px solid #eab308; }
    .b-approved { background: rgba(16, 185, 129, 0.2); color: #86efac; border: 1px solid #10b981; }
    .b-locked { background: rgba(100, 116, 139, 0.25); color: #94a3b8; border: 1px solid #475569; }

    /* NOTIFICATION CARDS */
    .notif-card {
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.1rem;
      margin-bottom: 0.85rem;
      position: relative;
    }
    .notif-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem; }
    .notif-title { font-weight: 700; font-size: 0.95rem; color: #fff; }
    .notif-meta { font-size: 0.75rem; color: var(--text-muted); }
    .notif-body { font-size: 0.85rem; color: #cbd5e1; line-height: 1.4; }

    /* PROGRESS BARS */
    .progress-bar-bg { width: 100%; height: 10px; background: rgba(255,255,255,0.1); border-radius: 5px; overflow:hidden; }
    .progress-bar-fill { height: 100%; border-radius: 5px; transition: width 0.4s ease; }

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
      background: rgba(7, 13, 30, 0.92);
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
      max-width: 520px;
      padding: 2.2rem;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6);
    }
    .code-console {
      background: #040813;
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
        <div class="brand-sub">Academic Prerequisite Graph • Teacher Approval Workflow • Attendance & Backlogs</div>
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
        <div style="font-size:2.5rem; margin-bottom:0.4rem;">🏛️</div>
        <h2 style="font-size:1.35rem; font-weight:700;">University Portal Login</h2>
        <p style="font-size:0.8rem; color:var(--text-muted); margin-top:0.3rem;">
          Sign in with your Student ID, Faculty Advisor, or Administrator Account
        </p>
      </div>

      <div class="form-group">
        <label>User ID / Student ID / Username</label>
        <input type="text" id="login-user" placeholder="e.g. STU001, TEACHER, or admin">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" id="login-pwd" placeholder="Enter your password">
      </div>
      <button class="btn btn-primary" style="width:100%; justify-content:center; padding:0.7rem;" onclick="handleLogin()">
        🔑 Sign In to Portal
      </button>

      <div style="margin-top:1.5rem; border-top:1px solid var(--border); padding-top:1rem;">
        <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.6rem; text-align:center;">
          ⚡ 1-Click Role-Based Quick Logins
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem;">
          <button class="btn btn-secondary" onclick="quickLogin('STU001', 'student123')">
            👤 Rahul Kumar (CSE)
          </button>
          <button class="btn btn-secondary" onclick="quickLogin('STU002', 'student123')">
            👤 Priya Sharma (AI&DS)
          </button>
          <button class="btn btn-secondary" onclick="quickLogin('TEACHER', 'teacher123')">
            👨‍🏫 Faculty Advisor
          </button>
          <button class="btn btn-secondary" onclick="quickLogin('admin', 'admin123')">
            🛡️ Admin / Dean
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
      <div class="nav-item active" id="btn-view-dashboard" onclick="switchNav('view-dashboard')">📊 Dashboard & Notices</div>
      <div class="nav-item" id="btn-view-mycourses" onclick="switchNav('view-mycourses')">📖 My Courses</div>
      <div class="nav-item" id="btn-view-attendance" onclick="switchNav('view-attendance')">📈 Attendance Tracker</div>
      <div class="nav-item" id="btn-view-enrollment" onclick="switchNav('view-enrollment')">✍️ Course Enrollment</div>
      <div class="nav-item" id="btn-view-courses" onclick="switchNav('view-courses')">📚 Department Catalogue</div>
      <div class="nav-item" id="btn-view-backlogs" onclick="switchNav('view-backlogs')">⚠️ Backlogs & Arrears</div>
      <div class="nav-item" id="btn-view-recommended" onclick="switchNav('view-recommended')">💡 Recommended Sequence</div>
      <div class="nav-item" id="btn-view-graph" onclick="switchNav('view-graph')">📈 Prerequisite Graph</div>
      <div class="nav-item" id="btn-view-profile" onclick="switchNav('view-profile')">👤 Student Profile</div>
      <!-- Teacher / Admin Specific Tabs -->
      <div class="nav-item" id="btn-view-approvals" style="display:none;" onclick="switchNav('view-approvals')">👨‍🏫 Teacher Approvals</div>
      <div class="nav-item" id="btn-view-admin" style="display:none;" onclick="switchNav('view-admin')">🛡️ Admin Management</div>
    </div>

    <!-- MAIN VIEW -->
    <div class="main-view">

      <!-- 1. DASHBOARD & NOTIFICATIONS VIEW -->
      <div id="view-dashboard">
        <div class="card">
          <div class="card-title">
            <div>
              <span id="dash-greeting" style="font-size:1.35rem;">Welcome!</span>
              <div id="dash-sub" style="font-size:0.85rem; color:var(--text-muted); font-weight:normal; margin-top:0.2rem;"></div>
            </div>
            <span class="status-badge b-approved" id="dash-dept-badge">CSE Department</span>
          </div>

          <div class="metrics-row">
            <div class="stat-card"><div class="stat-val" id="m-running" style="color:#10b981;">0</div><div class="stat-lbl">Running Courses</div></div>
            <div class="stat-card"><div class="stat-val" id="m-completed" style="color:#a855f7;">0</div><div class="stat-lbl">Completed Courses</div></div>
            <div class="stat-card"><div class="stat-val" id="m-pending" style="color:#eab308;">0</div><div class="stat-lbl">Pending Approval</div></div>
            <div class="stat-card"><div class="stat-val" id="m-available" style="color:#38bdf8;">0</div><div class="stat-lbl">Current Sem Eligible</div></div>
            <div class="stat-card"><div class="stat-val" id="m-backlogs" style="color:#ef4444;">0</div><div class="stat-lbl">Active Backlogs</div></div>
          </div>
        </div>

        <!-- Official University Announcements / Notifications Board -->
        <div class="card">
          <div class="card-title">
            <span>📢 University Announcements & Academic Notifications</span>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">Real-time updates posted by Academic Administration</span>
          </div>
          <div id="dashboard-notifs-list">Loading announcements...</div>
        </div>
      </div>

      <!-- 2. MY COURSES VIEW (Now Running Courses + Completed with Grade & Month) -->
      <div id="view-mycourses" style="display:none;">
        <!-- Section 1: Running Courses -->
        <div class="card">
          <div class="card-title">
            <span>🏃 Currently Running Courses (Ongoing Semester)</span>
            <span class="status-badge b-approved">Active Registrations</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">
            Courses officially approved by your Department Faculty Advisor for the current academic session.
          </p>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Course Title</th>
                  <th>Credits</th>
                  <th>Faculty Advisor</th>
                  <th>Attendance</th>
                  <th>Approval Status</th>
                </tr>
              </thead>
              <tbody id="my-running-body">
                <tr><td colspan="6" style="text-align:center;">Loading running courses...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 2: Completed Courses Transcript (Below Running Courses) -->
        <div class="card">
          <div class="card-title">
            <span>🎓 Completed Courses & Official Grade History</span>
            <span class="status-badge b-completed">Academic Transcript</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">
            Official record of successfully passed courses with letter grades and completed month/year.
          </p>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Course Code</th>
                  <th>Course Title</th>
                  <th>Credits</th>
                  <th>Completed Month</th>
                  <th>Grade</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody id="my-completed-body">
                <tr><td colspan="6" style="text-align:center;">Loading completed courses...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 3. ATTENDANCE TRACKER VIEW -->
      <div id="view-attendance" style="display:none;">
        <div class="card">
          <div class="card-title">
            <span>📈 Attendance Tracker (Running Courses)</span>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:normal;">Minimum 75% attendance required to sit for End-Semester Exams</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.5rem;">
            Attendance is recorded per classroom and laboratory contact hour.
          </p>
          <div id="attendance-cards-list">Loading attendance records...</div>
        </div>
      </div>

      <!-- 4. COURSE ENROLLMENT VIEW (SEMESTER LOCKED + TEACHER APPROVAL) -->
      <div id="view-enrollment" style="display:none;">
        <div class="card">
          <div class="card-title">✍️ Academic Course Enrollment</div>
          <div style="background:rgba(37,99,235,0.1); border:1px solid rgba(37,99,235,0.3); padding:1rem; border-radius:8px; margin-bottom:1.5rem; font-size:0.85rem;">
            <strong>University Academic Enrollment Rules:</strong><br>
            1. <strong>Fixed Department:</strong> Only courses prescribed for your department are accessible.<br>
            2. <strong>Year & Semester Access:</strong> You have enrollment access <strong>ONLY</strong> for courses corresponding to your current academic year and semester.<br>
            3. <strong>Teacher Approval:</strong> Upon registration, enrollment is routed to your Department Faculty Advisor (Dr. K. Raman) for verification and formal approval.
          </div>

          <div class="form-group">
            <label>Select Current Semester Course to Enroll:</label>
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

      <!-- 5. DEPARTMENT CATALOGUE VIEW (FIXED DEPT) -->
      <div id="view-courses" style="display:none;">
        <div class="card">
          <div class="card-title">
            <span>📚 Department Curriculum Catalogue</span>
            <span class="status-badge b-available" id="cat-fixed-badge">Fixed Department</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">
            Curriculum roadmaps are fixed to your registered department. Higher semester courses are locked until you advance to that academic level.
          </p>

          <div style="display:grid; grid-template-columns: 1fr 2fr; gap:1rem; margin-bottom:1rem;">
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Filter by Semester</label>
              <select id="course-filter-sem" onchange="loadCatalogue()">
                <option value="All">All Semesters (Sem 1 - Sem 8)</option>
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
              <label style="font-size:0.75rem; color:var(--text-muted);">Search by Code or Course Name</label>
              <input type="text" id="course-search" placeholder="e.g. CS104, Algorithms, Database" oninput="loadCatalogue()">
            </div>
          </div>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Course Title</th>
                  <th>Credits</th>
                  <th>Semester</th>
                  <th>Required Prerequisites</th>
                  <th>Enrollment Access</th>
                </tr>
              </thead>
              <tbody id="catalogue-table-body">
                <tr><td colspan="6" style="text-align:center;">Loading catalogue...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 6. BACKLOGS & ARREARS VIEW -->
      <div id="view-backlogs" style="display:none;">
        <div class="card">
          <div class="card-title">
            <span>⚠️ Backlogs & Arrear Examination Registry</span>
            <span class="status-badge b-blocked">Academic Arrears</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.5rem;">
            Students with uncleared courses must register and pay the supplementary examination fee before the deadline.
          </p>
          <div id="backlogs-content">Loading backlogs...</div>
        </div>
      </div>

      <!-- 7. RECOMMENDED SEQUENCE VIEW -->
      <div id="view-recommended" style="display:none;">
        <div class="card">
          <div class="card-title">💡 Topologically Sequenced Course Recommendations</div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.5rem;">
            Courses prioritized based on prerequisite graph in-degrees and downstream unlock potential.
          </p>
          <div id="rec-list"></div>
        </div>
      </div>

      <!-- 8. PREREQUISITE GRAPH VIEW -->
      <div id="view-graph" style="display:none;">
        <div class="card">
          <div class="card-title">
            <span>📈 Department Prerequisite Directed Graph G = (V, E)</span>
            <div style="display:flex; gap:0.5rem;">
              <button class="btn btn-secondary" onclick="runGraphBFS()">1. Run Kahn's BFS</button>
              <button class="btn btn-secondary" onclick="runGraphDFS()">2. Run DFS 3-State</button>
              <button class="btn btn-danger" onclick="runDemoCycle()">🚨 Test Injected Cycle</button>
            </div>
          </div>
          <div class="metrics-row">
            <div class="stat-card"><div class="stat-val" id="g-v">0</div><div class="stat-lbl">Courses (|V|)</div></div>
            <div class="stat-card"><div class="stat-val" id="g-e">0</div><div class="stat-lbl">Prerequisite Edges (|E|)</div></div>
            <div class="stat-card"><div class="stat-val" id="g-entry" style="color:#10b981;">0</div><div class="stat-lbl">In-Degree 0 (Entry)</div></div>
          </div>
          <canvas id="canvas-graph" width="950" height="380" style="background:#050914; border:1px solid var(--border); border-radius:10px; width:100%; margin-bottom:1rem;"></canvas>
          <div class="code-console" id="graph-console">Click an algorithm button above to execute Kahn's BFS, DFS 3-State sort, or Cycle Detection.</div>
        </div>
      </div>

      <!-- 9. STUDENT PROFILE VIEW -->
      <div id="view-profile" style="display:none;">
        <div class="card">
          <div class="card-title">👤 Official Student Academic Profile</div>
          <div style="display:flex; gap:2rem; align-items:flex-start; margin-bottom:1.5rem;">
            <div style="font-size:4.5rem; background:var(--surface-card); border-radius:50%; width:110px; height:110px; display:flex; align-items:center; justify-content:center; border:2px solid var(--cyan);">
              👨‍🎓
            </div>
            <div style="flex:1;">
              <h2 id="prof-name" style="font-size:1.5rem; font-weight:800; color:#fff;">Student Name</h2>
              <div id="prof-id" style="font-family:'JetBrains Mono'; color:var(--cyan); margin-bottom:0.8rem;">STU001</div>
              <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.6rem; font-size:0.88rem;">
                <div><strong>Department:</strong> <span id="prof-dept">CSE</span></div>
                <div><strong>Current Level:</strong> <span id="prof-year-sem">Year 2, Semester 4</span></div>
                <div><strong>Email:</strong> <span id="prof-email">student@university.edu</span></div>
                <div><strong>Mobile:</strong> <span id="prof-phone">+91 9876543210</span></div>
                <div><strong>Faculty Advisor:</strong> <span id="prof-advisor">Dr. K. Raman (Associate Professor)</span></div>
                <div><strong>Academic Standing:</strong> <span class="status-badge b-approved">Good Standing (No Disciplinary Actions)</span></div>
              </div>
            </div>
          </div>

          <div style="background:var(--surface-card); padding:1.2rem; border-radius:10px; border:1px solid var(--border);">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem; font-size:0.85rem;">
              <span>Degree Credits Progress</span>
              <strong id="prof-credits-lbl">42 / 160 Credits (26.2%)</strong>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" id="prof-credits-fill" style="width:26%; background:linear-gradient(90deg, #2563eb, #38bdf8);"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 10. TEACHER APPROVAL VIEW -->
      <div id="view-approvals" style="display:none;">
        <div class="card">
          <div class="card-title">
            <span>👨‍🏫 Faculty Advisor Course Enrollment Approvals</span>
            <span class="status-badge b-pending" id="pending-count-badge">0 Pending</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.5rem;">
            Review and approve student course registration requests. Only requests meeting all prerequisite requirements should be approved.
          </p>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Department</th>
                  <th>Year / Sem</th>
                  <th>Course Code & Title</th>
                  <th>Credits</th>
                  <th>Prerequisite Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="approvals-table-body">
                <tr><td colspan="7" style="text-align:center;">Loading pending requests...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 11. ADMIN VIEW (NOTIFICATIONS POSTING & SYSTEM MANAGEMENT) -->
      <div id="view-admin" style="display:none;">
        <div class="card">
          <div class="card-title">
            <span>📢 Post University Announcements & Notifications</span>
            <span class="status-badge b-approved">Admin Control</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">
            Announcements posted here immediately display on all student dashboards (e.g. Semester Exams, Holidays, Academic deadlines).
          </p>

          <div style="background:var(--surface-card); padding:1.2rem; border-radius:10px; border:1px solid var(--border); margin-bottom:1.5rem;">
            <div style="display:grid; grid-template-columns: 2fr 1fr 1fr; gap:1rem; margin-bottom:0.8rem;">
              <div>
                <label style="font-size:0.75rem; color:var(--text-muted);">Announcement Title</label>
                <input type="text" id="notif-input-title" placeholder="e.g. End-Semester Examination Timetable 2026">
              </div>
              <div>
                <label style="font-size:0.75rem; color:var(--text-muted);">Category</label>
                <select id="notif-input-cat">
                  <option value="Exam">Exam Schedule</option>
                  <option value="Holiday">University Holiday</option>
                  <option value="Academic">Academic Notice</option>
                  <option value="Fee">Fee Payment</option>
                  <option value="General">General Event</option>
                </select>
              </div>
              <div>
                <label style="font-size:0.75rem; color:var(--text-muted);">Priority Level</label>
                <select id="notif-input-priority">
                  <option value="Normal">Normal</option>
                  <option value="High">High</option>
                  <option value="Urgent">Urgent</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label style="font-size:0.75rem; color:var(--text-muted);">Detailed Announcement Message</label>
              <textarea id="notif-input-msg" rows="3" placeholder="Enter notification message text..."></textarea>
            </div>
            <button class="btn btn-primary" onclick="adminPostNotification()">📢 Publish Announcement to Dashboard</button>
          </div>

          <div class="card-title">Existing Published Announcements</div>
          <div id="admin-notifs-table">Loading announcements...</div>
        </div>
      </div>

    </div>
  </div>

  <script>
    let CURRENT_USER = null;
    let GRAPH_DATA = null;

    async function handleLogin() {
      const user = document.getElementById('login-user').value.trim();
      const pwd = document.getElementById('login-pwd').value.trim();
      if (!user || !pwd) {
        document.getElementById('login-err').innerText = 'Please enter User ID and Password.';
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

      const btnAdmin = document.getElementById('btn-view-admin');
      const btnApprovals = document.getElementById('btn-view-approvals');

      if (data.role === 'admin') {
        document.getElementById('u-name').innerText = 'Administrator';
        document.getElementById('u-badge').innerText = 'ADMIN / DEAN';
        btnAdmin.style.display = 'flex';
        btnApprovals.style.display = 'flex';
        switchNav('view-admin');
      } else if (data.role === 'teacher') {
        document.getElementById('u-name').innerText = data.name;
        document.getElementById('u-badge').innerText = 'FACULTY ADVISOR';
        btnAdmin.style.display = 'none';
        btnApprovals.style.display = 'flex';
        switchNav('view-approvals');
      } else {
        document.getElementById('u-name').innerText = data.student.name;
        document.getElementById('u-badge').innerText = `${data.student.department} • Sem ${data.student.semester}`;
        btnAdmin.style.display = 'none';
        btnApprovals.style.display = 'none';
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

      const views = [
        'view-dashboard', 'view-mycourses', 'view-attendance', 'view-enrollment',
        'view-courses', 'view-backlogs', 'view-recommended', 'view-graph',
        'view-profile', 'view-approvals', 'view-admin'
      ];
      views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.style.display = (v === viewId) ? 'block' : 'none';
      });

      if (viewId === 'view-dashboard') loadDashboard();
      else if (viewId === 'view-mycourses') loadMyCourses();
      else if (viewId === 'view-attendance') loadAttendance();
      else if (viewId === 'view-enrollment') loadEnrollment();
      else if (viewId === 'view-courses') loadCatalogue();
      else if (viewId === 'view-backlogs') loadBacklogs();
      else if (viewId === 'view-recommended') loadRecommended();
      else if (viewId === 'view-graph') loadGraph();
      else if (viewId === 'view-profile') loadProfile();
      else if (viewId === 'view-approvals') loadApprovals();
      else if (viewId === 'view-admin') loadAdminNotifications();
    }

    // 1. DASHBOARD LOADER
    async function loadDashboard() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/student/dashboard?student_id=' + stuId);
      const data = await res.json();

      document.getElementById('dash-greeting').innerText = `Welcome, ${data.student.name}! 👋`;
      document.getElementById('dash-sub').innerText = `Department: ${data.student.department} (Fixed) | Academic Year: Year ${data.student.year} | Current Semester: Semester ${data.student.semester}`;
      document.getElementById('dash-dept-badge').innerText = `${data.student.department} Department`;

      document.getElementById('m-running').innerText = data.metrics.running_courses;
      document.getElementById('m-completed').innerText = data.metrics.completed_courses;
      document.getElementById('m-pending').innerText = data.metrics.pending_approvals;
      document.getElementById('m-available').innerText = data.metrics.available_current_sem;
      document.getElementById('m-backlogs').innerText = data.metrics.active_backlogs;

      // Render Announcements / Notifications List
      const nList = document.getElementById('dashboard-notifs-list');
      nList.innerHTML = '';
      if (data.notifications.length === 0) {
        nList.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem;">No current university announcements.</div>';
      } else {
        data.notifications.forEach(n => {
          let priorityColor = '#38bdf8';
          if (n.priority === 'Urgent') priorityColor = '#ef4444';
          else if (n.priority === 'High') priorityColor = '#f59e0b';

          nList.innerHTML += `
            <div class="notif-card" style="border-left: 4px solid ${priorityColor};">
              <div class="notif-header">
                <div class="notif-title">${n.title}</div>
                <div>
                  <span class="status-badge" style="background:rgba(255,255,255,0.08); color:#cbd5e1; margin-right:0.4rem;">${n.category}</span>
                  <span class="status-badge" style="background:${priorityColor}22; color:${priorityColor}; border:1px solid ${priorityColor};">${n.priority}</span>
                </div>
              </div>
              <div class="notif-body">${n.message}</div>
              <div class="notif-meta" style="margin-top:0.5rem;">Posted by: ${n.posted_by} • ${n.posted_date}</div>
            </div>
          `;
        });
      }
    }

    // 2. MY COURSES LOADER (Running Courses + Completed Courses with Month & Grade)
    async function loadMyCourses() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/student/mycourses?student_id=' + stuId);
      const data = await res.json();

      // Running courses table
      const rBody = document.getElementById('my-running-body');
      rBody.innerHTML = '';
      if (data.running_courses.length === 0 && data.pending_approvals.length === 0) {
        rBody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No active courses running currently. Go to Course Enrollment to register.</td></tr>';
      } else {
        data.running_courses.forEach(c => {
          rBody.innerHTML += `
            <tr>
              <td><strong>${c.course_code}</strong></td>
              <td>${c.course_name}</td>
              <td>${c.credits} Credits</td>
              <td>${c.faculty_name || 'Dr. K. Raman'}</td>
              <td><span class="status-badge b-available">${c.attendance_percentage}% Attended</span></td>
              <td><span class="status-badge b-approved">Approved & Running</span></td>
            </tr>
          `;
        });
        data.pending_approvals.forEach(p => {
          rBody.innerHTML += `
            <tr style="background:rgba(234,179,8,0.04);">
              <td><strong>${p.course_code}</strong></td>
              <td>${p.course_name}</td>
              <td>${p.credits} Credits</td>
              <td>${p.faculty_name}</td>
              <td><span style="color:var(--text-muted); font-size:0.75rem;">Awaiting Approval</span></td>
              <td><span class="status-badge b-pending">Pending Teacher Approval</span></td>
            </tr>
          `;
        });
      }

      // Completed courses table (below running)
      const cBody = document.getElementById('my-completed-body');
      cBody.innerHTML = '';
      if (data.completed_courses.length === 0) {
        cBody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No completed coursework recorded yet.</td></tr>';
      } else {
        data.completed_courses.forEach(cc => {
          cBody.innerHTML += `
            <tr>
              <td><strong>${cc.course_code}</strong></td>
              <td>${cc.course_name}</td>
              <td>${cc.credits} Cr</td>
              <td style="color:var(--cyan);">${cc.completed_month || 'May 2025'}</td>
              <td><strong style="color:#a855f7; font-size:0.95rem;">${cc.grade}</strong></td>
              <td><span class="status-badge b-completed">Passed</span></td>
            </tr>
          `;
        });
      }
    }

    // 3. ATTENDANCE TRACKER LOADER
    async function loadAttendance() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/student/attendance?student_id=' + stuId);
      const data = await res.json();

      const container = document.getElementById('attendance-cards-list');
      container.innerHTML = '';
      if (data.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted); font-size:0.9rem;">No active running courses with attendance tracker.</div>';
        return;
      }

      data.forEach(att => {
        const pct = att.attendance_percentage;
        let statusClass = 'b-approved';
        let statusText = '✓ Eligible for End-Sem Exam';
        let barColor = '#10b981';

        if (pct < 75) {
          statusClass = 'b-blocked';
          statusText = '⚠️ Shortage Warning (<75%)';
          barColor = '#ef4444';
        } else if (pct < 80) {
          statusClass = 'b-enrolled';
          statusText = 'Acceptable (Near 75% Limit)';
          barColor = '#f59e0b';
        }

        container.innerHTML += `
          <div style="background:var(--surface-card); border:1px solid var(--border); border-radius:10px; padding:1.2rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
              <div>
                <span style="font-weight:700; font-size:1.1rem; color:#fff;">${att.course_code} – ${att.course_name}</span>
                <span style="color:var(--text-muted); font-size:0.8rem; margin-left:0.5rem;">(${att.credits} Credits • Sem ${att.semester})</span>
              </div>
              <span class="status-badge ${statusClass}">${statusText}</span>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:1rem; margin-bottom:0.8rem; font-size:0.85rem;">
              <div>Classes Attended: <strong>${att.attended_classes} / ${att.total_classes}</strong></div>
              <div>Attendance: <strong style="color:${barColor}; font-size:1.1rem;">${pct}%</strong></div>
              <div>Faculty: <span style="color:var(--text-muted);">${att.faculty_name || 'Dr. K. Raman'}</span></div>
            </div>

            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width:${pct}%; background:${barColor};"></div>
            </div>
          </div>
        `;
      });
    }

    // 4. ENROLLMENT LOADER (SEMESTER LOCKED)
    async function loadEnrollment() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch(`/api/courses?student_id=${stuId}&semester=All`);
      const courses = await res.json();

      const sel = document.getElementById('enroll-course-select');
      sel.innerHTML = '<option value="">-- Choose an Available Course --</option>';

      // Only show current semester candidate courses for enrollment
      courses.forEach(c => {
        if (c.status !== 'COMPLETED' && c.status !== 'ENROLLED' && c.status !== 'Approved') {
          if (c.is_current_semester) {
            sel.innerHTML += `<option value="${c.course_id}">[Sem ${c.semester}] ${c.course_code} - ${c.course_name} (${c.credits} Cr) • Status: ${c.status}</option>`;
          }
        }
      });
      document.getElementById('enroll-verify-panel').style.display = 'none';
    }

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
      document.getElementById('enroll-course-meta').innerText = `Department: ${data.course.department} (Fixed) | Credits: ${data.course.credits} | Current Semester: Semester ${data.student_sem}`;

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
      if (data.check.eligible && data.is_sem_allowed) {
        decBox.style.background = 'rgba(16, 185, 129, 0.15)';
        decBox.style.border = '1px solid #10b981';
        decBox.innerHTML = `
          <div style="color:#6ee7b7; font-weight:700; margin-bottom:0.4rem;">🎉 ALL PREREQUISITES SATISFIED!</div>
          <p style="font-size:0.8rem; color:#cbd5e1; margin-bottom:0.75rem;">
            Click below to register. Your enrollment will be submitted directly to your Department Faculty Advisor (Dr. K. Raman) for acceptance.
          </p>
          <button class="btn btn-success" style="width:100%; justify-content:center; padding:0.75rem;" onclick="submitEnrollmentRequest(${data.course.course_id})">
            📝 SUBMIT ENROLLMENT FOR TEACHER APPROVAL
          </button>
        `;
      } else if (!data.is_sem_allowed) {
        decBox.style.background = 'rgba(100, 116, 139, 0.2)';
        decBox.style.border = '1px solid #64748b';
        decBox.innerHTML = `
          <div style="color:#cbd5e1; font-weight:700;">🔒 SEMESTER ACCESS RESTRICTED</div>
          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.4rem;">
            You are enrolled in Semester ${data.student_sem}. Courses from higher semesters are locked and cannot be enrolled prematurely.
          </div>
        `;
      } else {
        decBox.style.background = 'rgba(239, 68, 68, 0.15)';
        decBox.style.border = '1px solid #ef4444';
        const missing = data.check.missing_prereqs.map(m => m.course_code).join(', ');
        decBox.innerHTML = `
          <div style="color:#fca5a5; font-weight:700;">❌ ENROLLMENT BLOCKED</div>
          <div style="font-size:0.85rem; color:#fca5a5; margin-top:0.3rem;">
            Incomplete required prerequisite(s): <strong>${missing}</strong>.
          </div>
        `;
      }
    }

    async function submitEnrollmentRequest(courseId) {
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/enroll', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ student_id: stuId, course_id: courseId })
      });
      const data = await res.json();
      alert(data.message);
      loadEnrollment();
      switchNav('view-mycourses');
    }

    // 5. DEPARTMENT CATALOGUE LOADER (FIXED DEPT)
    async function loadCatalogue() {
      const stuId = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.student_id : 'STU001';
      const sem = document.getElementById('course-filter-sem').value;
      const search = document.getElementById('course-search').value.trim();

      const res = await fetch(`/api/courses?student_id=${stuId}&semester=${sem}&search=${encodeURIComponent(search)}`);
      const courses = await res.json();

      const tbody = document.getElementById('catalogue-table-body');
      tbody.innerHTML = '';
      if (courses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No courses found matching criteria.</td></tr>';
        return;
      }

      courses.forEach(c => {
        let badgeClass = 'b-available';
        let accessText = c.status;

        if (c.is_locked_by_semester) {
          badgeClass = 'b-locked';
          accessText = `🔒 Locked (Sem ${c.semester})`;
        } else if (c.status === 'COMPLETED') {
          badgeClass = 'b-completed';
          accessText = 'Passed';
        } else if (c.status === 'Approved' || c.status === 'ENROLLED') {
          badgeClass = 'b-approved';
          accessText = 'Enrolled / Running';
        } else if (c.status === 'ELIGIBLE') {
          badgeClass = 'b-eligible';
          accessText = 'Eligible (Open)';
        } else if (c.status === 'BLOCKED') {
          badgeClass = 'b-blocked';
          accessText = 'Blocked Prereq';
        }

        tbody.innerHTML += `
          <tr>
            <td><strong>${c.course_code}</strong></td>
            <td>${c.course_name}</td>
            <td>${c.credits}</td>
            <td>Semester ${c.semester}</td>
            <td style="font-size:0.75rem; color:var(--text-muted);">${c.prerequisites_str}</td>
            <td><span class="status-badge ${badgeClass}">${accessText}</span></td>
          </tr>
        `;
      });
    }

    // 6. BACKLOGS & ARREARS LOADER
    async function loadBacklogs() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stuId = CURRENT_USER.student.student_id;
      const res = await fetch('/api/student/backlogs?student_id=' + stuId);
      const backlogs = await res.json();

      const container = document.getElementById('backlogs-content');
      if (backlogs.length === 0) {
        container.innerHTML = `
          <div style="background:rgba(16,185,129,0.1); border:1px solid #10b981; border-radius:10px; padding:2rem; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎉</div>
            <h3 style="color:#86efac;">Congratulations! Zero Active Backlogs</h3>
            <p style="color:#cbd5e1; font-size:0.85rem; margin-top:0.3rem;">
              You have successfully cleared all examinations in your degree curriculum with no pending arrears.
            </p>
          </div>
        `;
        return;
      }

      let html = '<div class="table-container"><table><thead><tr><th>Course Code</th><th>Course Name</th><th>Origin Sem</th><th>Grade</th><th>Attempts</th><th>Fee Status</th><th>Action</th></tr></thead><tbody>';
      backlogs.forEach(b => {
        html += `
          <tr>
            <td><strong>${b.course_code}</strong></td>
            <td>${b.course_name}</td>
            <td>Sem ${b.semester}</td>
            <td><span class="status-badge b-blocked">${b.grade} (Fail)</span></td>
            <td>Attempt #${b.attempt_count}</td>
            <td><span class="status-badge ${b.exam_fee_status === 'Unpaid' ? 'b-blocked' : 'b-approved'}">${b.exam_fee_status}</span></td>
            <td>
              ${b.exam_fee_status === 'Unpaid' 
                ? `<button class="btn btn-primary" style="padding:0.25rem 0.6rem; font-size:0.75rem;" onclick="payBacklogFee(${b.backlog_id})">💳 Pay Fee & Register Exam</button>`
                : `<span style="color:#10b981; font-size:0.75rem;">✓ Registered for Supplementary Exam</span>`
              }
            </td>
          </tr>
        `;
      });
      html += '</tbody></table></div>';
      container.innerHTML = html;
    }

    async function payBacklogFee(backlogId) {
      const res = await fetch('/api/student/backlogs/pay', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ backlog_id: backlogId })
      });
      const data = await res.json();
      alert(data.message);
      loadBacklogs();
    }

    // 7. RECOMMENDED SEQUENCE LOADER
    async function loadRecommended() {
      const stuId = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.student_id : 'STU001';
      const res = await fetch('/api/recommended?student_id=' + stuId);
      const data = await res.json();

      const list = document.getElementById('rec-list');
      list.innerHTML = '';
      if (data.length === 0) {
        list.innerHTML = '<div style="color:var(--success); text-align:center; padding:2rem;">🎉 All departmental courses completed or registered!</div>';
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
              <span style="font-size:0.8rem; color:var(--text-muted);">Semester ${rec.semester} • ${rec.credits} Credits</span>
            </div>
            <div style="font-size:0.85rem; color:var(--text-muted); margin-top:0.4rem;">${rec.description}</div>
            <div style="margin-top:0.6rem; font-size:0.8rem; color:var(--cyan);">
              ★ Downstream Unlock Impact: Clears prerequisite dependencies for <strong>${rec.unlocked_courses.length > 0 ? rec.unlocked_courses.join(', ') : 'Terminal Elective'}</strong>
            </div>
          </div>
        `;
      });
    }

    // 8. GRAPH VISUALIZATION & ALGORITHMS
    async function loadGraph() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.department : 'CSE';
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

      const courses = GRAPH_DATA.courses.slice(0, 20);
      const total = courses.length;
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const radius = 140;

      const positions = {};
      courses.forEach((c, idx) => {
        const angle = (idx / total) * 2 * Math.PI - Math.PI / 2;
        positions[c.code] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
          indegree: c.indegree
        };
      });

      Object.keys(GRAPH_DATA.adj_list).forEach(u => {
        const p1 = positions[u];
        if (!p1) return;
        const targets = GRAPH_DATA.adj_list[u];
        targets.forEach(v => {
          const p2 = positions[v];
          if (!p2) return;
          ctx.beginPath();
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
          ctx.lineWidth = 1.5;
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();
        });
      });

      Object.keys(positions).forEach(code => {
        const p = positions[code];
        ctx.beginPath();
        ctx.arc(p.x, p.y, 16, 0, 2 * Math.PI);
        ctx.fillStyle = p.indegree === 0 ? 'rgba(16, 185, 129, 0.85)' : 'rgba(30, 58, 138, 0.9)';
        ctx.fill();
        ctx.strokeStyle = p.indegree === 0 ? '#6ee7b7' : '#38bdf8';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = '#fff';
        ctx.font = 'bold 8.5px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(code, p.x, p.y);
      });
    }

    async function runGraphBFS() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.department : 'CSE';
      const res = await fetch('/api/graph/bfs?department=' + encodeURIComponent(dept));
      const data = await res.json();
      let out = "=== BFS / KAHN'S TOPOLOGICAL SORT EXECUTION TRACE ===\\n";
      out += `Total Ordered Courses: ${data.order.length}\\n`;
      out += `Formal Order Precedence Validated [pos(u) < pos(v)]: ${data.is_valid}\\n\\n`;
      out += data.logs.join('\\n');
      document.getElementById('graph-console').innerText = out;
    }

    async function runGraphDFS() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'student' ? CURRENT_USER.student.department : 'CSE';
      const res = await fetch('/api/graph/dfs?department=' + encodeURIComponent(dept));
      const data = await res.json();
      let out = "=== DFS 3-STATE TOPOLOGICAL SORT EXECUTION TRACE ===\\n";
      out += `Total Ordered Courses: ${data.order.length}\\n`;
      out += `Formal Precedence Validated: ${data.is_valid}\\n\\n`;
      out += data.logs.join('\\n');
      document.getElementById('graph-console').innerText = out;
    }

    async function runDemoCycle() {
      const res = await fetch('/api/graph/cycle-demo');
      const data = await res.json();
      let out = "=== ARTIFICIAL PREREQUISITE DEADLOCK DEMONSTRATION ===\\n";
      out += `Circular Path Injected: ${data.cycle_string}\\n\\n`;
      out += `[Engine 1 - BFS Kahn's Starvation Check]: Cycle Caught = ${data.bfs.has_cycle}\\n${data.bfs.explanation}\\n\\n`;
      out += `[Engine 2 - DFS Back-Edge Search]: Cycle Caught = ${data.dfs.has_cycle}\\n${data.dfs.explanation}\\n\\n`;
      out += "Real-World University Scenario: Prerequisite cycles create complete enrollment deadlocks because each course in the loop requires another incomplete course in the loop!";
      document.getElementById('graph-console').innerText = out;
    }

    // 9. STUDENT PROFILE LOADER
    async function loadProfile() {
      if (!CURRENT_USER || CURRENT_USER.role !== 'student') return;
      const stu = CURRENT_USER.student;
      document.getElementById('prof-name').innerText = stu.name;
      document.getElementById('prof-id').innerText = stu.student_id;
      document.getElementById('prof-dept').innerText = stu.department;
      document.getElementById('prof-year-sem').innerText = `Year ${stu.year}, Semester ${stu.semester}`;
      document.getElementById('prof-email').innerText = stu.email;
      document.getElementById('prof-phone').innerText = stu.phone || '+91 9876543210';
      document.getElementById('prof-advisor').innerText = 'Dr. K. Raman, Associate Professor (CSE)';

      const res = await fetch('/api/student/dashboard?student_id=' + stu.student_id);
      const data = await res.json();
      const earned = data.metrics.total_credits_earned;
      const pct = Math.min((earned / 160) * 100, 100).toFixed(1);
      document.getElementById('prof-credits-lbl').innerText = `${earned} / 160 Credits (${pct}%)`;
      document.getElementById('prof-credits-fill').style.width = `${pct}%`;
    }

    // 10. TEACHER / FACULTY APPROVALS LOADER
    async function loadApprovals() {
      const dept = CURRENT_USER && CURRENT_USER.role === 'teacher' ? CURRENT_USER.department : 'All';
      const res = await fetch('/api/teacher/pending?department=' + encodeURIComponent(dept));
      const pending = await res.json();

      document.getElementById('pending-count-badge').innerText = `${pending.length} Pending`;

      const tbody = document.getElementById('approvals-table-body');
      tbody.innerHTML = '';
      if (pending.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No pending enrollment requests. All student registrations reviewed.</td></tr>';
        return;
      }

      pending.forEach(p => {
        tbody.innerHTML += `
          <tr>
            <td><strong>${p.student_name}</strong><br><span style="font-size:0.75rem; color:var(--cyan);">${p.student_id}</span></td>
            <td>${p.student_dept}</td>
            <td>Year ${p.student_year} • Sem ${p.student_semester}</td>
            <td><strong>${p.course_code}</strong> – ${p.course_name}</td>
            <td>${p.credits} Cr</td>
            <td><span class="status-badge b-available">✓ All Prerequisites Passed</span></td>
            <td>
              <button class="btn btn-success" style="padding:0.25rem 0.6rem; font-size:0.75rem; margin-right:0.3rem;" onclick="processApproval(${p.enrollment_id}, 'Approve')">✅ Approve</button>
              <button class="btn btn-danger" style="padding:0.25rem 0.6rem; font-size:0.75rem;" onclick="processApproval(${p.enrollment_id}, 'Reject')">❌ Reject</button>
            </td>
          </tr>
        `;
      });
    }

    async function processApproval(enrId, action) {
      const res = await fetch('/api/teacher/approval', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ enrollment_id: enrId, action: action })
      });
      const data = await res.json();
      alert(data.message);
      loadApprovals();
    }

    // 11. ADMIN NOTIFICATIONS LOADER & PUBLISHER
    async function loadAdminNotifications() {
      const res = await fetch('/api/notifications');
      const notifs = await res.json();

      const container = document.getElementById('admin-notifs-table');
      if (notifs.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted);">No announcements posted yet.</div>';
        return;
      }

      let html = '<div class="table-container"><table><thead><tr><th>Title</th><th>Category</th><th>Priority</th><th>Posted Date</th><th>Posted By</th><th>Action</th></tr></thead><tbody>';
      notifs.forEach(n => {
        html += `
          <tr>
            <td><strong>${n.title}</strong></td>
            <td><span class="status-badge b-eligible">${n.category}</span></td>
            <td><span class="status-badge ${n.priority === 'Urgent' ? 'b-blocked' : 'b-enrolled'}">${n.priority}</span></td>
            <td>${n.posted_date}</td>
            <td>${n.posted_by}</td>
            <td><button class="btn btn-danger" style="padding:0.2rem 0.5rem; font-size:0.75rem;" onclick="adminDeleteNotification(${n.notification_id})">Delete</button></td>
          </tr>
        `;
      });
      html += '</tbody></table></div>';
      container.innerHTML = html;
    }

    async function adminPostNotification() {
      const title = document.getElementById('notif-input-title').value.trim();
      const cat = document.getElementById('notif-input-cat').value;
      const prio = document.getElementById('notif-input-priority').value;
      const msg = document.getElementById('notif-input-msg').value.trim();

      if (!title || !msg) {
        alert("Please enter Announcement Title and Message.");
        return;
      }

      const res = await fetch('/api/notifications', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ title: title, category: cat, priority: prio, message: msg, posted_by: 'Office of Academic Affairs' })
      });
      const data = await res.json();
      if (data.success) {
        alert("Announcement published successfully to all student dashboards!");
        document.getElementById('notif-input-title').value = '';
        document.getElementById('notif-input-msg').value = '';
        loadAdminNotifications();
      } else {
        alert("Error: " + data.message);
      }
    }

    async function adminDeleteNotification(id) {
      if (!confirm("Are you sure you want to delete this notification?")) return;
      const res = await fetch('/api/notifications?id=' + id, { method: 'DELETE' });
      loadAdminNotifications();
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
