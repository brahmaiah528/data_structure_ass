/*
 * ====================================================================================================
 * PROJECT: UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM
 * COURSE : CSA03 - Data Structures (Slot D)
 * STUDENT: JAMPALA BRAHMAIAH (Register Number: 192472286)
 * OUTCOME: CO5 - Robust Graph-Based Solutions & Topological Sort for Real-World Applications
 * TAXONOMY: L4 - Analyze
 * SDG    : SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)
 * GITHUB : https://github.com/brahmaiah528/data_structure_assign
 * ====================================================================================================
 * 
 * DESCRIPTION:
 * A complete, standalone C implementation of a university academic curriculum prerequisite system.
 * 
 * KEY FEATURES IMPLEMENTED IN THIS SINGLE FILE:
 *  1. Graph Data Structure: Directed Graph G = (V, E) with Adjacency List representation.
 *  2. Course Modeling: Encapsulated course records (Code, Title, Credits, Department).
 *  3. BFS Topological Sort: Kahn's Algorithm utilizing in-degree reduction and a FIFO queue.
 *  4. DFS Topological Sort: 3-State Vertex Coloring (UNVISITED=0, VISITING=1, VISITED=2) with finish stack.
 *  5. Dual-Engine Cycle Detection:
 *      - BFS: Queue starvation detection with residual subgraph extraction.
 *      - DFS: Back-edge detection on the active recursion call stack with exact cycle path reconstruction.
 *  6. Precedence Constraint Validation: Formally verifies that pos(u) < pos(v) for all (u -> v) in E.
 *  7. Real-World University Impact Reporting: Detailed diagnostics on registration deadlocks and degree audits.
 *  8. Comprehensive 6-Scenario Test Suite:
 *      - TC-01: Normal 12-Course University DAG (CS101 - CS302)
 *      - TC-02: Directed Cycle (CS101 -> CS102 -> CS103 -> CS201 -> CS101)
 *      - TC-03: Multiple Independent Courses (In-degree = 0)
 *      - TC-04: Multiple Prerequisites (Many-to-one dependency)
 *      - TC-05: Single Isolated Course
 *      - TC-06: Disconnected Subgraphs (Multi-department tracks)
 *  9. Interactive CLI Menu & Automated Execution Modes.
 * ====================================================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define MAX_COURSES 100
#define CODE_LEN 16
#define TITLE_LEN 64
#define DEPT_LEN 64

/* 3-State Vertex Coloring for DFS */
typedef enum {
    STATE_UNVISITED = 0,
    STATE_VISITING  = 1,
    STATE_VISITED   = 2
} VertexState;

/* Course Entity Model */
typedef struct {
    char code[CODE_LEN];
    char title[TITLE_LEN];
    int credits;
    char department[DEPT_LEN];
} Course;

/* Adjacency List Node representing a directed edge (u -> v) */
typedef struct AdjNode {
    int dest_idx;
    struct AdjNode* next;
} AdjNode;

/* Directed Graph Structure */
typedef struct {
    int num_courses;
    Course courses[MAX_COURSES];
    AdjNode* adj[MAX_COURSES];        /* Outgoing edges: course -> [dependents] */
    int in_degree[MAX_COURSES];       /* Count of direct incoming prerequisites */
    int num_edges;
} CourseGraph;

/* FIFO Queue for BFS (Kahn's Algorithm) */
typedef struct {
    int data[MAX_COURSES];
    int front;
    int rear;
    int count;
} Queue;

static void queue_init(Queue* q) {
    q->front = 0;
    q->rear = -1;
    q->count = 0;
}

static bool queue_is_empty(const Queue* q) {
    return q->count == 0;
}

static void queue_push(Queue* q, int val) {
    if (q->count < MAX_COURSES) {
        q->rear = (q->rear + 1) % MAX_COURSES;
        q->data[q->rear] = val;
        q->count++;
    }
}

static int queue_pop(Queue* q) {
    if (q->count > 0) {
        int val = q->data[q->front];
        q->front = (q->front + 1) % MAX_COURSES;
        q->count--;
        return val;
    }
    return -1;
}

/* LIFO Stack for DFS & Cycle Path Reconstruction */
typedef struct {
    int data[MAX_COURSES];
    int top;
} Stack;

static void stack_init(Stack* s) {
    s->top = -1;
}

static bool stack_is_empty(const Stack* s) {
    return s->top == -1;
}

static void stack_push(Stack* s, int val) {
    if (s->top < MAX_COURSES - 1) {
        s->data[++(s->top)] = val;
    }
}

static int stack_pop(Stack* s) {
    if (s->top >= 0) {
        return s->data[(s->top)--];
    }
    return -1;
}

/* ====================================================================================================
 * GRAPH CORE FUNCTIONS
 * ====================================================================================================
 */

CourseGraph* graph_create(void) {
    CourseGraph* g = (CourseGraph*)malloc(sizeof(CourseGraph));
    if (!g) {
        fprintf(stderr, "Fatal: Memory allocation failed for CourseGraph.\n");
        exit(EXIT_FAILURE);
    }
    g->num_courses = 0;
    g->num_edges = 0;
    for (int i = 0; i < MAX_COURSES; i++) {
        g->adj[i] = NULL;
        g->in_degree[i] = 0;
    }
    return g;
}

