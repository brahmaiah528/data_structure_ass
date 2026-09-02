"""
Topological Sort Algorithms module for University Course Prerequisite Management System.
Implements:
1. BFS-based Topological Sort using Kahn's Algorithm
2. DFS-based Topological Sort using 3-State Vertex Coloring (UNVISITED=0, VISITING=1, VISITED=2)

Provides full execution trace, in-degree updates, queue states, and cycle status.
"""

from collections import deque
from typing import Dict, List, Tuple, Optional, Any
from src.course_graph import CourseGraph


class TopologicalSortResult:
    """Encapsulates the complete output and diagnostics of a topological sort run."""

    def __init__(self, algorithm: str):
        self.algorithm: str = algorithm
        self.success: bool = False
        self.has_cycle: bool = False
        self.order: List[str] = []
        self.initial_indegrees: Dict[str, int] = {}
        self.steps: List[str] = []
        self.cycle_info: Optional[str] = None
        self.summary: str = ""

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "success": self.success,
            "has_cycle": self.has_cycle,
            "order": self.order,
            "initial_indegrees": self.initial_indegrees,
            "steps": self.steps,
            "cycle_info": self.cycle_info,
            "summary": self.summary
        }

    def format_report(self, graph: CourseGraph) -> str:
        """Formats an academic report string suitable for GUI display and reports."""
        lines = []
        lines.append("=" * 70)
        lines.append(f"{self.algorithm.upper()} TOPOLOGICAL SORT RESULT")
        lines.append("=" * 70)

        if self.initial_indegrees:
            lines.append("\n[1] INITIAL INDEGREES (Number of Direct Prerequisites):")
            lines.append("-" * 55)
            for code in sorted(self.initial_indegrees.keys()):
                course = graph.get_course(code)
                title = course.title if course else ""
                lines.append(f"  {code:<8} = {self.initial_indegrees[code]:<3} ({title})")

        lines.append("\n[2] STEP-BY-STEP EXECUTION TRACE:")
        lines.append("-" * 55)
        for idx, step in enumerate(self.steps, 1):
            lines.append(f"  Step {idx:>2}: {step}")

        lines.append("\n[3] CYCLE STATUS & VERDICT:")
        lines.append("-" * 55)
        if self.has_cycle:
            lines.append("  STATUS: CYCLE DETECTED!")
            lines.append(f"  DIAGNOSIS: {self.cycle_info}")
            lines.append("  NOTE: A valid topological course ordering CANNOT be generated.")
            lines.append("  REAL-WORLD IMPACT: A circular dependency exists. Students in this chain")
            lines.append("  cannot register for any of the affected courses because each course")
            lines.append("  requires another course that cannot be completed first.")
        else:
            lines.append("  STATUS: NO CYCLE DETECTED (Valid Directed Acyclic Graph - DAG)")

        lines.append("\n[4] FINAL COURSE-TAKING ORDER:")
        lines.append("-" * 55)
        if self.success and self.order:
            for rank, code in enumerate(self.order, 1):
                course = graph.get_course(code)
                if course:
                    lines.append(f"  {rank:>2}. {code} – {course.title} ({course.credits} Credits)")
                else:
                    lines.append(f"  {rank:>2}. {code}")
            lines.append(f"\nTotal Courses Ordered: {len(self.order)} of {graph.get_num_vertices()}")
        else:
            lines.append("  None (Topological sort aborted due to circular dependency)")

        lines.append("=" * 70)
        return "\n".join(lines)


