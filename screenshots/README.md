# Execution Output & Screenshot Records

This directory contains the documented outputs corresponding to the 8 mandatory screenshot requirements for academic evaluation.

---

### Screenshot 1: Main Application Window
- **Interface:** Desktop Tkinter Application / Localhost Web Dashboard (`http://localhost:8000`)
- **State:** Application launched with curriculum metrics, control panels, and loaded 12-course sample dataset.
- **Console Log:**
```
======================================================================
LOADED REALISTIC SAMPLE UNIVERSITY DATASET (12 COURSES - DAG)
======================================================================
Total Courses Registered: 12
Total Prerequisite Edges: 12
----------------------------------------------------------------------
Code     | Credits | Department                       | Title
---------------------------------------------------------------------------
CS101    | 4       | Computer Science & Engineering   | Programming Fundamentals
CS102    | 4       | Computer Science & Engineering   | Object Oriented Programming
CS103    | 4       | Computer Science & Engineering   | Data Structures
CS104    | 3       | Computer Science & Engineering   | Discrete Mathematics
CS105    | 3       | Computer Science & Engineering   | Database Management Systems
CS106    | 3       | Computer Science & Engineering   | Computer Organization
CS201    | 4       | Computer Science & Engineering   | Algorithms
CS202    | 4       | Computer Science & Engineering   | Operating Systems
CS203    | 3       | Computer Science & Engineering   | Computer Networks
CS204    | 3       | Computer Science & Engineering   | Software Engineering
CS301    | 4       | Computer Science & Engineering   | Artificial Intelligence
CS302    | 4       | Computer Science & Engineering   | Machine Learning
```

---

### Screenshot 2: Course / Prerequisite Graph Representation
- **State:** Adjacency List (Out-edges) and Prerequisite Requirements (In-edges).
- **Console Log:**
```
======================================================================
UNIVERSITY CURRICULUM GRAPH TOPOLOGY & ADJACENCY REPRESENTATION
======================================================================
Total Courses (Vertices |V|): 12
Total Prerequisite Edges (|E|): 12
----------------------------------------------------------------------

[A] ADJACENCY LIST (Out-edges: Course -> [Dependent Courses]):
CS101 (Programming Fundamentals) -> [CS102, CS103]
CS102 (Object Oriented Programming) -> [CS204]
CS103 (Data Structures) -> [CS201, CS202, CS203, CS105]
CS104 (Discrete Mathematics) -> [CS103]
CS105 (Database Management Systems) -> [None (Terminal Course)]
CS106 (Computer Organization) -> [CS202]
CS201 (Algorithms) -> [CS301, CS302]
CS202 (Operating Systems) -> [None (Terminal Course)]
CS203 (Computer Networks) -> [None (Terminal Course)]
CS204 (Software Engineering) -> [None (Terminal Course)]
CS301 (Artificial Intelligence) -> [CS302]
CS302 (Machine Learning) -> [None (Terminal Course)]

[B] PREREQUISITE MATRIX (In-edges: Course <- [Required Prerequisites]):
CS101 requires: [None (Entry-level course)]
CS102 requires: [CS101]
CS103 requires: [CS101, CS104]
CS104 requires: [None (Entry-level course)]
CS105 requires: [CS103]
CS106 requires: [None (Entry-level course)]
CS201 requires: [CS103]
CS202 requires: [CS106, CS103]
CS203 requires: [CS103]
CS204 requires: [CS102]
CS301 requires: [CS201]
CS302 requires: [CS201, CS301]
```

---