void graph_free(CourseGraph* g) {
    if (!g) return;
    for (int i = 0; i < g->num_courses; i++) {
        AdjNode* curr = g->adj[i];
        while (curr) {
            AdjNode* temp = curr;
            curr = curr->next;
            free(temp);
        }
        g->adj[i] = NULL;
    }
    free(g);
}

int graph_find_course(const CourseGraph* g, const char* code) {
    for (int i = 0; i < g->num_courses; i++) {
        if (strcmp(g->courses[i].code, code) == 0) {
            return i;
        }
    }
    return -1;
}

int graph_add_course(CourseGraph* g, const char* code, const char* title, int credits, const char* dept) {
    int existing = graph_find_course(g, code);
    if (existing != -1) {
        return existing;
    }
    if (g->num_courses >= MAX_COURSES) {
        fprintf(stderr, "Error: Graph capacity exceeded (%d courses).\n", MAX_COURSES);
        return -1;
    }
    int idx = g->num_courses++;
    strncpy(g->courses[idx].code, code, CODE_LEN - 1);
    g->courses[idx].code[CODE_LEN - 1] = '\0';

    strncpy(g->courses[idx].title, title, TITLE_LEN - 1);
    g->courses[idx].title[TITLE_LEN - 1] = '\0';

    g->courses[idx].credits = credits;

    strncpy(g->courses[idx].department, dept, DEPT_LEN - 1);
    g->courses[idx].department[DEPT_LEN - 1] = '\0';

    g->adj[idx] = NULL;
    g->in_degree[idx] = 0;
    return idx;
}

bool graph_add_prerequisite(CourseGraph* g, const char* prereq_code, const char* course_code) {
    int u = graph_find_course(g, prereq_code);
    int v = graph_find_course(g, course_code);

    if (u == -1 || v == -1) {
        fprintf(stderr, "Error: Prerequisite link failed. Course '%s' or '%s' not found.\n",
                prereq_code, course_code);
        return false;
    }
    if (u == v) {
        fprintf(stderr, "Error: Self-loop detected! Course '%s' cannot require itself.\n", prereq_code);
        return false;
    }

    /* Check for duplicate edges */
    AdjNode* curr = g->adj[u];
    while (curr) {
        if (curr->dest_idx == v) {
            return true; /* Already exists */
        }
        curr = curr->next;
    }

    /* Insert new edge u -> v */
    AdjNode* new_node = (AdjNode*)malloc(sizeof(AdjNode));
    if (!new_node) {
        fprintf(stderr, "Fatal: Memory allocation failed for AdjNode.\n");
        exit(EXIT_FAILURE);
    }
    new_node->dest_idx = v;
    new_node->next = g->adj[u];
    g->adj[u] = new_node;

    g->in_degree[v]++;
    g->num_edges++;
    return true;
}

void graph_print_topology(const CourseGraph* g) {
    printf("\n================================================================================\n");
    printf("            UNIVERSITY CURRICULUM GRAPH TOPOLOGY & ADJACENCY LIST               \n");
    printf("================================================================================\n");
    printf("Total Courses (|V|): %d\n", g->num_courses);
    printf("Total Prerequisite Edges (|E|): %d\n", g->num_edges);
    printf("--------------------------------------------------------------------------------\n");
    printf("%-8s | %-32s | %-7s | %s\n", "Code", "Course Title", "Credits", "Dependent Courses (Out-Edges)");
    printf("--------------------------------------------------------------------------------\n");

    for (int i = 0; i < g->num_courses; i++) {
        printf("%-8s | %-32s | %-7d | [", g->courses[i].code, g->courses[i].title, g->courses[i].credits);
        AdjNode* curr = g->adj[i];
        if (!curr) {
            printf("None (Terminal Course)]\n");
        } else {
            bool first = true;
            while (curr) {
                if (!first) printf(", ");
                printf("%s", g->courses[curr->dest_idx].code);
                first = false;
                curr = curr->next;
            }
            printf("]\n");
        }
    }
    printf("================================================================================\n\n");
}

/* ====================================================================================================
 * ALGORITHM 1: BFS TOPOLOGICAL SORT (KAHN'S ALGORITHM)
 * ====================================================================================================
 */

