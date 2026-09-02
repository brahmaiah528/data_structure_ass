# Algorithmic Pseudocode Specification

**Course:** CSA03 – Data Structures (Slot D)  
**Outcome:** CO5 – Develop robust graph-based solutions by implementing and analyzing graph algorithms for real-world applications.  
**Project Title:** University Course Prerequisite Management System Using Topological Sort  

---

## 1. Graph Creation

```text
ALGORITHM InitializeCourseGraph()
INPUT: None
OUTPUT: An initialized CourseGraph instance

BEGIN
    INITIALIZE courses AS Empty HashTable (mapping: courseCode -> Course)
    INITIALIZE adjList AS Empty HashTable (mapping: courseCode -> List of courseCodes)
    INITIALIZE prereqMap AS Empty HashTable (mapping: courseCode -> List of courseCodes)
    RETURN CourseGraph(courses, adjList, prereqMap)
END
```

---

## 2. Adding a Course

```text
ALGORITHM AddCourse(graph, code, title, credits, department)
INPUT: graph, code (String), title (String), credits (Integer), department (String)
OUTPUT: Newly created Course object, or raises exception if duplicate

BEGIN
    sanitizedCode <- TrimAndUpperCase(code)
    sanitizedTitle <- Trim(title)
    
    IF sanitizedCode is Empty OR sanitizedTitle is Empty THEN
        RAISE ValueError("Course code and title cannot be blank.")
    END IF
    
    IF sanitizedCode EXISTS IN graph.courses THEN
        RAISE ValueError("Course already registered in graph.")
    END IF
    
    courseObj <- Instantiate Course(sanitizedCode, sanitizedTitle, credits, department)
    graph.courses[sanitizedCode] <- courseObj
    graph.adjList[sanitizedCode] <- Empty List
    graph.prereqMap[sanitizedCode] <- Empty List
    
    RETURN courseObj
END
```

---

## 3. Adding a Prerequisite Relationship (Directed Edge)

```text
ALGORITHM AddPrerequisite(graph, prereqCode, targetCode)
INPUT: graph, prereqCode (Course A), targetCode (Course B)
OUTPUT: None (Updates graph with directed edge A -> B)

BEGIN
    u <- TrimAndUpperCase(prereqCode)
    v <- TrimAndUpperCase(targetCode)
    
    IF u NOT IN graph.courses THEN
        RAISE KeyError("Prerequisite course does not exist.")
    END IF
    IF v NOT IN graph.courses THEN
        RAISE KeyError("Target course does not exist.")
    END IF
    IF u == v THEN
        RAISE ValueError("Self-loop prohibited: A course cannot require itself.")
    END IF
    IF v EXISTS IN graph.adjList[u] THEN
        RAISE ValueError("Prerequisite edge already exists.")
    END IF
    
    APPEND v TO graph.adjList[u]       // Outgoing edge: u enables v
    APPEND u TO graph.prereqMap[v]      // Incoming edge: v requires u
END
```

---

## 4. BFS / Kahn's Algorithm for Topological Sort

```text
ALGORITHM KahnTopologicalSort(graph)
INPUT: graph (CourseGraph with vertices V and directed edges E)
OUTPUT: topologicalOrder (List), cycleDetected (Boolean), traceLogs (List)

BEGIN
    totalVertices <- COUNT(graph.courses)
    topologicalOrder <- Empty List
    indegrees <- Empty HashTable
    
    // Step 1: Compute in-degree for every course vertex
    FOR EACH courseCode IN graph.courses DO
        indegrees[courseCode] <- 0
    END FOR
    FOR EACH u IN graph.courses DO
        FOR EACH v IN graph.adjList[u] DO
            indegrees[v] <- indegrees[v] + 1
        END FOR
    END FOR
    
    // Step 2: Initialize Queue with all vertices having in-degree 0
    queue <- Empty FIFO Queue
    FOR EACH courseCode IN SORTED(graph.courses) DO
        IF indegrees[courseCode] == 0 THEN
            ENQUEUE(queue, courseCode)
        END IF
    END FOR
    
    RECORD TRACE: "Queue initialized with in-degree 0 courses: " + queue
    
    // Step 3-7: Iteratively dequeue and decrement adjacent in-degrees
    WHILE queue IS NOT EMPTY DO
        curr <- DEQUEUE(queue)
        APPEND curr TO topologicalOrder
        
        FOR EACH dependent IN graph.adjList[curr] DO
            indegrees[dependent] <- indegrees[dependent] - 1
            IF indegrees[dependent] == 0 THEN
                ENQUEUE(queue, dependent)
                RECORD TRACE: dependent + " in-degree reached 0; added to Queue."
            END IF
        END FOR
    END WHILE
    
    // Step 8: Verify whether all vertices were processed
    IF LENGTH(topologicalOrder) == totalVertices THEN
        cycleDetected <- FALSE
        RETURN (topologicalOrder, cycleDetected, "Success")
    ELSE
        cycleDetected <- TRUE
        unprocessed <- ALL courses NOT IN topologicalOrder
        RETURN (Empty List, cycleDetected, "Cycle detected; unprocessed: " + unprocessed)
    END IF
END
```

---

## 5. DFS-Based Topological Sort (3-State Vertex Coloring)

