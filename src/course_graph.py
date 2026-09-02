"""
Directed Graph module using an Adjacency List representation for the
University Course Prerequisite Management System.

Prerequisite Edge Convention:
An edge u -> v means course 'u' is a prerequisite for course 'v'.
Course 'u' MUST be successfully completed BEFORE enrolling in 'v'.
"""

from typing import Dict, List, Set, Optional
from src.course import Course


class CourseGraph:
    """
    Manages a directed graph of courses and their prerequisite dependencies
    using an Adjacency List representation.
    """

    def __init__(self):
        # Map of course code to Course instance
        self.courses: Dict[str, Course] = {}
        # Adjacency list: u -> list of courses that depend on u (dependents/outgoing edges)
        self.adj_list: Dict[str, List[str]] = {}
        # Reverse adjacency list: v -> list of prerequisites required for v (incoming edges)
        self.prereq_map: Dict[str, List[str]] = {}

    def add_course(self, code: str, title: str, credits: int = 3, department: Optional[str] = None) -> Course:
        """
        Adds a new course vertex to the graph.
        Prevents duplicate registration.
        """
        clean_code = code.strip().upper()
        if clean_code in self.courses:
            raise ValueError(f"Course '{clean_code}' already exists in the graph.")
        course = Course(clean_code, title, credits, department)
        self.courses[clean_code] = course
        self.adj_list[clean_code] = []
        self.prereq_map[clean_code] = []
        return course

    def add_prerequisite(self, prereq_code: str, target_code: str) -> None:
        """
        Adds a directed prerequisite edge: prereq_code -> target_code.
        Meaning: prereq_code must be completed before target_code can be taken.
        """
        u = prereq_code.strip().upper()
        v = target_code.strip().upper()

        if u not in self.courses:
            raise KeyError(f"Prerequisite course '{u}' does not exist in the curriculum.")
        if v not in self.courses:
            raise KeyError(f"Target course '{v}' does not exist in the curriculum.")
        if u == v:
            raise ValueError(f"Invalid prerequisite: A course cannot be a prerequisite of itself ('{u}' -> '{v}').")
        if v in self.adj_list[u]:
            raise ValueError(f"Duplicate prerequisite edge already exists: '{u}' -> '{v}'.")

        self.adj_list[u].append(v)
        self.prereq_map[v].append(u)

    def remove_prerequisite(self, prereq_code: str, target_code: str) -> bool:
        """Removes a directed edge if present."""
        u = prereq_code.strip().upper()
        v = target_code.strip().upper()
        if u in self.adj_list and v in self.adj_list[u]:
            self.adj_list[u].remove(v)
            if v in self.prereq_map and u in self.prereq_map[v]:
                self.prereq_map[v].remove(u)
            return True
        return False

    def get_course(self, code: str) -> Optional[Course]:
        return self.courses.get(code.strip().upper())

    def get_all_courses(self) -> List[Course]:
        """Returns sorted list of courses by course code."""
        return sorted(list(self.courses.values()), key=lambda c: c.code)

    def get_num_vertices(self) -> int:
        return len(self.courses)

    def get_num_edges(self) -> int:
        return sum(len(neighbors) for neighbors in self.adj_list.values())

    def calculate_indegrees(self) -> Dict[str, int]:
        """
        Calculates the in-degree for every course vertex.
        In-degree of course v = number of direct prerequisites required for v.
        """
        indegrees = {code: 0 for code in self.courses}
        for u in self.courses:
            for v in self.adj_list.get(u, []):
                indegrees[v] += 1
        return indegrees

    def calculate_outdegrees(self) -> Dict[str, int]:
        """
        Calculates the out-degree for every course vertex.
        Out-degree of course u = number of subsequent courses that require u.
        """
        return {code: len(self.adj_list.get(code, [])) for code in self.courses}

    def display_courses_str(self) -> str:
        """Formats the registered courses list."""
        if not self.courses:
            return "No courses registered in the system."
        lines = [f"{'Code':<8} | {'Credits':<7} | {'Department':<32} | {'Title'}"]
        lines.append("-" * 75)
        for c in self.get_all_courses():
            lines.append(f"{c.code:<8} | {c.credits:<7} | {c.department:<32} | {c.title}")
        return "\n".join(lines)

    def display_adjacency_list_str(self) -> str:
        """
        Formats the adjacency list view:
        u -> [dependent courses requiring u]
        """
        if not self.courses:
            return "Graph is empty."
        lines = []
        for code in sorted(self.courses.keys()):
            course = self.courses[code]
            dependents = self.adj_list.get(code, [])
            if dependents:
                dep_str = ", ".join(dependents)
                lines.append(f"{code} ({course.title}) -> [{dep_str}]")
            else:
                lines.append(f"{code} ({course.title}) -> [None (Terminal Course)]")
        return "\n".join(lines)

    def display_prerequisites_str(self) -> str:
        """
        Formats the prerequisite requirement view:
        v requires <- [prerequisite courses needed before v]
        """
        if not self.courses:
            return "Graph is empty."
        lines = []
        for code in sorted(self.courses.keys()):
            course = self.courses[code]
            prereqs = self.prereq_map.get(code, [])
            if prereqs:
                p_str = ", ".join(prereqs)
                lines.append(f"{code} ({course.title}) requires: [{p_str}]")
            else:
                lines.append(f"{code} ({course.title}) requires: [None (Entry-level course)]")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clears all courses and dependencies."""
        self.courses.clear()
        self.adj_list.clear()
        self.prereq_map.clear()

    def load_sample_dataset(self) -> None:
        """
        Loads the standard 12-course realistic university curriculum DAG
        as specified in the academic requirements.
        """
        self.clear()

        # 12 Realistic Courses
        sample_courses = [
            ("CS101", "Programming Fundamentals", 4),
            ("CS102", "Object Oriented Programming", 4),
            ("CS103", "Data Structures", 4),
            ("CS104", "Discrete Mathematics", 3),
            ("CS105", "Database Management Systems", 3),
            ("CS106", "Computer Organization", 3),
            ("CS201", "Algorithms", 4),
            ("CS202", "Operating Systems", 4),
            ("CS203", "Computer Networks", 3),
            ("CS204", "Software Engineering", 3),
            ("CS301", "Artificial Intelligence", 4),
            ("CS302", "Machine Learning", 4)
        ]

        for code, title, credits in sample_courses:
            self.add_course(code, title, credits)

        # Realistic Prerequisite Relationships (DAG):
        # CS101 -> CS102
        # CS101 -> CS103
        # CS104 -> CS103
        # CS103 -> CS201
        # CS106 -> CS202
        # CS103 -> CS202
        # CS103 -> CS203
        # CS102 -> CS204
        # CS201 -> CS301
        # CS201 -> CS302
        # CS301 -> CS302
        # CS103 -> CS105
        prerequisites = [
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

        for prereq, target in prerequisites:
            self.add_prerequisite(prereq, target)

    def load_cyclic_dataset(self) -> None:
        """
        Loads a sample curriculum with an intentional circular dependency
        to demonstrate cycle detection:
        CS101 -> CS102 -> CS103 -> CS201 -> CS101
        """
        self.clear()
        courses = [
            ("CS101", "Programming Fundamentals", 4),
            ("CS102", "Object Oriented Programming", 4),
            ("CS103", "Data Structures", 4),
            ("CS201", "Algorithms", 4),
            ("CS202", "Operating Systems", 3),
            ("CS301", "Artificial Intelligence", 3)
        ]
        for code, title, credits in courses:
            self.add_course(code, title, credits)

        # Cyclic dependency chain
        cyclic_edges = [
            ("CS101", "CS102"),
            ("CS102", "CS103"),
            ("CS103", "CS201"),
            ("CS201", "CS101"),  # Cycle back to CS101!
            ("CS103", "CS202"),
            ("CS201", "CS301")
        ]
        for prereq, target in cyclic_edges:
            self.add_prerequisite(prereq, target)

    def to_dict(self) -> dict:
        """Converts graph to dictionary representation for Web/JSON serialization."""
        return {
            "num_vertices": self.get_num_vertices(),
            "num_edges": self.get_num_edges(),
            "courses": [c.to_dict() for c in self.get_all_courses()],
            "adj_list": self.adj_list,
            "prereq_map": self.prereq_map,
            "indegrees": self.calculate_indegrees()
        }