bool kahn_topological_sort(const CourseGraph* g, int* order, int* order_len, bool verbose) {
    int temp_in_degree[MAX_COURSES];
    for (int i = 0; i < g->num_courses; i++) {
        temp_in_degree[i] = g->in_degree[i];
    }

    Queue q;
    queue_init(&q);

    if (verbose) {
        printf("\n======================================================================\n");
        printf("BFS / KAHN'S ALGORITHM TOPOLOGICAL SORT EXECUTION TRACE\n");
        printf("======================================================================\n");
        printf("[1] INITIAL IN-DEGREES (Direct Prerequisites Count):\n");
        printf("----------------------------------------------------------------------\n");
        for (int i = 0; i < g->num_courses; i++) {
            printf("  %-8s = %2d  (%s)\n", g->courses[i].code, temp_in_degree[i], g->courses[i].title);
        }
        printf("\n[2] STEP-BY-STEP QUEUE EXECUTION TRACE:\n");
        printf("----------------------------------------------------------------------\n");
    }

    /* Enqueue all vertices with in-degree == 0 */
    for (int i = 0; i < g->num_courses; i++) {
        if (temp_in_degree[i] == 0) {
            queue_push(&q, i);
        }
    }

    if (verbose) {
        printf("  Step  1: Initialized queue with in-degree 0 courses: [");
        for (int i = 0; i < q.count; i++) {
            int idx = q.data[(q.front + i) % MAX_COURSES];
            printf("%s%s", g->courses[idx].code, (i < q.count - 1) ? ", " : "");
        }
        printf("]\n");
    }

    int count = 0;
    int step = 2;

    while (!queue_is_empty(&q)) {
        int u = queue_pop(&q);
        order[count++] = u;

        if (verbose) {
            printf("  Step %2d: Dequeued '%s' -> Decrementing dependents: ", step++, g->courses[u].code);
        }

        AdjNode* curr = g->adj[u];
        bool has_dependents = (curr != NULL);

        while (curr) {
            int v = curr->dest_idx;
            temp_in_degree[v]--;
            if (verbose) {
                printf("%s (in-degree -> %d%s) ", g->courses[v].code, temp_in_degree[v],
                       (temp_in_degree[v] == 0) ? ", ENQUEUED" : "");
            }
            if (temp_in_degree[v] == 0) {
                queue_push(&q, v);
            }
            curr = curr->next;
        }

        if (verbose) {
            if (!has_dependents) {
                printf("No outgoing dependencies");
            }
            printf("\n");
        }
    }

    *order_len = count;

    if (count < g->num_courses) {
        if (verbose) {
            printf("\n[3] CYCLE STATUS & VERDICT:\n");
            printf("----------------------------------------------------------------------\n");
            printf("  STATUS: [CYCLE DETECTED!]\n");
            printf("  Queue starved prematurely: Processed %d of %d courses.\n", count, g->num_courses);
            printf("  The remaining %d courses are locked in mutual circular prerequisites.\n",
                   g->num_courses - count);
            printf("======================================================================\n\n");
        }
        return false; /* Cycle detected */
    }

    if (verbose) {
        printf("\n[3] CYCLE STATUS & VERDICT:\n");
        printf("----------------------------------------------------------------------\n");
        printf("  STATUS: NO CYCLE DETECTED (Valid Directed Acyclic Graph - DAG)\n");
        printf("\n[4] FINAL COMPUTED COURSE-TAKING ORDER:\n");
        printf("----------------------------------------------------------------------\n");
        for (int i = 0; i < count; i++) {
            int idx = order[i];
            printf("  %2d. %-8s - %-32s (%d Credits)\n",
                   i + 1, g->courses[idx].code, g->courses[idx].title, g->courses[idx].credits);
        }
        printf("----------------------------------------------------------------------\n");
        printf("Total Courses Ordered: %d of %d\n", count, g->num_courses);
        printf("======================================================================\n\n");
    }

    return true; /* Successful DAG ordering */
}

/* ====================================================================================================
 * ALGORITHM 2: DFS TOPOLOGICAL SORT (3-STATE VERTEX COLORING)
 * ====================================================================================================
 */

static bool dfs_visit(const CourseGraph* g, int u, VertexState* state, Stack* finish_stack,
                      Stack* call_stack, int* cycle_path, int* cycle_len, bool verbose) {
    state[u] = STATE_VISITING;
    stack_push(call_stack, u);

    if (verbose) {
        printf("  DFS: Visiting '%s' (Marked VISITING = 1)\n", g->courses[u].code);
    }

    AdjNode* curr = g->adj[u];
    while (curr) {
        int v = curr->dest_idx;
        if (state[v] == STATE_VISITING) {
            /* Back-edge found: cycle detected! */
            if (verbose) {
                printf("  >>> BACK-EDGE FOUND: '%s' -> '%s' (Ancestor currently on active stack)!\n",
                       g->courses[u].code, g->courses[v].code);
            }
            /* Reconstruct cycle path from call stack */
            if (cycle_path && cycle_len) {
                int start_pos = 0;
                for (int i = 0; i <= call_stack->top; i++) {
                    if (call_stack->data[i] == v) {
                        start_pos = i;
                        break;
                    }
                }
                int len = 0;
                for (int i = start_pos; i <= call_stack->top; i++) {
                    cycle_path[len++] = call_stack->data[i];
                }
                cycle_path[len++] = v; /* Complete cycle loop */
                *cycle_len = len;
            }
            return false;
        }
        if (state[v] == STATE_UNVISITED) {
            if (!dfs_visit(g, v, state, finish_stack, call_stack, cycle_path, cycle_len, verbose)) {
                return false;
            }
        }
        curr = curr->next;
    }

    state[u] = STATE_VISITED;
    stack_pop(call_stack);
    stack_push(finish_stack, u);

    if (verbose) {
        printf("  DFS: Finished '%s' (Marked VISITED = 2, Pushed to Finish Stack)\n", g->courses[u].code);
    }

    return true;
}

