"""
Main Entry Point for the University Course Prerequisite Management System.

Course: CSA03 – Data Structures – Slot D
Outcome: CO5 – Develop robust graph-based solutions for real-world applications.
SDG Mapping: SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)

Usage:
  python main.py             # Launches both Desktop GUI and Localhost Web Server (http://localhost:8000)
  python main.py --server    # Runs Localhost Web Server exclusively
  python main.py --gui       # Runs Desktop Tkinter GUI exclusively
  python main.py --test      # Runs all 6 academic test cases with validation
  python main.py --cli       # Runs interactive terminal menu
"""

import sys
import os
import threading
import argparse

# Ensure project root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) if os.path.basename(CURRENT_DIR) == "src" else CURRENT_DIR
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.course_graph import CourseGraph
from src.topological_sort import TopologicalSort
from src.cycle_detector import CycleDetector
from src.validator import OrderValidator
from src.test_suite import TestSuite


def run_tests():
    """Executes all 6 academic test cases and displays complete audit report."""
    print("\n" + "=" * 80)
    print("RUNNING ACADEMIC TEST SUITE (6 MANDATORY SCENARIOS)".center(80))
    print("=" * 80)
    results = TestSuite.run_all_tests()
    print(TestSuite.format_summary_report(results))
    all_passed = all(r.status == "PASSED" for r in results)
    print(f"\nOverall Academic Test Suite Result: {'ALL TESTS PASSED [100%]' if all_passed else 'SOME TESTS FAILED'}")
    return 0 if all_passed else 1


def run_cli():
    """Interactive command-line interface for the course prerequisite system."""
    graph = CourseGraph()
    graph.load_sample_dataset()
    last_order = []

    print("\n" + "=" * 75)
    print("UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM (CLI MODE)".center(75))
    print("CSA03 – Data Structures (Slot D) | Outcome CO5 | SDG 4 & 9".center(75))
    print("=" * 75)

    while True:
        print("\n--- CURRICULUM MANAGEMENT MENU ---")
        print("1. Display Registered Courses & Adjacency List")
        print("2. Run BFS / Kahn's Algorithm (Topological Sort)")
        print("3. Run DFS Topological Sort (3-State Vertex Coloring)")
        print("4. Detect Dependency Cycles (Dual Engine: BFS & DFS)")
        print("5. Validate Topological Order [position(u) < position(v)]")
        print("6. Add New Course")
        print("7. Add Prerequisite Relationship (A -> B)")
        print("8. Load Sample DAG Dataset (12 Courses)")
        print("9. Load Cyclic Prerequisite Dataset (Cycle Demo)")
        print("10. Run All 6 Academic Test Cases")
        print("11. Clear Graph")
        print("12. Start Localhost Web Server (http://localhost:8000)")
        print("0. Exit Application")

        try:
            choice = input("\nEnter choice [0-12]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if choice == "0":
            print("Exiting University Course Prerequisite Management System. Goodbye!")
            break
        elif choice == "1":
            print("\n" + graph.display_courses_str())
            print("\n[Adjacency List (Out-Edges)]:")
            print(graph.display_adjacency_list_str())
            print("\n[Prerequisite Requirements (In-Edges)]:")
            print(graph.display_prerequisites_str())
        elif choice == "2":
            res = TopologicalSort.kahn_sort(graph)
            last_order = res.order if res.success else []
            print("\n" + res.format_report(graph))
        elif choice == "3":
            res = TopologicalSort.dfs_sort(graph)
            last_order = res.order if res.success else []
            print("\n" + res.format_report(graph))
        elif choice == "4":
            rep_bfs = CycleDetector.detect_cycle_bfs(graph)
            rep_dfs = CycleDetector.detect_cycle_dfs(graph)
            print("\n" + rep_bfs.format_report())
            print("\n" + rep_dfs.format_report())
        elif choice == "5":
            if not last_order:
                res = TopologicalSort.kahn_sort(graph)
                if res.success:
                    last_order = res.order
                else:
                    print("\n[!] Cannot validate: Current curriculum contains cycles. Generate a DAG first.")
                    continue
            val = OrderValidator.validate(graph, last_order)
            print("\n" + val.format_report())
        elif choice == "6":
            code = input("Enter Course Code (e.g., CS401): ").strip()
            title = input("Enter Course Title: ").strip()
            cred_str = input("Enter Credits [default 3]: ").strip()
            credits = int(cred_str) if cred_str.isdigit() else 3
            try:
                c = graph.add_course(code, title, credits)
                print(f"[OK] Added: {c.detailed_str()}")
            except Exception as e:
                print(f"[ERROR] {e}")
        elif choice == "7":
            prereq = input("Enter Prerequisite Course Code (A): ").strip()
            target = input("Enter Target Dependent Course Code (B): ").strip()
            try:
                graph.add_prerequisite(prereq, target)
                print(f"[OK] Dependency recorded: {prereq.upper()} -> {target.upper()}")
            except Exception as e:
                print(f"[ERROR] {e}")
        elif choice == "8":
            graph.load_sample_dataset()
            last_order = []
            print(f"[OK] Loaded 12-course sample DAG dataset ({graph.get_num_vertices()} vertices, {graph.get_num_edges()} edges).")
        elif choice == "9":
            graph.load_cyclic_dataset()
            last_order = []
            print(f"[OK] Loaded cyclic dataset (CS101 -> CS102 -> CS103 -> CS201 -> CS101).")
        elif choice == "10":
            results = TestSuite.run_all_tests()
            print(TestSuite.format_summary_report(results))
        elif choice == "11":
            graph.clear()
            last_order = []
            print("[OK] Curriculum graph cleared.")
        elif choice == "12":
            start_server_thread()
        else:
            print("[!] Invalid option. Please enter a number between 0 and 12.")


def start_server_thread(port: int = 8000):
    """Starts the localhost web server on a background daemon thread."""
    from src.server import run_server
    server = run_server(port)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"\n[+] Localhost Web Application active at: http://localhost:{port}/")
    return server


