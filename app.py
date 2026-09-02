"""
University Student Course Enrollment Portal
Using Prerequisite Graph and Topological Sort

Streamlit Web Application Entry Point.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import database
import auth
from models import CourseStatus
from graph import CourseGraph
from prerequisites import check_prerequisites, get_course_status, get_recommended_courses
from enrollment import enroll_student_in_course, drop_course_enrollment
from admin import render_admin_portal

# =============================================================================
# PAGE CONFIGURATION & STYLING
# =============================================================================
st.set_page_config(
    page_title="University Student Course Enrollment Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern university portal aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #64748b;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-available { background-color: #dcfce7; color: #15803d; }
    .status-eligible { background-color: #dbeafe; color: #1d4ed8; }
    .status-blocked { background-color: #fee2e2; color: #b91c1c; }
    .status-completed { background-color: #f3e8ff; color: #7e22ce; }
    .status-enrolled { background-color: #ffedd5; color: #c2410c; }
    .prereq-check-box {
        background: #f1f5f9;
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database on Application Startup
database.init_database()
auth.init_session_state()


# =============================================================================
# MAIN CONTROLLER ROUTER
# =============================================================================
def main():
    if not auth.is_authenticated():
        render_login_page()
    else:
        if auth.is_admin():
            render_admin_sidebar()
            render_admin_portal()
        else:
            render_student_sidebar()
            render_student_portal()


# =============================================================================
# LOGIN PAGE
# =============================================================================
def render_login_page():
    st.markdown("<div class='main-header'>🎓 University Student Course Enrollment Portal</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Powered by Directed Graphs, Prerequisites, Kahn's BFS, and DFS 3-State Topological Sort</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("### 🔐 Portal Login")
        st.markdown("Sign in with your **Student ID** or **Administrator Account**.")

        with st.form("login_form"):
            user_id = st.text_input("Student ID / Username:", placeholder="e.g. STU001 or admin").strip()
            password = st.text_input("Password:", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("🔑 Login to Portal", use_container_width=True)

            if submitted:
                if user_id.lower() == "admin":
                    ok, err = auth.authenticate_admin(user_id, password)
                    if ok:
                        st.success("Admin login successful!")
                        st.rerun()
                    else:
                        st.error(err)
                else:
                    ok, err = auth.authenticate_student(user_id, password)
                    if ok:
                        st.success("Student login successful!")
                        st.rerun()
                    else:
                        st.error(err)

        st.markdown("---")
        st.markdown("#### ⚡ Quick Demo Logins")
        demo_cols = st.columns(3)
        if demo_cols[0].button("👤 Rahul Kumar\n(CSE - STU001)", use_container_width=True):
            auth.authenticate_student("STU001", "student123")
            st.rerun()
        if demo_cols[1].button("👤 Priya Sharma\n(AI&DS - STU002)", use_container_width=True):
            auth.authenticate_student("STU002", "student123")
            st.rerun()
        if demo_cols[2].button("🛡️ Administrator\n(admin)", use_container_width=True):
            auth.authenticate_admin("admin", "admin123")
            st.rerun()

    with col2:
        st.markdown("### ℹ️ System Features & Data Structures")
        st.info("""
        **Data Structures & Algorithms Implemented:**
        * **Directed Graph Representation:** Adjacency List $O(V + E)$
        * **BFS / Kahn's Algorithm:** Queue-based topological sort with in-degree decrements
        * **DFS Topological Sort:** 3-State Vertex Coloring (`UNVISITED`, `VISITING`, `VISITED`)
        * **Dual Cycle Detection:** In-degree queue starvation & DFS back-edge recognition
        * **Precedence Validation:** Automated proof checking $\\text{pos}(u) < \\text{pos}(v)$
        * **Curriculum Scale:** 112+ Courses across 9 Departments stored in SQLite
        """)

        st.markdown("""
        **Demo Accounts Credentials:**
        * `STU001` (Rahul Kumar, CSE Sem 4) - Password: `student123`
        * `STU002` (Priya Sharma, AI&DS Sem 6) - Password: `student123`
        * `STU003` (Arun Kumar, ECE Sem 5) - Password: `student123`
        * `admin` (Administrator) - Password: `admin123`
        """)


# =============================================================================
# STUDENT SIDEBAR
# =============================================================================
def render_student_sidebar():
    stu = auth.get_current_student()
    st.sidebar.markdown(f"### 🎓 Student Portal")
    st.sidebar.markdown(f"**{stu['name']}**  \n`{stu['student_id']}` | {stu['department']}")
    st.sidebar.caption(f"Semester {stu['semester']} | Year {stu['year']}")
    st.sidebar.markdown("---")

    menu_options = [
        "📊 Dashboard",
        "📚 Courses Catalogue",
        "✍️ Course Enrollment",
        "🎓 Completed Courses",
        "💡 Recommended Sequences",
        "📈 Prerequisite Graph",
        "👤 My Profile"
    ]

    selected_page = st.sidebar.radio("Navigation Menu", menu_options, label_visibility="collapsed")
    st.session_state["student_page"] = selected_page

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        auth.logout()
        st.rerun()


# =============================================================================
# ADMIN SIDEBAR
# =============================================================================
def render_admin_sidebar():
    st.sidebar.markdown("### 🛡️ Portal Administrator")
    st.sidebar.markdown("**Administrator Mode**  \nGlobal System Control")
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Admin Logout", use_container_width=True):
        auth.logout()
        st.rerun()


# =============================================================================
# STUDENT PORTAL ROUTER
# =============================================================================
def render_student_portal():
    page = st.session_state.get("student_page", "📊 Dashboard")

    if page == "📊 Dashboard":
        _page_student_dashboard()
    elif page == "📚 Courses Catalogue":
        _page_student_courses()
    elif page == "✍️ Course Enrollment":
        _page_student_enrollment()
    elif page == "🎓 Completed Courses":
        _page_student_completed()
    elif page == "💡 Recommended Sequences":
        _page_student_recommended()
    elif page == "📈 Prerequisite Graph":
        _page_student_graph()
    elif page == "👤 My Profile":
        _page_student_profile()


# =============================================================================
# 1. STUDENT DASHBOARD
# =============================================================================
def _page_student_dashboard():
    stu = auth.get_current_student()
    stu_id = stu["student_id"]
    dept = stu["department"]

    st.markdown(f"<div class='main-header'>Welcome, {stu['name']}! 👋</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>{dept} | Semester {stu['semester']} | Academic Year {stu['year']}</div>", unsafe_allow_html=True)

    # Compute live metrics
    dept_courses = database.get_courses_by_department(dept, include_common=True)
    completed_courses = database.get_student_completed_courses(stu_id)
    active_enrollments = database.get_student_enrollments(stu_id)

    completed_ids = {c["course_id"] for c in completed_courses}
    enrolled_ids = {e["course_id"] for e in active_enrollments}

    available_count = 0
    blocked_count = 0

    for c in dept_courses:
        if c["course_id"] not in completed_ids and c["course_id"] not in enrolled_ids:
            status = get_course_status(stu_id, c["course_id"])
            if status in (CourseStatus.AVAILABLE, CourseStatus.ELIGIBLE):
                available_count += 1
            elif status == CourseStatus.BLOCKED:
                blocked_count += 1

    # Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Curriculum Courses", len(dept_courses))
    c2.metric("Completed Courses", len(completed_courses))
    c3.metric("Current Enrollments", len(active_enrollments))
    c4.metric("Available / Eligible", available_count)
    c5.metric("Blocked Prerequisites", blocked_count)

    st.markdown("---")
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("📌 Current Semester Enrollments")
        if active_enrollments:
            df_enr = pd.DataFrame(active_enrollments)
            st.dataframe(df_enr[["course_code", "course_name", "credits", "enrollment_date", "status"]], use_container_width=True, hide_index=True)
        else:
            st.info("No active course enrollments yet for this semester. Visit the Course Enrollment page to register.")

    with col_right:
        st.subheader("💡 Recommended Next Courses")
        recommended = get_recommended_courses(stu_id)
        if recommended:
            df_rec = pd.DataFrame(recommended[:5])
            st.dataframe(df_rec[["course_code", "course_name", "credits", "semester", "status"]], use_container_width=True, hide_index=True)
        else:
            st.success("All departmental courses for this stage are completed!")


# =============================================================================
# 2. COURSES MODULE (DEPARTMENT FILTERED)
# =============================================================================
def _page_student_courses():
    stu = auth.get_current_student()
    stu_id = stu["student_id"]
    default_dept = stu["department"]

    st.title("📚 Department Course Catalogue")
    st.markdown(f"Showing curriculum courses for **{default_dept}** and approved university common subjects.")

    # Department and search filters
    f1, f2, f3 = st.columns([1, 1, 2])
    dept_choice = f1.selectbox("Filter Department:", [default_dept, "All Departments", "Common", "CSE", "AI&DS", "Information Technology", "Cyber Security", "ECE", "EEE", "MECH", "Civil Engineering", "Computer Applications"])
    sem_choice = f2.selectbox("Filter Semester:", ["All Semesters"] + list(range(1, 9)))
    search_query = f3.text_input("🔍 Search Course Code or Name:", placeholder="e.g. CS104 or Algorithms")

    # Fetch courses based on filter
    if dept_choice == "All Departments":
        courses = database.get_all_courses()
    elif dept_choice == default_dept:
        courses = database.get_courses_by_department(default_dept, include_common=True)
    else:
        courses = database.get_courses_by_department(dept_choice, include_common=False)

    # Apply semester filter
    if sem_choice != "All Semesters":
        courses = [c for c in courses if c["semester"] == sem_choice]

    # Apply search filter
    if search_query:
        sq = search_query.strip().lower()
        courses = [c for c in courses if sq in c["course_code"].lower() or sq in c["course_name"].lower()]

    # Format table data
    table_data = []
    for c in courses:
        c_id = c["course_id"]
        status = get_course_status(stu_id, c_id)
        prereqs = database.get_prerequisites_for_course(c_id)
        prereq_str = ", ".join(p["course_code"] for p in prereqs) if prereqs else "None"

        table_data.append({
            "Course ID": c_id,
            "Code": c["course_code"],
            "Course Name": c["course_name"],
            "Department": c["department"],
            "Credits": c["credits"],
            "Semester": c["semester"],
            "Prerequisites": prereq_str,
            "Status": status.value
        })

    if table_data:
        df_display = pd.DataFrame(table_data)
        st.dataframe(df_display[["Code", "Course Name", "Department", "Credits", "Semester", "Prerequisites", "Status"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔍 Inspect Course Prerequisite Details")
        sel_code = st.selectbox("Select a Course to View Detailed Prerequisite Status:", [row["Code"] + " - " + row["Course Name"] for row in table_data])
        if sel_code:
            code_only = sel_code.split(" - ")[0]
            target_course = database.get_course_by_code(code_only)
            if target_course:
                c_check = check_prerequisites(stu_id, target_course["course_id"])
                c_status = get_course_status(stu_id, target_course["course_id"])

                c_box = st.container()
                c_box.markdown(f"### {target_course['course_code']} – {target_course['course_name']}")
                c_box.write(f"**Department:** {target_course['department']} | **Credits:** {target_course['credits']} | **Semester:** {target_course['semester']}")
                c_box.write(f"**Description:** {target_course['description']}")
                c_box.write(f"**Current Status:** `{c_status.value}`")

                st.markdown("#### Prerequisite Requirement Breakdown:")
                if not c_check["required_prereqs"]:
                    st.success("✓ No prerequisites required. Course is open to all students.")
                else:
                    for p in c_check["required_prereqs"]:
                        is_done = p["course_id"] in database.get_student_completed_course_ids(stu_id)
                        if is_done:
                            st.write(f"✓ **{p['course_code']} - {p['course_name']}** (Completed)")
                        else:
                            st.write(f"❌ **{p['course_code']} - {p['course_name']}** (Missing / Incomplete)")
    else:
        st.warning("No courses match the specified filters.")


# =============================================================================
# 3. ENROLLMENT MODULE (STRICT PREREQUISITE ENFORCEMENT)
# =============================================================================
def _page_student_enrollment():
    stu = auth.get_current_student()
    stu_id = stu["student_id"]
    dept = stu["department"]

    st.title("✍️ Academic Course Enrollment")
    st.markdown("""
    **Core University Enrollment Rule:**  
    A student **CANNOT** enroll in any course unless **ALL** required prerequisites have been successfully completed.
    """)

    # Get department courses
    courses = database.get_courses_by_department(dept, include_common=True)
    completed_ids = database.get_student_completed_course_ids(stu_id)
    enrolled_ids = database.get_student_enrolled_course_ids(stu_id)

    # Filter available options (exclude already completed or already enrolled)
    candidate_courses = [c for c in courses if c["course_id"] not in completed_ids and c["course_id"] not in enrolled_ids]

    if not candidate_courses:
        st.success("🎉 You have enrolled in or completed all currently available courses for your department!")
        return

    course_options = {f"{c['course_code']} - {c['course_name']} ({c['department']}, Sem {c['semester']})": c for c in candidate_courses}

    st.markdown("### Step 1: Select Course for Enrollment")
    selected_label = st.selectbox("Choose a course:", list(course_options.keys()))
    selected_course = course_options[selected_label]
    course_id = selected_course["course_id"]

    # Step 2: Automatic Prerequisite Validation
    st.markdown("### Step 2: Automated Prerequisite Verification")
    check_result = check_prerequisites(stu_id, course_id)
    status = get_course_status(stu_id, course_id)

    with st.container():
        st.markdown(f"**Selected Course:** `{selected_course['course_code']}` – **{selected_course['course_name']}**")
        st.markdown(f"**Credits:** {selected_course['credits']} | **Department:** {selected_course['department']} | **Semester:** {selected_course['semester']}")

        if not check_result["required_prereqs"]:
            st.success("✓ **Type 1 Course (No Prerequisites):** This course is directly available for enrollment.")
        else:
            st.markdown("#### Required Prerequisites Checklist:")
            for p in check_result["required_prereqs"]:
                is_done = p["course_id"] in completed_ids
                if is_done:
                    st.markdown(f"✅ **{p['course_code']} – {p['course_name']}** (Completed)")
                else:
                    st.markdown(f"❌ **{p['course_code']} – {p['course_name']}** (Incomplete / Not Completed)")

        st.markdown("---")

        # Step 3: Enforcement Action
        if check_result["eligible"]:
            st.success("🎉 **ALL PREREQUISITES SATISFIED!** You are eligible to enroll in this course.")
            if st.button("🚀 ENROLL NOW IN THIS COURSE", type="primary", use_container_width=True):
                success, msg = enroll_student_in_course(stu_id, course_id, semester=stu["semester"])
                if success:
                    st.success(msg)
                    st.balloons()
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.error("❌ **ENROLLMENT BLOCKED!**")
            missing_names = ", ".join(f"{m['course_code']} ({m['course_name']})" for m in check_result["missing_prereqs"])
            st.warning(f"You cannot enroll in this course because the following required prerequisite(s) are incomplete: **{missing_names}**.")
            st.button("🚫 ENROLLMENT BLOCKED (Complete Prerequisites First)", disabled=True, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 My Active Course Enrollments")
    enrollments = database.get_student_enrollments(stu_id)
    if enrollments:
        for enr in enrollments:
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1.5])
            c1.markdown(f"**{enr['course_code']}**")
            c2.markdown(f"{enr['course_name']} ({enr['credits']} Cr)")
            c3.caption(f"Enrolled on: {enr['enrollment_date']}")
            if c4.button("Drop Course", key=f"drop_{enr['enrollment_id']}"):
                ok, drop_msg = drop_course_enrollment(enr["enrollment_id"], stu_id)
                if ok:
                    st.success(drop_msg)
                    st.rerun()
                else:
                    st.error(drop_msg)
    else:
        st.info("No active enrollments for this student.")


# =============================================================================
# 4. COMPLETED COURSES MODULE
# =============================================================================
def _page_student_completed():
    stu = auth.get_current_student()
    stu_id = stu["student_id"]

    st.title("🎓 Completed Academic Coursework")
    st.markdown("Official record of successfully cleared courses and earned grade points.")

    completed = database.get_student_completed_courses(stu_id)
    if completed:
        df = pd.DataFrame(completed)
        total_credits = df["credits"].sum()

        m1, m2 = st.columns(2)
        m1.metric("Courses Cleared", len(completed))
        m2.metric("Total Credits Earned", total_credits)

        st.dataframe(df[["course_code", "course_name", "department", "credits", "semester", "grade", "completed_on"]], use_container_width=True, hide_index=True)
    else:
        st.info("No completed coursework recorded yet for this student.")


# =============================================================================
# 5. RECOMMENDED COURSES MODULE (TOPOLOGICAL SEQUENCING)
# =============================================================================
def _page_student_recommended():
    stu = auth.get_current_student()
    stu_id = stu["student_id"]

    st.title("💡 Recommended Course Sequence")
    st.markdown("Topologically sequenced course suggestions derived from your completed prerequisites and department graduation roadmaps.")

    recommended = get_recommended_courses(stu_id)
    if recommended:
        for idx, rec in enumerate(recommended, 1):
            with st.expander(f"#{idx} | {rec['course_code']} – {rec['course_name']} (Semester {rec['semester']}) | Status: {rec['status']}", expanded=(idx <= 3)):
                st.write(f"**Department:** {rec['department']} | **Credits:** {rec['credits']}")
                st.write(f"**Course Description:** {rec['description']}")
                st.write(f"**Downstream Courses Unlocked Upon Completion:** {rec['downstream_unlocks']}")
                if rec["unlocked_courses"]:
                    st.info(f"Clearing this course opens up: {', '.join(rec['unlocked_courses'])}")
                
                if st.button(f"Enroll in {rec['course_code']}", key=f"rec_enr_{rec['course_id']}"):
                    ok, msg = enroll_student_in_course(stu_id, rec["course_id"], semester=stu["semester"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    else:
        st.success("All courses in your curriculum are completed or currently enrolled!")


# =============================================================================
# 6. PREREQUISITE GRAPH MODULE
# =============================================================================
def _page_student_graph():
    stu = auth.get_current_student()
    dept = stu["department"]

    st.title("📈 Prerequisite Graph Theory & Algorithm Engine")
    st.markdown(f"Graph-based prerequisite resolution for **{dept}** curriculum using Kahn's BFS and DFS 3-state sort.")

    g = CourseGraph.load_from_database(database.DB_PATH, department=dept)

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. BFS / Kahn's Topological Sort",
        "2. DFS 3-State Sort",
        "3. Dual Cycle Detection",
        "4. Complexity Analysis & Comparison"
    ])

    with tab1:
        st.subheader("Kahn's Algorithm (BFS) Queue Execution")
        if st.button("▶ Run BFS / Kahn's Sort on Department Graph"):
            success, order, logs, _ = g.bfs_topological_sort()
            if success:
                st.success(f"✓ Valid Topological Order ({len(order)} Courses Scheduled)!")
                df = pd.DataFrame([{"Step": i + 1, "Code": c, "Name": g.course_names.get(c, c)} for i, c in enumerate(order)])
                st.dataframe(df, use_container_width=True, hide_index=True)
            with st.expander("View Kahn Queue Diagnostic Step Trace"):
                st.code("\n".join(logs), language="text")

    with tab2:
        st.subheader("DFS Topological Sort (3-State Coloring)")
        if st.button("▶ Run DFS 3-State Sort on Department Graph"):
            success, order, logs, _ = g.dfs_topological_sort()
            if success:
                st.success(f"✓ DFS Topological Sort Successful ({len(order)} Courses)!")
                df = pd.DataFrame([{"Sequence": i + 1, "Code": c, "Name": g.course_names.get(c, c)} for i, c in enumerate(order)])
                st.dataframe(df, use_container_width=True, hide_index=True)
            with st.expander("View DFS Recursion Stack Trace"):
                st.code("\n".join(logs), language="text")

    with tab3:
        st.subheader("Cycle Detection Audit & Real-World Demonstration")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Department Graph Audit")
            if st.button("Run Audit on Department"):
                has_c, _, expl = g.detect_cycle_bfs()
                if has_c:
                    st.error("Cycle detected in department curriculum!")
                else:
                    st.success("✓ Department curriculum is a valid Directed Acyclic Graph (DAG).")
                st.write(expl)

        with c2:
            st.markdown("#### Artificial Cycle Demonstration")
            st.markdown("Test circular loop: `CS101 -> CS102 -> CS104 -> CS201 -> CS101`")
            if st.button("🚨 Test Circular Deadlock Injection"):
                demo = CourseGraph.create_demo_cycle_graph()
                c_bfs, _, _ = demo.detect_cycle_bfs()
                c_dfs, path, _ = demo.detect_cycle_dfs()
                st.error(f"BFS Cycle Detected: {c_bfs}")
                st.error(f"DFS Cycle Detected: {c_dfs}")
                if path:
                    st.code(f"Cycle Loop: {' -> '.join(path)}", language="text")
                st.warning("Real-World Impact: Prerequisite deadlock prevents student registration and degree completion.")

    with tab4:
        st.subheader("Algorithmic Complexity & BFS vs DFS Comparison")
        st.markdown("""
        ### Asymptotic Complexity:
        * **Graph Construction:** $O(V + E)$ time, $\\Theta(V + E)$ space
        * **BFS / Kahn's Algorithm:** $O(V + E)$ time, $O(V)$ auxiliary space
        * **DFS 3-State Sort:** $O(V + E)$ time, $O(V)$ recursion stack space
        * **Cycle Detection:** $O(V + E)$ optimal time
        """)

        comp_data = [
            {"Feature": "Core Metric", "BFS / Kahn's Algorithm": "In-Degree calculation", "DFS 3-State Algorithm": "Recursion call stack"},
            {"Feature": "Data Structure", "BFS / Kahn's Algorithm": "FIFO Queue", "DFS 3-State Algorithm": "LIFO Stack / Recursion"},
            {"Feature": "Cycle Detection", "BFS / Kahn's Algorithm": "Queue starvation (processed < |V|)", "DFS 3-State Algorithm": "Back-edge to VISITING ancestor"},
            {"Feature": "Time Complexity", "BFS / Kahn's Algorithm": "O(V + E)", "DFS 3-State Algorithm": "O(V + E)"},
            {"Feature": "Space Complexity", "BFS / Kahn's Algorithm": "O(V)", "DFS 3-State Algorithm": "O(V)"},
            {"Feature": "Prerequisite Intuition", "BFS / Kahn's Algorithm": "Very High (in-degree = blocking prereqs)", "DFS 3-State Algorithm": "Medium (depth dependency resolution)"},
            {"Feature": "Academic Enrollment Fit", "BFS / Kahn's Algorithm": "Ideal (shows immediately available)", "DFS 3-State Algorithm": "Good (validates terminal specializations)"}
        ]
        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)


# =============================================================================
# 7. PROFILE MODULE
# =============================================================================
def _page_student_profile():
    stu = auth.get_current_student()
    st.title("👤 Student Academic Profile")

    c1, c2 = st.columns([1, 2])
    with c1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=140)
    with c2:
        st.markdown(f"### {stu['name']}")
        st.write(f"**Student ID:** `{stu['student_id']}`")
        st.write(f"**Email:** {stu['email']}")
        st.write(f"**Department:** {stu['department']}")
        st.write(f"**Current Semester:** Semester {stu['semester']}")
        st.write(f"**Academic Year:** Year {stu['year']}")
        st.write(f"**Contact:** {stu['phone']}")

    st.markdown("---")
    completed = database.get_student_completed_courses(stu['student_id'])
    earned_cr = sum(c['credits'] for c in completed)
    st.write(f"**Total Earned Credits:** {earned_cr} / 160 Credits Required for Degree Completion")
    st.progress(min(earned_cr / 160, 1.0))


if __name__ == "__main__":
    main()