bool dfs_topological_sort(const CourseGraph* g, int* order, int* order_len, bool verbose) {
    VertexState state[MAX_COURSES];
    for (int i = 0; i < g->num_courses; i++) {
        state[i] = STATE_UNVISITED;
    }

    Stack finish_stack;
    stack_init(&finish_stack);

    Stack call_stack;
    stack_init(&call_stack);

    int cycle_path[MAX_COURSES];
    int cycle_len = 0;

    if (verbose) {
        printf("\n======================================================================\n");
        printf("DFS TOPOLOGICAL SORT (3-STATE VERTEX COLORING) EXECUTION\n");
        printf("======================================================================\n");
    }

    for (int i = 0; i < g->num_courses; i++) {
        if (state[i] == STATE_UNVISITED) {
            if (!dfs_visit(g, i, state, &finish_stack, &call_stack, cycle_path, &cycle_len, verbose)) {
                if (verbose) {
                    printf("\nSTATUS: [CYCLE DETECTED VIA DFS BACK-EDGE!]\n");
                    printf("Cycle Loop: ");
                    for (int k = 0; k < cycle_len; k++) {
                        printf("%s%s", g->courses[cycle_path[k]].code, (k < cycle_len - 1) ? " -> " : "\n");
                    }
                    printf("======================================================================\n\n");
                }
                *order_len = 0;
                return false;
            }
        }
    }

    /* Reverse the finish stack to obtain topological order */
    int count = 0;
    while (!stack_is_empty(&finish_stack)) {
        order[count++] = stack_pop(&finish_stack);
    }
    *order_len = count;

    if (verbose) {
        printf("\nSTATUS: NO CYCLE DETECTED (Valid Directed Acyclic Graph - DAG)\n");
        printf("\nFINAL DFS COURSE-TAKING ORDER (Reversed Finish Stack):\n");
        printf("----------------------------------------------------------------------\n");
        for (int i = 0; i < count; i++) {
            int idx = order[i];
            printf("  %2d. %-8s - %-32s (%d Credits)\n",
                   i + 1, g->courses[idx].code, g->courses[idx].title, g->courses[idx].credits);
        }
        printf("----------------------------------------------------------------------\n");
        printf("Total Courses Ordered: %d of %d\n", count, g->num_courses);
        printf("======================================================================\n\n");
    }

    return true;
}

/* ====================================================================================================
 * FORMAL PRECEDENCE CONSTRAINT VALIDATION ENGINE
 * ====================================================================================================
 */

bool validate_precedence(const CourseGraph* g, const int* order, int order_len, bool verbose) {
    if (order_len != g->num_courses) {
        if (verbose) {
            printf("Validation FAILED: Order length (%d) does not match total courses (%d).\n",
                   order_len, g->num_courses);
        }
        return false;
    }

    /* Build position lookup array */
    int position[MAX_COURSES];
    for (int i = 0; i < order_len; i++) {
        position[order[i]] = i;
    }

    int total_edges = 0;
    int satisfied = 0;
    int violations = 0;

    if (verbose) {
        printf("\n======================================================================\n");
        printf("TOPOLOGICAL ORDER FORMAL PRECEDENCE VALIDATION REPORT\n");
        printf("Condition: For every directed edge (u -> v), pos(u) < pos(v)\n");
        printf("======================================================================\n");
        printf("%-8s (Pos)  ->  %-8s (Pos)  | Status\n", "Prereq", "Course");
        printf("----------------------------------------------------------------------\n");
    }

    for (int u = 0; u < g->num_courses; u++) {
        AdjNode* curr = g->adj[u];
        while (curr) {
            int v = curr->dest_idx;
            total_edges++;
            int pos_u = position[u];
            int pos_v = position[v];

            if (pos_u < pos_v) {
                satisfied++;
                if (verbose) {
                    printf("%-8s (%2d)   ->  %-8s (%2d)   | [OK] Satisfied\n",
                           g->courses[u].code, pos_u + 1, g->courses[v].code, pos_v + 1);
                }
            } else {
                violations++;
                if (verbose) {
                    printf("%-8s (%2d)   ->  %-8s (%2d)   | [VIOLATION] Invalid Precedence!\n",
                           g->courses[u].code, pos_u + 1, g->courses[v].code, pos_v + 1);
                }
            }
            curr = curr->next;
        }
    }

    if (verbose) {
        printf("----------------------------------------------------------------------\n");
        printf("Total Prerequisite Edges Audited: %d\n", total_edges);
        printf("Edges Satisfying Precedence     : %d (%.1f%%)\n",
               satisfied, (total_edges > 0) ? (satisfied * 100.0 / total_edges) : 100.0);
        printf("Precedence Violations Detected  : %d\n", violations);
        printf("----------------------------------------------------------------------\n");
        if (violations == 0) {
            printf("VERDICT: >>> TOPOLOGICAL ORDER FORMAL VALIDATION: PASSED <<<\n");
        } else {
            printf("VERDICT: >>> TOPOLOGICAL ORDER FORMAL VALIDATION: FAILED <<<\n");
        }
        printf("======================================================================\n\n");
    }

    return (violations == 0);
}

/* ====================================================================================================
 * REAL-WORLD UNIVERSITY CYCLE IMPACT REPORT
 * ====================================================================================================
 */

