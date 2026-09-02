"""
Course entity module for the University Course Prerequisite Management System.

Course: CSA03 – Data Structures – Slot D
Course Outcome: CO5 – Develop robust graph-based solutions for real-world applications.
SDG Mapping: SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)
"""

from typing import Optional


class Course:
    """
    Represents an academic course in the university curriculum.
    Encapsulates course code, title, credit hours, and department.
    """

    def __init__(self, code: str, title: str, credits: int = 3, department: Optional[str] = None):
        if not code or not code.strip():
            raise ValueError("Course code cannot be empty.")
        if not title or not title.strip():
            raise ValueError("Course title cannot be empty.")

        self.code: str = code.strip().upper()
        self.title: str = title.strip()
        self.credits: int = max(1, credits)
        self.department: str = department.strip() if department and department.strip() else self._derive_department(self.code)

    @staticmethod
    def _derive_department(code: str) -> str:
        clean = code.strip().upper()
        if clean.startswith("CS"):
            return "Computer Science & Engineering"
        if clean.startswith("IT"):
            return "Information Technology"
        if clean.startswith("MA"):
            return "Mathematics"
        if clean.startswith("EC"):
            return "Electronics & Communication"
        if clean.startswith("PHY"):
            return "Physics"
        return "General Academic Studies"

    def to_dict(self) -> dict:
        """Returns dictionary representation for JSON serialization."""
        return {
            "code": self.code,
            "title": self.title,
            "credits": self.credits,
            "department": self.department
        }

    def detailed_str(self) -> str:
        return f"{self.code} – {self.title} ({self.credits} Credits | {self.department})"

    def __str__(self) -> str:
        return f"{self.code} – {self.title}"

    def __repr__(self) -> str:
        return f"Course(code='{self.code}', title='{self.title}', credits={self.credits})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Course):
            return self.code == other.code
        if isinstance(other, str):
            return self.code == other.strip().upper()
        return False

    def __hash__(self) -> int:
        return hash(self.code)

    def __lt__(self, other: "Course") -> bool:
        return self.code < other.code
