"""
Data models and enumerations for the University Student Course Enrollment Portal.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class CourseStatus(Enum):
    AVAILABLE = "AVAILABLE"      # No prerequisites required; immediately open
    ELIGIBLE = "ELIGIBLE"        # Prerequisites required and ALL successfully completed
    BLOCKED = "BLOCKED"          # One or more prerequisites missing/incomplete
    COMPLETED = "COMPLETED"      # Course already completed by the student
    ENROLLED = "ENROLLED"        # Student is currently enrolled in this course


@dataclass
class Course:
    course_id: int
    course_code: str
    course_name: str
    department: str
    credits: int
    semester: int
    description: str


@dataclass
class Student:
    student_id: str
    name: str
    email: str
    password: str
    department: str
    semester: int
    year: int
    phone: str


@dataclass
class Prerequisite:
    prerequisite_id: int
    course_id: int
    prerequisite_course_id: int


@dataclass
class CompletedCourse:
    completion_id: int
    student_id: str
    course_id: int
    grade: str
    completion_status: str
    completed_on: str


@dataclass
class Enrollment:
    enrollment_id: int
    student_id: str
    course_id: int
    enrollment_date: str
    semester: int
    status: str