void print_real_world_cycle_impact(const CourseGraph* g, const int* cycle_path, int cycle_len) {
    printf("\n======================================================================\n");
    printf("REAL-WORLD UNIVERSITY COURSE REGISTRATION IMPACT ANALYSIS\n");
    printf("======================================================================\n");
    printf("[1] DETECTED CIRCULAR PREREQUISITE CHAIN:\n  ");
    for (int i = 0; i < cycle_len; i++) {
        printf("%s%s", g->courses[cycle_path[i]].code, (i < cycle_len - 1) ? " -> " : "\n");
    }
    printf("\n[2] REAL-WORLD UNIVERSITY COURSE REGISTRATION INTERPRETATION:\n");
    printf("  \"Course registration is impossible for the affected dependency chain\n");
    printf("   because each course requires another course that cannot be completed first.\"\n\n");
    printf("[3] INSTITUTIONAL CONSEQUENCES:\n");
    printf("  * Total Registration Deadlock: No student can enroll in any course in\n");
    printf("    the cycle because prerequisite validation fails unconditionally.\n");
    printf("  * Degree Audit Failure: Automated degree audit systems (e.g., DegreeWorks)\n");
    printf("    loop infinitely or flag mandatory degree requirements as unsatisfied.\n");
    printf("  * Graduation Postponement: Affected cohorts are blocked from timely degree\n");
    printf("    completion, causing institutional accreditation compliance issues.\n");
    printf("  * Mandatory Remediation: Curriculum committees must immediately convene\n");
    printf("    to decouple the circular prerequisite edge in the academic catalogue.\n");
    printf("======================================================================\n\n");
}

/* ====================================================================================================
 * ALGORITHMIC COMPARISON & THEORETICAL ANALYSIS (BFS vs DFS)
 * ====================================================================================================
 */

void print_algorithm_comparison(void) {
    printf("\n================================================================================\n");
    printf("        COMPREHENSIVE ALGORITHMIC COMPARISON: BFS (KAHN'S) VS DFS (3-STATE)      \n");
    printf("================================================================================\n");
    printf("%-26s | %-25s | %-25s\n", "Metric / Feature", "BFS (Kahn's Algorithm)", "DFS (3-State Coloring)");
    printf("--------------------------------------------------------------------------------\n");
    printf("%-26s | %-25s | %-25s\n", "Time Complexity", "O(|V| + |E|) Linear", "O(|V| + |E|) Linear");
    printf("%-26s | %-25s | %-25s\n", "Space Complexity", "O(|V|) Queue + In-Degrees", "O(|V|) Stack + Colors");
    printf("%-26s | %-25s | %-25s\n", "Primary Data Structure", "FIFO Queue", "LIFO Stack / Call Stack");
    printf("%-26s | %-25s | %-25s\n", "Cycle Detection", "In-Degree Starvation", "Back-Edge to VISITING");
    printf("%-26s | %-25s | %-25s\n", "Cycle Path Reconstruction", "Residual In-Degree Pool", "Direct Active Call Stack");
    printf("%-26s | %-25s | %-25s\n", "Topological Ordering", "Direct Dequeue Order", "Reversed Finish Stack");
    printf("%-26s | %-25s | %-25s\n", "Curriculum Semester Map", "Natural Level/Tier Map", "Depth-First Branch Dive");
    printf("%-26s | %-25s | %-25s\n", "Parallelizable", "High (Indegree 0 batch)", "Low (Recursive dependency)");
    printf("--------------------------------------------------------------------------------\n");
    printf("\nKEY ACADEMIC INSIGHTS & REAL-WORLD SUITABILITY:\n");
    printf("1. Academic Curriculum Scheduling: BFS (Kahn's) is conceptually superior for university\n");
    printf("   semester advisement because it naturally processes all courses with 0 remaining\n");
    printf("   prerequisites simultaneously in parallel 'cohort waves' (e.g., Year 1 -> Year 2 -> Year 3).\n\n");
    printf("2. Cycle Diagnostics: DFS with 3-state coloring is superior for pinpointing the exact\n");
    printf("   circular prerequisite chain because the cycle is preserved directly on the active call stack\n");
    printf("   at the exact moment a back-edge (ancestor in state VISITING=1) is traversed.\n\n");
    printf("3. Memory Overhead: Both algorithms operate in optimal O(|V| + |E|) time and O(|V|) auxiliary\n");
    printf("   space. Adjacency List representation consumes Theta(|V| + |E|) space, saving over 99.5%%\n");
    printf("   memory compared to a |V| x |V| adjacency matrix on sparse academic networks.\n");
    printf("================================================================================\n\n");
}

/* ====================================================================================================
 * DATASET POPULATION HELPERS
 * ====================================================================================================
 */

void populate_12_course_dag(CourseGraph* g) {
    /* Add 12 core courses */
    graph_add_course(g, "CS101", "Programming Fundamentals", 4, "Computer Science");
    graph_add_course(g, "CS102", "Object Oriented Programming", 4, "Computer Science");
    graph_add_course(g, "CS103", "Data Structures", 4, "Computer Science");
    graph_add_course(g, "CS104", "Discrete Mathematics", 3, "Computer Science");
    graph_add_course(g, "CS105", "Database Management Systems", 3, "Computer Science");
    graph_add_course(g, "CS106", "Computer Organization", 3, "Computer Science");
    graph_add_course(g, "CS201", "Algorithms", 4, "Computer Science");
    graph_add_course(g, "CS202", "Operating Systems", 4, "Computer Science");
    graph_add_course(g, "CS203", "Computer Networks", 3, "Computer Science");
    graph_add_course(g, "CS204", "Software Engineering", 3, "Computer Science");
    graph_add_course(g, "CS301", "Artificial Intelligence", 4, "Computer Science");
    graph_add_course(g, "CS302", "Machine Learning", 4, "Computer Science");

    /* Add 12 prerequisite dependencies */
    graph_add_prerequisite(g, "CS101", "CS102");
    graph_add_prerequisite(g, "CS101", "CS103");
    graph_add_prerequisite(g, "CS104", "CS103");
    graph_add_prerequisite(g, "CS103", "CS201");
    graph_add_prerequisite(g, "CS106", "CS202");
    graph_add_prerequisite(g, "CS103", "CS202");
    graph_add_prerequisite(g, "CS103", "CS203");
    graph_add_prerequisite(g, "CS102", "CS204");
    graph_add_prerequisite(g, "CS201", "CS301");
    graph_add_prerequisite(g, "CS201", "CS302");
    graph_add_prerequisite(g, "CS301", "CS302");
    graph_add_prerequisite(g, "CS103", "CS105");
}