### Screenshot 3: BFS / Kahn's Topological Sort
- **State:** Initial in-degrees, queue processing sequence, and final course ordering.
- **Console Log:**
```
======================================================================
BFS / KAHN'S ALGORITHM TOPOLOGICAL SORT RESULT
======================================================================

[1] INITIAL INDEGREES (Number of Direct Prerequisites):
-------------------------------------------------------
  CS101    = 0   (Programming Fundamentals)
  CS102    = 1   (Object Oriented Programming)
  CS103    = 2   (Data Structures)
  CS104    = 0   (Discrete Mathematics)
  CS105    = 1   (Database Management Systems)
  CS106    = 0   (Computer Organization)
  CS201    = 1   (Algorithms)
  CS202    = 2   (Operating Systems)
  CS203    = 1   (Computer Networks)
  CS204    = 1   (Software Engineering)
  CS301    = 1   (Artificial Intelligence)
  CS302    = 2   (Machine Learning)

[2] STEP-BY-STEP EXECUTION TRACE:
-------------------------------------------------------
  Step  1: Initialized queue with courses having In-Degree 0: [CS101, CS104, CS106]
  Step  2: Dequeued 'CS101' -> Decremented dependents: CS102 (in-degree -> 0, ENQUEUED), CS103 (in-degree -> 1)
  Step  3: Dequeued 'CS104' -> Decremented dependents: CS103 (in-degree -> 0, ENQUEUED)
  Step  4: Dequeued 'CS106' -> Decremented dependents: CS202 (in-degree -> 1)
  Step  5: Dequeued 'CS102' -> Decremented dependents: CS204 (in-degree -> 0, ENQUEUED)
  Step  6: Dequeued 'CS103' -> Decremented dependents: CS201 (0, ENQ), CS202 (0, ENQ), CS203 (0, ENQ), CS105 (0, ENQ)
  Step  7: Dequeued 'CS204' -> Decremented dependents: No outgoing dependencies
  Step  8: Dequeued 'CS201' -> Decremented dependents: CS301 (0, ENQ), CS302 (in-degree -> 1)
  Step  9: Dequeued 'CS202' -> Decremented dependents: No outgoing dependencies
  Step 10: Dequeued 'CS203' -> Decremented dependents: No outgoing dependencies
  Step 11: Dequeued 'CS105' -> Decremented dependents: No outgoing dependencies
  Step 12: Dequeued 'CS301' -> Decremented dependents: CS302 (in-degree -> 0, ENQUEUED)
  Step 13: Dequeued 'CS302' -> Decremented dependents: No outgoing dependencies -> Current Queue: [] (Empty)

[3] CYCLE STATUS & VERDICT:
-------------------------------------------------------
  STATUS: NO CYCLE DETECTED (Valid Directed Acyclic Graph - DAG)

[4] FINAL COURSE-TAKING ORDER:
-------------------------------------------------------
   1. CS101 – Programming Fundamentals (4 Credits)
   2. CS104 – Discrete Mathematics (3 Credits)
   3. CS106 – Computer Organization (3 Credits)
   4. CS102 – Object Oriented Programming (4 Credits)
   5. CS103 – Data Structures (4 Credits)
   6. CS204 – Software Engineering (3 Credits)
   7. CS201 – Algorithms (4 Credits)
   8. CS202 – Operating Systems (4 Credits)
   9. CS203 – Computer Networks (3 Credits)
  10. CS105 – Database Management Systems (3 Credits)
  11. CS301 – Artificial Intelligence (4 Credits)
  12. CS302 – Machine Learning (4 Credits)
```

---

### Screenshot 4: DFS Topological Sort
- **State:** 3-state coloring traversal (`UNVISITED`, `VISITING`, `VISITED`), call stack, finish stack, and reversed ordering.
- **Console Log:**
```
======================================================================
DFS TOPOLOGICAL SORT RESULT
======================================================================
STATUS: NO CYCLE DETECTED (Valid Directed Acyclic Graph - DAG)

FINAL COURSE-TAKING ORDER:
   1. CS106 – Computer Organization (3 Credits)
   2. CS104 – Discrete Mathematics (3 Credits)
   3. CS101 – Programming Fundamentals (4 Credits)
   4. CS103 – Data Structures (4 Credits)
   5. CS105 – Database Management Systems (3 Credits)
   6. CS203 – Computer Networks (3 Credits)
   7. CS202 – Operating Systems (4 Credits)
   8. CS201 – Algorithms (4 Credits)
   9. CS301 – Artificial Intelligence (4 Credits)
  10. CS302 – Machine Learning (4 Credits)
  11. CS102 – Object Oriented Programming (4 Credits)
  12. CS204 – Software Engineering (3 Credits)

Total Courses Ordered: 12 of 12
```

