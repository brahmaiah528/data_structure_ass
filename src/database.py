"""
Database module for the Department of Computer Science and Engineering Assignment.
Uses Python's standard library sqlite3 (Zero external dependencies).

Database Schema:
1. assignment_metadata: Assignment specifications, Course Outcome (CO5), Bloom's Level (L4), SDG mappings.
2. rubrics: Detailed assessment rubrics and marking criteria (Total 100 marks).
3. courses: Academic courses with codes, titles, credits, and departments.
4. prerequisites: Directed prerequisite dependencies (u -> v).
5. execution_logs: Audit trail of algorithm executions, cycle detections, and validations.
"""

import sqlite3
import os
from typing import Dict, List, Tuple, Optional
from src.course import Course
from src.course_graph import CourseGraph

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "curriculum.db")


class DatabaseManager:
    """Manages SQLite persistent storage for curriculum and assignment data."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
        self.seed_default_data()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initializes database schema tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Assignment Metadata Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignment_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # 2. Assessment Rubrics Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rubrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    criteria TEXT NOT NULL,
                    co_mapping TEXT NOT NULL,
                    max_marks INTEGER NOT NULL,
                    excellent TEXT NOT NULL,
                    good TEXT NOT NULL,
                    satisfactory TEXT NOT NULL,
                    needs_improvement TEXT NOT NULL
                )
            """)

            # 3. Courses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    code TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    credits INTEGER NOT NULL DEFAULT 3,
                    department TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. Prerequisites Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prerequisites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prereq_code TEXT NOT NULL,
                    target_code TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(prereq_code, target_code),
                    FOREIGN KEY(prereq_code) REFERENCES courses(code) ON DELETE CASCADE,
                    FOREIGN KEY(target_code) REFERENCES courses(code) ON DELETE CASCADE
                )
            """)

            # 5. Algorithm Execution Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    algorithm TEXT NOT NULL,
                    has_cycle INTEGER NOT NULL,
                    order_result TEXT,
                    cycle_path TEXT,
                    validation_status TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def seed_default_data(self) -> None:
        """Populates the database with official assignment metadata, rubrics, and initial curriculum."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if metadata already seeded
            cursor.execute("SELECT COUNT(*) FROM assignment_metadata")
            if cursor.fetchone()[0] == 0:
                metadata = [
                    ("institution", "Department of Computer Science and Engineering"),
                    ("course_code_name", "CSA03 – Data Structures – Slot D"),
                    ("assignment_title", "Design a graph representation of this prerequisite system and use Topological Sort to generate a valid course-taking order. Your design must also detect whether the prerequisite system contains a cycle. Analyze what the existence of a cycle means in the real-world university scenario and compare a BFS-based and DFS-based approach for solving the problem."),
                    ("course_outcome", "CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications."),
                    ("blooms_taxonomy", "L4 – Analyze"),
                    ("sdg_mapping", "SDG 4 – Quality Education; SDG 9 – Industry, Innovation and Infrastructure (with SDG 11 Sustainable Cities & Communities)"),
                    ("problem_statement", "A university offers hundreds of courses across different departments and academic programmes, where several courses require students to successfully complete one or more prerequisite courses before enrollment. The prerequisite relationships among these courses can be represented using a directed graph, in which each vertex represents a course and each directed edge represents a prerequisite dependency. Design a suitable graph representation, implement Kahn's BFS and 3-state DFS Topological Sort, incorporate dual-engine cycle detection, analyze the real-world impact of cycles, and rigorously compare the algorithms.")
                ]
                cursor.executemany("INSERT INTO assignment_metadata (key, value) VALUES (?, ?)", metadata)

            # Check if rubrics seeded
            cursor.execute("SELECT COUNT(*) FROM rubrics")
            if cursor.fetchone()[0] == 0:
                rubrics_data = [
                    (
                        "Graph Representation & Prerequisite Modeling",
                        "CO5",
                        15,
                        "Accurate graph and prerequisites with adjacency list implementation",
                        "Minor graph errors",
                        "Several missing relationships",
                        "Major graph errors"
                    ),
                    (
                        "Topological Sort & Valid Course-Taking Order",
                        "CO5",
                        20,
                        "Correct sort and valid order verified by position precedence",
                        "Minor sorting errors",
                        "Partially correct course order",
                        "Invalid course order"
                    ),
                    (
                        "Cycle Detection & Real-World Interpretation",
                        "CO5",
                        15,
                        "Accurate cycle detection (both BFS & DFS) and thorough real-world impact analysis",
                        "Correct cycle identification",
                        "Limited cycle explanation",
                        "Unable to detect cycles"
                    ),
                    (
                        "BFS vs DFS Comparison & Algorithm Analysis",
                        "CO5",
                        15,
                        "Thorough BFS-DFS comparison across logic, data structures, complexity, and scalability",
                        "Good comparison with minor omissions",
                        "Basic comparison, lacks details",
                        "Incomplete or inaccurate comparison"
                    ),
                    (
                        "Solution Justification & University Application",
                        "CO5",
                        25,
                        "Efficient solution with rigorous institutional justification as primary/secondary engines",
                        "Suitable solution and justification",
                        "Limited justification and analysis",
                        "Poor or impractical solution"
                    ),
                    (
                        "Reflection: Design Decisions, SDG Relevance & Learning Outcomes",
                        "CO5",
                        10,
                        "Thoughtful justification of design choices, clear connection to SDG 4, 9 and 11 relevance, and honest, specific account of challenges and learnings.",
                        "General justification of design choices; sustainability connection mentioned but lacks depth.",
                        "Reflection present but generic; limited justification of design or vague account of learning outcomes.",
                        "No genuine reflection submitted, or content is generic with no real design/SDG/learning connection."
                    )
                ]
                cursor.executemany("""
                    INSERT INTO rubrics (criteria, co_mapping, max_marks, excellent, good, satisfactory, needs_improvement)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, rubrics_data)

            # Check if courses seeded
            cursor.execute("SELECT COUNT(*) FROM courses")
            if cursor.fetchone()[0] == 0:
                courses = [
                    ("CS101", "Programming Fundamentals", 4, "Computer Science & Engineering"),
                    ("CS102", "Object Oriented Programming", 4, "Computer Science & Engineering"),
                    ("CS103", "Data Structures", 4, "Computer Science & Engineering"),
                    ("CS104", "Discrete Mathematics", 3, "Computer Science & Engineering"),
                    ("CS105", "Database Management Systems", 3, "Computer Science & Engineering"),
                    ("CS106", "Computer Organization", 3, "Computer Science & Engineering"),
                    ("CS201", "Algorithms", 4, "Computer Science & Engineering"),
                    ("CS202", "Operating Systems", 4, "Computer Science & Engineering"),
                    ("CS203", "Computer Networks", 3, "Computer Science & Engineering"),
                    ("CS204", "Software Engineering", 3, "Computer Science & Engineering"),
                    ("CS301", "Artificial Intelligence", 4, "Computer Science & Engineering"),
                    ("CS302", "Machine Learning", 4, "Computer Science & Engineering")
                ]
                cursor.executemany("INSERT INTO courses (code, title, credits, department) VALUES (?, ?, ?, ?)", courses)

                prereqs = [
                    ("CS101", "CS102"),
                    ("CS101", "CS103"),
                    ("CS104", "CS103"),
                    ("CS103", "CS201"),
                    ("CS106", "CS202"),
                    ("CS103", "CS202"),
                    ("CS103", "CS203"),
                    ("CS102", "CS204"),
                    ("CS201", "CS301"),
                    ("CS201", "CS302"),
                    ("CS301", "CS302"),
                    ("CS103", "CS105")
                ]
                cursor.executemany("INSERT INTO prerequisites (prereq_code, target_code) VALUES (?, ?)", prereqs)

            conn.commit()

    def load_graph_from_db(self) -> CourseGraph:
        """Constructs a CourseGraph instance directly from the SQLite database."""
        graph = CourseGraph()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT code, title, credits, department FROM courses ORDER BY code")
            for row in cursor.fetchall():
                graph.add_course(row["code"], row["title"], row["credits"], row["department"])

            cursor.execute("SELECT prereq_code, target_code FROM prerequisites")
            for row in cursor.fetchall():
                try:
                    graph.add_prerequisite(row["prereq_code"], row["target_code"])
                except Exception:
                    pass
        return graph

    def save_graph_to_db(self, graph: CourseGraph) -> None:
        """Persists the in-memory CourseGraph into SQLite."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM prerequisites")
            cursor.execute("DELETE FROM courses")

            for c in graph.get_all_courses():
                cursor.execute(
                    "INSERT INTO courses (code, title, credits, department) VALUES (?, ?, ?, ?)",
                    (c.code, c.title, c.credits, c.department)
                )

            for u, neighbors in graph.adj_list.items():
                for v in neighbors:
                    cursor.execute(
                        "INSERT OR IGNORE INTO prerequisites (prereq_code, target_code) VALUES (?, ?)",
                        (u, v)
                    )
            conn.commit()

    def log_execution(self, algorithm: str, has_cycle: bool, order_result: List[str], cycle_path: List[str], validation_status: str):
        """Records an algorithm execution record into the database audit log."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO execution_logs (algorithm, has_cycle, order_result, cycle_path, validation_status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                algorithm,
                1 if has_cycle else 0,
                " -> ".join(order_result) if order_result else "None",
                " -> ".join(cycle_path) if cycle_path else "None",
                validation_status
            ))
            conn.commit()

    def get_assignment_info(self) -> Dict[str, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM assignment_metadata")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    def get_rubrics(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rubrics ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]

    def get_execution_logs(self, limit: int = 15) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM execution_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_database_summary(self) -> Dict:
        """Returns overall database statistics and table contents for API / Web UI."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM courses")
            total_courses = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM prerequisites")
            total_prereqs = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM execution_logs")
            total_logs = cursor.fetchone()[0]

            return {
                "db_file": os.path.basename(self.db_path),
                "total_courses": total_courses,
                "total_prerequisites": total_prereqs,
                "total_execution_logs": total_logs,
                "assignment_metadata": self.get_assignment_info(),
                "rubrics": self.get_rubrics(),
                "recent_logs": self.get_execution_logs(10)
            }