class TopologicalSort:
    """Implements BFS (Kahn's) and DFS Topological Sort algorithms."""

    @staticmethod
    def kahn_sort(graph: CourseGraph) -> TopologicalSortResult:
        """
        Executes Kahn's Algorithm (BFS-based Topological Sort).

        Working:
        1. Calculate indegree of every vertex.
        2. Insert all vertices having indegree 0 into a queue.
        3. Remove a course from the queue.
        4. Add it to the topological ordering.
        5. Decrease indegree of all adjacent courses.
        6. If any adjacent course becomes indegree 0, add it to the queue.
        7. Continue until queue becomes empty.
        8. If the number of processed courses is less than total vertices, a cycle exists.
        """
        result = TopologicalSortResult("BFS / Kahn's Algorithm")
        total_vertices = graph.get_num_vertices()

        if total_vertices == 0:
            result.success = True
            result.summary = "Graph is empty."
            return result

        # 1. Calculate in-degrees
        indegrees = graph.calculate_indegrees()
        result.initial_indegrees = dict(indegrees)
        working_indegrees = dict(indegrees)

        # 2. Queue all vertices with indegree 0 (using lexicographical sort for deterministic order)
        initial_zeroes = sorted([code for code, deg in working_indegrees.items() if deg == 0])
        queue: deque[str] = deque(initial_zeroes)

        result.steps.append(
            f"Initialized queue with courses having In-Degree 0: [{', '.join(queue) if queue else 'None'}]"
        )

        topological_order: List[str] = []

        # 3-7. Process queue
        step_num = 1
        while queue:
            current = queue.popleft()
            topological_order.append(current)
            course = graph.get_course(current)
            title = course.title if course else ""

            dependents = graph.adj_list.get(current, [])
            updated_info = []

            for neighbor in dependents:
                working_indegrees[neighbor] -= 1
                new_deg = working_indegrees[neighbor]
                if new_deg == 0:
                    queue.append(neighbor)
                    updated_info.append(f"{neighbor} (in-degree -> 0, ENQUEUED)")
                else:
                    updated_info.append(f"{neighbor} (in-degree -> {new_deg})")

            updates_str = ", ".join(updated_info) if updated_info else "No outgoing dependencies"
            queue_str = f"[{', '.join(queue)}]" if queue else "[] (Empty)"
            result.steps.append(
                f"Dequeued '{current}' ({title}) -> Decremented dependents: {updates_str} -> Current Queue: {queue_str}"
            )
            step_num += 1

        # 8. Cycle verification
        if len(topological_order) == total_vertices:
            result.success = True
            result.has_cycle = False
            result.order = topological_order
            result.summary = f"Successfully generated valid topological order for all {total_vertices} courses."
        else:
            result.success = False
            result.has_cycle = True
            unprocessed = sorted([c for c in graph.courses if c not in topological_order])
            result.cycle_info = (
                f"Processed {len(topological_order)} of {total_vertices} courses. "
                f"Queue became empty prematurely. {len(unprocessed)} courses could not be scheduled "
                f"due to circular prerequisites: {unprocessed}"
            )
            result.summary = "Cycle detected via Kahn's algorithm; processed count < total courses."

        return result

    @staticmethod
    def dfs_sort(graph: CourseGraph) -> TopologicalSortResult:
        """
        Executes DFS-based Topological Sort using 3-state vertex coloring:
        0 = UNVISITED (Course has not been explored)
        1 = VISITING  (Course is currently in the active DFS recursion stack)
        2 = VISITED   (Course and all its descendants have been completely explored)

        Algorithm:
        1. Start DFS from every unvisited course.
        2. Mark current course as VISITING.
        3. Visit each adjacent course.
        4. If an adjacent course is VISITING, a back-edge exists -> CYCLE DETECTED!
        5. If an adjacent course is UNVISITED, recursively visit it.
        6. After processing all adjacent courses, mark course as VISITED.
        7. Push the course onto a stack.
        8. Reverse/pop stack to obtain topological order.
        """
        result = TopologicalSortResult("DFS Topological Sort")
        total_vertices = graph.get_num_vertices()

        if total_vertices == 0:
            result.success = True
            result.summary = "Graph is empty."
            return result

        UNVISITED = 0
        VISITING = 1
        VISITED = 2

        state: Dict[str, int] = {code: UNVISITED for code in graph.courses}
        call_stack: List[str] = []
        finish_stack: List[str] = []
        cycle_detected = False
        cycle_path: List[str] = []

        result.initial_indegrees = graph.calculate_indegrees()

        def dfs(u: str) -> bool:
            nonlocal cycle_detected, cycle_path
            state[u] = VISITING
            call_stack.append(u)
            result.steps.append(f"Enter DFS({u}) -> State: VISITING | Active Recursion Stack: {' -> '.join(call_stack)}")

            # Iterate over adjacent courses (dependents that require u)
            for v in graph.adj_list.get(u, []):
                if state[v] == VISITING:
                    # Back edge detected: v is an ancestor in current recursion stack
                    cycle_detected = True
                    cycle_start_idx = call_stack.index(v)
                    cycle_path = call_stack[cycle_start_idx:] + [v]
                    result.steps.append(
                        f"Back-Edge detected from '{u}' to '{v}'! Course '{v}' is currently VISITING in recursion stack. Cycle: {' -> '.join(cycle_path)}"
                    )
                    return False  # Abort due to cycle

                elif state[v] == UNVISITED:
                    result.steps.append(f"Traversing dependency edge {u} -> {v} (UNVISITED)")
                    if not dfs(v):
                        return False

            state[u] = VISITED
            call_stack.pop()
            finish_stack.append(u)
            result.steps.append(f"Exit DFS({u}) -> State: VISITED | Pushed to Finish Stack: [{', '.join(finish_stack)}]")
            return True

        # Process all courses to handle disconnected components
        for code in sorted(graph.courses.keys()):
            if state[code] == UNVISITED:
                result.steps.append(f"--- Starting DFS component exploration from root: '{code}' ---")
                if not dfs(code):
                    break

        if cycle_detected:
            result.success = False
            result.has_cycle = True
            result.cycle_info = f"Back edge found during DFS recursion traversal. Circular chain: {' -> '.join(cycle_path)}"
            result.summary = "Cycle detected via DFS 3-state traversal."
        else:
            result.success = True
            result.has_cycle = False
            # Reverse finish stack to get topological order
            result.order = list(reversed(finish_stack))
            result.summary = f"Successfully generated valid topological order for all {total_vertices} courses via DFS."

        return result
