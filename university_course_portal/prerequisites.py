"""
Prerequisite validation and course recommendation engine for University Student Course Enrollment Portal.
Enforces the core business rule: A student cannot enroll in a course unless ALL prerequisites are completed.
"""

from typing import Dict, List, Any, Optional
import database
from models import CourseStatus


def check_prerequisites(student_id: str, course_id: int, db_path: str = database.DB_PATH) -> Dict[str, Any]:
    """
    Checks prerequisite completion for a given student and course.
    Returns:
        {
            "eligible": bool,
            "required_prereqs": List[Dict],
            "completed_prereqs": List[Dict],
            "missing_prereqs": List[Dict],
            "message": str
        }
    """
    required_prereqs = database.get_prerequisites_for_course(course_id, db_path)
    completed_ids = database.get_student_completed_course_ids(student_id, db_path)

    completed_list = []
    missing_list = []

    for prereq in required_prereqs:
        p_id = prereq["course_id"]
        prereq_info = {
            "course_id": p_id,
            "course_code": prereq["course_code"],
            "course_name": prereq["course_name"],
            "credits": prereq["credits"],
            "is_completed": p_id in completed_ids
        }
        if p_id in completed_ids:
            completed_list.append(prereq_info)
        else:
            missing_list.append(prereq_info)

    eligible = (len(missing_list) == 0)

    if not required_prereqs:
        message = "✓ No prerequisites required. Course is directly available for enrollment."
    elif eligible:
        message = f"✓ All {len(required_prereqs)} prerequisite(s) successfully completed. Eligible for enrollment."
    else:
        missing_names = ", ".join(f"{m['course_code']} ({m['course_name']})" for m in missing_list)
        message = f"❌ Enrollment Blocked: Incomplete prerequisite(s): {missing_names}"

    return {
        "eligible": eligible,
        "required_prereqs": required_prereqs,
        "completed_prereqs": completed_list,
        "missing_prereqs": missing_list,
        "message": message
    }


def get_course_status(student_id: str, course_id: int, db_path: str = database.DB_PATH) -> CourseStatus:
    """
    Computes the precise academic status of a course for a student:
    - COMPLETED: Student has already passed this course
    - ENROLLED: Student is currently registered in this course
    - AVAILABLE: No prerequisites required
    - ELIGIBLE: All prerequisites satisfied
    - BLOCKED: One or more prerequisites missing
    """
    completed_ids = database.get_student_completed_course_ids(student_id, db_path)
    if course_id in completed_ids:
        return CourseStatus.COMPLETED

    enrolled_ids = database.get_student_enrolled_course_ids(student_id, db_path)
    if course_id in enrolled_ids:
        return CourseStatus.ENROLLED

    check = check_prerequisites(student_id, course_id, db_path)
    if not check["required_prereqs"]:
        return CourseStatus.AVAILABLE
    elif check["eligible"]:
        return CourseStatus.ELIGIBLE
    else:
        return CourseStatus.BLOCKED


def get_recommended_courses(student_id: str, db_path: str = database.DB_PATH) -> List[Dict[str, Any]]:
    """
    Generates an intelligent, topologically sequenced recommendation list for the student.
    Considers:
    1. Student department and current semester.
    2. Completed courses and current enrollments.
    3. Prerequisite clearance.
    4. Downstream unlocked courses count (unlocks highest future electives/core).
    """
    student = database.get_student_by_id(student_id, db_path)
    if not student:
        return []

    dept = student["department"]
    sem = student["semester"]

    all_dept_courses = database.get_courses_by_department(dept, include_common=True, db_path=db_path)
    completed_ids = database.get_student_completed_course_ids(student_id, db_path)
    enrolled_ids = database.get_student_enrolled_course_ids(student_id, db_path)

    recommended = []
    for c in all_dept_courses:
        c_id = c["course_id"]
        # Skip already completed or currently enrolled courses
        if c_id in completed_ids or c_id in enrolled_ids:
            continue

        status = get_course_status(student_id, c_id, db_path)
        if status in (CourseStatus.ELIGIBLE, CourseStatus.AVAILABLE):
            dependents = database.get_dependent_courses(c_id, db_path)
            c_dict = dict(c)
            c_dict["status"] = status.value
            c_dict["downstream_unlocks"] = len(dependents)
            c_dict["unlocked_courses"] = [d["course_code"] for d in dependents]
            # Prioritize courses close to current semester and with high unlock potential
            sem_diff = abs(c["semester"] - sem)
            c_dict["priority_score"] = (10 - sem_diff) * 2 + len(dependents)
            recommended.append(c_dict)

    # Sort by priority score descending, then semester ascending
    recommended.sort(key=lambda x: (-x["priority_score"], x["semester"], x["course_code"]))
    return recommended
