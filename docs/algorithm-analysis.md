# Algorithm Complexity & Architectural Analysis

**Course:** CSA03 – Data Structures (Slot D)  
**Course Outcome:** CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications.  
**Project Title:** University Course Prerequisite Management System Using Topological Sort  
**SDG Alignment:** SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)

---

## 1. Graph Representation: Adjacency List vs. Adjacency Matrix

A university academic curriculum consists of $V$ course offerings and $E$ directed prerequisite dependencies. In real-world academic institutions, curriculum graphs are **inherently sparse**:
- Each course typically specifies between $0$ and $3$ prerequisites.
- For a university with $V = 500$ courses, total prerequisite edges $E \approx 700$ to $1,200$.
- The maximum possible edges in a directed graph is $V(V - 1) = 249,500$.
- Edge density:
  $$\rho = \frac{|E|}{|V|(|V| - 1)} \approx \frac{1000}{249500} \approx 0.004 \quad (0.4\% \text{ density})$$

### Comparative Analysis

| Evaluation Criterion | Adjacency Matrix ($V \times V$) | Adjacency List ($V + E$) | Winner / Rationale |
| :--- | :--- | :--- | :--- |
| **Memory Space Complexity** | $\Theta(V^2)$ contiguous cells | $\Theta(V + E)$ dynamic elements | **Adjacency List**: Conserves over $99.5\%$ memory for sparse curriculum networks. |
| **Iteration over Outgoing Edges** | $\Theta(V)$ time per vertex | $\Theta(\text{deg}^+(u))$ time per vertex | **Adjacency List**: Accesses only actual dependent courses without scanning empty cells. |
| **In-Degree Calculation** | $\Theta(V^2)$ to scan all columns | $\Theta(V + E)$ by traversing all lists | **Adjacency List**: Scales linearly with graph size. |
| **Edge Existence Query ($u \to v$)** | $O(1)$ direct array indexing | $O(\text{deg}^+(u))$ linked search | Matrix is faster for single edge queries, but lists with hash sets achieve $O(1)$ amortized lookup. |
| **Dynamic Curriculum Expansion** | $O(V^2)$ reallocation when adding course | $O(1)$ amortized map insertion | **Adjacency List**: Allows seamless addition of new electives and prerequisite updates. |

**Conclusion:** The **Adjacency List** representation is overwhelmingly superior for large-scale university prerequisite management systems, ensuring minimal memory overhead and linear algorithmic traversal.

---

## 2. Asymptotic Complexity Analysis

### 2.1 BFS-Based Topological Sort (Kahn's Algorithm)

#### Time Complexity: $O(V + E)$
1. **In-degree Initialization:** We traverse every vertex and each of its outgoing edges once:
   $$\sum_{u \in V} \text{deg}^+(u) = |E|$$
   This phase executes in $\Theta(V + E)$ time.
2. **Queue Initialization:** Scanning all vertices to locate zero in-degree courses requires $\Theta(V)$ time.
3. **Queue Processing:**
   - Every vertex enters and leaves the queue at most once: $V \times O(1) = O(V)$.
   - For each dequeued vertex $u$, we iterate over all its outgoing edges $(u, v)$ and decrement `indegree[v]`.
   - The total number of decrements across the entire execution is exactly equal to the total number of edges $|E|$:
     $$\sum_{u \in V} \text{deg}^+(u) = |E|$$
4. **Total Time:**
   $$T(V, E) = O(V) + O(V + E) + O(V) + O(E) = \mathbf{O(V + E)}$$

#### Space Complexity: $O(V)$
- **In-degree Table:** Stores one integer per course: $\Theta(V)$.
- **FIFO Queue:** In the worst-case (all courses independent), holds up to $V$ vertices: $O(V)$.
- **Topological Order List:** Stores $V$ course codes: $O(V)$.
- **Auxiliary Graph Storage:** $O(V + E)$ for adjacency list.
- **Pure Algorithm Auxiliary Space:** $\mathbf{O(V)}$.

---

### 2.2 DFS-Based Topological Sort (3-State Vertex Coloring)

#### Time Complexity: $O(V + E)$
1. **State Array Initialization:** Initializing all vertices to `UNVISITED (0)` takes $\Theta(V)$ time.
2. **Vertex Traversal:** The outer loop guarantees every vertex is visited:
   - Each vertex transitions through states: $\text{UNVISITED} \to \text{VISITING} \to \text{VISITED}$ exactly once.
   - For each vertex $u$, all outgoing edges $(u, v)$ are examined once.
   - Total edge explorations across all DFS calls:
     $$\sum_{u \in V} \text{outdeg}(u) = |E|$$
