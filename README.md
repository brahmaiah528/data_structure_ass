# University Course Prerequisite Management System (Pure C Implementation)

[![Language](https://img.shields.io/badge/Language-C99%20%2F%20C11-00599C.svg)](https://en.wikipedia.org/wiki/C_(programming_language))
[![Standard](https://img.shields.io/badge/Standard-ANSI%20C%20%2F%20POSIX-grey.svg)](https://en.wikipedia.org/wiki/C99)
[![Compiler](https://img.shields.io/badge/Compiler-GCC%20%7C%20Clang%20%7C%20MSVC-brightgreen.svg)](https://gcc.gnu.org/)
[![License](https://img.shields.io/badge/License-Academic%20Evaluation-blue.svg)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing%20(100%25)-success.svg)]()
[![SDG 4](https://img.shields.io/badge/SDG%204-Quality%20Education-C5192D.svg)](https://sdgs.un.org/goals/goal4)
[![SDG 9](https://img.shields.io/badge/SDG%209-Industry%2C%20Innovation%20%26%20Infrastructure-F36E24.svg)](https://sdgs.un.org/goals/goal9)

A high-performance, robust, standalone **C implementation** of a university academic curriculum prerequisite management system. The application models university course requirements as a **Directed Graph $G = (V, E)$** using an efficient **Adjacency List** representation. It implements **Kahn's Algorithm (BFS)**, **3-State DFS Topological Sorting**, **Dual-Engine Cycle Detection**, and a **Formal Precedence Constraint Validation Engine** ($pos(u) < pos(v)$).

---

## Academic Metadata

* **Department:** Department of Computer Science and Engineering (CSE AI)
* **Course Code & Name:** CSA03 – Data Structures (Slot D)
* **Student Name:** Jampala Brahmaiah
* **Register Number:** 192472286
* **Course Outcome:** CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications.
* **Bloom's Taxonomy Level:** L4 – Analyze
* **Assignment Title:** Design a graph representation of this prerequisite system and use Topological Sort to generate a valid course-taking order. Your design must also detect whether the prerequisite system contains a cycle. Analyze what the existence of a cycle means in the real-world university scenario and compare a BFS-based and DFS-based approach for solving the problem.
* **SDG Alignment:** SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)
* **GitHub Repository:** [https://github.com/brahmaiah528/data_structure_assign](https://github.com/brahmaiah528/data_structure_ass)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Graph Formulation & Data Structures](#graph-formulation--data-structures)
3. [Topological Sort Algorithms](#topological-sort-algorithms)
   - [Algorithm 1: BFS Kahn's Algorithm](#algorithm-1-bfs-kahns-algorithm)
   - [Algorithm 2: DFS 3-State Vertex Coloring](#algorithm-2-dfs-3-state-vertex-coloring)
4. [Dual-Engine Cycle Detection](#dual-engine-cycle-detection)
5. [Real-World University Scenario Interpretation](#real-world-university-scenario-interpretation)
6. [Comparative Analysis: BFS vs. DFS](#comparative-analysis-bfs-vs-dfs)
7. [Asymptotic Time & Space Complexity](#asymptotic-time--space-complexity)
8. [Automated Test Suite (TC-01 to TC-06)](#automated-test-suite-tc-01-to-tc-06)
9. [Build & Compilation Instructions](#build--compilation-instructions)
10. [Interactive CLI Menu](#interactive-cli-menu)
11. [Project Structure](#project-structure)

---

## Problem Statement

Modern university engineering programs feature intricate multi-tier prerequisite requirements. Foundational courses (e.g., *Programming Fundamentals*, *Discrete Mathematics*) serve as mandatory gateways for intermediate subjects (*Data Structures*, *Computer Organization*), which in turn gate specialized disciplines (*Operating Systems*, *Machine Learning*, *Artificial Intelligence*).

Without strict algorithmic sequencing:
1. **Academic Prematurity:** Undergraduates register for advanced topics without mastering foundational theory, causing course failure spikes.
2. **Circular Prerequisite Deadlocks:** Curriculum revisions may unintentionally introduce cyclic dependencies (e.g., $CS101 \to CS102 \to CS103 \to CS201 \to CS101$). In a cycle, no course can be completed first, halting student graduation progress.
3. **Invalid Ordering:** Manual course scheduling lacks formal proof that prerequisite constraints are preserved.

This project delivers a mathematically rigorous, zero-dependency C solution that enforces prerequisite validity, computes optimal graduation paths, isolates cyclic loops, and verifies precedence invariants.

---

## Graph Formulation & Data Structures

The curriculum is formalized as a **Directed Graph $G = (V, E)$**:
* **Vertices $V$:** Academic courses represented by `Course` records containing:
  - `code` (e.g., `"CS103"`)
  - `title` (e.g., `"Data Structures"`)
  - `credits` (e.g., `4`)
  - `department` (e.g., `"Computer Science"`)
* **Directed Edges $E$:** Directed prerequisite relationships $(u \to v)$ where course $u$ is a prerequisite for course $v$.
* **Representation:** Dynamic **Adjacency List** using linked nodes (`AdjNode`) anchored in an array of heads.
* **Auxiliary Structures:**
  - Direct In-Degree Tracking Array (`in_degree[MAX_COURSES]`)
  - Circular FIFO Queue (`Queue`) for Kahn's algorithm
  - LIFO Stack (`Stack`) for DFS finish order and recursion back-edge cycle reconstruction

```c
typedef struct {
    char code[CODE_LEN];
    char title[TITLE_LEN];
    int credits;
    char department[DEPT_LEN];
} Course;

typedef struct AdjNode {
    int dest_idx;
    struct AdjNode* next;
} AdjNode;

typedef struct {
    int num_courses;
    Course courses[MAX_COURSES];
    AdjNode* adj[MAX_COURSES];
    int in_degree[MAX_COURSES];
    int num_edges;
} CourseGraph;
```

---

## Topological Sort Algorithms

### Algorithm 1: BFS Kahn's Algorithm

Kahn's Algorithm operates on in-degree reduction:
1. Compute the direct in-degree for all vertices $u \in V$.
2. Enqueue all vertices with $\text{in-degree}(u) = 0$ (courses with no prerequisites) into a FIFO Queue.
3. While the queue is non-empty:
   - Dequeue vertex $u$ and append $u$ to the topological sequence.
   - For each outgoing directed edge $(u \to v)$, decrement $\text{in-degree}(v)$.
   - If $\text{in-degree}(v)$ becomes $0$, enqueue $v$.
4. **Cycle Verification:** If total dequeued vertices $< |V|$, the graph contains a directed cycle (queue starvation).

### Algorithm 2: DFS 3-State Vertex Coloring

DFS classifies vertices into 3 states to prevent duplicate visits and detect back-edges:
* **`STATE_UNVISITED (0)`:** Vertex has not yet been discovered.
* **`STATE_VISITING (1)`:** Vertex is actively being explored on the current recursion call stack.
* **`STATE_VISITED (2)`:** Vertex and all its reachable descendants have been fully processed.

1. Iterate over all vertices $i \in \{0, \dots, |V|-1\}$. If $state[i] == \text{UNVISITED}$, invoke `dfs_visit`.
2. In `dfs_visit(u)`:
   - Mark $state[u] = \text{VISITING}$ and push $u$ to the active call stack.
   - For each neighbor $v$ in $adj[u]$:
     - If $state[v] == \text{VISITING}$, a **back-edge** $(u \to v)$ is detected $\implies$ **Directed Cycle**.
     - If $state[v] == \text{UNVISITED}$, recursively visit $v$.
   - Mark $state[u] = \text{VISITED}$, pop $u$ from call stack, and push $u$ to the finish stack.
3. Reversing the finish stack produces a valid topological sequence.

---

## Dual-Engine Cycle Detection

| Algorithm | Cycle Detection Mechanism | Diagnostic Output |
| :--- | :--- | :--- |
| **BFS (Kahn's)** | **In-Degree Starvation:** Queue terminates before processing all $|V|$ vertices. | Identifies total unresolved courses locked in circular prerequisites. |
| **DFS (3-State)** | **Back-Edge Detection:** Traverses an edge $(u \to v)$ where $v$ is in state `VISITING`. | Extracts the **exact circular chain** directly from the active call stack. |

### Cycle Path Example (Extracted by DFS Engine):
```
CS101 -> CS102 -> CS103 -> CS201 -> CS101
```

---

## Real-World University Scenario Interpretation

When an academic curriculum contains a directed cycle, the real-world institutional consequences are severe:

1. **Total Registration Deadlock:**
   Every course in the cycle requires another course in the cycle to be completed first. No student can ever satisfy the prerequisite threshold to begin the sequence.
2. **Degree Audit System Failure:**
   Automated degree audit platforms (e.g., Ellucian DegreeWorks) either loop infinitely or flag mandatory graduation requirements as permanently unsatisfied.
3. **Delayed Graduation & Cohort Blockage:**
   Entire student cohorts are blocked from entering senior capstone electives, postponing graduation and endangering institutional accreditation standards (ABET / NBA).
4. **Mandatory Administrative Remediation:**
   Curriculum and academic senate committees must intervene to decouple the circular prerequisite edge in the university course catalogue.

---

## Comparative Analysis: BFS vs. DFS

| Comparison Attribute | BFS / Kahn's Algorithm | DFS 3-State Coloring |
| :--- | :--- | :--- |
| **Time Complexity** | $O(\|V\| + \|E\|)$ linear | $O(\|V\| + \|E\|)$ linear |
| **Space Complexity** | $O(\|V\|)$ auxiliary queue + in-degree array | $O(\|V\|)$ auxiliary stack + state array |
| **Primary Data Structure** | FIFO Queue | LIFO Stack (or Call Stack) |
| **Cycle Detection Principle** | In-Degree queue starvation | Back-edge to an active `VISITING` ancestor |
| **Cycle Reconstruction** | Identifies residual unresolved pool | Reconstructs exact cyclic path from call stack |
| **Topological Sequence** | Direct FIFO dequeue order | Reversed finish stack order |
| **Academic Advising Fit** | **Superior:** Naturally groups courses into semester tiers (courses unlock simultaneously) | Explores single dependency branches deeply before backtracking |
| **Parallelizability** | High (all in-degree 0 courses can be taken concurrently) | Low (inherently sequential depth recursion) |

---

## Asymptotic Time & Space Complexity

### 1. Time Complexity: $\Theta(|V| + |E|)$
* **Graph Initialization:** Adding $|V|$ courses takes $O(|V|)$. Adding $|E|$ prerequisite edges takes $O(|E|)$.
* **BFS Kahn:** Every vertex enters and leaves the queue once ($O(|V|)$). Every edge is traversed exactly once to decrement in-degree ($O(|E|)$). Total time: $O(|V| + |E|)$.
* **DFS 3-State:** Every vertex is marked `UNVISITED` $\to$ `VISITING` $\to$ `VISITED` once ($O(|V|)$). Each directed edge is checked once ($O(|E|)$). Total time: $O(|V| + |E|)$.
* **Precedence Validation:** Checks each directed edge $(u \to v)$ comparing $pos[u] < pos[v]$ in $O(|V| + |E|)$.

### 2. Space Complexity: $\Theta(|V| + |E|)$
* **Adjacency List:** $|V|$ pointers + $|E|$ nodes $\implies \Theta(|V| + |E|)$ space.
* **Savings vs. Adjacency Matrix:** For a university with $|V| = 100$ and $|E| = 150$, the adjacency list uses $\approx 250$ units of memory, whereas a $|V| \times |V|$ matrix requires $10,000$ entries — **over 97.5% memory reduction**.

---

## Automated Test Suite (TC-01 to TC-06)

The application includes an automated academic test suite verifying 6 distinct graph topologies:

| Test ID | Scenario Description | Graph Characteristics | Expected Result | Result Status |
| :--- | :--- | :--- | :--- | :---: |
| **TC-01** | Normal University DAG | 12 courses, 12 prerequisite edges | Valid Topological Order ($|V|=12$) | **[PASSED]** |
| **TC-02** | Simple Directed Cycle | 4 courses in mutual loop ($CS101 \leftrightarrow CS201$) | Cycle Detected by BFS & DFS | **[PASSED]** |
| **TC-03** | Multiple Independent Courses | 4 courses with in-degree 0, 0 edges | All courses included in order | **[PASSED]** |
| **TC-04** | Multiple Prerequisites | Many-to-one prerequisites ($CS101, CS104 \to CS103$) | Precedence verified $pos(u) < pos(v)$ | **[PASSED]** |
| **TC-05** | Single Isolated Course | 1 single course, 0 edges | Ordered solo cleanly | **[PASSED]** |
| **TC-06** | Disconnected Components | Multi-department tracks (CS track + Math track) | Valid intra-department sequence | **[PASSED]** |

**Test Result Summary:** **6 of 6 Test Cases Passed (100.0% Pass Rate)**

---

## Build & Compilation Instructions

The project is written in standard ANSI C99 / C11 with zero third-party dependencies. It compiles cleanly on Windows, Linux, and macOS.

### Compilation Options

#### 1. Using GCC / Clang (Linux, macOS, WSL)
```bash
gcc -Wall -Wextra -pedantic -std=c99 -O2 course_prerequisite_system.c -o course_prerequisite_system
```

#### 2. Using Makefile
```bash
make          # Compiles the application
make run      # Runs interactive CLI
make test     # Runs automated test suite (--all mode)
make clean    # Cleans compiled binaries
```

#### 3. Using Windows Batch Script (`build.bat`)
```cmd
build.bat          # Compiles course_prerequisite_system.exe
build.bat --all    # Compiles and runs all automated tests
```

#### 4. Using Shell Script (`compile.sh`)
```bash
chmod +x compile.sh
./compile.sh --all
```

---

## Interactive CLI Menu

Running the application displays the interactive system control menu:

```
********************************************************************************
*           UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM                   *
*                      CSA03 - DATA STRUCTURES (SLOT D)                       *
*       STUDENT: JAMPALA BRAHMAIAH  |  REGISTER NUMBER: 192472286              *
*       DEPARTMENT: COMPUTER SCIENCE AND ENGINEERING (CSE AI)                  *
*       OUTCOME: CO5 (L4 Analyze)   |  SDG: SDG 4 & SDG 9                      *
*       GITHUB: https://github.com/brahmaiah528/data_structure_assign          *
********************************************************************************

--- SYSTEM CONTROL MENU ---
 1. Run Full Demonstration (12-Course DAG: BFS + DFS + Validation + Tests)
 2. Display Curriculum Graph Topology & Adjacency List
 3. Run BFS / Kahn's Algorithm (with step-by-step queue transitions)
 4. Run DFS Topological Sort (with 3-state coloring & finish stack)
 5. Run Formal Precedence Constraint Validation [pos(u) < pos(v)]
 6. Inject Circular Dependency & Perform Cycle Audit (BFS & DFS)
 7. Display Real-World University Cycle Impact Report
 8. Display BFS vs DFS Comparative Analysis & Asymptotic Complexity
 9. Interactively Add Custom Course or Prerequisite Edge
10. Run Automated 6-Scenario Test Suite
11. Reset Curriculum Graph to Default 12 Courses
12. Exit Application
Select option (1-12):
```

### Non-Interactive / Batch Mode
Run with the `--all` or `-a` flag for automated evaluation:
```bash
./course_prerequisite_system --all
```

---

## Project Structure

```
d1/
├── course_prerequisite_system.c   # Complete, self-contained C implementation
├── Makefile                       # Standard GNU Makefile (all, run, test, clean)
├── build.bat                      # Windows build automation script
├── compile.sh                     # POSIX shell compilation script
├── README.md                      # Comprehensive academic documentation
├── docs/                          # Academic documentation & theoretical analyses
│   ├── academic-report.md         # Full formal academic assignment report
│   ├── algorithm-analysis.md      # Detailed BFS vs DFS complexity proofs
│   ├── one-page-writeup.md        # One-page executive project summary
│   └── pseudocode.md              # Algorithmic pseudocode specifications
└── screenshots/                   # Verification execution traces & test results
```

---

## SDG Mapping

* **SDG 4 (Quality Education):** Prevents academic registration failures, guarantees students complete required prerequisite foundations sequentially, and eliminates curriculum deadlocks.
* **SDG 9 (Industry, Innovation and Infrastructure):** Replaces error-prone manual scheduling with mathematically verified, high-performance graph algorithms that scale to large institutional curricula.

---

## Conclusion

The **University Course Prerequisite Management System in C** demonstrates how fundamental graph algorithms solve critical real-world academic scheduling challenges. By leveraging an Adjacency List, Kahn's algorithm, 3-state DFS coloring, and formal precedence verification, the system achieves optimal $O(|V| + |E|)$ runtime and guarantees complete, deadlock-free student progression roadmaps.
