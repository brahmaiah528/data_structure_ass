"""
Desktop GUI module for the University Course Prerequisite Management System.
Built with standard library Tkinter and TTK (Zero External Dependencies).

Course: CSA03 – Data Structures – Slot D
Outcome: CO5 – Develop robust graph-based solutions for real-world applications.
SDG: SDG 4 (Quality Education) & SDG 9 (Industry, Innovation and Infrastructure)
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

from src.course_graph import CourseGraph
from src.topological_sort import TopologicalSort
from src.cycle_detector import CycleDetector
from src.validator import OrderValidator
from src.test_suite import TestSuite
from src.database import DatabaseManager


class CoursePrerequisiteGUI:
    """Professional GUI Application for University Course Prerequisite Management."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("University Course Prerequisite Management System - CSE Department")
        self.root.geometry("1100x820")
        self.root.minsize(950, 680)

        # Database and Graph Model
        self.db = DatabaseManager()
        self.graph = self.db.load_graph_from_db()
        if self.graph.get_num_vertices() == 0:
            self.graph.load_sample_dataset()
            self.db.save_graph_to_db(self.graph)
        self.last_order = []

        # Configure Aesthetics & Styles
        self._configure_styles()
        self._build_layout()

        # Load initial sample dataset
        self.on_load_sample_data()

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Color Palette
        self.BG_MAIN = "#f8f9fa"
        self.PRIMARY = "#1e3a8a"      # Deep Navy
        self.SECONDARY = "#0284c7"    # Ocean Blue
        self.ACCENT = "#059669"       # Emerald Green
        self.WARNING = "#dc2626"      # Crimson Red
        self.PANEL_BG = "#ffffff"

        self.root.configure(bg=self.BG_MAIN)

        style.configure("Header.TFrame", background=self.PRIMARY)
        style.configure("HeaderTitle.TLabel", background=self.PRIMARY, foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("HeaderSub.TLabel", background=self.PRIMARY, foreground="#e0e7ff", font=("Segoe UI", 10))

        style.configure("Section.TLabelframe", background=self.PANEL_BG)
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=self.PRIMARY)

        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 9, "bold"), foreground=self.PRIMARY)
        style.configure("Warning.TButton", font=("Segoe UI", 9, "bold"), foreground=self.WARNING)

    def _build_layout(self):
        # 1. HEADER SECTION
        header_frame = ttk.Frame(self.root, style="Header.TFrame", padding=(15, 12))
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_lbl = ttk.Label(
            header_frame,
            text="University Course Prerequisite Management System",
            style="HeaderTitle.TLabel"
        )
        title_lbl.pack(anchor=tk.W)

        sub_lbl = ttk.Label(
            header_frame,
            text="CSA03 – Data Structures (Slot D) | Outcome CO5 | Topological Sort & Cycle Detection Engine (SDG 4 & 9)",
            style="HeaderSub.TLabel"
        )
        sub_lbl.pack(anchor=tk.W, pady=(2, 0))

        # MAIN CONTAINER
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # LEFT CONTROL PANEL (Inputs & Actions)
        left_panel = ttk.Frame(main_paned, width=380, padding=5)
        main_paned.add(left_panel, weight=0)

        # RIGHT DISPLAY PANEL (Output Console)
        right_panel = ttk.Frame(main_paned, padding=5)
        main_paned.add(right_panel, weight=1)

        # Build Sub-sections in Left Panel
        self._build_input_section(left_panel)
        self._build_prereq_section(left_panel)
        self._build_algorithm_section(left_panel)
        self._build_footer_buttons(left_panel)

        # Build Output Section in Right Panel
        self._build_output_section(right_panel)

    def _build_input_section(self, parent):
        box = ttk.LabelFrame(parent, text=" 1. Course Management ", style="Section.TLabelframe", padding=10)
        box.pack(fill=tk.X, pady=(0, 8))

        # Course Code
        lbl_code = ttk.Label(box, text="Course Code:")
        lbl_code.grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_code = ttk.Entry(box, width=12)
        self.entry_code.grid(row=0, column=1, sticky=tk.W, pady=2, padx=4)

        # Course Credits
        lbl_cred = ttk.Label(box, text="Credits:")
        lbl_cred.grid(row=0, column=2, sticky=tk.W, pady=2)
        self.spin_credits = ttk.Spinbox(box, from_=1, to=6, width=4)
        self.spin_credits.set(3)
        self.spin_credits.grid(row=0, column=3, sticky=tk.W, pady=2, padx=4)

        # Course Title
        lbl_title = ttk.Label(box, text="Course Name:")
        lbl_title.grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_title = ttk.Entry(box, width=28)
        self.entry_title.grid(row=1, column=1, columnspan=3, sticky=tk.EW, pady=2, padx=4)

        btn_add_course = ttk.Button(box, text="Add Course", command=self.on_add_course, style="Primary.TButton")
        btn_add_course.grid(row=2, column=0, columnspan=4, sticky=tk.EW, pady=(6, 2))

    def _build_prereq_section(self, parent):
        box = ttk.LabelFrame(parent, text=" 2. Prerequisite Dependencies ", style="Section.TLabelframe", padding=10)
        box.pack(fill=tk.X, pady=(0, 8))

        lbl_prereq = ttk.Label(box, text="Prerequisite (A):")
        lbl_prereq.grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_prereq = ttk.Entry(box, width=12)
        self.entry_prereq.grid(row=0, column=1, sticky=tk.W, pady=2, padx=4)

        lbl_target = ttk.Label(box, text="Target (B):")
        lbl_target.grid(row=0, column=2, sticky=tk.W, pady=2)
        self.entry_target = ttk.Entry(box, width=12)
        self.entry_target.grid(row=0, column=3, sticky=tk.W, pady=2, padx=4)

        note_lbl = ttk.Label(box, text="Dependency Rule: Course A must be completed before Course B (A -> B)", font=("Segoe UI", 8, "italic"))
        note_lbl.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(2, 4))

        btn_add_edge = ttk.Button(box, text="Add Prerequisite (A -> B)", command=self.on_add_prereq)
        btn_add_edge.grid(row=2, column=0, columnspan=4, sticky=tk.EW, pady=(2, 2))

        # Dataset loader buttons
        btn_sample = ttk.Button(box, text="Load Sample DAG Data (12 Courses)", command=self.on_load_sample_data)
        btn_sample.grid(row=3, column=0, columnspan=4, sticky=tk.EW, pady=(4, 2))

        btn_cyclic = ttk.Button(box, text="Load Cyclic Dataset (Cycle Demo)", command=self.on_load_cyclic_data)
        btn_cyclic.grid(row=4, column=0, columnspan=4, sticky=tk.EW, pady=(2, 2))

        btn_clear = ttk.Button(box, text="Clear Graph", command=self.on_clear_graph)
        btn_clear.grid(row=5, column=0, columnspan=4, sticky=tk.EW, pady=(2, 2))

    def _build_algorithm_section(self, parent):
        box = ttk.LabelFrame(parent, text=" 3. Graph Algorithms & Analysis ", style="Section.TLabelframe", padding=10)
        box.pack(fill=tk.X, pady=(0, 8))

        btn_bfs = ttk.Button(box, text="1. BFS / Kahn's Topological Sort", command=self.on_bfs_sort)
        btn_bfs.pack(fill=tk.X, pady=2)

        btn_dfs = ttk.Button(box, text="2. DFS Topological Sort", command=self.on_dfs_sort)
        btn_dfs.pack(fill=tk.X, pady=2)

        btn_cycle = ttk.Button(box, text="3. Detect Cycle (Dual Engine: BFS & DFS)", command=self.on_detect_cycle)
        btn_cycle.pack(fill=tk.X, pady=2)

        btn_display = ttk.Button(box, text="4. Display Graph & Adjacency List", command=self.on_display_graph)
        btn_display.pack(fill=tk.X, pady=2)

        btn_validate = ttk.Button(box, text="5. Validate Topological Order", command=self.on_validate_order)
        btn_validate.pack(fill=tk.X, pady=2)

        btn_tests = ttk.Button(box, text="6. Run All Test Cases (TC1 - TC6)", command=self.on_run_test_suite)
        btn_tests.pack(fill=tk.X, pady=2)

        btn_db_info = ttk.Button(box, text="7. Assignment Info & Rubrics (DB)", command=self.on_view_assignment_rubrics)
        btn_db_info.pack(fill=tk.X, pady=2)

        btn_db_save = ttk.Button(box, text="8. Save Graph to SQLite DB", command=self.on_save_db)
        btn_db_save.pack(fill=tk.X, pady=2)

        btn_db_load = ttk.Button(box, text="9. Load Graph from SQLite DB", command=self.on_load_db)
        btn_db_load.pack(fill=tk.X, pady=2)

    def _build_footer_buttons(self, parent):
        f_box = ttk.Frame(parent)
        f_box.pack(fill=tk.X, pady=(5, 0))

        btn_reset = ttk.Button(f_box, text="Reset", command=self.on_reset)
        btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        btn_exit = ttk.Button(f_box, text="Exit", command=self.root.quit, style="Warning.TButton")
        btn_exit.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

    def _build_output_section(self, parent):
        box = ttk.LabelFrame(parent, text=" Academic Diagnostics & Execution Output Console ", padding=8)
        box.pack(fill=tk.BOTH, expand=True)

        self.txt_output = scrolledtext.ScrolledText(
            box,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#111827",
            padx=10,
            pady=10
        )
        self.txt_output.pack(fill=tk.BOTH, expand=True)

    def _write_console(self, text: str, clear: bool = True):
        """Helper to write formatted text to console output."""
        if clear:
            self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, text + "\n")
        self.txt_output.see(tk.END)

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    def on_add_course(self):
        code = self.entry_code.get().strip()
        title = self.entry_title.get().strip()
        try:
            credits = int(self.spin_credits.get())
        except ValueError:
            credits = 3

        if not code or not title:
            messagebox.showerror("Validation Error", "Please provide both Course Code and Course Title.")
            return

        try:
            c = self.graph.add_course(code, title, credits)
            self._write_console(f"Successfully added course: {c.detailed_str()}")
            self.entry_code.delete(0, tk.END)
            self.entry_title.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error Adding Course", str(e))

    def on_add_prereq(self):
        prereq = self.entry_prereq.get().strip()
        target = self.entry_target.get().strip()

        if not prereq or not target:
            messagebox.showerror("Validation Error", "Please enter both Prerequisite code (A) and Target code (B).")
            return

        try:
            self.graph.add_prerequisite(prereq, target)
            self._write_console(f"Successfully recorded prerequisite: {prereq.upper()} -> {target.upper()}")
            self.entry_prereq.delete(0, tk.END)
            self.entry_target.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error Adding Prerequisite", str(e))

    def on_load_sample_data(self):
        self.graph.load_sample_dataset()
        self.last_order = []
        msg = []
        msg.append("=" * 70)
        msg.append("LOADED REALISTIC SAMPLE UNIVERSITY DATASET (12 COURSES - DAG)")
        msg.append("=" * 70)
        msg.append(f"Total Courses Registered: {self.graph.get_num_vertices()}")
        msg.append(f"Total Prerequisite Edges: {self.graph.get_num_edges()}")
        msg.append("-" * 70)
        msg.append(self.graph.display_courses_str())
        msg.append("\n" + self.graph.display_prerequisites_str())
        self._write_console("\n".join(msg))

    def on_load_cyclic_data(self):
        self.graph.load_cyclic_dataset()
        self.last_order = []
        msg = []
        msg.append("=" * 70)
        msg.append("LOADED CYCLIC DATASET (CIRCULAR PREREQUISITE DEMONSTRATION)")
        msg.append("=" * 70)
        msg.append("Circular Chain Injected: CS101 -> CS102 -> CS103 -> CS201 -> CS101")
        msg.append(f"Total Courses: {self.graph.get_num_vertices()} | Total Edges: {self.graph.get_num_edges()}")
        msg.append("-" * 70)
        msg.append(self.graph.display_prerequisites_str())
        self._write_console("\n".join(msg))

    def on_clear_graph(self):
        self.graph.clear()
        self.last_order = []
        self._write_console("Curriculum graph cleared. 0 courses and 0 prerequisite edges registered.")

    def on_display_graph(self):
        msg = []
        msg.append("=" * 70)
        msg.append("UNIVERSITY CURRICULUM GRAPH TOPOLOGY & ADJACENCY REPRESENTATION")
        msg.append("=" * 70)
        msg.append(f"Total Courses (Vertices |V|): {self.graph.get_num_vertices()}")
        msg.append(f"Total Prerequisite Edges (|E|): {self.graph.get_num_edges()}")
        msg.append("-" * 70)
        msg.append("\n[A] REGISTERED COURSES:")
        msg.append(self.graph.display_courses_str())
        msg.append("\n[B] ADJACENCY LIST (Out-edges: Course -> [Dependent Courses]):")
        msg.append(self.graph.display_adjacency_list_str())
        msg.append("\n[C] PREREQUISITE MATRIX (In-edges: Course <- [Required Prerequisites]):")
        msg.append(self.graph.display_prerequisites_str())
        msg.append("\n[D] IN-DEGREE COUNTS (Number of direct prerequisite courses):")
        for code, deg in sorted(self.graph.calculate_indegrees().items()):
            msg.append(f"  {code:<8} : In-Degree = {deg}")
        self._write_console("\n".join(msg))

    def on_bfs_sort(self):
        res = TopologicalSort.kahn_sort(self.graph)
        self.last_order = res.order if res.success else []
        self._write_console(res.format_report(self.graph))

    def on_dfs_sort(self):
        res = TopologicalSort.dfs_sort(self.graph)
        self.last_order = res.order if res.success else []
        self._write_console(res.format_report(self.graph))

    def on_detect_cycle(self):
        rep_bfs = CycleDetector.detect_cycle_bfs(self.graph)
        rep_dfs = CycleDetector.detect_cycle_dfs(self.graph)

        msg = []
        msg.append("=" * 70)
        msg.append("COMPREHENSIVE DUAL-ENGINE CYCLE DETECTION AUDIT")
        msg.append("=" * 70)
        msg.append(rep_bfs.format_report())
        msg.append("\n")
        msg.append(rep_dfs.format_report())
        self._write_console("\n".join(msg))

    def on_validate_order(self):
        if not self.last_order:
            # Try running Kahn sort first to get an order
            res = TopologicalSort.kahn_sort(self.graph)
            if res.success:
                self.last_order = res.order
            else:
                self._write_console(
                    "Cannot validate order: No valid topological ordering currently exists.\n"
                    "Please run BFS or DFS on a valid Directed Acyclic Graph (DAG) first."
                )
                return

        v_res = OrderValidator.validate(self.graph, self.last_order)
        self._write_console(v_res.format_report())

    def on_run_test_suite(self):
        results = TestSuite.run_all_tests()
        summary = TestSuite.format_summary_report(results)
        self._write_console(summary)

    def on_save_db(self):
        try:
            self.db.save_graph_to_db(self.graph)
            messagebox.showinfo("SQLite Database", "Current curriculum graph successfully saved to 'curriculum.db'.")
            self._write_console("[SQLITE] Graph persisted successfully to 'curriculum.db'.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def on_load_db(self):
        try:
            self.graph = self.db.load_graph_from_db()
            self.last_order = []
            self.on_display_graph()
            messagebox.showinfo("SQLite Database", "Curriculum graph reloaded from 'curriculum.db'.")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def on_view_assignment_rubrics(self):
        summary = self.db.get_database_summary()
        meta = summary.get("assignment_metadata", {})
        rubrics = summary.get("rubrics", [])

        msg = []
        msg.append("=" * 75)
        msg.append("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING – ASSIGNMENT SPECIFICATION")
        msg.append("=" * 75)
        msg.append(f"Institution:     {meta.get('institution', 'Department of Computer Science and Engineering')}")
        msg.append(f"Course:          {meta.get('course_code_name', 'CSA03 – Data Structures – Slot D')}")
        msg.append(f"Course Outcome:  {meta.get('course_outcome', 'CO5')}")
        msg.append(f"Bloom's Level:   {meta.get('blooms_taxonomy', 'L4 – Analyze')}")
        msg.append(f"SDG Mapping:     {meta.get('sdg_mapping', 'SDG 4 & SDG 9')}")
        msg.append("-" * 75)
        msg.append("ASSIGNMENT TITLE:")
        msg.append(f"{meta.get('assignment_title', '')}\n")
        msg.append("=" * 75)
        msg.append(f"{'OFFICIAL ASSESSMENT RUBRICS (TOTAL: 100 MARKS)':^75}")
        msg.append("=" * 75)
        for idx, r in enumerate(rubrics, 1):
            msg.append(f"\n{idx}. {r['criteria']} ({r['co_mapping']}) — [Max Marks: {r['max_marks']}]")
            msg.append(f"   * Excellent:         {r['excellent']}")
            msg.append(f"   * Good:              {r['good']}")
            msg.append(f"   * Satisfactory:      {r['satisfactory']}")
            msg.append(f"   * Needs Improvement: {r['needs_improvement']}")
        msg.append("\n" + "=" * 75)
        self._write_console("\n".join(msg))

    def on_reset(self):
        self.entry_code.delete(0, tk.END)
        self.entry_title.delete(0, tk.END)
        self.entry_prereq.delete(0, tk.END)
        self.entry_target.delete(0, tk.END)
        self.spin_credits.set(3)
        self.on_load_sample_data()


def run_gui():
    """Launches the Tkinter Desktop GUI application."""
    root = tk.Tk()
    app = CoursePrerequisiteGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
