package com.university.prerequisite;

import java.util.*;

/**
 * Directed Graph representing academic courses and prerequisites using an Adjacency List.
 * Edge u -> v means course u is a prerequisite for course v.
 */
public class CourseGraph {
    private final Map<String, Course> courses = new TreeMap<>();
    private final Map<String, List<String>> adjList = new TreeMap<>();
    private final Map<String, List<String>> prereqMap = new TreeMap<>();

    public Course addCourse(String code, String title, int credits) {
        String clean = code.trim().toUpperCase();
        if (courses.containsKey(clean)) {
            throw new IllegalArgumentException("Course '" + clean + "' already exists.");
        }
        Course course = new Course(clean, title, credits, null);
        courses.put(clean, course);
        adjList.put(clean, new ArrayList<>());
        prereqMap.put(clean, new ArrayList<>());
        return course;
    }

    public void addPrerequisite(String prereqCode, String targetCode) {
        String u = prereqCode.trim().toUpperCase();
        String v = targetCode.trim().toUpperCase();
        if (!courses.containsKey(u)) throw new NoSuchElementException("Prerequisite course '" + u + "' does not exist.");
        if (!courses.containsKey(v)) throw new NoSuchElementException("Target course '" + v + "' does not exist.");
        if (u.equals(v)) throw new IllegalArgumentException("Course cannot be a prerequisite of itself ('" + u + "').");
        if (adjList.get(u).contains(v)) throw new IllegalArgumentException("Prerequisite relationship '" + u + " -> " + v + "' already exists.");

        adjList.get(u).add(v);
        prereqMap.get(v).add(u);
    }

    public Course getCourse(String code) {
        return courses.get(code.trim().toUpperCase());
    }

    public Map<String, Course> getCourses() {
        return Collections.unmodifiableMap(courses);
    }

    public Map<String, List<String>> getAdjList() {
        return Collections.unmodifiableMap(adjList);
    }

    public Map<String, List<String>> getPrereqMap() {
        return Collections.unmodifiableMap(prereqMap);
    }

    public int getNumVertices() {
        return courses.size();
    }

    public int getNumEdges() {
        int count = 0;
        for (List<String> list : adjList.values()) count += list.size();
        return count;
    }

    public Map<String, Integer> calculateIndegrees() {
        Map<String, Integer> indegrees = new TreeMap<>();
        for (String c : courses.keySet()) indegrees.put(c, 0);
        for (String u : courses.keySet()) {
            for (String v : adjList.get(u)) {
                indegrees.put(v, indegrees.get(v) + 1);
            }
        }
        return indegrees;
    }

    public void clear() {
        courses.clear();
        adjList.clear();
        prereqMap.clear();
    }

    public void loadSampleDataset() {
        clear();
        addCourse("CS101", "Programming Fundamentals", 4);
        addCourse("CS102", "Object Oriented Programming", 4);
        addCourse("CS103", "Data Structures", 4);
        addCourse("CS104", "Discrete Mathematics", 3);
        addCourse("CS105", "Database Management Systems", 3);
        addCourse("CS106", "Computer Organization", 3);
        addCourse("CS201", "Algorithms", 4);
        addCourse("CS202", "Operating Systems", 4);
        addCourse("CS203", "Computer Networks", 3);
        addCourse("CS204", "Software Engineering", 3);
        addCourse("CS301", "Artificial Intelligence", 4);
        addCourse("CS302", "Machine Learning", 4);

        addPrerequisite("CS101", "CS102");
        addPrerequisite("CS101", "CS103");
        addPrerequisite("CS104", "CS103");
        addPrerequisite("CS103", "CS201");
        addPrerequisite("CS106", "CS202");
        addPrerequisite("CS103", "CS202");
        addPrerequisite("CS103", "CS203");
        addPrerequisite("CS102", "CS204");
        addPrerequisite("CS201", "CS301");
        addPrerequisite("CS201", "CS302");
        addPrerequisite("CS301", "CS302");
        addPrerequisite("CS103", "CS105");
    }

    public void loadCyclicDataset() {
        clear();
        addCourse("CS101", "Programming Fundamentals", 4);
        addCourse("CS102", "Object Oriented Programming", 4);
        addCourse("CS103", "Data Structures", 4);
        addCourse("CS201", "Algorithms", 4);
        addCourse("CS202", "Operating Systems", 3);
        addCourse("CS301", "Artificial Intelligence", 3);

        addPrerequisite("CS101", "CS102");
        addPrerequisite("CS102", "CS103");
        addPrerequisite("CS103", "CS201");
        addPrerequisite("CS201", "CS101"); // Circular dependency!
        addPrerequisite("CS103", "CS202");
        addPrerequisite("CS201", "CS301");
    }
}