def main():
    parser = argparse.ArgumentParser(description="University Course Prerequisite Management System")
    parser.add_argument("--test", action="store_true", help="Run automated test suite and exit")
    parser.add_argument("--cli", action="store_true", help="Launch interactive terminal CLI menu")
    parser.add_argument("--server", action="store_true", help="Run localhost HTTP web server exclusively")
    parser.add_argument("--gui", action="store_true", help="Launch Desktop Tkinter GUI exclusively")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")

    args = parser.parse_args()

    if args.test:
        sys.exit(run_tests())
    elif args.cli:
        run_cli()
    elif args.server:
        print(f"Starting Localhost Web Server on port {args.port}...")
        from src.server import run_server
        server = run_server(args.port)
        print(f"Server is live at http://localhost:{args.port}/ (Press Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
    elif args.gui:
        from src.gui import run_gui
        run_gui()
    else:
        # Default behavior:
        # 1. Start web server in background thread so http://localhost:8000 is immediately live!
        # 2. Try launching Tkinter GUI. If no display is available (e.g. headless), fall back cleanly to server.
        print("\n" + "=" * 70)
        print("UNIVERSITY COURSE PREREQUISITE MANAGEMENT SYSTEM".center(70))
        print("CSA03 – Data Structures (Slot D) | Outcome CO5 | SDG 4 & 9".center(70))
        print("=" * 70)

        server = start_server_thread(args.port)

        try:
            import tkinter
            from src.gui import run_gui
            print("[+] Launching Desktop Tkinter GUI...")
            run_gui()
        except Exception as e:
            print(f"[*] Note: Desktop GUI not available in this environment ({e}).")
            print(f"[*] Localhost Web Dashboard is running at: http://localhost:{args.port}/")
            print("[*] Press Ctrl+C to exit.")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nExiting.")


if __name__ == "__main__":
    main()