```text
ALGORITHM DFSTopologicalSort(graph)
INPUT: graph (CourseGraph with vertices V and directed edges E)
OUTPUT: topologicalOrder (List), cycleDetected (Boolean), cyclePath (List)

BEGIN
    UNVISITED <- 0
    VISITING  <- 1  // In current recursion stack
    VISITED   <- 2  // Completely processed
    
    state <- Empty HashTable
    FOR EACH courseCode IN graph.courses DO
        state[courseCode] <- UNVISITED
    END FOR
    
    finishStack <- Empty LIFO Stack
    recursionStack <- Empty List
    cycleDetected <- FALSE
    cyclePath <- Empty List
    
    FUNCTION DFS(u)
        state[u] <- VISITING
        APPEND u TO recursionStack
        
        FOR EACH v IN graph.adjList[u] DO
            IF state[v] == VISITING THEN
                // Back-edge discovered: cycle detected!
                cycleDetected <- TRUE
                startIndex <- INDEX_OF(recursionStack, v)
                cyclePath <- SLICE(recursionStack, startIndex, END) + [v]
                RETURN FALSE
            ELSE IF state[v] == UNVISITED THEN
                IF NOT DFS(v) THEN
                    RETURN FALSE
                END IF
            END IF
        END FOR
        
        state[u] <- VISITED
        REMOVE_LAST(recursionStack)
        PUSH(finishStack, u)
        RETURN TRUE
    END FUNCTION
    
    // Outer loop to visit all components
    FOR EACH courseCode IN SORTED(graph.courses) DO
        IF state[courseCode] == UNVISITED THEN
            IF NOT DFS(courseCode) THEN
                BREAK
            END IF
        END IF
    END FOR
    
    IF cycleDetected THEN
        RETURN (Empty List, TRUE, cyclePath)
    ELSE
        topologicalOrder <- REVERSE(finishStack)
        RETURN (topologicalOrder, FALSE, Empty List)
    END IF
END
```

---

## 6. BFS Cycle Detection

```text
ALGORITHM DetectCycleBFS(graph)
INPUT: graph (CourseGraph)
OUTPUT: hasCycle (Boolean), unprocessedCourses (List)

BEGIN
    totalV <- COUNT(graph.courses)
    indegrees <- CalculateIndegrees(graph)
    queue <- Queue of all vertices with indegree == 0
    visitedCount <- 0
    
    WHILE queue IS NOT EMPTY DO
        curr <- DEQUEUE(queue)
        visitedCount <- visitedCount + 1
        FOR EACH v IN graph.adjList[curr] DO
            indegrees[v] <- indegrees[v] - 1
            IF indegrees[v] == 0 THEN
                ENQUEUE(queue, v)
            END IF
        END FOR
    END WHILE
    
    IF visitedCount < totalV THEN
        unprocessed <- Vertices with indegrees > 0
        RETURN (TRUE, unprocessed)
    ELSE
        RETURN (FALSE, Empty List)
    END IF
END
```

---

## 7. DFS Cycle Detection

```text
ALGORITHM DetectCycleDFS(graph)
INPUT: graph (CourseGraph)
OUTPUT: hasCycle (Boolean), exactCycleLoop (List)

BEGIN
    state <- Map all vertices to UNVISITED (0)
    recStack <- Empty List
    cycleLoop <- Empty List
    
    FUNCTION Explore(u)
        state[u] <- VISITING (1)
        APPEND u TO recStack
        
        FOR EACH v IN graph.adjList[u] DO
            IF state[v] == VISITING THEN
                cycleStart <- INDEX_OF(recStack, v)
                cycleLoop <- SLICE(recStack, cycleStart, END) + [v]
                RETURN TRUE
            ELSE IF state[v] == UNVISITED THEN
                IF Explore(v) THEN
                    RETURN TRUE
                END IF
            END IF
        END FOR
        
        state[u] <- VISITED (2)
        REMOVE_LAST(recStack)
        RETURN FALSE
    END FUNCTION
    
    FOR EACH courseCode IN graph.courses DO
        IF state[courseCode] == UNVISITED THEN
            IF Explore(courseCode) THEN
                RETURN (TRUE, cycleLoop)
            END IF
        END IF
    END FOR
    
    RETURN (FALSE, Empty List)
END
```

---

## 8. Topological Order Formal Validation

```text
ALGORITHM ValidateTopologicalOrder(graph, orderList)
INPUT: graph (CourseGraph), orderList (List of course codes)
OUTPUT: isValid (Boolean), auditReport (ValidationResult)

BEGIN
    IF LENGTH(orderList) != COUNT(graph.courses) THEN
        RETURN (FALSE, "Order does not contain all courses.")
    END IF
    
    positionMap <- Empty HashTable
    FOR i FROM 0 TO LENGTH(orderList) - 1 DO
        course <- orderList[i]
        positionMap[course] <- i
    END FOR
    
    FOR EACH u IN graph.courses DO
        FOR EACH v IN graph.adjList[u] DO
            posU <- positionMap[u]
            posV <- positionMap[v]
            
            // In a valid ordering, prerequisite u must precede dependent v
            IF posU >= posV THEN
                RETURN (FALSE, "Violation: " + u + " (pos " + posU + ") is not before " + v + " (pos " + posV + ")")
            END IF
        END FOR
    END FOR
    
    RETURN (TRUE, "Topological Order Validation: PASSED")
END
```
