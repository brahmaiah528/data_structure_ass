"""
Graph data structure module for University Student Course Enrollment Portal.
Implements Adjacency List, Kahn's BFS Topological Sort, DFS 3-State Topological Sort,
Dual-Engine Cycle Detection, and Precedence Validation.
"""

from collections import deque
from typing import Dict, List, Set, Tuple, Optional, Any


class CourseGraph:
    """
    Represents university course prerequisite dependencies as a Directed Graph G = (V, E).
    Edge u -> v means Course 'u' is a mandatory prerequisite for Course 'v'.
    """

    def __init__(self):
        # Adjacency list: u -> list of courses that depend on u (outgoing edges)
        self.adj_list: Dict[str, List[str]] = {}
        # Reverse adjacency list: v -> list of prerequisites required for v (incoming edges)
        self.prereq_list: Dict[str, List[str]] = {}
        # Course metadata lookups
        self.course_names: Dict[str, str] = {}
        self.departments: Dict[str, str] = {}
        self.credits: Dict[str, int] = {}
        self.semesters: Dict[str, int] = {}

    def add_course(self, code: str, name: str = "", department: str = "", credits: int = 3, semester: int = 1) -> None:
        code = code.strip().upper()
        if code not in self.adj_list:
            self.adj_list[code] = []
            self.prereq_list[code] = []
        self.course_names[code] = name or code
        self.departments[code] = department
        self.credits[code] = credits
        self.semesters[code] = semester

    def add_prerequisite(self, prereq_code: str, target_code: str) -> None:
        """
        Adds directed edge prereq_code -> target_code.
        Means prereq_code must be completed before target_code.
        """
        prereq = prereq_code.strip().upper()
        target = target_code.strip().upper()

        if prereq not in self.adj_list:
            self.add_course(prereq)
        if target not in self.adj_list:
            self.add_course(target)

        if target not in self.adj_list[prereq]:
            self.adj_list[prereq].append(target)
        if prereq not in self.prereq_list[target]:
            self.prereq_list[target].append(prereq)

    def get_all_courses(self) -> List[str]:
        return sorted(list(self.adj_list.keys()))

    def get_neighbors(self, code: str) -> List[str]:
        """Returns courses that depend on 'code'."""
        return self.adj_list.get(code.strip().upper(), [])

    def get_prerequisites(self, code: str) -> List[str]:
        """Returns prerequisites required for 'code'."""
        return self.prereq_list.get(code.strip().upper(), [])

    def calculate_indegrees(self) -> Dict[str, int]:
        """
        Calculates in-degree for every course.
        In-degree = number of unsatisfied prerequisite courses required before taking this course.
        """
        indegrees = {code: len(self.prereq_list.get(code, [])) for code in self.adj_list}
        return indegrees

    # =========================================================================
    # 1. BFS / KAHN'S ALGORITHM TOPOLOGICAL SORT & CYCLE DETECTION
    # =========================================================================
    def bfs_topological_sort(self) -> Tuple[bool, List[str], List[str], List[str]]:
        """
        Kahn's Algorithm for Topological Sorting using a FIFO Queue.
        Returns:
            success (bool): True if DAG (no cycles), False if cycle detected
            order (List[str]): Valid topological course-taking sequence
            steps_log (List[str]): Step-by-step diagnostic execution trace
            cycle_nodes (List[str]): List of courses caught in dependency cycle (if any)
        """
        indegrees = self.calculate_indegrees()
        queue = deque([c for c, deg in indegrees.items() if deg == 0])
        queue = deque(sorted(list(queue)))  # Deterministic tie-breaking

        order: List[str] = []
        steps_log: List[str] = []
        step_num = 1

        steps_log.append("=== INITIATING BFS / KAHN'S TOPOLOGICAL SORT ===")
        steps_log.append(f"Total Course Vertices (|V|): {len(self.adj_list)}")
        total_edges = sum(len(neighbors) for neighbors in self.adj_list.values())
        steps_log.append(f"Total Prerequisite Edges (|E|): {total_edges}")
        
        initial_zero = list(queue)
        steps_log.append(f"Initial Courses with In-degree 0 (Available immediately): {initial_zero}")

        while queue:
            curr = queue.popleft()
            order.append(curr)
            name = self.course_names.get(curr, curr)
            steps_log.append(f"Step {step_num}: Dequeue [{curr}: {name}] -> Appended to enrollment schedule.")
            step_num += 1

            for neighbor in sorted(self.adj_list.get(curr, [])):
                indegrees[neighbor] -= 1
                steps_log.append(f"   ↳ Decrement in-degree of dependent [{neighbor}] -> Remaining: {indegrees[neighbor]}")
                if indegrees[neighbor] == 0:
                    queue.append(neighbor)
                    steps_log.append(f"   ★ [{neighbor}] in-degree reached 0! Enqueued as now eligible.")

        # Cycle check
        if len(order) == len(self.adj_list):
            steps_log.append("✓ SUCCESS: All courses ordered successfully. Graph is a valid Directed Acyclic Graph (DAG).")
            return True, order, steps_log, []
        else:
            cycle_nodes = [c for c, deg in indegrees.items() if deg > 0]
            steps_log.append(f"❌ CYCLE DETECTED via Kahn's Algorithm!")
            steps_log.append(f"Processed: {len(order)} of {len(self.adj_list)} courses.")
            steps_log.append(f"Starved Courses with unresolved in-degrees > 0: {cycle_nodes}")
            return False, order, steps_log, cycle_nodes

    # =========================================================================
    # 2. DFS TOPOLOGICAL SORT WITH 3-STATE VERTEX COLORING
    # =========================================================================
    def dfs_topological_sort(self) -> Tuple[bool, List[str], List[str], Optional[List[str]]]:
        """
        DFS Topological Sort using 3-State Vertex Coloring:
            0 = UNVISITED (White)
            1 = VISITING (Gray - currently in recursion stack)
            2 = VISITED (Black - fully explored)
        Returns:
            success (bool): True if DAG, False if back-edge cycle detected
            order (List[str]): Valid topological course-taking sequence
            steps_log (List[str]): Diagnostic trace
            cycle_path (Optional[List[str]]): Exact back-edge cycle path if detected
        """
        UNVISITED, VISITING, VISITED = 0, 1, 2
        state = {code: UNVISITED for code in self.adj_list}
        parent = {code: None for code in self.adj_list}
        stack: List[str] = []
        steps_log: List[str] = []
        cycle_path: Optional[List[str]] = None

        steps_log.append("=== INITIATING DFS 3-STATE TOPOLOGICAL SORT ===")
        steps_log.append("Color States: UNVISITED=0, VISITING=1 (in recursion stack), VISITED=2 (finished)")

        def dfs_visit(u: str) -> bool:
            nonlocal cycle_path
            state[u] = VISITING
            steps_log.append(f"ENTER [{u}] -> State set to VISITING (1)")

            for v in sorted(self.adj_list.get(u, [])):
                if state[v] == VISITING:
                    # Back-edge detected! Reconstruct circular path
                    curr = u
                    path = [v, curr]
                    while curr != v and parent.get(curr) is not None:
                        curr = parent[curr]
                        path.append(curr)
                    path.reverse()
                    cycle_path = path
                    steps_log.append(f"❌ BACK-EDGE DETECTED: Edge [{u} -> {v}] points to active ancestor in state VISITING!")
                    steps_log.append(f"Circular Dependency Cycle: {' -> '.join(path)}")
                    return False  # Cycle exists

                elif state[v] == UNVISITED:
                    parent[v] = u
                    if not dfs_visit(v):
                        return False

            state[u] = VISITED
            stack.append(u)
            steps_log.append(f"EXIT  [{u}] -> State set to VISITED (2). Pushed onto finish stack.")
            return True

        # Outer loop to handle disconnected components
        for node in sorted(self.adj_list.keys()):
            if state[node] == UNVISITED:
                steps_log.append(f"Starting new DFS traversal tree rooted at [{node}]")
                if not dfs_visit(node):
                    return False, [], steps_log, cycle_path

        # Reverse finish stack to get topological order
        order = list(reversed(stack))
        steps_log.append("✓ SUCCESS: DFS finished without back-edges. Reversed finish stack yields valid course schedule.")
        return True, order, steps_log, None

    # =========================================================================
    # 3. CYCLE DETECTION ENGINES
    # =========================================================================
    def detect_cycle_bfs(self) -> Tuple[bool, List[str], str]:
        """
        Runs BFS Kahn cycle check and returns (has_cycle, cycle_nodes, explanation).
        """
        success, order, _, cycle_nodes = self.bfs_topological_sort()
        has_cycle = not success
        if has_cycle:
            explanation = (
                f"Kahn's Algorithm terminated prematurely. {len(order)} of {len(self.adj_list)} "
                f"courses could be scheduled. The following {len(cycle_nodes)} course(s) remain locked "
                f"with unresolved prerequisites: {', '.join(cycle_nodes)}."
            )
        else:
            explanation = "No cycles detected by BFS. All prerequisite dependencies are strictly forward-directed."
        return has_cycle, cycle_nodes, explanation

    def detect_cycle_dfs(self) -> Tuple[bool, Optional[List[str]], str]:
        """
        Runs DFS 3-state back-edge detector and returns (has_cycle, cycle_path, explanation).
        """
        success, _, _, cycle_path = self.dfs_topological_sort()
        has_cycle = not success
        if has_cycle and cycle_path:
            path_str = " -> ".join(cycle_path)
            explanation = (
                f"DFS encountered a back-edge pointing to an ancestor currently in the VISITING (gray) state. "
                f"Exact circular dependency loop identified: {path_str}. "
                f"In this scenario, every course in the loop requires another course in the loop, creating an impossible deadlock."
            )
        else:
            explanation = "No back-edges encountered during DFS traversal. Graph is strictly acyclic."
        return has_cycle, cycle_path, explanation

    # =========================================================================
    # 4. TOPOLOGICAL ORDER FORMAL VALIDATION
    # =========================================================================
    def validate_topological_order(self, order: List[str]) -> Tuple[bool, List[str]]:
        """
        Validates that for every prerequisite edge u -> v:
        position(u) < position(v) in the proposed order.
        """
        if len(order) != len(self.adj_list):
            return False, [f"Order length ({len(order)}) does not match graph vertex count ({len(self.adj_list)})."]

        pos = {code: i for i, code in enumerate(order)}
        violations = []

        for u, neighbors in self.adj_list.items():
            for v in neighbors:
                if u in pos and v in pos:
                    if pos[u] >= pos[v]:
                        violations.append(
                            f"Precedence Violation: Prerequisite [{u}] (index {pos[u]}) appears AFTER dependent [{v}] (index {pos[v]})."
                        )

        is_valid = len(violations) == 0
        return is_valid, violations

    # =========================================================================
    # 5. DEMO ARTIFICIAL CYCLE BUILDER
    # =========================================================================
    @staticmethod
    def create_demo_cycle_graph() -> "CourseGraph":
        """
        Builds a dedicated demonstration cycle:
        CS101 -> CS102 -> CS104 -> CS201 -> CS101
        """
        g = CourseGraph()
        g.add_course("CS101", "Programming Fundamentals", "CSE", 4, 1)
        g.add_course("CS102", "Object Oriented Programming", "CSE", 4, 2)
        g.add_course("CS104", "Data Structures", "CSE", 4, 3)
        g.add_course("CS201", "Design and Analysis of Algorithms", "CSE", 4, 4)

        g.add_prerequisite("CS101", "CS102")
        g.add_prerequisite("CS102", "CS104")
        g.add_prerequisite("CS104", "CS201")
        g.add_prerequisite("CS201", "CS101")  # Circular back-edge closing the loop!

        return g

    # =========================================================================
    # 6. DATABASE INTEGRATION LOADER
    # =========================================================================
    @classmethod
    def load_from_database(cls, db_path: str, department: Optional[str] = None) -> "CourseGraph":
        """
        Constructs a CourseGraph directly from the SQLite database.
        If department is specified, filters courses relevant to that department.
        """
        from database import get_connection

        g = cls()
        with get_connection(db_path) as conn:
            cursor = conn.cursor()

            # Fetch courses
            if department:
                common_depts = ("Common", "Basic Sciences", "Humanities", "Mathematics")
                placeholders = ",".join("?" for _ in common_depts)
                cursor.execute(f"""
                    SELECT course_id, course_code, course_name, department, credits, semester 
                    FROM courses 
                    WHERE department = ? OR department IN ({placeholders})
                """, (department, *common_depts))
            else:
                cursor.execute("SELECT course_id, course_code, course_name, department, credits, semester FROM courses")

            courses = cursor.fetchall()
            id_to_code = {}
            for c in courses:
                id_to_code[c["course_id"]] = c["course_code"]
                g.add_course(c["course_code"], c["course_name"], c["department"], c["credits"], c["semester"])

            # Fetch prerequisites
            cursor.execute("SELECT course_id, prerequisite_course_id FROM prerequisites")
            prereqs = cursor.fetchall()
            for p in prereqs:
                target_id = p["course_id"]
                prereq_id = p["prerequisite_course_id"]
                if target_id in id_to_code and prereq_id in id_to_code:
                    g.add_prerequisite(id_to_code[prereq_id], id_to_code[target_id])

        return g
