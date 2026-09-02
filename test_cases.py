"""
Automated Test Suite for University Student Course Enrollment Portal.
Verifies all 10 academic test scenarios defined in Section 34.
"""

import os
import sys
import unittest

import database
from graph import CourseGraph
from prerequisites import check_prerequisites, get_course_status
from enrollment import enroll_student_in_course, drop_course_enrollment
from models import CourseStatus


class TestUniversityCoursePortal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_database()
        cls.db_path = database.DB_PATH

    def test_tc01_zero_prerequisites_eligible(self):
        """TC-1: Course with zero prerequisites -> Must be ELIGIBLE / AVAILABLE."""
        # STU010 is Sem 2 CSE student
        # CS100 or MA101 or EN101 have 0 prerequisites
        course = database.get_course_by_code("EV101")  # Environmental Science has 0 prereqs
        self.assertIsNotNone(course)
        check = check_prerequisites("STU010", course["course_id"])
        self.assertTrue(check["eligible"], "Course with 0 prerequisites must be eligible.")
        self.assertEqual(len(check["required_prereqs"]), 0)

    def test_tc02_one_prerequisite_completed_eligible(self):
        """TC-2: Course with 1 prerequisite completed -> Must be ELIGIBLE."""
        # STU001 (Rahul Kumar) has completed CS100.
        # CS101 requires CS100. Since CS100 is completed, CS101 must be eligible.
        course = database.get_course_by_code("CS101")
        self.assertIsNotNone(course)
        check = check_prerequisites("STU001", course["course_id"])
        self.assertTrue(check["eligible"], "Course with single completed prerequisite must be eligible.")

    def test_tc03_one_prerequisite_incomplete_blocked(self):
        """TC-3: Course with 1 prerequisite incomplete -> Must be BLOCKED."""
        # STU010 (Pooja Reddy) has NOT completed CS104 (Data Structures).
        # CS201 (Algorithms) requires CS104. Thus CS201 must be blocked for STU010.
        course = database.get_course_by_code("CS201")
        self.assertIsNotNone(course)
        check = check_prerequisites("STU010", course["course_id"])
        self.assertFalse(check["eligible"], "Course with incomplete prerequisite must be blocked.")
        self.assertTrue(len(check["missing_prereqs"]) > 0)

    def test_tc04_two_prerequisites_both_completed_eligible(self):
        """TC-4: Course with two prerequisites and both completed -> Must be ELIGIBLE."""
        # CS202 (Operating Systems) requires CS104 (Data Structures) and CS106 (Computer Org).
        # STU001 has completed both CS104 and CS106!
        course = database.get_course_by_code("CS202")
        self.assertIsNotNone(course)
        check = check_prerequisites("STU001", course["course_id"])
        self.assertTrue(check["eligible"], "Course with all 2 prerequisites completed must be eligible.")
        self.assertEqual(len(check["missing_prereqs"]), 0)

    def test_tc05_two_prerequisites_one_incomplete_blocked(self):
        """TC-5: Course with two prerequisites and one incomplete -> Must be BLOCKED."""
        # STU004 (Sneha Patel - IT) has completed CS100 and CS101, but NOT CS105 (DBMS).
        # IT201 (Full Stack Web Dev) requires IT101 and CS105.
        # Since CS105 is not completed, IT201 must be blocked!
        course = database.get_course_by_code("IT201")
        self.assertIsNotNone(course)
        check = check_prerequisites("STU004", course["course_id"])
        self.assertFalse(check["eligible"], "Course with partially incomplete prerequisites must be blocked.")

    def test_tc06_three_or_more_prerequisites_all_checked(self):
        """TC-6: Course with three or more prerequisites -> All must be checked."""
        # AI301 (Machine Learning) requires:
        # 1. AI101 (Python)
        # 2. CS104 (Data Structures)
        # 3. MA202 (Probability)
        # 4. MA204 (Linear Algebra)
        course = database.get_course_by_code("AI301")
        self.assertIsNotNone(course)
        prereqs = database.get_prerequisites_for_course(course["course_id"])
        self.assertGreaterEqual(len(prereqs), 3, "AI301 must have at least 3 prerequisites.")

        # STU001 has NOT completed AI101, MA202, MA204.
        check_stu1 = check_prerequisites("STU001", course["course_id"])
        self.assertFalse(check_stu1["eligible"], "STU001 must be blocked from AI301.")
        self.assertGreaterEqual(len(check_stu1["missing_prereqs"]), 3)

        # STU002 (Priya Sharma - AI&DS Sem 6) HAS completed all 4 foundational courses!
        # Thus STU002 satisfied all 4 prerequisites!
        completed_ids_stu2 = database.get_student_completed_course_ids("STU002")
        prereq_ids = {p["course_id"] for p in prereqs}
        self.assertTrue(prereq_ids.issubset(completed_ids_stu2), "STU002 completed all prerequisites for AI301.")

    def test_tc07_duplicate_enrollment_rejected(self):
        """TC-7: Duplicate enrollment of same student in same course -> Must be rejected."""
        # STU001 is already enrolled in CS105.
        course = database.get_course_by_code("CS105")
        self.assertIsNotNone(course)
        success, msg = enroll_student_in_course("STU001", course["course_id"])
        self.assertFalse(success, "Duplicate enrollment must be strictly rejected.")
        self.assertIn("Duplicate Enrollment", msg)

    def test_tc08_cycle_detection(self):
        """TC-8: Cycle detection on artificial cyclic graph -> Caught by BFS and DFS."""
        demo_g = CourseGraph.create_demo_cycle_graph()
        has_c_bfs, nodes, _ = demo_g.detect_cycle_bfs()
        has_c_dfs, path, _ = demo_g.detect_cycle_dfs()

        self.assertTrue(has_c_bfs, "Kahn BFS must detect prerequisite cycle.")
        self.assertTrue(has_c_dfs, "DFS 3-state must detect back-edge cycle.")
        self.assertIsNotNone(path, "DFS must reconstruct cycle path.")

    def test_tc09_normal_dag_valid_ordering(self):
        """TC-9: Normal academic curriculum DAG -> Must generate valid topological ordering."""
        g = CourseGraph.load_from_database(self.db_path)
        success, order, _, _ = g.bfs_topological_sort()
        self.assertTrue(success, "Curriculum graph must be a valid DAG.")
        self.assertEqual(len(order), len(g.adj_list), "Topological order must include all courses.")

        is_valid, violations = g.validate_topological_order(order)
        self.assertTrue(is_valid, f"Topological order must satisfy precedence: {violations}")

    def test_tc10_student_department_filtering(self):
        """TC-10: Student department course filtering -> Shows only relevant department & common courses."""
        cse_courses = database.get_courses_by_department("CSE", include_common=True)
        cse_depts = {c["department"] for c in cse_courses}
        # Should contain CSE and Common subjects
        self.assertIn("CSE", cse_depts)
        self.assertNotIn("Civil Engineering", cse_depts, "CSE view should not include Civil courses.")
        self.assertNotIn("Mechanical Engineering", cse_depts, "CSE view should not include Mech courses.")

        ece_courses = database.get_courses_by_department("ECE", include_common=True)
        ece_depts = {c["department"] for c in ece_courses}
        self.assertIn("ECE", ece_depts)
        self.assertNotIn("Cyber Security", ece_depts, "ECE view should not include Cyber Security courses.")


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUniversityCoursePortal)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
