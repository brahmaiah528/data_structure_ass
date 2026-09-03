# One-Page Academic Project Summary

**Department:** Department of Computer Science and Engineering (CSE AI)  
**Course Code & Name:** CSA03 – Data Structures – Slot D  
**Student Name:** Jampala Brahmaiah  
**Register Number:** 192472286  
**Assignment Title:** Design a graph representation of this prerequisite system and use Topological Sort to generate a valid course-taking order. Your design must also detect whether the prerequisite system contains a cycle. Analyze what the existence of a cycle means in the real-world university scenario and compare a BFS-based and DFS-based approach for solving the problem.  
**Course Outcome:** CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications.  
**Bloom’s Taxonomy Level:** L4 – Analyze  
**SDG Alignment:** SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure) with relevance to SDG 11 (Sustainable Cities and Communities)  
**GitHub Repository:** [https://github.com/brahmaiah528/data_structure_assign](https://github.com/brahmaiah528/data_structure_assign)

---

### Deliverables Checklist
1. **Pseudo Code:** Clean algorithms for graph creation, BFS Kahn, DFS 3-state, cycle detection, and validation $\to$ [docs/pseudocode.md](pseudocode.md)
2. **Implementation & Results:** Complete, standalone ANSI C implementation (`course_prerequisite_system.c`), Makefile, build automation scripts, automated test suite (TC-01 to TC-06: 100% Passed) $\to$ [course_prerequisite_system.c](file:///c:/Users/brami/OneDrive/Desktop/d1/course_prerequisite_system.c)
3. **GitHub Upload:** Verified and pushed to [https://github.com/brahmaiah528/data_structure_assign](https://github.com/brahmaiah528/data_structure_assign)
4. **One Page Write-up:** This document

---

### 1. Problem Statement
Modern university curricula feature hundreds of interconnected courses where advanced subjects enforce strict prerequisite dependencies. Students and academic administrators require automated, error-free systems to determine valid course-taking sequences and to detect pathological circular dependencies that paralyze student progression.

### 2. Objective
To design, implement, and analyze a robust directed graph system in standard **C language** that models academic prerequisite networks, generates valid course completion schedules using BFS (Kahn's Algorithm) and DFS (3-State Coloring), detects circular prerequisite deadlocks, and formally validates sequential precedence ($pos(u) < pos(v)$).

### 3. Requirements and Environment
- **Platform & Language:** Standard ANSI C99 / C11 (Zero External Dependencies)
- **Compilers:** GCC, Clang, MSVC
- **Data Structures in C:** Dynamic Adjacency List (`AdjNode*`), Circular FIFO Queue (`Queue`), LIFO Stack (`Stack`), In-Degree tracking arrays
- **Build Tools:** Standard GNU `Makefile`, Windows `build.bat`, and POSIX `compile.sh`
- **Interfaces:** Dual-mode deployment featuring an interactive CLI control menu and automated batch execution (`--all`)

### 4. Proposed Solution
The curriculum is modeled as a Directed Graph $G = (V, E)$ where each vertex represents an academic course entity (`Course`) and each directed edge $u \to v$ signifies that course $u$ is a mandatory prerequisite for course $v$. The system implements dual algorithmic pipelines (BFS and DFS) to process the graph, alongside automated precedence validation checking that $\text{pos}(u) < \text{pos}(v)$ for every edge.

### 5. Algorithm
1. **BFS (Kahn's Algorithm):** Calculates in-degree for all $|V|$ vertices. Courses with in-degree $0$ enter a FIFO queue. Dequeuing vertex $u$ appends it to the topological order and decrements in-degrees of all neighbors $v$. If `in_degree[v]` reaches $0$, $v$ is enqueued. If ordered count $< |V|$, a cycle exists (queue starvation).
2. **DFS (3-State Traversal):** Classifies vertices into `UNVISITED (0)`, `VISITING (1)`, and `VISITED (2)`. Encountering a `VISITING` neighbor identifies a back-edge, exposing a cycle. Vertices entering state `2` are pushed onto a finish stack; reversing the stack produces the topological sequence.

### 6. Implementation
The solution is implemented in modular C:
- Course modeling (`Course` struct: code, title, credits, department)
- Adjacency list engine (`CourseGraph`, `AdjNode`, `graph_create`, `graph_add_course`, `graph_add_prerequisite`)
- Queue and stack abstractions (`Queue`, `Stack`)
- Algorithmic engines (`kahn_topological_sort`, `dfs_topological_sort`)
- Diagnostic & validation engines (`validate_precedence`, `print_real_world_cycle_impact`, `print_algorithm_comparison`)
- Automated test suite (`run_test_suite` for TC-01 to TC-06)
- Interactive CLI menu and `--all` batch runner

### 7. Results
The system was verified against 6 rigorous test cases:
1. **Normal DAG (12 Courses):** Valid 12-course sequence generated; formal validation PASSED.
2. **Simple Cycle:** Circular dependency ($CS101 \to CS102 \to CS103 \to CS201 \to CS101$) detected by both algorithms; order safely rejected.
3. **Independent Courses, Multi-Prerequisites, Single Course, and Disconnected Components:** All passed with 100% verification accuracy.

### 8. Analysis
Both algorithms achieve optimal linear time complexity $O(V + E)$ and auxiliary space $O(V)$. The Adjacency List representation consumes $\Theta(V + E)$ space, saving over $99.5\%$ memory compared to a $V \times V$ matrix for sparse academic networks. Kahn's algorithm is preferred as the primary engine because in-degrees map directly to unmet prerequisites and the queue naturally models immediately available courses.

### 9. Real-World Significance
Circular prerequisite loops cause total enrollment deadlocks, delayed graduations, and degree audit failures. This system automates curriculum validation, safeguarding institutional operational integrity (SDG 9) and ensuring seamless, high-quality educational delivery (SDG 4).

### 10. Conclusion
The University Course Prerequisite Management System successfully proves that graph theory and topological sort algorithms implemented in C provide robust, mathematically sound, and computationally efficient foundations for university curriculum planning and automated registration systems.
