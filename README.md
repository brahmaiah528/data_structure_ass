# University Course Prerequisite Management System Using Topological Sort

[![Course Outcome](https://img.shields.io/badge/Course%20Outcome-CO5%20Graph%20Algorithms-blue.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.13%2B-brightgreen.svg)](#)
[![SDG 4](https://img.shields.io/badge/SDG%204-Quality%20Education-red.svg)](https://sdgs.un.org/goals/goal4)
[![SDG 9](https://img.shields.io/badge/SDG%209-Industry%20%26%20Infrastructure-orange.svg)](https://sdgs.un.org/goals/goal9)
[![License](https://img.shields.io/badge/Academic%20Project-CSA03%20Slot%20D-purple.svg)](#)

> **Course:** CSA03 – Data Structures – Slot D  
> **Course Outcome:** CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications.  
> **SDG Mapping:** SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Objectives](#objectives)
4. [Key Features](#key-features)
5. [Technologies Used](#technologies-used)
6. [Graph Representation](#graph-representation)
7. [Algorithmic Implementation](#algorithmic-implementation)
   - [BFS / Kahn's Algorithm](#bfs--kahns-algorithm)
   - [DFS Topological Sort (3-State Coloring)](#dfs-topological-sort-3-state-coloring)
   - [Dual-Engine Cycle Detection](#dual-engine-cycle-detection)
   - [Topological Order Formal Validation](#topological-order-formal-validation)
8. [Asymptotic Complexity Analysis](#asymptotic-complexity-analysis)
9. [BFS vs. DFS Comparison](#bfs-vs-dfs-comparison)
10. [Test Cases & Results](#test-cases--results)
11. [Sample Execution Outputs](#sample-execution-outputs)
12. [Project Structure](#project-structure)
13. [How to Run](#how-to-run)
    - [Desktop GUI Mode](#desktop-gui-mode)
    - [Localhost Web Server Mode](#localhost-web-server-mode)
    - [Automated Test Suite Mode](#automated-test-suite-mode)
    - [Interactive CLI Mode](#interactive-cli-mode)
14. [GitHub Upload Instructions](#github-upload-instructions)
15. [Real-World Institutional Significance](#real-world-institutional-significance)
16. [Academic Deliverables & Documentation](#academic-deliverables--documentation)
17. [Conclusion](#conclusion)

---

## Project Overview
The **University Course Prerequisite Management System** is a robust, graph-based software application designed to automate academic curriculum planning, resolve prerequisite dependencies, detect circular deadlocks, and generate valid course completion sequences.

Built with clean Object-Oriented principles and zero external dependencies, the system features a **desktop GUI (Tkinter)**, an **interactive Localhost Web Application (`http://localhost:8000`)**, an **interactive CLI**, and an **automated test suite**.

---

## Problem Statement
A modern university offers hundreds of academic courses across diverse degree programmes. Advanced courses enforce prerequisite constraints to guarantee that students master foundational concepts prior to enrollment. 

Representing these dependencies requires a **Directed Graph**:
- Each **vertex** represents an academic course (e.g., `CS101`, `CS102`, `CS103`).
- Each **directed edge** $u \to v$ signifies that course $u$ is a prerequisite for course $v$ ($u$ must be cleared before $v$).
- Example: $\text{CS103 (Data Structures)} \longrightarrow \text{CS201 (Algorithms)} \longrightarrow \text{CS302 (Machine Learning)}$

If an erroneous circular dependency is created (e.g., $A \to B \to C \to A$), no course in the chain can ever be completed first. This project provides automated graph algorithms to resolve and audit academic dependency structures.

---

## Objectives
- Construct an Adjacency List directed graph of academic courses and prerequisite relationships.
- Implement **Kahn's Algorithm (BFS)** with queue transition tracing and in-degree reduction.
- Implement **DFS Topological Sort** using 3-state vertex coloring (`UNVISITED`, `VISITING`, `VISITED`).
- Detect dependency cycles across both BFS and DFS pipelines and isolate the exact circular path.
- Formally validate that for every edge $u \to v$, $\text{position}(u) < \text{position}(v)$.
- Deliver dual-interface accessibility via desktop Tkinter GUI and embedded localhost HTTP web dashboard.

---

## Key Features
- **Pure Standard Library Implementation:** 100% standard Python 3.13 with zero third-party dependencies.
- **Dual User Interfaces:**
  - **Desktop GUI (Tkinter/TTK):** Clean native interface with course input panels, algorithm action buttons, and diagnostic console.
  - **Localhost Web Dashboard (`http://localhost:8000`):** Interactive SVG/Canvas animated graph visualizer, live step simulators, and REST API.
- **Dual Algorithmic Engines:** BFS Kahn's algorithm and DFS 3-state coloring with step-by-step audit logging.
- **Cycle Path Isolation:** Automatically extracts and prints circular dependency loops (e.g., $CS101 \to CS102 \to CS103 \to CS201 \to CS101$).
- **Automated Validation:** Guarantees precedence compliance across 100% of prerequisite edges.
- **Automated Academic Test Suite:** Covers all 6 mandatory academic test scenarios.

---

## Technologies Used
- **Language:** Python 3.13.14 (Object-Oriented Programming)
- **Data Structures:** Adjacency List (Hash Tables + Dynamic Lists), FIFO Queue (`collections.deque`), LIFO Stack, Sets
- **Desktop UI:** Tkinter / TTK
- **Local Web Server:** Built-in `http.server` & `socketserver` (Zero external packages required)
- **Web Frontend:** HTML5, CSS3 Glassmorphism, Vanilla JavaScript Canvas/SVG API

---

## Graph Representation
Curriculum prerequisite networks are **sparse graphs** where $|E| \ll |V|^2$. The system uses an **Adjacency List** representation:
- `courses: dict[str, Course]` — Maps course codes to `Course` objects.
- `adj_list: dict[str, list[str]]` — Outgoing directed edges ($u \to \text{dependents}$).
- `prereq_map: dict[str, list[str]]` — Incoming prerequisite edges ($v \leftarrow \text{prerequisites}$).

### 12-Course Realistic Academic Dataset (DAG)
```
CS101 (Programming Fundamentals)
  ├──> CS102 (Object Oriented Programming) ──> CS204 (Software Engineering)
  └──> CS103 (Data Structures)
         ├──> CS201 (Algorithms) ──┬─> CS301 (Artificial Intelligence) ──> CS302 (Machine Learning)
         │                         └─────────────────────────────────────> CS302
         ├──> CS202 (Operating Systems) <── CS106 (Computer Organization)
         ├──> CS203 (Computer Networks)
         └──> CS105 (Database Management Systems)
CS104 (Discrete Mathematics) ──> CS103
```

---

## Algorithmic Implementation

### BFS / Kahn's Algorithm
```text
1. Compute in-degree for every course vertex.
2. Enqueue all courses having in-degree == 0 into a FIFO Queue.
3. While queue is not empty:
     a. Dequeue course u, append u to topological ordering.
     b. For each dependent neighbor v of u:
          - Decrement in-degree of v by 1.
          - If in-degree of v reaches 0, enqueue v.
4. If processed course count < total courses, flag CYCLE DETECTED.
```

### DFS Topological Sort (3-State Coloring)
```text
State 0: UNVISITED  (Vertex not yet encountered)
State 1: VISITING   (Vertex is in current active recursion stack)
State 2: VISITED    (Vertex and all its descendants are completely explored)

1. For each course u with State 0:
     - Mark State 1, push to recursion stack.
     - For each dependent neighbor v:
          - If State 1: BACK-EDGE DETECTED! Cycle proven.
          - If State 0: Recursively visit v.
     - Mark State 2, push u to finish stack.
2. Reverse finish stack to obtain valid Topological Order.
```

### Dual-Engine Cycle Detection
- **BFS:** Detects cycle when queue empties prematurely with unprocessed courses remaining.
- **DFS:** Detects cycle when an edge encounters an ancestor in state `VISITING`, immediately capturing the cycle path.

### Topological Order Formal Validation
Audits every prerequisite edge $u \to v$ against the generated sequence:
$$\forall (u, v) \in E, \quad \text{position}(u) < \text{position}(v)$$
Outputs: `Topological Order Validation: PASSED`

---

## Asymptotic Complexity Analysis

| Algorithm / Structure | Time Complexity | Auxiliary Space Complexity | Dominant Operations |
| :--- | :---: | :---: | :--- |
| **BFS / Kahn's Algorithm** | $O(V + E)$ | $O(V)$ | In-degree calculation, queue operations |
| **DFS 3-State Traversal** | $O(V + E)$ | $O(V)$ | Recursive tree traversal, stack operations |
| **Order Validator** | $O(V + E)$ | $O(V)$ | Position mapping and edge verification |
| **Adjacency List Storage** | — | $\Theta(V + E)$ | Saves $>99.5\%$ space over $V \times V$ matrix |

---

## BFS vs. DFS Comparison

| Dimension | BFS / Kahn's Algorithm | DFS 3-State Coloring |
| :--- | :--- | :--- |
| **Core Principle** | In-degree depletion & queue starvation | Depth-first search & finish-time stack |
| **Data Structure** | FIFO Queue | LIFO Stack / Recursion Call Stack |
| **Topological Order** | Emitted forward as in-degrees reach 0 | Emitted in reverse post-order |
| **Cycle Detection** | Count comparison (`processed < |V|`) | Back-edge to `VISITING` ancestor |
| **Cycle Path Extraction** | Requires secondary subgraph traversal | Immediate from recursion call stack |
| **Student Progression Metaphor** | **Direct**: Models eligible courses per term | Abstract: Subtree exploration |
| **Stack Overflow Risk** | **None** (Iterative on heap memory) | Present on extremely deep graphs |
| **Institutional Role** | **Primary Registration Engine** | **Secondary Circular Audit Engine** |

---

## Test Cases & Results

All 6 mandatory test scenarios are automated in `src/test_suite.py`:

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
Overall Academic Test Suite Result: ALL TESTS PASSED [100%]
```

---

## Sample Execution Outputs

### Valid Topological Course Sequence (DAG)
```
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

Topological Order Validation: PASSED
```

### Cycle Detection Output (Cyclic Dataset)
```
======================================================================
CYCLE DETECTION REPORT – [DFS 3-STATE RECURSION STACK]
======================================================================
STATUS: [CYCLE DETECTED!]

[1] CIRCULAR DEPENDENCY TRACE:
-------------------------------------------------------
  Cycle Chain: CS101 -> CS102 -> CS103 -> CS201 -> CS101
  Affected Courses: CS101, CS102, CS103, CS201

[2] REAL-WORLD UNIVERSITY COURSE REGISTRATION INTERPRETATION:
-------------------------------------------------------
  "Course registration is impossible for the affected dependency chain
   because each course requires another course that cannot be completed first."
```

---

## Project Structure
```
University-Course-Prerequisite-System/
├── src/
│   ├── __init__.py             # Package initializer
│   ├── course.py               # Course entity with validation & credits
│   ├── course_graph.py         # Directed graph with Adjacency List representation
│   ├── topological_sort.py     # BFS (Kahn's) and DFS 3-state topological sort
│   ├── cycle_detector.py       # Dual-engine cycle detector and path extractor
│   ├── validator.py            # Formal topological order validator
│   ├── test_suite.py           # Automated test suite (TC-01 to TC-06)
│   ├── gui.py                  # Tkinter Desktop GUI application
│   ├── server.py               # Localhost interactive web server (http://localhost:8000)
│   └── main.py                 # Multi-mode unified application entry point
├── docs/
│   ├── pseudocode.md           # Formal pseudocode for all 8 algorithms
│   ├── algorithm-analysis.md   # Complexity, sparse graph analysis & BFS vs DFS
│   ├── one-page-writeup.md     # One-page academic write-up
│   └── academic-report.md      # Full 22-section academic lab report
├── screenshots/                # Application output captures
├── main.py                     # Root execution proxy
├── README.md                   # Complete repository documentation
└── .gitignore                  # Python & IDE ignore rules
```

---

## How to Run

### 1. Run Desktop GUI Mode
Launches the Tkinter Desktop Application:
```bash
python main.py --gui
```

### 2. Run Localhost Web Server Mode
Starts the embedded web server on port 8000:
```bash
python main.py --server
```
Open your browser at: **`http://localhost:8000/`**

### 3. Run Automated Academic Test Suite
Executes all 6 test scenarios and prints the validation audit:
```bash
python main.py --test
```

### 4. Run Interactive CLI Mode
Terminal-based menu for course registration and algorithm execution:
```bash
python main.py --cli
```

### 5. Default Launch
Running with no arguments starts the localhost web server in the background and opens the desktop GUI:
```bash
python main.py
```

---

## GitHub Upload Instructions

To push this repository to GitHub:

```bash
# 1. Initialize git repository
git init

# 2. Add all project files
git add .

# 3. Commit with descriptive message
git commit -m "feat: complete university course prerequisite management system"

# 4. Set remote branch to main
git branch -M main

# 5. Link to your GitHub repository
git remote add origin https://github.com/brahmaiah528/data_structure_assign.git

# 6. Push code to GitHub
git push -u origin main
```

---

## Real-World Institutional Significance

### Connection to United Nations Sustainable Development Goals
- **SDG 4 – Quality Education:**  
  Eliminates prerequisite scheduling deadlocks, optimizes degree progression pathways, reduces time-to-graduation, and prevents enrollment registration deadlocks.
- **SDG 9 – Industry, Innovation and Infrastructure:**  
  Establishes robust, automated educational IT infrastructure, replacing error-prone manual transcript audits with mathematically validated algorithmic solutions.

---

## Academic Deliverables & Documentation
- **Formal Pseudocode:** [docs/pseudocode.md](docs/pseudocode.md)
- **Algorithm Analysis & BFS vs DFS Matrix:** [docs/algorithm-analysis.md](docs/algorithm-analysis.md)
- **One-Page Academic Write-up:** [docs/one-page-writeup.md](docs/one-page-writeup.md)
- **Comprehensive 22-Heading Academic Report:** [docs/academic-report.md](docs/academic-report.md)

---

## Conclusion
The **University Course Prerequisite Management System Using Topological Sort** demonstrates how fundamental graph algorithms (Kahn's BFS and 3-state DFS) solve complex, real-world educational logistical challenges. By combining mathematical correctness, optimal $O(V + E)$ efficiency, and intuitive interfaces, the system fulfills all academic requirements for **CSA03 – Data Structures (Slot D, CO5)**.
