"""
University Course Prerequisite Management System package.
Course: CSA03 – Data Structures – Slot D
Outcome: CO5 – Develop robust graph-based solutions for real-world applications.
SDG: SDG 4 & SDG 9
"""

from src.course import Course
from src.course_graph import CourseGraph
from src.topological_sort import TopologicalSort
from src.cycle_detector import CycleDetector
from src.validator import OrderValidator
from src.test_suite import TestSuite
from src.database import DatabaseManager

__all__ = [
    "Course",
    "CourseGraph",
    "TopologicalSort",
    "CycleDetector",
    "OrderValidator",
    "TestSuite",
    "DatabaseManager"
]
