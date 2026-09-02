# University Student Course Enrollment Portal Using Prerequisite Graph and Topological Sort

[![Streamlit](https://img.shields.io/badge/Streamlit-1.60.0-FF4B4B.svg)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%203-003B57.svg)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-3.0.2-150458.svg)](https://pandas.pydata.org/)
[![SDG 4](https://img.shields.io/badge/SDG%204-Quality%20Education-C5192D.svg)](https://sdgs.un.org/goals/goal4)
[![SDG 9](https://img.shields.io/badge/SDG%209-Industry%2C%20Innovation%20%26%20Infrastructure-F36E24.svg)](https://sdgs.un.org/goals/goal9)

A comprehensive, database-driven, enterprise-grade university course registration portal built with **Python 3.13**, **Streamlit**, and **SQLite 3**. The application models academic course requirements as a **Directed Graph** and leverages **Kahn's Algorithm (BFS)**, **3-State DFS Topological Sorting**, and **Dual-Engine Cycle Detection** to ensure students complete prerequisite courses in valid sequential order.

---

## Table of Contents
1. [Project Title & Metadata](#1-project-title--metadata)
2. [Problem Statement](#2-problem-statement)
3. [Objectives](#3-objectives)
4. [Key Features](#4-key-features)
5. [Technologies Used](#5-technologies-used)
6. [Database Design & Schema](#6-database-design--schema)
7. [Graph Representation (Adjacency List)](#7-graph-representation-adjacency-list)
8. [BFS / Kahn's Topological Sort Algorithm](#8-bfs--kahns-topological-sort-algorithm)
9. [DFS Topological Sort (3-State Coloring)](#9-dfs-topological-sort-3-state-coloring)
10. [Dual-Engine Cycle Detection](#10-dual-engine-cycle-detection)
11. [Strict Enrollment Prerequisite Logic](#11-strict-enrollment-prerequisite-logic)
12. [Asymptotic Complexity Analysis](#12-asymptotic-complexity-analysis)
13. [BFS vs. DFS Comparison](#13-bfs-vs-dfs-comparison)
14. [Automated Academic Test Cases (TC-01 to TC-10)](#14-automated-academic-test-cases-tc-01-to-tc-10)
15. [Visual UI & Walkthrough](#15-visual-ui--walkthrough)
16. [Installation & Setup](#16-installation--setup)
17. [How to Run the Application](#17-how-to-run-the-application)
18. [Real-World University Scenario Interpretation](#18-real-world-university-scenario-interpretation)
19. [SDG Mapping (SDG 4 & SDG 9)](#19-sdg-mapping-sdg-4--sdg-9)
20. [Conclusion](#20-conclusion)

---

## 1. Project Title & Metadata

* **Project Title:** University Student Course Enrollment Portal Using Prerequisite Graph and Topological Sort
* **Course:** CSA03 – Data Structures (Slot D)
* **Course Outcome:** CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications.
* **Bloom's Taxonomy Level:** L4 – Analyze
* **Target Audience:** University Registrars, Academic Advisors, and Undergraduate Students
* **GitHub Repository:** [https://github.com/brahmaiah528/data_structure_assign](https://github.com/brahmaiah528/data_structure_assign)

---

## 2. Problem Statement

In contemporary higher education institutions, academic curricula feature hundreds of courses distributed across diverse departments. Foundational subjects provide essential prerequisites for higher-level electives and specialized disciplines. 

However, managing course enrollments manually or through basic relational forms presents severe vulnerabilities:
1. **Academic Prematurity:** Students attempt to enroll in advanced courses (e.g., *Machine Learning* or *Compiler Design*) without possessing foundational mastery in *Data Structures*, *Discrete Mathematics*, or *Probability Theory*.
2. **Circular Prerequisite Deadlocks:** Curriculum designers may inadvertently introduce circular dependencies ($CS101 \to CS102 \to CS104 \to CS201 \to CS101$). In such pathological scenarios, no course in the cycle can ever be completed first, paralyzing graduation pipelines.
3. **Curriculum Clutter:** Displaying all 100+ university courses indiscriminately to students across all engineering branches creates confusion and scheduling errors.

To solve this, an automated, graph-theoretic portal is required that accurately enforces prerequisites, dynamically computes topologically valid course sequences, eliminates circular dependencies, and customizes course discovery per student department.

---

## 3. Objectives

* **Graph Modeling:** Represent academic courses as vertices and prerequisite relationships as directed edges using an efficient Adjacency List.
* **Algorithmic Scheduling:** Implement both Kahn's Algorithm (BFS) and 3-State DFS to compute topologically sorted graduation roadmaps.
* **Deadlock Detection:** Implement dual cycle-detection algorithms to diagnose circular prerequisite deadlocks.
* **Strict Enrollment Enforcement:** Prohibit registration unless ALL prerequisite courses have been completed and verified against official grade records.
* **Curriculum Scale:** Construct and persist a rich database of **112 courses across 9 engineering departments** with multi-tier prerequisite trees.
* **Role-Based Access:** Provide distinct, authenticated workflows for Students and Academic Administrators.

---

## 4. Key Features

* 🔐 **Secure Role-Based Authentication:** Distinct student and admin portals with session persistence.
* 🎓 **112+ Courses Across 9 Departments:** Covers CSE, IT, ECE, EEE, MECH, CIVIL, AI&DS, Cyber Security, and Computer Applications.
* 🔍 **Department-Specific Course Filtering:** Automatically filters course catalogues based on the logged-in student's branch.
* ⚡ **Real-Time Prerequisite Checking:** Instant visual verification displaying satisfied ($\checkmark$) vs. incomplete ($\times$) prerequisites.
* 🚫 **Strict Double-Validation at Backend:** Guarantees enrollment cannot be bypassed from UI manipulation.
* 💡 **Intelligent Course Recommender:** Topologically prioritizes courses that unlock the maximum downstream electives.
* 📈 **Interactive Graph Theory Sandbox:** Run Kahn's BFS queue sort, DFS 3-state sort, back-edge cycle detection, and circular deadlock injection tests.
* 🛡️ **Comprehensive Admin Suite:** Manage students, courses, prerequisite edges, and global enrollment audit trails.

---

## 5. Technologies Used

* **Language:** Python 3.10+ (Tested on Python 3.13)
* **Web Framework:** [Streamlit](https://streamlit.io/) (v1.60.0)
* **Database Engine:** SQLite 3 (`university.db`) with `PRAGMA foreign_keys = ON`
* **Data Processing:** [Pandas](https://pandas.pydata.org/) (v3.0.2)
* **Data Structures:** Adjacency List (`dict` + `list`), FIFO Queue (`collections.deque`), LIFO Stack (`list`), Hash Sets (`set`)
* **Version Control:** Git & GitHub

---

## 6. Database Design & Schema

The system uses an embedded SQLite database (`university.db`) with full relational integrity and foreign key cascading.

```
+-------------------------------------------------------------------------------+
|                            DATABASE SCHEMA ARCHITECTURE                       |
+-------------------------------------------------------------------------------+

 [courses] (112 Records)
  * course_id (PK, INTEGER)
  * course_code (TEXT, UNIQUE)
  * course_name (TEXT)
  * department (TEXT)
  * credits (INTEGER)
  * semester (INTEGER)
  * description (TEXT)
          ^                       ^
          | (FK)                  | (FK)
          |                       |
 [prerequisites] (139 Edges)      |
  * prerequisite_id (PK, INTEGER) |
  * course_id (FK -> courses)     |
  * prerequisite_course_id (FK)---|

 [students] (15 Records)
  * student_id (PK, TEXT)
  * name (TEXT)
  * email (TEXT, UNIQUE)
  * password (TEXT)
  * department (TEXT)
  * semester (INTEGER)
  * year (INTEGER)
  * phone (TEXT)
          ^
          | (FK)
          |
 [completed_courses] (56 Records)
  * completion_id (PK, INTEGER)
  * student_id (FK -> students)
  * course_id (FK -> courses)
  * grade (TEXT)
  * completion_status (TEXT)
  * completed_on (TEXT)

 [enrollments] (Active Registrations)
  * enrollment_id (PK, INTEGER)
  * student_id (FK -> students)
  * course_id (FK -> courses)
  * enrollment_date (TEXT)
  * semester (INTEGER)
  * status (TEXT: 'Enrolled' | 'Completed' | 'Dropped')
```

---

## 7. Graph Representation (Adjacency List)

The curriculum is represented as a Directed Graph $G = (V, E)$:
* **Vertices ($V$):** Each vertex represents an academic course entity.
* **Directed Edges ($E$):** A directed edge $u \to v$ denotes that course $u$ is a required prerequisite for course $v$.

### Adjacency List Implementation:
```python
class CourseGraph:
    def __init__(self):
        # Outgoing edges: u -> [dependents that require u]
        self.adj_list = {}
        # Incoming edges: v -> [prerequisites that v requires]
        self.prereq_list = {}
```

The Adjacency List requires $\Theta(V + E)$ space, conserving $>99\%$ memory compared to an adjacency matrix for sparse academic graphs.

---

## 8. BFS / Kahn's Topological Sort Algorithm

Kahn's algorithm utilizes in-degree calculation and a FIFO queue:
1. **In-Degree Calculation:** Calculate $\text{in-degree}(v) = |\text{prerequisites}(v)|$ for every course.
2. **Queue Initialization:** Enqueue all courses with in-degree 0 (courses with no remaining prerequisites).
3. **Queue Processing:** Dequeue vertex $u$, append $u$ to the topological schedule, and decrement in-degrees for all neighbors $v \in \text{Adj}[u]$.
4. **Eligibility Trigger:** When $\text{in-degree}(v)$ reaches 0, enqueue $v$.
5. **Cycle Detection:** If total ordered courses $< |V|$, a circular prerequisite dependency exists.

---

## 9. DFS Topological Sort (3-State Coloring)

The DFS approach implements 3-State Vertex Coloring to detect back-edges and compute course schedules:
* **State 0 (`UNVISITED`):** Vertex has not yet been encountered.
* **State 1 (`VISITING`):** Vertex is currently on the active recursion call stack.
* **State 2 (`VISITED`):** Vertex and all its descendant dependencies have been fully explored.

When exploring edge $u \to v$:
* If state of $v$ is `VISITING`: A **back-edge** is detected, confirming a circular dependency.
* Upon finishing exploration of $u$, $u$ is pushed onto a finish stack.
* Reversing the finish stack yields a valid topological order.

---

## 10. Dual-Engine Cycle Detection

The portal incorporates two independent cycle detection engines:
1. **BFS Starvation Engine:** Detects cycles when courses remain locked with in-degrees $> 0$ after queue exhaustion.
2. **DFS Back-Edge Engine:** Detects cycles during depth-first traversal and reconstructs the exact circular dependency path (e.g., $CS101 \to CS102 \to CS104 \to CS201 \to CS101$).

---

## 11. Strict Enrollment Prerequisite Logic

The portal enforces the following core business rule:
> **A student CANNOT enroll in a course unless ALL required prerequisites have been successfully completed.**

```
Student selects course B
         │
         ▼
Retrieve all prerequisites for B
         │
         ▼
Retrieve all completed courses for Student
         │
         ▼
Are ALL prerequisites in Student's Completed List?
   ├── YES ──► Allow Enrollment ──► Commit to Database
   └── NO  ──► Block Enrollment ──► Display Missing Prerequisites List
```

---

## 12. Asymptotic Complexity Analysis

| Operation | Time Complexity | Auxiliary Space | Remarks |
| :--- | :---: | :---: | :--- |
| **Graph Construction** | $O(V + E)$ | $\Theta(V + E)$ | Builds adjacency and prerequisite maps |
| **BFS / Kahn's Algorithm** | $O(V + E)$ | $O(V)$ | Queue stores zero-indegree vertices |
| **DFS 3-State Sort** | $O(V + E)$ | $O(V)$ | Recursion stack depth is at most $V$ |
| **BFS Cycle Detection** | $O(V + E)$ | $O(V)$ | Identifies starved vertices |
| **DFS Cycle Detection** | $O(V + E)$ | $O(V)$ | Identifies back-edge cycle loop |
| **Prerequisite Check** | $O(k)$ | $O(k)$ | $k$ = number of prerequisites ($k \ll V$) |
| **Topological Validation** | $O(V + E)$ | $O(V)$ | Verifies $pos(u) < pos(v)$ for all edges |

---

## 13. BFS vs. DFS Comparison

| Comparison Dimension | BFS / Kahn's Algorithm | DFS 3-State Algorithm |
| :--- | :--- | :--- |
| **Core Concept** | In-Degree queue starvation | Depth-first traversal & finish stack |
| **Primary Data Structure** | FIFO Queue (`collections.deque`) | LIFO Stack / System Call Stack |
| **Cycle Detection Principle** | Unprocessed vertices ($count < \|V\|$) | Back-edge to vertex in state `VISITING` |
| **Cycle Path Extraction** | Identifies starved set of nodes | Extracts exact circular loop sequence |
| **Time Complexity** | $O(V + E)$ | $O(V + E)$ |
| **Space Complexity** | $O(V)$ | $O(V)$ |
| **Academic Enrollment Fit** | **Optimal:** In-degree directly models unmet prerequisites | **Complementary:** Ideal for tree tracing |

---

## 14. Automated Academic Test Cases (TC-01 to TC-10)

The project includes an automated test runner (`test_cases.py`) covering all 10 mandated scenarios:

| Test Case | Scenario Description | Expected Outcome | Result |
| :---: | :--- | :--- | :---: |
| **TC-01** | Course with zero prerequisites (e.g. `EV101`) | Eligible / Immediately Available | **PASS** |
| **TC-02** | Course with 1 prerequisite completed (`CS100` completed $\to$ `CS101`) | Eligible for Enrollment | **PASS** |
| **TC-03** | Course with 1 prerequisite incomplete (`CS104` missing $\to$ `CS201`) | Enrollment Blocked | **PASS** |
| **TC-04** | Course with 2 prerequisites, both completed (`CS104` & `CS106` $\to$ `CS202`) | Eligible for Enrollment | **PASS** |
| **TC-05** | Course with 2 prerequisites, 1 incomplete (`CS105` missing $\to$ `IT201`) | Enrollment Blocked | **PASS** |
| **TC-06** | Course with 4 prerequisites (`AI301` requires 4 subjects) | All 4 checked; blocked if any missing | **PASS** |
| **TC-07** | Duplicate enrollment of same student in same course | Strictly Rejected | **PASS** |
| **TC-08** | Injected circular prerequisite loop | Detected by both BFS and DFS | **PASS** |
| **TC-09** | Full university curriculum graph | Valid DAG; Topological Order Validated | **PASS** |
| **TC-10** | Department course isolation | Only branch & common courses visible | **PASS** |

To run the automated test suite:
```bash
python test_cases.py
```

---

## 15. Visual UI & Walkthrough

The application features responsive Streamlit layouts:
* **Student Dashboard:** Welcome banner, academic metrics, and active enrollments.
* **Course Catalogue:** Filterable data table with expandable prerequisite breakdowns.
* **Enrollment Page:** Dynamic verification checklist with instant enrollment confirmation.
* **Graph Diagnostics:** Interactive algorithm logs and cycle injection sandbox.
* **Admin Control Center:** Multi-tab interface for curriculum, student, and prerequisite management.

---

## 16. Installation & Setup

### Prerequisites
* Python 3.10 or higher
* Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/brahmaiah528/data_structure_assign.git
cd data_structure_assign
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 17. How to Run the Application

### Option 1: Launch the Streamlit Portal (Recommended)
```bash
streamlit run app.py
```
The application will launch automatically at: `http://localhost:8501`

### Option 2: Run Automated Test Cases
```bash
python test_cases.py
```

### Demo Credentials:
* **Student 1 (CSE):** `STU001` / `student123` (Rahul Kumar)
* **Student 2 (AI&DS):** `STU002` / `student123` (Priya Sharma)
* **Administrator:** `admin` / `admin123`

---

## 18. Real-World University Scenario Interpretation

In an academic institution, prerequisite circularities represent catastrophic curriculum design faults. If Course A requires Course B, Course B requires Course C, and Course C requires Course A:
1. No student can complete the foundational preparation needed to qualify for any course in the loop.
2. Degree audit algorithms report impossible dependencies.
3. Students are blocked from graduating on schedule.

Automating curriculum validation with topological sorting and cycle detection safeguards university operational continuity and academic integrity.

---

## 19. SDG Mapping (SDG 4 & SDG 9)

* **SDG 4: Quality Education:** Enforces rigorous pedagogical progressions, ensuring students acquire foundational competencies before encountering advanced topics.
* **SDG 9: Industry, Innovation and Infrastructure:** Delivers reliable, resilient digital infrastructure that automates academic scheduling and eliminates administrative bottlenecks.

---

## 20. Conclusion

The **University Student Course Enrollment Portal** provides a complete, mathematically verified, and database-backed solution for academic curriculum management. By uniting Directed Graph representations, Kahn's algorithm, 3-state DFS traversal, and strict prerequisite enforcement, the portal proves the direct real-world utility of fundamental Data Structures in modern educational systems.