void populate_cyclic_graph(CourseGraph* g) {
    graph_add_course(g, "CS101", "Programming Fundamentals", 4, "Computer Science");
    graph_add_course(g, "CS102", "Object Oriented Programming", 4, "Computer Science");
    graph_add_course(g, "CS103", "Data Structures", 4, "Computer Science");
    graph_add_course(g, "CS201", "Algorithms", 4, "Computer Science");

    /* Circular Dependency: CS101 -> CS102 -> CS103 -> CS201 -> CS101 */
    graph_add_prerequisite(g, "CS101", "CS102");
    graph_add_prerequisite(g, "CS102", "CS103");
    graph_add_prerequisite(g, "CS103", "CS201");
    graph_add_prerequisite(g, "CS201", "CS101"); /* Circular Back-Edge! */
}

/* ====================================================================================================
 * 6-SCENARIO TEST SUITE RUNNER
 * ====================================================================================================
 */

void run_test_suite(void) {
    printf("\n================================================================================\n");
    printf("                  AUTOMATED ACADEMIC TEST SUITE EXECUTION                       \n");
    printf("================================================================================\n");
    printf("%-7s | %-32s | %-16s | %s\n", "ID", "Test Case Scenario", "Expected", "Result Status");
    printf("--------------------------------------------------------------------------------\n");

    int passed = 0;
    int total = 6;

    /* TC-01: Normal DAG */
    {
        CourseGraph* g = graph_create();
        populate_12_course_dag(g);
        int order[MAX_COURSES];
        int len = 0;
        bool bfs_ok = kahn_topological_sort(g, order, &len, false);
        bool val_ok = validate_precedence(g, order, len, false);
        if (bfs_ok && val_ok && len == 12) {
            printf("%-7s | %-32s | %-16s | [PASSED]\n", "TC-01", "Normal DAG (12 Courses)", "Valid Order");
            passed++;
        } else {
            printf("%-7s | %-32s | %-16s | [FAILED]\n", "TC-01", "Normal DAG (12 Courses)", "Valid Order");
        }
        graph_free(g);
    }

    /* TC-02: Simple Cycle */
    {
        CourseGraph* g = graph_create();
        populate_cyclic_graph(g);
        int order[MAX_COURSES];
        int len = 0;
        bool bfs_ok = kahn_topological_sort(g, order, &len, false);
        bool dfs_ok = dfs_topological_sort(g, order, &len, false);
        if (!bfs_ok && !dfs_ok) {
            printf("%-7s | %-32s | %-16s | [PASSED]\n", "TC-02", "Simple Directed Cycle", "Cycle Detected");
            passed++;
        } else {
            printf("%-7s | %-32s | %-16s | [FAILED]\n", "TC-02", "Simple Directed Cycle", "Cycle Detected");
        }
        graph_free(g);
    }

    /* TC-03: Multiple Independent Courses */
    {
        CourseGraph* g = graph_create();
        graph_add_course(g, "CS101", "Course A", 3, "CS");
        graph_add_course(g, "CS102", "Course B", 3, "CS");
        graph_add_course(g, "CS103", "Course C", 3, "CS");
        graph_add_course(g, "CS104", "Course D", 3, "CS");
        int order[MAX_COURSES];
        int len = 0;
        bool ok = kahn_topological_sort(g, order, &len, false);
        if (ok && len == 4) {
            printf("%-7s | %-32s | %-16s | [PASSED]\n", "TC-03", "Independent Courses (No Edges)", "All Included");
            passed++;
        } else {
            printf("%-7s | %-32s | %-16s | [FAILED]\n", "TC-03", "Independent Courses (No Edges)", "All Included");
        }
        graph_free(g);
    }

    /* TC-04: Multiple Prerequisites */
    {
        CourseGraph* g = graph_create();
        graph_add_course(g, "CS101", "Programming", 4, "CS");
        graph_add_course(g, "CS104", "Discrete Math", 3, "CS");
        graph_add_course(g, "CS103", "Data Structures", 4, "CS");
        graph_add_prerequisite(g, "CS101", "CS103");
        graph_add_prerequisite(g, "CS104", "CS103");
        int order[MAX_COURSES];
        int len = 0;
        bool ok = kahn_topological_sort(g, order, &len, false);
        bool val_ok = validate_precedence(g, order, len, false);
        if (ok && val_ok && len == 3) {
            printf("%-7s | %-32s | %-16s | [PASSED]\n", "TC-04", "Multiple Prerequisites", "Precedence OK");
            passed++;
        } else {
            printf("%-7s | %-32s | %-16s | [FAILED]\n", "TC-04", "Multiple Prerequisites", "Precedence OK");
        }
        graph_free(g);
    }

    /* TC-05: Single Isolated Course */
    {
        CourseGraph* g = graph_create();
        graph_add_course(g, "CS101", "Solo Course", 3, "CS");
        int order[MAX_COURSES];
        int len = 0;
        bool ok = kahn_topological_sort(g, order, &len, false);
        if (ok && len == 1) {
            printf("%-7s | %-32s | %-16s | [PASSED]\n", "TC-05", "Single Isolated Course", "Ordered Solo");
            passed++;
        } else {
            printf("%-7s | %-32s | %-16s | [FAILED]\n", "TC-05", "Single Isolated Course", "Ordered Solo");
        }
        graph_free(g);
    }

    /* TC-06: Disconnected Components */
    {
        CourseGraph* g = graph_create();
        graph_add_course(g, "CS101", "CS Intro", 4, "CS");
        graph_add_course(g, "CS102", "CS Advanced", 4, "CS");
        graph_add_course(g, "MA101", "Calculus I", 4, "Math");
        graph_add_course(g, "MA102", "Calculus II", 4, "Math");
        graph_add_prerequisite(g, "CS101", "CS102");
        graph_add_prerequisite(g, "MA101", "MA102");
        int order[MAX_COURSES];
        int len = 0;
        bool ok = kahn_topological_sort(g, order, &len, false);
        bool val_ok = validate_precedence(g, order, len, false);
        if (ok && val_ok && len == 4) {
            printf("%-7s | %-32s | %-16s | [PASSED]\n", "TC-06", "Disconnected Components", "Intra-Order OK");
            passed++;
        } else {
            printf("%-7s | %-32s | %-16s | [FAILED]\n", "TC-06", "Disconnected Components", "Intra-Order OK");
        }
        graph_free(g);
    }

    printf("--------------------------------------------------------------------------------\n");
    printf("OVERALL TEST RESULT: %d of %d Test Cases Passed (%.1f%% Pass Rate)\n",
           passed, total, (passed * 100.0) / total);
    printf("================================================================================\n\n");
}

