"""
Enrollment management module for University Student Course Enrollment Portal.
Enforces the mandatory business rule:
A student CANNOT enroll in a course unless ALL prerequisites are verified as completed.
"""

from datetime import datetime
from typing import Tuple, Optional
import database
from prerequisites import check_prerequisites, get_course_status
from models import CourseStatus


def enroll_student_in_course(
    student_id: str,
    course_id: int,
    semester: Optional[int] = None,
    db_path: str = database.DB_PATH
) -> Tuple[bool, str]:
    """
    Attempts to enroll a student in a course with strict validation:
    1. Verifies student and course exist.
    2. Checks for prior course completion.
    3. Prevents duplicate active enrollment.
    4. Validates completion of all prerequisite requirements.
    5. Inserts into enrollments table upon success.
    """
    student = database.get_student_by_id(student_id, db_path)
    if not student:
        return False, f"Student record [{student_id}] not found."

    course = database.get_course_by_id(course_id, db_path)
    if not course:
        return False, f"Course ID [{course_id}] not found."

    # Rule 1: Cannot enroll if already completed
    completed_ids = database.get_student_completed_course_ids(student_id, db_path)
    if course_id in completed_ids:
        return False, f"Cannot Enroll: You have already successfully completed {course['course_code']} ({course['course_name']})."

    # Rule 2: Cannot enroll if already actively enrolled
    enrolled_ids = database.get_student_enrolled_course_ids(student_id, db_path)
    if course_id in enrolled_ids:
        return False, f"Duplicate Enrollment Blocked: You are already currently enrolled in {course['course_code']} ({course['course_name']})."

    # Rule 3: STRICT PREREQUISITE VALIDATION AT BACKEND BOUNDARY
    check = check_prerequisites(student_id, course_id, db_path)
    if not check["eligible"]:
        missing_names = ", ".join(f"{m['course_code']} - {m['course_name']}" for m in check["missing_prereqs"])
        return False, f"Enrollment Blocked! Required prerequisite(s) incomplete: {missing_names}"

    # All checks passed: Commit enrollment
    enr_semester = semester if semester is not None else student["semester"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        database.add_enrollment(
            student_id=student_id,
            course_id=course_id,
            semester=enr_semester,
            enrollment_date=now_str,
            status="Enrolled",
            db_path=db_path
        )
        return True, f"✓ Enrollment Successful! You are now enrolled in {course['course_code']} - {course['course_name']} ({course['credits']} Credits)."
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, f"Duplicate Enrollment Blocked: You are already registered or pending approval for this course."
        return False, f"Database error during enrollment: {str(e)}"


def drop_course_enrollment(enrollment_id: int, student_id: str, db_path: str = database.DB_PATH) -> Tuple[bool, str]:
    """Drops an active course enrollment for the student."""
    enrollments = database.get_student_enrollments(student_id, db_path)
    target = None
    for e in enrollments:
        if e["enrollment_id"] == enrollment_id:
            target = e
            break

    if not target:
        return False, "Enrollment record not found or does not belong to this student."

    try:
        database.drop_enrollment(enrollment_id, db_path)
        return True, f"Successfully dropped course: {target['course_code']} - {target['course_name']}."
    except Exception as e:
        return False, f"Error dropping course: {str(e)}"
