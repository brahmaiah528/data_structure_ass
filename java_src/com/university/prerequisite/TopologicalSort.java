package com.university.prerequisite;

import java.util.*;

/**
 * Implements BFS (Kahn's) and DFS Topological Sort algorithms in Java.
 */
public class TopologicalSort {

    public static class Result {
        public final String algorithm;
        public boolean success;
        public boolean hasCycle;
        public final List<String> order = new ArrayList<>();
        public final Map<String, Integer> initialIndegrees = new TreeMap<>();
        public final List<String> steps = new ArrayList<>();
        public String cycleInfo;

        public Result(String algorithm) {
            this.algorithm = algorithm;
        }

        public String formatReport(CourseGraph graph) {
            StringBuilder sb = new StringBuilder();
            sb.append("======================================================================\n");
            sb.append(algorithm.toUpperCase()).append(" TOPOLOGICAL SORT RESULT\n");
            sb.append("======================================================================\n\n");

            sb.append("[1] INITIAL INDEGREES (Number of Direct Prerequisites):\n");
            sb.append("-------------------------------------------------------\n");
            for (Map.Entry<String, Integer> e : initialIndegrees.entrySet()) {
                Course c = graph.getCourse(e.getKey());
                String title = c != null ? c.getTitle() : "";
                sb.append(String.format("  %-8s = %-3d (%s)\n", e.getKey(), e.getValue(), title));
            }

            sb.append("\n[2] STEP-BY-STEP EXECUTION TRACE:\n");
            sb.append("-------------------------------------------------------\n");
            for (int i = 0; i < steps.size(); i++) {
                sb.append(String.format("  Step %2d: %s\n", (i + 1), steps.get(i)));
            }

            sb.append("\n[3] CYCLE STATUS & VERDICT:\n");
            sb.append("-------------------------------------------------------\n");
            if (hasCycle) {
                sb.append("  STATUS: CYCLE DETECTED!\n");
                sb.append("  DIAGNOSIS: ").append(cycleInfo).append("\n");
                sb.append("  NOTE: Topological ordering cannot be generated.\n");
            } else {
                sb.append("  STATUS: NO CYCLE DETECTED (Valid DAG)\n");
            }

            sb.append("\n[4] FINAL COURSE-TAKING ORDER:\n");
            sb.append("-------------------------------------------------------\n");
            if (success && !order.isEmpty()) {
                for (int i = 0; i < order.size(); i++) {
                    String code = order.get(i);
                    Course c = graph.getCourse(code);
                    String title = c != null ? c.getTitle() : "";
                    int cred = c != null ? c.getCredits() : 3;
                    sb.append(String.format("  %2d. %s – %s (%d Credits)\n", (i + 1), code, title, cred));
                }
            } else {
                sb.append("  None (Aborted due to circular dependency)\n");
            }
            sb.append("======================================================================\n");
            return sb.toString();
        }
    }

    public static Result kahnSort(CourseGraph graph) {
        Result res = new Result("BFS / Kahn's Algorithm");
        int totalV = graph.getNumVertices();
        if (totalV == 0) {
            res.success = true;
            return res;
        }

        Map<String, Integer> indegrees = graph.calculateIndegrees();
        res.initialIndegrees.putAll(indegrees);
        Map<String, Integer> working = new HashMap<>(indegrees);

        Queue<String> queue = new LinkedList<>();
        for (String c : graph.getCourses().keySet()) {
            if (working.get(c) == 0) queue.offer(c);
        }

        res.steps.add("Queue initialized with In-Degree 0: " + queue);

        while (!queue.isEmpty()) {
            String curr = queue.poll();
            res.order.add(curr);
            Course c = graph.getCourse(curr);
            String title = c != null ? c.getTitle() : "";

            List<String> dependents = graph.getAdjList().get(curr);
            List<String> updates = new ArrayList<>();

            if (dependents != null) {
                for (String neighbor : dependents) {
                    int newDeg = working.get(neighbor) - 1;
                    working.put(neighbor, newDeg);
                    if (newDeg == 0) {
                        queue.offer(neighbor);
                        updates.add(neighbor + " (deg -> 0, ENQ)");
                    } else {
                        updates.add(neighbor + " (deg -> " + newDeg + ")");
                    }
                }
            }

            res.steps.add(String.format("Dequeued '%s' (%s) -> Dependents: %s -> Queue: %s",
                    curr, title, (updates.isEmpty() ? "None" : String.join(", ", updates)), queue));
        }

        if (res.order.size() == totalV) {
            res.success = true;
            res.hasCycle = false;
        } else {
            res.success = false;
            res.hasCycle = true;
            res.cycleInfo = "Queue exhausted after ordering " + res.order.size() + " of " + totalV + " courses.";
        }
        return res;
    }

    public static Result dfsSort(CourseGraph graph) {
        Result res = new Result("DFS Topological Sort");
        int totalV = graph.getNumVertices();
        if (totalV == 0) {
            res.success = true;
            return res;
        }

        final int UNVISITED = 0, VISITING = 1, VISITED = 2;
        Map<String, Integer> state = new HashMap<>();
        for (String c : graph.getCourses().keySet()) state.put(c, UNVISITED);
        res.initialIndegrees.putAll(graph.calculateIndegrees());

        List<String> recStack = new ArrayList<>();
        Deque<String> finishStack = new ArrayDeque<>();
        boolean[] cycleFound = {false};
        List<String> cyclePath = new ArrayList<>();

        class DFSHelper {
            boolean dfs(String u) {
                state.put(u, VISITING);
                recStack.add(u);
                res.steps.add("Enter DFS(" + u + ") -> State: VISITING | Stack: " + recStack);

                List<String> neighbors = graph.getAdjList().get(u);
                if (neighbors != null) {
                    for (String v : neighbors) {
                        if (state.get(v) == VISITING) {
                            cycleFound[0] = true;
                            int idx = recStack.indexOf(v);
                            cyclePath.addAll(recStack.subList(idx, recStack.size()));
                            cyclePath.add(v);
                            res.steps.add("Back-Edge found from " + u + " to " + v + "! Cycle: " + cyclePath);
                            return false;
                        } else if (state.get(v) == UNVISITED) {
                            if (!dfs(v)) return false;
                        }
                    }
                }

                state.put(u, VISITED);
                recStack.remove(recStack.size() - 1);
                finishStack.push(u);
                res.steps.add("Exit DFS(" + u + ") -> State: VISITED | Pushed to Finish Stack");
                return true;
            }
        }

        DFSHelper helper = new DFSHelper();
        for (String code : graph.getCourses().keySet()) {
            if (state.get(code) == UNVISITED) {
                if (!helper.dfs(code)) break;
            }
        }

        if (cycleFound[0]) {
            res.success = false;
            res.hasCycle = true;
            res.cycleInfo = "Back edge found during DFS recursion traversal. Cycle: " + String.join(" -> ", cyclePath);
        } else {
            res.success = true;
            res.hasCycle = false;
            while (!finishStack.isEmpty()) {
                res.order.add(finishStack.pop());
            }
        }
        return res;
    }
}