3. **Stack Push/Pop Operations:** Pushing and popping each vertex into the finish stack executes in $O(1)$ time per vertex: $O(V)$.
4. **Total Time:**
   $$T(V, E) = \mathbf{O(V + E)}$$

#### Space Complexity: $O(V)$
- **Coloring State Map:** One entry per course: $\Theta(V)$.
- **Active Recursion Call Stack:** In the worst-case (a single linear chain $C_1 \to C_2 \to \dots \to C_V$), call stack depth is $V$: $O(V)$.
- **Finish Stack:** Stores $V$ vertices: $O(V)$.
- **Pure Algorithm Auxiliary Space:** $\mathbf{O(V)}$.

---

## 3. Comprehensive BFS vs. DFS Comparison

| # | Comparison Dimension | BFS / Kahn's Algorithm | DFS 3-State Vertex Coloring |
| :---: | :--- | :--- | :--- |
| **1** | **Core Underlying Principle** | **In-degree reduction & queue starvation** | **Depth-first tree traversal & finish-time stack** |
| **2** | **Primary Data Structure** | First-In-First-Out (FIFO) Queue | Last-In-First-Out (LIFO) Stack / Call Stack |
| **3** | **Ordering Mechanism** | Forward order: Vertices emitted as prerequisites reach 0 | Reverse post-order: Emits vertices as subtrees terminate |
| **4** | **Cycle Detection Mechanism** | Compares `processedCount < |V|` (queue empties early) | Detects **back-edges** pointing to `VISITING` ancestors |
| **5** | **Cycle Path Extraction** | Requires secondary search over unprocessed subgraph | **Immediate**: Call stack holds exact circular dependency path |
| **6** | **Time Complexity** | $O(V + E)$ | $O(V + E)$ |
| **7** | **Space Complexity** | $O(V)$ | $O(V)$ (recursion depth up to $V$) |
| **8** | **Intuitive Real-World Meaning** | **High**: Directly models student semester course availability | **Moderate**: Abstract recursion finish ordering |
| **9** | **Parallelization Potential** | **High**: All vertices in queue can be taken concurrently | **Low**: Inherently sequential recursive tree search |
| **10** | **Risk of Stack Overflow** | **Zero**: Operates iteratively on heap memory | **Present**: Deep linear graphs can exceed recursion limits |
| **11** | **University Domain Fitness** | **Optimal Primary Solution**: Models eligible enrollment directly | **Ideal Secondary Auditor**: Pinpoints circular deadlocks |

---

## 4. Institutional Justification: Why Kahn's Algorithm is Primary

In university academic administration, Kahn's algorithm provides an exact mathematical isomorphism to real-world course progression:

1. **In-Degree Represents Unmet Prerequisites:**  
   The in-degree of a course vertex $v$ directly quantifies the number of prerequisite subjects a student must clear before becoming eligible to register for $v$. An in-degree of `0` signifies an immediate, unrestricted entry-level course.

2. **The Queue Models "Current Semester Available Courses":**  
   All courses present in the queue simultaneously represent courses whose prerequisites have been cleared. Students or academic schedulers can schedule all queue contents in the current academic term.

3. **In-Degree Decrement Models Course Completion:**  
   When a student passes course $u$ (dequeued), decrements to all dependent courses $v$ reflect that one prerequisite hurdle has been cleared. When `indegree[v]` drops to `0`, $v$ unlocks into the queue.

---

## 5. Real-World Cycle Analysis & Institutional Impact

In a university course catalogue, a **directed cycle** represents an **impossible circular dependency**.

### Canonical Example
$$\text{CS101 (Programming)} \longrightarrow \text{CS102 (OOP)} \longrightarrow \text{CS103 (Data Structures)} \longrightarrow \text{CS201 (Algorithms)} \longrightarrow \text{CS101}$$

- CS101 requires CS201
- CS201 requires CS103
- CS103 requires CS102
- CS102 requires CS101

### Real-World Academic Consequences
1. **Total Registration Deadlock:** No student can enroll in CS101 because they have not completed CS201. However, they cannot enroll in CS201 because they have not completed CS103, and so forth. The entire academic cohort is blocked.
2. **Graduation Clearance Failure:** Degree audit software (e.g., DegreeWorks) loops infinitely or flags mandatory degree requirements as unsatisfied, preventing student graduation.
3. **Institutional Resource Waste:** Faculty assignments, classroom allocations, and lab scheduling are paralyzed for locked courses.
4. **Mandatory Remediation Protocol:**
   - The automated registration engine must immediately detect and reject the curriculum graph upload.
   - The academic dean and curriculum advisory committee must review the historical syllabus and sever the invalid back-edge (e.g., remove the requirement for CS201 from CS101).
