"""
Authentication and session management module for University Student Course Enrollment Portal.
Provides student authentication, admin authentication, and Streamlit session state management.
"""

from typing import Optional, Dict, Any, Tuple
import streamlit as st
import database

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def init_session_state() -> None:
    """Initializes authentication variables in Streamlit session_state."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = None  # "student" or "admin"
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = None
    if "student_info" not in st.session_state:
        st.session_state["student_info"] = None


def authenticate_student(student_id: str, password: str, db_path: str = database.DB_PATH) -> Tuple[bool, Optional[str]]:
    """Validates student credentials against the students table in SQLite."""
    student_id = student_id.strip().upper()
    if not student_id or not password:
        return False, "Please enter both Student ID and Password."

    student = database.get_student_by_id(student_id, db_path)
    if not student:
        return False, f"No student account found with ID '{student_id}'."

    if student["password"] != password:
        return False, "Incorrect password. Please try again."

    # Login successful
    st.session_state["authenticated"] = True
    st.session_state["user_role"] = "student"
    st.session_state["user_id"] = student["student_id"]
    st.session_state["user_name"] = student["name"]
    st.session_state["student_info"] = dict(student)
    return True, None


def authenticate_admin(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """Validates administrator credentials."""
    username = username.strip()
    if not username or not password:
        return False, "Please enter both Admin Username and Password."

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state["authenticated"] = True
        st.session_state["user_role"] = "admin"
        st.session_state["user_id"] = "admin"
        st.session_state["user_name"] = "Portal Administrator"
        st.session_state["student_info"] = None
        return True, None
    else:
        return False, "Invalid administrator credentials."


def logout() -> None:
    """Clears authentication session state."""
    st.session_state["authenticated"] = False
    st.session_state["user_role"] = None
    st.session_state["user_id"] = None
    st.session_state["user_name"] = None
    st.session_state["student_info"] = None


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def is_admin() -> bool:
    return is_authenticated() and st.session_state.get("user_role") == "admin"


def is_student() -> bool:
    return is_authenticated() and st.session_state.get("user_role") == "student"


def get_current_user_id() -> Optional[str]:
    return st.session_state.get("user_id")


def get_current_student() -> Optional[Dict[str, Any]]:
    return st.session_state.get("student_info")
