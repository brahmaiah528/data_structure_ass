# One-Page Academic Project Summary

**Project Title:** University Course Prerequisite Management System Using Topological Sort  
**Course & Code:** CSA03 – Data Structures (Slot D)  
**Course Outcome:** CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications.  
**SDG Alignment:** SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)

---

### 1. Problem Statement
Modern university curricula feature hundreds of interconnected courses where advanced subjects enforce strict prerequisite dependencies. Students and academic administrators require automated, error-free systems to determine valid course-taking sequences and to detect pathological circular dependencies that paralyze student progression.

### 2. Objective
To design, implement, and analyze a robust directed graph system that models academic prerequisite networks, generates valid course completion schedules using BFS (Kahn's Algorithm) and DFS (3-State Coloring), detects circular prerequisite deadlocks, and validates sequential precedence.

### 3. Requirements and Environment
- **Platform:** Python 3.13 / Standard Library (Zero External Dependencies)
- **Data Structures:** Adjacency List (Hash Map + Dynamic Lists), FIFO Queue (`collections.deque`), LIFO Stack, Sets
- **Interfaces:** Dual-mode deployment featuring a desktop Tkinter GUI and an embedded localhost web dashboard (`http://localhost:8000`)

### 4. Proposed Solution
The curriculum is modeled as a Directed Graph $G = (V, E)$ where each vertex represents an academic course and each directed edge $u \to v$ signifies that course $u$ is a mandatory prerequisite for course $v$. The system implements dual algorithmic pipelines (BFS and DFS) to process the graph, alongside automated precedence validation checking that $\text{pos}(u) < \text{pos}(v)$ for every edge.

### 5. Algorithm
1. **BFS (Kahn's Algorithm):** Calculates in-degree for all $V$ vertices. Courses with in-degree $0$ enter a FIFO queue. Dequeuing vertex $u$ appends it to the topological order and decrements in-degrees of all neighbors $v$. If `indegree[v]` reaches $0$, $v$ is enqueued. If ordered count $< |V|$, a cycle exists.
2. **DFS (3-State Traversal):** Classifies vertices into `UNVISITED (0)`, `VISITING (1)`, and `VISITED (2)`. Encountering a `VISITING` neighbor identifies a back-edge, exposing a cycle. Vertices entering state `2` are pushed onto a finish stack; reversing the stack produces the topological sequence.

### 6. Implementation
The solution follows strict Object-Oriented principles across dedicated modules:
`Course` (encapsulation), `CourseGraph` (adjacency list engine), `TopologicalSort` (Kahn and DFS implementations with execution step tracing), `CycleDetector` (cycle path extractor and institutional impact reporter), `OrderValidator` (formal verification), `TestSuite` (6 automated test cases), and `server.py` / `gui.py` (user interfaces).

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
The University Course Prerequisite Management System successfully proves that graph theory and topological sort algorithms provide robust, mathematically sound, and computationally efficient foundations for university curriculum planning and automated registration systems.
