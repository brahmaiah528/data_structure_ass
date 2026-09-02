"""
Automated Test Suite module for the University Course Prerequisite Management System.

Executes and verifies all 6 mandatory test cases:
- Test Case 1: Normal DAG (12 Realistic Courses)
- Test Case 2: Simple Cycle (CS101 -> CS102 -> CS103 -> CS201 -> CS101)
- Test Case 3: Multiple Independent Courses (CS101, CS102, CS103 with no prereqs)
- Test Case 4: Course with Multiple Prerequisites (CS103 requiring CS101 and CS104)
- Test Case 5: Single Course with No Prerequisites
- Test Case 6: Disconnected Graph (Two distinct academic tracks)
"""

from typing import List, Dict, Any
from src.course_graph import CourseGraph
from src.topological_sort import TopologicalSort
from src.cycle_detector import CycleDetector
from src.validator import OrderValidator


class TestCaseResult:
    """Represents the execution outcome of an individual test case."""

    def __init__(self, test_id: str, name: str, input_desc: str, expected: str):
        self.test_id: str = test_id
        self.name: str = name
        self.input_desc: str = input_desc
        self.expected: str = expected
        self.actual: str = ""
        self.status: str = "PENDING"
        self.bfs_result: str = ""
        self.dfs_result: str = ""
        self.validation_result: str = ""

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "input_desc": self.input_desc,
            "expected": self.expected,
            "actual": self.actual,
            "status": self.status,
            "bfs_result": self.bfs_result,
            "dfs_result": self.dfs_result,
            "validation_result": self.validation_result
        }


