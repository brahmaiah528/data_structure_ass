"""
Database management module for University Student Course Enrollment Portal.
Interacts with SQLite database 'university.db' with full foreign key constraints.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple

DB_NAME = "university.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Returns an SQLite connection with row_factory enabled and foreign keys enforced."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(db_path: str = DB_PATH) -> None:
    """Initializes the database schema with all required tables and constraints."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Courses Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                department TEXT NOT NULL,
                credits INTEGER NOT NULL DEFAULT 3,
                semester INTEGER NOT NULL DEFAULT 1,
                description TEXT
            )
        """)

        # 2. Prerequisites Table (Directed Graph Edge: prerequisite_course_id -> course_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prerequisites (
                prerequisite_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                prerequisite_course_id INTEGER NOT NULL,
                UNIQUE(course_id, prerequisite_course_id),
                FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
                FOREIGN KEY(prerequisite_course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            )
        """)

        # 3. Students Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                department TEXT NOT NULL,
                semester INTEGER NOT NULL DEFAULT 1,
                year INTEGER NOT NULL DEFAULT 1,
                phone TEXT
            )
        """)

        # 4. Completed Courses Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS completed_courses (
                completion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_id INTEGER NOT NULL,
                grade TEXT NOT NULL DEFAULT 'A',
                completion_status TEXT NOT NULL DEFAULT 'Completed',
                completed_on TEXT NOT NULL,
                UNIQUE(student_id, course_id),
                FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            )
        """)

        # 5. Enrollments Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_id INTEGER NOT NULL,
                enrollment_date TEXT NOT NULL,
                semester INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Enrolled',
                UNIQUE(student_id, course_id),
                FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            )
        """)
        conn.commit()

    # Check if database needs initial seeding
    if is_database_empty(db_path):
        from seed_data import seed_database
        seed_database(db_path)


def is_database_empty(db_path: str = DB_PATH) -> bool:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM courses")
        count = cursor.fetchone()[0]
        return count == 0


# =============================================================================
# COURSE QUERIES
# =============================================================================

def get_all_courses(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses ORDER BY semester, course_code")
        return [dict(row) for row in cursor.fetchall()]


def get_course_by_id(course_id: int, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_course_by_code(course_code: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM courses WHERE UPPER(course_code) = UPPER(?)", (course_code.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_courses_by_department(department: str, include_common: bool = True, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """
    Returns courses for a specific department.
    If include_common is True, includes university-wide common courses (Basic Sciences, Humanities, Math).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if include_common:
            common_depts = ("Common", "Basic Sciences", "Humanities", "Mathematics")
            placeholders = ",".join("?" for _ in common_depts)
            query = f"""
                SELECT * FROM courses 
                WHERE department = ? OR department IN ({placeholders})
                ORDER BY semester, course_code
            """
            cursor.execute(query, (department, *common_depts))
        else:
            cursor.execute("SELECT * FROM courses WHERE department = ? ORDER BY semester, course_code", (department,))
        return [dict(row) for row in cursor.fetchall()]


