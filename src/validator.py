"""
Topological Order Validation module for University Course Prerequisite Management System.

Formally verifies that for every prerequisite edge:
A -> B (Course A is a prerequisite for Course B)
position(A) < position(B) in the generated topological ordering.
"""

from typing import List, Dict, Tuple, Optional
from src.course_graph import CourseGraph


class ValidationResult:
    """Contains topological sort validation results and edge-by-edge audit logs."""

    def __init__(self, passed: bool, total_edges: int):
        self.passed: bool = passed
        self.total_edges: int = total_edges
        self.violations: List[str] = []
        self.verified_edges: List[str] = []

    def format_report(self) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("TOPOLOGICAL ORDER FORMAL VALIDATION REPORT")
        lines.append("=" * 70)

        lines.append(f"Total Prerequisite Edges Audited: {self.total_edges}")
        lines.append(f"Edges Satisfying Precedence:       {len(self.verified_edges)}")
        lines.append(f"Precedence Violations Detected:    {len(self.violations)}")
        lines.append("-" * 55)

        if self.passed:
            lines.append("VERDICT: >>> Topological Order Validation: PASSED <<<")
            lines.append("All prerequisite relationships strictly satisfy precedence:")
            lines.append("For all edges (A -> B), position(A) < position(B).")
            lines.append("\nSample Validated Dependencies:")
            for edge in self.verified_edges[:8]:
                lines.append(f"  [OK] {edge}")
            if len(self.verified_edges) > 8:
                lines.append(f"  ... and {len(self.verified_edges) - 8} more verified edges.")
        else:
            lines.append("VERDICT: >>> Topological Order Validation: FAILED <<<")
            lines.append("Violations Detected:")
            for violation in self.violations:
                lines.append(f"  [FAIL] {violation}")

        lines.append("=" * 70)
        return "\n".join(lines)


class OrderValidator:
    """Validates that a course ordering strictly conforms to prerequisite constraints."""

    @staticmethod
    def validate(graph: CourseGraph, ordering: List[str]) -> ValidationResult:
        """
        Verifies that for every directed edge u -> v:
        position(u) < position(v).
        """
        total_edges = graph.get_num_edges()
        if not ordering:
            res = ValidationResult(False, total_edges)
            res.violations.append("Provided ordering is empty or topological sort failed.")
            return res

        # Map course code to its 0-indexed position in the ordering
        pos_map: Dict[str, int] = {code: idx for idx, code in enumerate(ordering)}
        violations: List[str] = []
        verified: List[str] = []

        # Audit every directed prerequisite edge u -> v
        for u in graph.courses:
            for v in graph.adj_list.get(u, []):
                if u not in pos_map:
                    violations.append(f"Prerequisite course '{u}' is missing from the ordered sequence.")
                    continue
                if v not in pos_map:
                    violations.append(f"Target course '{v}' is missing from the ordered sequence.")
                    continue

                pos_u = pos_map[u]
                pos_v = pos_map[v]

                if pos_u < pos_v:
                    verified.append(f"{u} (Pos {pos_u + 1}) -> {v} (Pos {pos_v + 1}) | pos({u}) < pos({v})")
                else:
                    violations.append(
                        f"Precedence Violation: '{u}' (Pos {pos_u + 1}) appears AFTER or AT dependent '{v}' (Pos {pos_v + 1})!"
                    )

        passed = (len(violations) == 0) and (len(pos_map) == graph.get_num_vertices())
        result = ValidationResult(passed, total_edges)
        result.violations = violations
        result.verified_edges = verified
        return result