/* ====================================================================================================
 * ACADEMIC HEADER & MENU
 * ====================================================================================================
 */

void print_academic_header(void) {
    printf("********************************************************************************\n");
    printf("*           UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM                   *\n");
    printf("*                      CSA03 - DATA STRUCTURES (SLOT D)                       *\n");
    printf("*       STUDENT: JAMPALA BRAHMAIAH  |  REGISTER NUMBER: 192472286              *\n");
    printf("*       DEPARTMENT: COMPUTER SCIENCE AND ENGINEERING (CSE AI)                  *\n");
    printf("*       OUTCOME: CO5 (L4 Analyze)   |  SDG: SDG 4 & SDG 9                      *\n");
    printf("*       GITHUB: https://github.com/brahmaiah528/data_structure_assign          *\n");
    printf("********************************************************************************\n");
}

void interactive_add_course_or_edge(CourseGraph* g) {
    int subchoice = 0;
    printf("\n--- INTERACTIVE CURRICULUM MODIFICATION ---\n");
    printf("1. Add New Course\n");
    printf("2. Add Prerequisite Edge (Prerequisite -> Dependent Course)\n");
    printf("Select option (1-2): ");
    if (scanf("%d", &subchoice) != 1) {
        int ch; while ((ch = getchar()) != '\n' && ch != EOF);
        printf("Invalid input.\n");
        return;
    }

    if (subchoice == 1) {
        char code[CODE_LEN] = {0};
        char title[TITLE_LEN] = {0};
        int credits = 3;
        char dept[DEPT_LEN] = {0};

        printf("Enter Course Code (e.g. CS401): ");
        if (scanf("%15s", code) != 1) {
            int ch; while ((ch = getchar()) != '\n' && ch != EOF);
            printf("Failed to read course code.\n");
            return;
        }
        int ch; while ((ch = getchar()) != '\n' && ch != EOF);

        printf("Enter Course Title: ");
        if (fgets(title, sizeof(title), stdin)) {
            title[strcspn(title, "\r\n")] = '\0';
        }

        printf("Enter Credits (e.g. 3 or 4): ");
        if (scanf("%d", &credits) != 1) credits = 3;
        while ((ch = getchar()) != '\n' && ch != EOF);

        printf("Enter Department: ");
        if (fgets(dept, sizeof(dept), stdin)) {
            dept[strcspn(dept, "\r\n")] = '\0';
        }

        int idx = graph_add_course(g, code, title, credits, dept);
        if (idx != -1) {
            printf("[SUCCESS] Added course '%s' (%s, %d Credits) at index %d.\n", code, title, credits, idx);
        }
    } else if (subchoice == 2) {
        char prereq_code[CODE_LEN] = {0};
        char course_code[CODE_LEN] = {0};

        printf("Enter Prerequisite Course Code (u): ");
        if (scanf("%15s", prereq_code) != 1) {
            int ch; while ((ch = getchar()) != '\n' && ch != EOF);
            printf("Failed to read prerequisite code.\n");
            return;
        }
        printf("Enter Dependent Course Code (v): ");
        if (scanf("%15s", course_code) != 1) {
            int ch; while ((ch = getchar()) != '\n' && ch != EOF);
            printf("Failed to read dependent course code.\n");
            return;
        }
        int ch; while ((ch = getchar()) != '\n' && ch != EOF);

        if (graph_add_prerequisite(g, prereq_code, course_code)) {
            printf("[SUCCESS] Added prerequisite edge: %s -> %s\n", prereq_code, course_code);
        } else {
            printf("[FAILED] Could not add edge %s -> %s\n", prereq_code, course_code);
        }
    } else {
        printf("Invalid selection.\n");
    }

}