---

### Screenshot 5: BFS Cycle Detection
- **State:** In-degree reduction exhaustion with unvisited courses.
- **Console Log:**
```
======================================================================
CYCLE DETECTION REPORT – [BFS / KAHN'S IN-DEGREE REDUCTION]
======================================================================
STATUS: [CYCLE DETECTED!]

[1] CIRCULAR DEPENDENCY TRACE:
  Cycle Chain: CS101 -> CS102 -> CS103 -> CS201 -> CS101
  Affected Courses: CS101, CS102, CS103, CS201, CS202, CS301

[2] ALGORITHM DIAGNOSIS:
  Kahn's algorithm terminated with queue exhaustion after ordering only 0 of 6 courses.
  The remaining 6 courses have remaining in-degrees > 0 due to circular prerequisite mutual dependencies.
```

---

### Screenshot 6: DFS Cycle Detection
- **State:** Back-edge detection during active recursion stack traversal.
- **Console Log:**
```
======================================================================
CYCLE DETECTION REPORT – [DFS 3-STATE RECURSION STACK]
======================================================================
STATUS: [CYCLE DETECTED!]

[1] CIRCULAR DEPENDENCY TRACE:
  Cycle Chain: CS101 -> CS102 -> CS103 -> CS201 -> CS101
  Affected Courses: CS101, CS102, CS103, CS201

[2] ALGORITHM DIAGNOSIS:
  DFS encountered a back-edge pointing to ancestor course 'CS101'
  which was already present in the active recursion call stack.
  Exact circular path: CS101 -> CS102 -> CS103 -> CS201 -> CS101
```

---

### Screenshot 7: Cycle Warning & Real-World Interpretation
- **State:** Administrative warning displayed to registrar and students.
- **Console Log:**
```
======================================================================
REAL-WORLD UNIVERSITY COURSE REGISTRATION INTERPRETATION
======================================================================
"Course registration is impossible for the affected dependency chain
 because each course requires another course that cannot be completed first."

Institutional Consequences:
* Student Enrollment Deadlock: Students attempting to register for any course
  in this loop are blocked by registration validation rules.
* Degree Audit Failure: Automated degree progression systems encounter an
  unresolvable dependency loop, preventing graduation clearance.
* Administrative Intervention: Academic advisors and curriculum committees
  must review the course catalogue and eliminate the circular edge.
* Automated System Rejection: The university registration portal must
  immediately reject this curriculum catalog configuration.
```

---

### Screenshot 8: Test Case Results & Formal Precedence Validation
- **State:** All 6 academic test cases evaluated and passed with 100% success rate.
- **Console Log:**
```
================================================================================
                           TEST CASE RESULTS SUMMARY                            
================================================================================
ID      | Test Case Name                   | Expected           | Status
--------------------------------------------------------------------------------
TC-01   | Normal DAG (12 University Course | Valid topological  | [PASSED]
TC-02   | Simple Cycle (Circular Dependenc | Cycle detected by  | [PASSED]
TC-03   | Multiple Independent Courses     | All 4 courses incl | [PASSED]
TC-04   | Course with Multiple Prerequisit | CS103 appears in t | [PASSED]
TC-05   | Single Course with No Prerequisi | Course appears imm | [PASSED]
TC-06   | Disconnected Graph (Multi-track  | All vertices from  | [PASSED]
================================================================================

Topological Order Formal Precedence Validation:
Total Prerequisite Edges Audited: 12
Edges Satisfying Precedence:       12
Precedence Violations Detected:    0
VERDICT: >>> Topological Order Validation: PASSED <<<
```