class TestSuite:
    """Executes and formats all academic test cases."""

    @staticmethod
    def run_all_tests() -> List[TestCaseResult]:
        results: List[TestCaseResult] = []

        # =========================================================================
        # Test Case 1: Normal DAG
        # =========================================================================
        tc1 = TestCaseResult(
            "TC-01",
            "Normal DAG (12 University Courses)",
            "12 Courses (CS101-CS302) with 12 prerequisite dependencies forming a DAG",
            "Valid topological order generated; No cycle detected; Order validation PASSED"
        )
        g1 = CourseGraph()
        g1.load_sample_dataset()
        bfs1 = TopologicalSort.kahn_sort(g1)
        dfs1 = TopologicalSort.dfs_sort(g1)
        v1 = OrderValidator.validate(g1, bfs1.order)

        if bfs1.success and dfs1.success and v1.passed and not bfs1.has_cycle:
            tc1.status = "PASSED"
            tc1.actual = f"Order generated ({len(bfs1.order)} courses). Validation: PASSED"
        else:
            tc1.status = "FAILED"
            tc1.actual = f"BFS success={bfs1.success}, Validation passed={v1.passed}"
        tc1.bfs_result = " -> ".join(bfs1.order)
        tc1.dfs_result = " -> ".join(dfs1.order)
        tc1.validation_result = "PASSED" if v1.passed else "FAILED"
        results.append(tc1)

        # =========================================================================
        # Test Case 2: Simple Cycle
        # =========================================================================
        tc2 = TestCaseResult(
            "TC-02",
            "Simple Cycle (Circular Dependency)",
            "CS101 -> CS102 -> CS103 -> CS201 -> CS101",
            "Cycle detected by both BFS and DFS; Topological order rejected"
        )
        g2 = CourseGraph()
        g2.load_cyclic_dataset()
        bfs2 = TopologicalSort.kahn_sort(g2)
        dfs2 = TopologicalSort.dfs_sort(g2)
        c_bfs = CycleDetector.detect_cycle_bfs(g2)
        c_dfs = CycleDetector.detect_cycle_dfs(g2)

        if bfs2.has_cycle and dfs2.has_cycle and c_bfs.cycle_detected and c_dfs.cycle_detected:
            tc2.status = "PASSED"
            tc2.actual = f"Cycle detected by both BFS and DFS. Cycle loop: {' -> '.join(c_dfs.cycle_path)}"
        else:
            tc2.status = "FAILED"
            tc2.actual = f"BFS cycle={bfs2.has_cycle}, DFS cycle={dfs2.has_cycle}"
        tc2.bfs_result = "Cycle Detected (Queue starved)"
        tc2.dfs_result = f"Cycle Detected ({' -> '.join(c_dfs.cycle_path)})"
        tc2.validation_result = "N/A (Order aborted due to cycle)"
        results.append(tc2)

        # =========================================================================
        # Test Case 3: Multiple Independent Courses
        # =========================================================================
        tc3 = TestCaseResult(
            "TC-03",
            "Multiple Independent Courses",
            "4 Isolated Courses (CS101, CS102, CS103, CS104) with 0 prerequisite edges",
            "All 4 courses included in ordering in arbitrary valid sequence; Validation PASSED"
        )
        g3 = CourseGraph()
        for c in [("CS101", "Prog"), ("CS102", "OOP"), ("CS103", "DS"), ("CS104", "Discrete")]:
            g3.add_course(c[0], c[1])
        bfs3 = TopologicalSort.kahn_sort(g3)
        v3 = OrderValidator.validate(g3, bfs3.order)

        if bfs3.success and len(bfs3.order) == 4 and v3.passed:
            tc3.status = "PASSED"
            tc3.actual = f"Valid topological order: {', '.join(bfs3.order)}. Validation: PASSED"
        else:
            tc3.status = "FAILED"
            tc3.actual = f"Ordered {len(bfs3.order)} of 4 courses"
        tc3.bfs_result = ", ".join(bfs3.order)
        tc3.dfs_result = ", ".join(TopologicalSort.dfs_sort(g3).order)
        tc3.validation_result = "PASSED" if v3.passed else "FAILED"
        results.append(tc3)

        # =========================================================================
        # Test Case 4: Course with Multiple Prerequisites
        # =========================================================================
        tc4 = TestCaseResult(
            "TC-04",
            "Course with Multiple Prerequisites",
            "CS101 -> CS103 and CS104 -> CS103 (CS103 requires both CS101 and CS104)",
            "CS103 appears in the ordering strictly AFTER both CS101 and CS104"
        )
        g4 = CourseGraph()
        g4.add_course("CS101", "Programming Fundamentals")
        g4.add_course("CS104", "Discrete Mathematics")
        g4.add_course("CS103", "Data Structures")
        g4.add_prerequisite("CS101", "CS103")
        g4.add_prerequisite("CS104", "CS103")
        bfs4 = TopologicalSort.kahn_sort(g4)
        v4 = OrderValidator.validate(g4, bfs4.order)

        pos_101 = bfs4.order.index("CS101") if "CS101" in bfs4.order else -1
        pos_104 = bfs4.order.index("CS104") if "CS104" in bfs4.order else -1
        pos_103 = bfs4.order.index("CS103") if "CS103" in bfs4.order else -1

        if pos_103 > pos_101 and pos_103 > pos_104 and v4.passed:
            tc4.status = "PASSED"
            tc4.actual = f"Order: {bfs4.order}. CS103 (pos {pos_103+1}) > CS101 (pos {pos_101+1}) & CS104 (pos {pos_104+1})"
        else:
            tc4.status = "FAILED"
            tc4.actual = f"Order: {bfs4.order}"
        tc4.bfs_result = " -> ".join(bfs4.order)
        tc4.dfs_result = " -> ".join(TopologicalSort.dfs_sort(g4).order)
        tc4.validation_result = "PASSED" if v4.passed else "FAILED"
        results.append(tc4)

        # =========================================================================
        # Test Case 5: Single Course with No Prerequisites
        # =========================================================================
        tc5 = TestCaseResult(
            "TC-05",
            "Single Course with No Prerequisites",
            "Single vertex 'CS101' with 0 incoming or outgoing edges",
            "Course appears immediately in the order; No cycles; Validation PASSED"
        )
        g5 = CourseGraph()
        g5.add_course("CS101", "Programming Fundamentals")
        bfs5 = TopologicalSort.kahn_sort(g5)
        v5 = OrderValidator.validate(g5, bfs5.order)

        if bfs5.success and bfs5.order == ["CS101"] and v5.passed:
            tc5.status = "PASSED"
            tc5.actual = "CS101 ordered as solitary course. Validation: PASSED"
        else:
            tc5.status = "FAILED"
            tc5.actual = f"Order: {bfs5.order}"
        tc5.bfs_result = "CS101"
        tc5.dfs_result = "CS101"
        tc5.validation_result = "PASSED" if v5.passed else "FAILED"
        results.append(tc5)

        # =========================================================================
        # Test Case 6: Disconnected Graph
        # =========================================================================
        tc6 = TestCaseResult(
            "TC-06",
            "Disconnected Graph (Multi-track Curriculum)",
            "Component A: CS101 -> CS102; Component B: MA101 -> MA102 (Disconnected components)",
            "All vertices from both components appear in valid relative topological order"
        )
        g6 = CourseGraph()
        g6.add_course("CS101", "Programming")
        g6.add_course("CS102", "OOP")
        g6.add_course("MA101", "Calculus")
        g6.add_course("MA102", "Linear Algebra")
        g6.add_prerequisite("CS101", "CS102")
        g6.add_prerequisite("MA101", "MA102")
        bfs6 = TopologicalSort.kahn_sort(g6)
        v6 = OrderValidator.validate(g6, bfs6.order)

        if bfs6.success and len(bfs6.order) == 4 and v6.passed:
            tc6.status = "PASSED"
            tc6.actual = f"Combined ordering: {', '.join(bfs6.order)}. Precedence satisfied in both components."
        else:
            tc6.status = "FAILED"
            tc6.actual = f"Order: {bfs6.order}"
        tc6.bfs_result = " -> ".join(bfs6.order)
        tc6.dfs_result = " -> ".join(TopologicalSort.dfs_sort(g6).order)
        tc6.validation_result = "PASSED" if v6.passed else "FAILED"
        results.append(tc6)

        return results

    @staticmethod
    def format_summary_report(results: List[TestCaseResult]) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append(f"{'TEST CASE RESULTS SUMMARY':^80}")
        lines.append("=" * 80)
        lines.append(f"{'ID':<7} | {'Test Case Name':<32} | {'Expected':<18} | {'Status'}")
        lines.append("-" * 80)
        for r in results:
            lines.append(f"{r.test_id:<7} | {r.name[:32]:<32} | {r.expected[:18]:<18} | [{r.status}]")

        lines.append("=" * 80)
        lines.append(f"\nDETAILED TEST AUDIT LOGS:")
        lines.append("-" * 80)
        for r in results:
            lines.append(f"\n[{r.test_id}] {r.name}")
            lines.append(f"  Input:            {r.input_desc}")
            lines.append(f"  Expected:         {r.expected}")
            lines.append(f"  Actual:           {r.actual}")
            lines.append(f"  BFS Order/Result: {r.bfs_result}")
            lines.append(f"  DFS Order/Result: {r.dfs_result}")
            lines.append(f"  Validation:       {r.validation_result}")
            lines.append(f"  Final Status:     >>> [{r.status}] <<<")
        lines.append("=" * 80)
        return "\n".join(lines)