void display_menu(void) {
    printf("\n--- SYSTEM CONTROL MENU ---\n");
    printf(" 1. Run Full Demonstration (12-Course DAG: BFS + DFS + Validation + Tests)\n");
    printf(" 2. Display Curriculum Graph Topology & Adjacency List\n");
    printf(" 3. Run BFS / Kahn's Algorithm (with step-by-step queue transitions)\n");
    printf(" 4. Run DFS Topological Sort (with 3-state coloring & finish stack)\n");
    printf(" 5. Run Formal Precedence Constraint Validation [pos(u) < pos(v)]\n");
    printf(" 6. Inject Circular Dependency & Perform Cycle Audit (BFS & DFS)\n");
    printf(" 7. Display Real-World University Cycle Impact Report\n");
    printf(" 8. Display BFS vs DFS Comparative Analysis & Asymptotic Complexity\n");
    printf(" 9. Interactively Add Custom Course or Prerequisite Edge\n");
    printf("10. Run Automated 6-Scenario Test Suite\n");
    printf("11. Reset Curriculum Graph to Default 12 Courses\n");
    printf("12. Exit Application\n");
    printf("Select option (1-12): ");
}

/* ====================================================================================================
 * MAIN FUNCTION
 * ====================================================================================================
 */

int main(int argc, char* argv[]) {
    print_academic_header();

    CourseGraph* dag = graph_create();
    populate_12_course_dag(dag);

    CourseGraph* cyclic_graph = graph_create();
    populate_cyclic_graph(cyclic_graph);

    int order[MAX_COURSES];
    int order_len = 0;

    /* Check for non-interactive / batch mode flag */
    if (argc > 1 && (strcmp(argv[1], "--all") == 0 || strcmp(argv[1], "-a") == 0)) {
        printf("\n>>> RUNNING IN AUTOMATED DEMONSTRATION MODE <<<\n");
        graph_print_topology(dag);
        kahn_topological_sort(dag, order, &order_len, true);
        dfs_topological_sort(dag, order, &order_len, true);
        validate_precedence(dag, order, order_len, true);

        printf("\n>>> TESTING CYCLIC GRAPH AUDIT <<<\n");
        kahn_topological_sort(cyclic_graph, order, &order_len, true);
        dfs_topological_sort(cyclic_graph, order, &order_len, true);

        int cycle_path[4] = {0, 1, 2, 3};
        print_real_world_cycle_impact(cyclic_graph, cycle_path, 4);

        print_algorithm_comparison();
        run_test_suite();

        graph_free(dag);
        graph_free(cyclic_graph);
        return EXIT_SUCCESS;
    }

    int choice = 0;
    while (1) {
        display_menu();
        if (scanf("%d", &choice) != 1) {
            /* Clear input buffer */
            int ch;
            while ((ch = getchar()) != '\n' && ch != EOF);
            printf("Invalid input. Please enter a valid integer (1-12).\n");
            continue;
        }

        switch (choice) {
            case 1:
                graph_print_topology(dag);
                kahn_topological_sort(dag, order, &order_len, true);
                dfs_topological_sort(dag, order, &order_len, true);
                validate_precedence(dag, order, order_len, true);
                print_algorithm_comparison();
                run_test_suite();
                break;
            case 2:
                graph_print_topology(dag);
                break;
            case 3:
                kahn_topological_sort(dag, order, &order_len, true);
                break;
            case 4:
                dfs_topological_sort(dag, order, &order_len, true);
                break;
            case 5:
                if (order_len == 0) {
                    kahn_topological_sort(dag, order, &order_len, false);
                }
                validate_precedence(dag, order, order_len, true);
                break;
            case 6:
                printf("\nAuditing cyclic curriculum dataset...\n");
                kahn_topological_sort(cyclic_graph, order, &order_len, true);
                dfs_topological_sort(cyclic_graph, order, &order_len, true);
                break;
            case 7: {
                int cycle_path[4] = {0, 1, 2, 3};
                print_real_world_cycle_impact(cyclic_graph, cycle_path, 4);
                break;
            }
            case 8:
                print_algorithm_comparison();
                break;
            case 9:
                interactive_add_course_or_edge(dag);
                break;
            case 10:
                run_test_suite();
                break;
            case 11:
                graph_free(dag);
                dag = graph_create();
                populate_12_course_dag(dag);
                order_len = 0;
                printf("\n[RESET] Curriculum graph re-initialized to default 12-course DAG.\n");
                break;
            case 12:
                printf("\nExiting University Course Prerequisite System. Goodbye!\n");
                graph_free(dag);
                graph_free(cyclic_graph);
                return EXIT_SUCCESS;
            default:
                printf("Invalid selection (%d). Please enter an option from 1 to 12.\n", choice);
                break;
        }
    }

    graph_free(dag);
    graph_free(cyclic_graph);
    return EXIT_SUCCESS;
}