def add_course(course_code: str, course_name: str, department: str, credits: int, semester: int, description: str, db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO courses (course_code, course_name, department, credits, semester, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (course_code.strip().upper(), course_name.strip(), department.strip(), credits, semester, description.strip()))
        conn.commit()
        return cursor.lastrowid


def update_course(course_id: int, course_code: str, course_name: str, department: str, credits: int, semester: int, description: str, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE courses 
            SET course_code = ?, course_name = ?, department = ?, credits = ?, semester = ?, description = ?
            WHERE course_id = ?
        """, (course_code.strip().upper(), course_name.strip(), department.strip(), credits, semester, description.strip(), course_id))
        conn.commit()


def delete_course(course_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        conn.commit()


# =============================================================================
# PREREQUISITE QUERIES
# =============================================================================

def get_prerequisites_for_course(course_id: int, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns list of prerequisite courses required for the given course_id."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.* 
            FROM courses c
            JOIN prerequisites p ON c.course_id = p.prerequisite_course_id
            WHERE p.course_id = ?
            ORDER BY c.course_code
        """, (course_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_dependent_courses(course_id: int, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns courses that require the given course_id as a prerequisite."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.* 
            FROM courses c
            JOIN prerequisites p ON c.course_id = p.course_id
            WHERE p.prerequisite_course_id = ?
            ORDER BY c.course_code
        """, (course_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_all_prerequisites(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns all prerequisite relationships with course details."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.prerequisite_id,
                p.course_id,
                c.course_code,
                c.course_name,
                c.department AS course_dept,
                p.prerequisite_course_id,
                pr.course_code AS prereq_code,
                pr.course_name AS prereq_name,
                pr.department AS prereq_dept
            FROM prerequisites p
            JOIN courses c ON p.course_id = c.course_id
            JOIN courses pr ON p.prerequisite_course_id = pr.course_id
            ORDER BY pr.course_code, c.course_code
        """)
        return [dict(row) for row in cursor.fetchall()]


def add_prerequisite(course_id: int, prereq_course_id: int, db_path: str = DB_PATH) -> None:
    if course_id == prereq_course_id:
        raise ValueError("A course cannot be a prerequisite of itself.")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prerequisites (course_id, prerequisite_course_id)
            VALUES (?, ?)
        """, (course_id, prereq_course_id))
        conn.commit()


def remove_prerequisite(course_id: int, prereq_course_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM prerequisites 
            WHERE course_id = ? AND prerequisite_course_id = ?
        """, (course_id, prereq_course_id))
        conn.commit()


# =============================================================================
# STUDENT & ENROLLMENT QUERIES
# =============================================================================

def get_student_by_id(student_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id.strip().upper(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_students(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students ORDER BY student_id")
        return [dict(row) for row in cursor.fetchall()]


def add_student(student_id: str, name: str, email: str, password: str, department: str, semester: int, year: int, phone: str, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (student_id, name, email, password, department, semester, year, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id.strip().upper(), name.strip(), email.strip(), password, department.strip(), semester, year, phone.strip()))
        conn.commit()


def delete_student(student_id: str, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id.strip().upper(),))
        conn.commit()


def get_student_completed_courses(student_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns courses completed by a student with grade and credits."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cc.*, c.course_code, c.course_name, c.department, c.credits, c.semester
            FROM completed_courses cc
            JOIN courses c ON cc.course_id = c.course_id
            WHERE cc.student_id = ?
            ORDER BY c.semester, c.course_code
        """, (student_id.strip().upper(),))
        return [dict(row) for row in cursor.fetchall()]


def get_student_completed_course_ids(student_id: str, db_path: str = DB_PATH) -> set:
    """Returns set of course_ids completed by the student."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT course_id FROM completed_courses WHERE student_id = ?", (student_id.strip().upper(),))
        return {row["course_id"] for row in cursor.fetchall()}


def get_student_enrollments(student_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns active and past enrollments of the student."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, c.course_code, c.course_name, c.department, c.credits, c.semester as course_semester
            FROM enrollments e
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.student_id = ?
            ORDER BY e.enrollment_date DESC
        """, (student_id.strip().upper(),))
        return [dict(row) for row in cursor.fetchall()]


def get_student_enrolled_course_ids(student_id: str, db_path: str = DB_PATH) -> set:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT course_id FROM enrollments 
            WHERE student_id = ? AND status = 'Enrolled'
        """, (student_id.strip().upper(),))
        return {row["course_id"] for row in cursor.fetchall()}


def add_enrollment(student_id: str, course_id: int, semester: int, enrollment_date: str, status: str = "Enrolled", db_path: str = DB_PATH) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO enrollments (student_id, course_id, enrollment_date, semester, status)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id.strip().upper(), course_id, enrollment_date, semester, status))
        conn.commit()
        return cursor.lastrowid


def drop_enrollment(enrollment_id: int, db_path: str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM enrollments WHERE enrollment_id = ?", (enrollment_id,))
        conn.commit()


def get_all_enrollments(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, s.name as student_name, s.department as student_dept,
                   c.course_code, c.course_name, c.credits
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY e.enrollment_date DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_system_stats(db_path: str = DB_PATH) -> Dict[str, int]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM courses")
        total_courses = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM prerequisites")
        total_prereqs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM enrollments WHERE status = 'Enrolled'")
        active_enrollments = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM completed_courses")
        total_completions = cursor.fetchone()[0]
        return {
            "total_courses": total_courses,
            "total_prerequisites": total_prereqs,
            "total_students": total_students,
            "active_enrollments": active_enrollments,
            "total_completions": total_completions
        }
