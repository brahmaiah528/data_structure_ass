"""
Cycle Detector module for the University Course Prerequisite Management System.

Demonstrates and compares cycle detection using BOTH:
1. BFS / Kahn's Algorithm (In-degree depletion and queue starvation)
2. DFS 3-State Vertex Coloring (Back-edge detection via active recursion stack)

Includes full academic diagnostic and real-world institutional impact reporting.
"""

from collections import deque
from typing import Dict, List, Tuple, Optional
from src.course_graph import CourseGraph


class CycleDetectionReport:
    """Contains diagnostics, cycle paths, and academic impact analysis."""

    def __init__(self, method: str):
        self.method: str = method
        self.cycle_detected: bool = False
        self.cycle_path: List[str] = []
        self.involved_courses: List[str] = []
        self.explanation: str = ""
        self.real_world_impact: str = ""

    def format_report(self) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append(f"CYCLE DETECTION REPORT – [{self.method.upper()}]")
        lines.append("=" * 70)

        if self.cycle_detected:
            lines.append("STATUS: [CYCLE DETECTED!]")
            lines.append("\n[1] CIRCULAR DEPENDENCY TRACE:")
            lines.append("-" * 55)
            if self.cycle_path:
                lines.append("  Cycle Chain: " + " -> ".join(self.cycle_path))
            if self.involved_courses:
                lines.append(f"  Affected Courses: {', '.join(self.involved_courses)}")

            lines.append("\n[2] ALGORITHM DIAGNOSIS:")
            lines.append("-" * 55)
            lines.append(f"  {self.explanation}")

            lines.append("\n[3] REAL-WORLD UNIVERSITY COURSE REGISTRATION INTERPRETATION:")
            lines.append("-" * 55)
            lines.append("  \"Course registration is impossible for the affected dependency chain")
            lines.append("   because each course requires another course that cannot be completed first.\"")
            lines.append("\n  Institutional Consequences:")
            lines.append("  * Student Enrollment Deadlock: Students attempting to register for any")
            lines.append("    course in this loop are blocked by registration validation rules.")
            lines.append("  * Degree Audit Failure: Automated degree progression systems encounter an")
            lines.append("    unresolvable dependency loop, preventing graduation clearance.")
            lines.append("  * Administrative Intervention: Academic advisors and curriculum committees")
            lines.append("    must review the course catalogue and eliminate the circular edge.")
            lines.append("  * Automated System Rejection: The university registration portal must")
            lines.append("    immediately reject this curriculum catalog configuration.")
        else:
            lines.append("STATUS: [NO CYCLE DETECTED]")
            lines.append("The prerequisite graph is a valid Directed Acyclic Graph (DAG).")
            lines.append("Students can progress through courses in a valid, achievable sequence.")

        lines.append("=" * 70)
        return "\n".join(lines)


class CycleDetector:
    """Provides dual-engine cycle detection (BFS and DFS)."""

    @staticmethod
    def detect_cycle_bfs(graph: CourseGraph) -> CycleDetectionReport:
        """
        Detects cycles using BFS / Kahn's algorithm.
        Principle: In a DAG, all vertices eventually reach in-degree 0 and get processed.
        If a cycle exists, vertices inside or reachable from the cycle maintain in-degrees > 0,
        causing queue starvation before all vertices are visited.
        """
        report = CycleDetectionReport("BFS / Kahn's In-Degree Reduction")
        total_v = graph.get_num_vertices()
        if total_v == 0:
            return report

        indegrees = graph.calculate_indegrees()
        queue = deque([c for c, deg in indegrees.items() if deg == 0])
        processed_count = 0
        processed_set = set()

        while queue:
            curr = queue.popleft()
            processed_count += 1
            processed_set.add(curr)
            for neighbor in graph.adj_list.get(curr, []):
                indegrees[neighbor] -= 1
                if indegrees[neighbor] == 0:
                    queue.append(neighbor)

        if processed_count < total_v:
            report.cycle_detected = True
            unprocessed = [c for c in graph.courses if c not in processed_set]
            report.involved_courses = sorted(unprocessed)
            report.explanation = (
                f"Kahn's algorithm terminated with queue exhaustion after ordering only "
                f"{processed_count} of {total_v} courses. The remaining {len(unprocessed)} courses "
                f"have remaining in-degrees > 0 due to circular prerequisite mutual dependencies: "
                f"{unprocessed}"
            )
            # Reconstruct cycle path from remaining subgraph
            report.cycle_path = CycleDetector._extract_cycle_from_subgraph(graph, set(unprocessed))
        else:
            report.cycle_detected = False

        return report

    @staticmethod
    def detect_cycle_dfs(graph: CourseGraph) -> CycleDetectionReport:
        """
        Detects cycles using DFS 3-state vertex coloring:
        UNVISITED = 0
        VISITING  = 1 (in active recursion stack)
        VISITED   = 2 (fully explored)

        A cycle is proven when an edge points to a vertex currently in state VISITING (a back-edge).
        """
        report = CycleDetectionReport("DFS 3-State Recursion Stack")
        UNVISITED, VISITING, VISITED = 0, 1, 2
        state = {c: UNVISITED for c in graph.courses}
        parent = {}
        active_stack: List[str] = []
        found_cycle: List[str] = []

        def dfs(u: str) -> bool:
            nonlocal found_cycle
            state[u] = VISITING
            active_stack.append(u)

            for v in graph.adj_list.get(u, []):
                if state[v] == VISITING:
                    # Back edge found: u -> v where v is in active recursion stack
                    idx = active_stack.index(v)
                    found_cycle = active_stack[idx:] + [v]
                    return True
                elif state[v] == UNVISITED:
                    parent[v] = u
                    if dfs(v):
                        return True

            state[u] = VISITED
            active_stack.pop()
            return False

        for code in sorted(graph.courses.keys()):
            if state[code] == UNVISITED:
                if dfs(code):
                    break

        if found_cycle:
            report.cycle_detected = True
            report.cycle_path = found_cycle
            report.involved_courses = sorted(list(set(found_cycle)))
            report.explanation = (
                f"DFS encountered a back-edge pointing to ancestor course '{found_cycle[-1]}' "
                f"which was already present in the active recursion call stack. "
                f"Exact circular path: {' -> '.join(found_cycle)}"
            )
        else:
            report.cycle_detected = False

        return report

    @staticmethod
    def _extract_cycle_from_subgraph(graph: CourseGraph, cycle_nodes: set) -> List[str]:
        """Extracts a simple cycle loop from nodes remaining in cycle subgraph."""
        if not cycle_nodes:
            return []
        visited = {}
        path = []

        def dfs_sub(curr: str) -> Optional[List[str]]:
            visited[curr] = True
            path.append(curr)
            for nxt in graph.adj_list.get(curr, []):
                if nxt in cycle_nodes:
                    if nxt in path:
                        idx = path.index(nxt)
                        return path[idx:] + [nxt]
                    if nxt not in visited:
                        res = dfs_sub(nxt)
                        if res:
                            return res
            path.pop()
            return None

        for node in sorted(cycle_nodes):
            res = dfs_sub(node)
            if res:
                return res
        return sorted(list(cycle_nodes))
