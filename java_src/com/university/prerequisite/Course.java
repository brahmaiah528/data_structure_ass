package com.university.prerequisite;

import java.util.Objects;

/**
 * Represents an academic course within the University Course Prerequisite Management System.
 * Encapsulates course code, title, credit hours, and academic department.
 *
 * Course: CSA03 – Data Structures – Slot D
 * Outcome: CO5 – Develop robust graph-based solutions for real-world applications.
 * SDG: SDG 4 & SDG 9
 */
public class Course implements Comparable<Course> {
    private final String code;
    private final String title;
    private final int credits;
    private final String department;

    public Course(String code, String title) {
        this(code, title, 3, deriveDepartment(code));
    }

    public Course(String code, String title, int credits, String department) {
        if (code == null || code.trim().isEmpty()) {
            throw new IllegalArgumentException("Course code cannot be null or empty.");
        }
        if (title == null || title.trim().isEmpty()) {
            throw new IllegalArgumentException("Course title cannot be null or empty.");
        }
        this.code = code.trim().toUpperCase();
        this.title = title.trim();
        this.credits = Math.max(1, credits);
        this.department = (department == null || department.trim().isEmpty()) 
                ? deriveDepartment(this.code) 
                : department.trim();
    }

    private static String deriveDepartment(String code) {
        String clean = code.trim().toUpperCase();
        if (clean.startsWith("CS")) return "Computer Science & Engineering";
        if (clean.startsWith("IT")) return "Information Technology";
        if (clean.startsWith("MA")) return "Mathematics";
        if (clean.startsWith("EC")) return "Electronics & Communication";
        return "General Academic";
    }

    public String getCode() { return code; }
    public String getTitle() { return title; }
    public int getCredits() { return credits; }
    public String getDepartment() { return department; }

    @Override
    public String toString() {
        return code + " – " + title;
    }

    public String toDetailedString() {
        return String.format("%s – %s (%d Credits | %s)", code, title, credits, department);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Course course = (Course) o;
        return code.equalsIgnoreCase(course.code);
    }

    @Override
    public int hashCode() {
        return Objects.hash(code.toUpperCase());
    }

    @Override
    public int compareTo(Course other) {
        return this.code.compareToIgnoreCase(other.code);
    }
}
