package com.university.prerequisite;

import java.util.*;

/**
 * Cycle Detector module in Java (BFS & DFS).
 */
public class CycleDetector {

    public static class Report {
        public final String method;
        public boolean cycleDetected;
        public final List<String> cyclePath = new ArrayList<>();
        public final List<String> affectedCourses = new ArrayList<>();
        public String diagnosis;

        public Report(String method) {
            this.method = method;
        }

        public String formatReport() {
            StringBuilder sb = new StringBuilder();
            sb.append("======================================================================\n");
            sb.append("CYCLE DETECTION REPORT – [").append(method.toUpperCase()).append("]\n");
            sb.append("======================================================================\n");
            if (cycleDetected) {
                sb.append("STATUS: >>> CYCLE DETECTED! <<<\n\n");
                if (!cyclePath.isEmpty()) {
                    sb.append("  Cycle Chain: ").append(String.join(" -> ", cyclePath)).append("\n");
                }
                sb.append("  Affected Courses: ").append(affectedCourses).append("\n\n");
                sb.append("DIAGNOSIS:\n  ").append(diagnosis).append("\n\n");
                sb.append("REAL-WORLD INTERPRETATION:\n");
                sb.append("  \"Course registration is impossible for the affected dependency chain\n");
                sb.append("   because each course requires another course that cannot be completed first.\"\n");
            } else {
                sb.append("STATUS: NO CYCLE DETECTED (Valid DAG)\n");
            }
            sb.append("======================================================================\n");
            return sb.toString();
        }
    }

    public static Report detectCycleBFS(CourseGraph graph) {
        Report rep = new Report("BFS / Kahn's Algorithm");
        TopologicalSort.Result res = TopologicalSort.kahnSort(graph);
        if (res.hasCycle) {
            rep.cycleDetected = true;
            for (String c : graph.getCourses().keySet()) {
                if (!res.order.contains(c)) rep.affectedCourses.add(c);
            }
            rep.diagnosis = res.cycleInfo;
        }
        return rep;
    }

    public static Report detectCycleDFS(CourseGraph graph) {
        Report rep = new Report("DFS 3-State Stack");
        TopologicalSort.Result res = TopologicalSort.dfsSort(graph);
        if (res.hasCycle) {
            rep.cycleDetected = true;
            rep.diagnosis = res.cycleInfo;
            if (res.cycleInfo.contains("Cycle: ")) {
                String pathStr = res.cycleInfo.substring(res.cycleInfo.indexOf("Cycle: ") + 7);
                for (String p : pathStr.split(" -> ")) rep.cyclePath.add(p.trim());
                rep.affectedCourses.addAll(new TreeSet<>(rep.cyclePath));
            }
        }
        return rep;
    }
}
