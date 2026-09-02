package com.university.prerequisite;

import javax.swing.*;
import java.awt.*;
import java.util.List;

/**
 * Java Entry Point & Swing GUI for University Course Prerequisite Management System.
 * CSA03 – Data Structures (Slot D) | Outcome CO5 | SDG 4 & SDG 9
 */
public class Main {

    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("--cli")) {
            runCli();
        } else if (args.length > 0 && args[0].equals("--test")) {
            runTests();
        } else {
            SwingUtilities.invokeLater(Main::launchGUI);
        }
    }

    public static void runTests() {
        System.out.println("Running Java Test Verification...");
        CourseGraph g = new CourseGraph();
        g.loadSampleDataset();
        TopologicalSort.Result bfs = TopologicalSort.kahnSort(g);
        TopologicalSort.Result dfs = TopologicalSort.dfsSort(g);
        System.out.println("Sample DAG BFS Order: " + bfs.order);
        System.out.println("Sample DAG DFS Order: " + dfs.order);
        System.out.println("DAG Validation: " + (bfs.success && dfs.success ? "PASSED" : "FAILED"));

        g.loadCyclicDataset();
        CycleDetector.Report rep = CycleDetector.detectCycleDFS(g);
        System.out.println("Cyclic Detection: " + (rep.cycleDetected ? "PASSED" : "FAILED"));
    }

    public static void runCli() {
        CourseGraph g = new CourseGraph();
        g.loadSampleDataset();
        System.out.println("=== UNIVERSITY COURSE PREREQUISITE SYSTEM (JAVA CLI) ===");
        TopologicalSort.Result res = TopologicalSort.kahnSort(g);
        System.out.println(res.formatReport(g));
    }

    public static void launchGUI() {
        JFrame frame = new JFrame("University Course Prerequisite Management System - Java Swing");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(1050, 720);
        frame.setLocationRelativeTo(null);

        CourseGraph graph = new CourseGraph();
        graph.loadSampleDataset();

        JPanel rootPanel = new JPanel(new BorderLayout(8, 8));
        rootPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Header
        JPanel header = new JPanel(new GridLayout(2, 1));
        header.setBackground(new Color(30, 58, 138));
        JLabel title = new JLabel("  University Course Prerequisite Management System", JLabel.LEFT);
        title.setFont(new Font("Segoe UI", Font.BOLD, 18));
        title.setForeground(Color.WHITE);
        JLabel sub = new JLabel("   CSA03 – Data Structures (Slot D) | Outcome CO5 | SDG 4 & 9", JLabel.LEFT);
        sub.setFont(new Font("Segoe UI", Font.PLAIN, 12));
        sub.setForeground(new Color(199, 210, 254));
        header.add(title);
        header.add(sub);
        rootPanel.add(header, BorderLayout.NORTH);

        // Center Split: Left Controls, Right Output Console
        JPanel leftPanel = new JPanel();
        leftPanel.setLayout(new BoxLayout(leftPanel, BoxLayout.Y_AXIS));
        leftPanel.setPreferredSize(new Dimension(320, 600));

        JTextArea console = new JTextArea();
        console.setFont(new Font("Consolas", Font.PLAIN, 12));
        console.setEditable(false);
        JScrollPane scroll = new JScrollPane(console);

        // Buttons
        JButton btnBfs = new JButton("1. BFS / Kahn's Topological Sort");
        JButton btnDfs = new JButton("2. DFS Topological Sort (3-State)");
        JButton btnCycle = new JButton("3. Detect Cycle (Dual Engine)");
        JButton btnDisplay = new JButton("4. Display Graph & Adjacency List");
        JButton btnSample = new JButton("Load Sample 12-Course DAG");
        JButton btnCyclic = new JButton("Load Cyclic Demo Dataset");
        JButton btnClear = new JButton("Clear Graph");
        JButton btnExit = new JButton("Exit");

        for (JButton b : new JButton[]{btnBfs, btnDfs, btnCycle, btnDisplay, btnSample, btnCyclic, btnClear, btnExit}) {
            b.setMaximumSize(new Dimension(300, 35));
            b.setAlignmentX(Component.CENTER_ALIGNMENT);
            leftPanel.add(b);
            leftPanel.add(Box.createVerticalStrut(6));
        }

        btnBfs.addActionListener(e -> {
            TopologicalSort.Result r = TopologicalSort.kahnSort(graph);
            console.setText(r.formatReport(graph));
        });

        btnDfs.addActionListener(e -> {
            TopologicalSort.Result r = TopologicalSort.dfsSort(graph);
            console.setText(r.formatReport(graph));
        });

        btnCycle.addActionListener(e -> {
            CycleDetector.Report rBfs = CycleDetector.detectCycleBFS(graph);
            CycleDetector.Report rDfs = CycleDetector.detectCycleDFS(graph);
            console.setText(rBfs.formatReport() + "\n" + rDfs.formatReport());
        });

        btnDisplay.addActionListener(e -> {
            StringBuilder sb = new StringBuilder("=== CURRICULUM TOPOLOGY ===\n");
            for (String code : graph.getCourses().keySet()) {
                Course c = graph.getCourse(code);
                List<String> deps = graph.getAdjList().get(code);
                sb.append(String.format("%-8s (%s) -> %s\n", code, c.getTitle(), deps));
            }
            console.setText(sb.toString());
        });

        btnSample.addActionListener(e -> {
            graph.loadSampleDataset();
            console.setText("Loaded realistic 12-course sample DAG dataset.");
        });

        btnCyclic.addActionListener(e -> {
            graph.loadCyclicDataset();
            console.setText("Loaded cyclic dataset (CS101 -> CS102 -> CS103 -> CS201 -> CS101).\nClick 'Detect Cycle' to run diagnostic.");
        });

        btnClear.addActionListener(e -> {
            graph.clear();
            console.setText("Graph cleared. 0 courses registered.");
        });

        btnExit.addActionListener(e -> System.exit(0));

        rootPanel.add(leftPanel, BorderLayout.WEST);
        rootPanel.add(scroll, BorderLayout.CENTER);

        frame.setContentPane(rootPanel);
        console.setText("Loaded realistic sample university dataset (12 courses, DAG).\nClick any button on the left to execute graph algorithms.");
        frame.setVisible(true);
    }
}
