"""
Administrator module for University Student Course Enrollment Portal.
Provides student management, course management, prerequisite configuration,
and comprehensive graph analysis tools for academic administrators.
"""

import streamlit as st
import pandas as pd
import database
from graph import CourseGraph


def render_admin_portal():
    """Renders the comprehensive administrative dashboard and toolset."""
    st.sidebar.markdown("### 🏛️ Admin Navigation")
    admin_menu = st.sidebar.radio(
        "Select Function:",
        [
            "📊 Admin Dashboard",
            "👥 Manage Students",
            "📚 Manage Courses",
            "🔗 Manage Prerequisites",
            "📝 View Enrollments",
            "📈 Prerequisite Graph Analysis",
        ],
        label_visibility="collapsed"
    )

    if admin_menu == "📊 Admin Dashboard":
        _render_admin_dashboard()
    elif admin_menu == "👥 Manage Students":
        _render_manage_students()
    elif admin_menu == "📚 Manage Courses":
        _render_manage_courses()
    elif admin_menu == "🔗 Manage Prerequisites":
        _render_manage_prerequisites()
    elif admin_menu == "📝 View Enrollments":
        _render_view_enrollments()
    elif admin_menu == "📈 Prerequisite Graph Analysis":
        _render_graph_analysis()


# =============================================================================
# 1. ADMIN DASHBOARD
# =============================================================================
def _render_admin_dashboard():
    st.title("🏛️ Academic Administration Dashboard")
    st.markdown("Global curriculum management, enrollment statistics, and graph diagnostics.")

    stats = database.get_system_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Courses", stats["total_courses"])
    c2.metric("Prerequisite Edges", stats["total_prerequisites"])
    c3.metric("Registered Students", stats["total_students"])
    c4.metric("Active Enrollments", stats["active_enrollments"])
    c5.metric("Completed Courses", stats["total_completions"])

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Departmental Course Distribution")
        courses = database.get_all_courses()
        df_courses = pd.DataFrame(courses)
        if not df_courses.empty:
            dept_counts = df_courses["department"].value_counts().reset_index()
            dept_counts.columns = ["Department", "Course Count"]
            st.dataframe(dept_counts, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Recent System Enrollments")
        enrollments = database.get_all_enrollments()
        if enrollments:
            df_enr = pd.DataFrame(enrollments[:10])
            display_cols = ["student_id", "student_name", "course_code", "course_name", "enrollment_date", "status"]
            st.dataframe(df_enr[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No enrollments recorded yet.")


# =============================================================================
# 2. MANAGE STUDENTS
# =============================================================================
def _render_manage_students():
    st.title("👥 Student Accounts Management")

    tab1, tab2 = st.tabs(["📋 View & Search Students", "➕ Register New Student"])

    with tab1:
        students = database.get_all_students()
        if students:
            df = pd.DataFrame(students)
            display_df = df[["student_id", "name", "email", "department", "semester", "year", "phone"]]
            search = st.text_input("🔍 Filter by Student ID, Name, or Department:")
            if search:
                mask = (
                    display_df["student_id"].str.contains(search, case=False, na=False) |
                    display_df["name"].str.contains(search, case=False, na=False) |
                    display_df["department"].str.contains(search, case=False, na=False)
                )
                display_df = display_df[mask]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("#### Delete Student Record")
            del_id = st.selectbox("Select Student to Delete:", [s["student_id"] for s in students], key="del_stu_select")
            if st.button("🗑️ Delete Selected Student", type="primary"):
                database.delete_student(del_id)
                st.success(f"Student account [{del_id}] deleted successfully.")
                st.rerun()
        else:
            st.warning("No student records found in database.")

    with tab2:
        st.markdown("#### Add New Student Account")
        with st.form("add_student_form"):
            c1, c2 = st.columns(2)
            new_id = c1.text_input("Student ID (e.g. STU016):").strip().upper()
            new_name = c2.text_input("Full Name:").strip()

            c3, c4 = st.columns(2)
            new_email = c3.text_input("Email Address:").strip()
            new_pwd = c4.text_input("Default Password:", value="student123", type="password")

            c5, c6, c7 = st.columns(3)
            new_dept = c5.selectbox("Department:", [
                "CSE", "Information Technology", "AI&DS", "Cyber Security", 
                "ECE", "EEE", "MECH", "Civil Engineering", "Computer Applications"
            ])
            new_sem = c6.number_input("Semester:", min_value=1, max_value=8, value=1)
            new_year = c7.number_input("Academic Year:", min_value=1, max_value=4, value=1)

            new_phone = st.text_input("Phone Number:", value="+91 9876543200")
            submit_student = st.form_submit_button("➕ Register Student Account")

            if submit_student:
                if not new_id or not new_name or not new_email:
                    st.error("Please fill in all mandatory fields.")
                else:
                    try:
                        database.add_student(new_id, new_name, new_email, new_pwd, new_dept, new_sem, new_year, new_phone)
                        st.success(f"Student account [{new_id} - {new_name}] created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create student: {str(e)}")


# =============================================================================
# 3. MANAGE COURSES
# =============================================================================
def _render_manage_courses():
    st.title("📚 Curriculum Course Management")

    tab1, tab2, tab3 = st.tabs(["📋 Course Catalogue", "➕ Add New Course", "✏️ Edit / Delete Course"])

    with tab1:
        courses = database.get_all_courses()
        if courses:
            df = pd.DataFrame(courses)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Total courses in catalogue: {len(courses)}")

    with tab2:
        st.markdown("#### Create New Academic Course Vertex")
        with st.form("add_course_form"):
            c1, c2 = st.columns(2)
            c_code = c1.text_input("Course Code (e.g. CS405):").strip().upper()
            c_name = c2.text_input("Course Name:").strip()

            c3, c4, c5 = st.columns(3)
            c_dept = c3.selectbox("Offering Department:", [
                "Common", "CSE", "Information Technology", "AI&DS", "Cyber Security",
                "ECE", "EEE", "MECH", "Civil Engineering", "Computer Applications"
            ])
            c_cred = c4.number_input("Credits:", min_value=1, max_value=6, value=3)
            c_sem = c5.number_input("Semester:", min_value=1, max_value=8, value=5)

            c_desc = st.text_area("Course Syllabus & Description:")
            submit_course = st.form_submit_button("➕ Create Course")

            if submit_course:
                if not c_code or not c_name:
                    st.error("Course Code and Course Name are mandatory.")
                else:
                    try:
                        database.add_course(c_code, c_name, c_dept, c_cred, c_sem, c_desc)
                        st.success(f"Course [{c_code} - {c_name}] created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating course: {str(e)}")

    with tab3:
        st.markdown("#### Modify or Remove Existing Course")
        courses = database.get_all_courses()
        course_options = {f"{c['course_code']} - {c['course_name']}": c for c in courses}
        sel_label = st.selectbox("Select Course to Modify:", list(course_options.keys()))

        if sel_label:
            target = course_options[sel_label]
            with st.form("edit_course_form"):
                e_code = st.text_input("Course Code:", value=target["course_code"])
                e_name = st.text_input("Course Name:", value=target["course_name"])
                c1, c2, c3 = st.columns(3)
                e_dept = c1.text_input("Department:", value=target["department"])
                e_cred = c2.number_input("Credits:", min_value=1, max_value=6, value=target["credits"])
                e_sem = c3.number_input("Semester:", min_value=1, max_value=8, value=target["semester"])
                e_desc = st.text_area("Description:", value=target["description"] or "")
                
                col_upd, col_del = st.columns([1, 1])
                save_btn = col_upd.form_submit_button("💾 Update Course")

                if save_btn:
                    try:
                        database.update_course(target["course_id"], e_code, e_name, e_dept, e_cred, e_sem, e_desc)
                        st.success(f"Course [{e_code}] updated successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {str(e)}")

            if st.button("🗑️ Delete Selected Course (Cascade Prereqs)", type="primary"):
                database.delete_course(target["course_id"])
                st.success(f"Course [{target['course_code']}] deleted.")
                st.rerun()


# =============================================================================
# 4. MANAGE PREREQUISITES
# =============================================================================
def _render_manage_prerequisites():
    st.title("🔗 Prerequisite Dependency Configuration")
    st.markdown("Manage directed graph edges: **Prerequisite Course (A) → Target Course (B)**.")

    tab1, tab2 = st.tabs(["📋 Current Prerequisite Relationships", "➕ Add Prerequisite Dependency"])

    with tab1:
        prereqs = database.get_all_prerequisites()
        if prereqs:
            df = pd.DataFrame(prereqs)
            display_df = df[["prereq_code", "prereq_name", "prereq_dept", "course_code", "course_name", "course_dept"]]
            display_df.columns = ["Prereq Code", "Prereq Course", "Prereq Dept", "Target Code", "Target Course", "Target Dept"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.caption(f"Total active prerequisite directed edges: {len(prereqs)}")

            st.markdown("#### Remove Prerequisite Edge")
            sel_prereq_edge = st.selectbox(
                "Select Prerequisite Edge to Remove:",
                [f"{p['prereq_code']} -> {p['course_code']} ({p['course_name']})" for p in prereqs]
            )
            if st.button("🗑️ Remove Selected Edge"):
                chosen = None
                for p in prereqs:
                    if f"{p['prereq_code']} -> {p['course_code']} ({p['course_name']})" == sel_prereq_edge:
                        chosen = p
                        break
                if chosen:
                    database.remove_prerequisite(chosen["course_id"], chosen["prerequisite_course_id"])
                    st.success("Prerequisite edge removed successfully.")
                    st.rerun()

    with tab2:
        st.markdown("#### Establish New Prerequisite Dependency")
        st.info("Rule: Course A must be successfully completed before enrolling in Course B (A → B).")
        courses = database.get_all_courses()
        course_map = {f"{c['course_code']} - {c['course_name']} ({c['department']})": c["course_id"] for c in courses}

        c1, c2 = st.columns(2)
        prereq_label = c1.selectbox("Select Prerequisite Course (A):", list(course_map.keys()), key="p_add_prereq")
        target_label = c2.selectbox("Select Dependent Course (B):", list(course_map.keys()), key="p_add_target")

        if st.button("➕ Establish Dependency Edge (A → B)", type="primary"):
            prereq_id = course_map[prereq_label]
            target_id = course_map[target_label]

            if prereq_id == target_id:
                st.error("Invalid Dependency: A course cannot be a prerequisite of itself (self-loop).")
            else:
                try:
                    database.add_prerequisite(target_id, prereq_id)
                    st.success("Prerequisite relationship established successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding prerequisite: {str(e)}")


# =============================================================================
# 5. VIEW ENROLLMENTS
# =============================================================================
def _render_view_enrollments():
    st.title("📝 System-Wide Student Enrollments")
    enrollments = database.get_all_enrollments()
    if enrollments:
        df = pd.DataFrame(enrollments)
        dept_filter = st.selectbox("Filter by Student Department:", ["All"] + list(df["student_dept"].unique()))
        if dept_filter != "All":
            df = df[df["student_dept"] == dept_filter]

        st.dataframe(df[["student_id", "student_name", "student_dept", "course_code", "course_name", "credits", "enrollment_date", "status"]], use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(df)} enrollment records.")
    else:
        st.info("No active student enrollments found.")


# =============================================================================
# 6. GRAPH ANALYSIS
# =============================================================================
def _render_graph_analysis():
    st.title("📈 Prerequisite Graph Theory & Algorithm Diagnostics")
    st.markdown("Comprehensive graph analysis using **BFS (Kahn's Algorithm)** and **DFS (3-State Coloring)**.")

    dept_filter = st.selectbox(
        "Select Curriculum Scope:",
        ["All Departments (Full University Graph)", "CSE", "AI&DS", "Information Technology", "Cyber Security", "ECE", "EEE", "MECH", "Civil Engineering", "Computer Applications"]
    )

    selected_dept = None if dept_filter.startswith("All") else dept_filter
    g = CourseGraph.load_from_database(database.DB_PATH, department=selected_dept)

    # Graph Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    total_v = len(g.adj_list)
    total_e = sum(len(neighbors) for neighbors in g.adj_list.values())
    indegrees = g.calculate_indegrees()
    entry_nodes = [c for c, deg in indegrees.items() if deg == 0]
    max_prereq = max(indegrees.values()) if indegrees else 0

    m1.metric("Course Vertices (|V|)", total_v)
    m2.metric("Prerequisite Edges (|E|)", total_e)
    m3.metric("Entry Courses (Deg 0)", len(entry_nodes))
    m4.metric("Max Prereqs on Single Course", max_prereq)

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. BFS / Kahn's Sort",
        "2. DFS 3-State Sort",
        "3. Dual Cycle Detection",
        "4. Cycle Injection Demo",
        "5. Adjacency List View"
    ])

    with tab1:
        st.subheader("1. BFS / Kahn's Topological Sort")
        if st.button("▶ Run BFS / Kahn's Algorithm"):
            success, order, logs, cycle_nodes = g.bfs_topological_sort()
            if success:
                st.success(f"✓ Valid Topological Order Generated ({len(order)} Courses Scheduled)!")
                is_valid, violations = g.validate_topological_order(order)
                if is_valid:
                    st.info("✓ Formal Precedence Validation PASSED: For all edges u -> v, position(u) < position(v).")
                
                # Render sequenced order
                order_df = pd.DataFrame([
                    {"Sequence": idx + 1, "Course Code": c, "Course Name": g.course_names.get(c, c), "Department": g.departments.get(c, "")}
                    for idx, c in enumerate(order)
                ])
                st.dataframe(order_df, use_container_width=True, hide_index=True)
            else:
                st.error("❌ Cycle Detected: Kahn's queue starved with pending unresolved in-degrees.")
                st.warning(f"Starved nodes: {cycle_nodes}")

            with st.expander("🔍 View Step-by-Step Kahn Queue Execution Log"):
                st.code("\n".join(logs), language="text")

    with tab2:
        st.subheader("2. DFS Topological Sort (3-State Coloring)")
        if st.button("▶ Run DFS 3-State Sort"):
            success, order, logs, cycle_path = g.dfs_topological_sort()
            if success:
                st.success(f"✓ DFS Topological Sort Successful ({len(order)} Courses Ordered)!")
                order_df = pd.DataFrame([
                    {"Sequence": idx + 1, "Course Code": c, "Course Name": g.course_names.get(c, c), "Department": g.departments.get(c, "")}
                    for idx, c in enumerate(order)
                ])
                st.dataframe(order_df, use_container_width=True, hide_index=True)
            else:
                st.error(f"❌ DFS Back-Edge Cycle Detected: {' -> '.join(cycle_path)}")

            with st.expander("🔍 View DFS Recursion State Traversal Trace"):
                st.code("\n".join(logs), language="text")

    with tab3:
        st.subheader("3. Dual-Engine Cycle Detection Audit")
        if st.button("🔍 Execute Dual-Engine Cycle Audit"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Engine 1: BFS / Kahn Starvation")
                has_c_bfs, c_nodes, expl_bfs = g.detect_cycle_bfs()
                if has_c_bfs:
                    st.error("Cycle Status: YES (Detected)")
                else:
                    st.success("Cycle Status: NO (Acyclic DAG)")
                st.write(expl_bfs)

            with c2:
                st.markdown("#### Engine 2: DFS Back-Edge Detection")
                has_c_dfs, c_path, expl_dfs = g.detect_cycle_dfs()
                if has_c_dfs:
                    st.error("Cycle Status: YES (Detected)")
                else:
                    st.success("Cycle Status: NO (Acyclic DAG)")
                st.write(expl_dfs)

    with tab4:
        st.subheader("4. Real-World Circular Dependency Demonstration")
        st.markdown("""
        **Institutional Scenario:**  
        Curriculum committee accidentally introduces circular prerequisite dependency:  
        `Programming Fundamentals (CS101) → OOP (CS102) → Data Structures (CS104) → Algorithms (CS201) → CS101`.  
        No student can ever enroll in the first course, deadlocking academic progression!
        """)
        if st.button("🚨 Test Cycle Detection on Injected Cycle Graph"):
            demo_g = CourseGraph.create_demo_cycle_graph()
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### BFS Kahn Test")
                c_bfs, nodes, expl_b = demo_g.detect_cycle_bfs()
                st.error(f"BFS Cycle Detected: {c_bfs}")
                st.write(expl_b)
            with col_b:
                st.markdown("#### DFS Back-Edge Test")
                c_dfs, path, expl_d = demo_g.detect_cycle_dfs()
                st.error(f"DFS Cycle Detected: {c_dfs}")
                st.write(expl_d)
                if path:
                    st.code(f"Cycle Path: {' -> '.join(path)}", language="text")

    with tab5:
        st.subheader("5. Graph Adjacency List Structure")
        st.markdown("Direct inspection of outgoing prerequisite edges ($u \\to v$).")
        adj_data = []
        for u in g.get_all_courses():
            neighbors = g.get_neighbors(u)
            adj_data.append({
                "Course Code": u,
                "Course Name": g.course_names.get(u, u),
                "Prerequisites Required For (Out-degree)": len(neighbors),
                "Dependent Courses": ", ".join(neighbors) if neighbors else "[Terminal Course - No Dependents]"
            })
        st.dataframe(pd.DataFrame(adj_data), use_container_width=True, hide_index=True)
