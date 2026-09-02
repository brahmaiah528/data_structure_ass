"""
Seed data module for University Student Course Enrollment Portal.
Populates university.db with 115+ courses across 9 engineering departments,
realistic multi-tier prerequisite graphs, 15 sample students, completed courses, and enrollments.
"""

import sqlite3
import os
from datetime import datetime, timedelta

def seed_database(db_path: str) -> None:
    """Seeds university.db with comprehensive academic data."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # 1. DEFINE COURSES (118 Courses across 9 departments + Common)
    courses_data = [
        # --- COMMON / BASIC SCIENCES & HUMANITIES (Semesters 1 - 2) ---
        ("MA101", "Engineering Mathematics I", "Common", 4, 1, "Differential calculus, linear algebra, and matrices."),
        ("PH101", "Engineering Physics", "Common", 3, 1, "Optics, quantum mechanics, lasers, and semiconductor physics."),
        ("CH101", "Engineering Chemistry", "Common", 3, 1, "Thermodynamics, electrochemistry, and material chemistry."),
        ("EN101", "Technical English Communication", "Common", 2, 1, "Professional vocabulary, technical writing, and oral communication."),
        ("ME101", "Engineering Graphics & Design", "Common", 3, 1, "Orthographic projection, isometric views, and CAD fundamentals."),
        ("CS100", "Problem Solving and Computer Programming", "Common", 4, 1, "Algorithmic thinking, flowcharting, and C programming basics."),
        
        ("MA102", "Engineering Mathematics II", "Common", 4, 2, "Integral calculus, multiple integrals, and vector calculus."),
        ("EE101", "Basic Electrical and Electronics Engineering", "Common", 3, 2, "AC/DC circuits, electromagnetic induction, diodes, and transistors."),
        ("EV101", "Environmental Science and Sustainability", "Common", 2, 2, "Ecosystems, biodiversity, pollution control, and renewable energy."),
        ("MA201", "Transforms and Partial Differential Equations", "Common", 4, 3, "Fourier series, Laplace transforms, and boundary value problems."),
        ("MA202", "Probability, Statistics and Queuing Theory", "Common", 4, 4, "Random variables, probability distributions, hypothesis testing, and Markov chains."),
        ("MA203", "Discrete Mathematics", "Common", 4, 3, "Set theory, graph theory, propositional logic, and combinatorics."),
        ("MA204", "Linear Algebra and Numerical Methods", "Common", 4, 4, "Vector spaces, eigenvalues, matrix decompositions, and numerical calculus."),

        # --- COMPUTER SCIENCE AND ENGINEERING (CSE) ---
        ("CS101", "Programming Fundamentals in C++", "CSE", 4, 1, "Syntax, pointers, dynamic memory, and structured programming in C++."),
        ("CS102", "Object Oriented Programming", "CSE", 4, 2, "Classes, objects, inheritance, polymorphism, and templates in Java/C++."),
        ("CS104", "Data Structures", "CSE", 4, 3, "Arrays, linked lists, stacks, queues, trees, hashing, and graphs."),
        ("CS105", "Database Management Systems", "CSE", 4, 4, "Relational algebra, SQL, normal forms, indexing, and transactions."),
        ("CS106", "Computer Organization and Architecture", "CSE", 4, 3, "Instruction set architecture, arithmetic logic units, pipelining, and memory hierarchy."),
        ("CS201", "Design and Analysis of Algorithms", "CSE", 4, 4, "Divide-and-conquer, greedy method, dynamic programming, and NP-completeness."),
        ("CS202", "Operating Systems", "CSE", 4, 4, "Process synchronization, deadlock avoidance, virtual memory, and file systems."),
        ("CS203", "Software Engineering", "CSE", 3, 5, "Software lifecycle models, agile methodology, requirements engineering, and testing."),
        ("CS204", "Theory of Computation", "CSE", 4, 5, "Finite automata, regular grammars, context-free languages, and Turing machines."),
        ("CS205", "Computer Networks", "CSE", 4, 5, "OSI model, TCP/IP, routing protocols, flow control, and network layer design."),
        ("CS301", "Compiler Design", "CSE", 4, 6, "Lexical analysis, syntax trees, semantic analysis, code generation, and optimization."),
        ("CS302", "Advanced Database Systems", "CSE", 3, 6, "Distributed databases, NoSQL stores, query optimization, and concurrency protocols."),
        ("CS303", "Distributed Computing", "CSE", 3, 6, "Remote procedure calls, distributed consensus (Paxos/Raft), and fault tolerance."),
        ("CS304", "Cloud Computing Architecture", "CSE", 3, 7, "IaaS, PaaS, SaaS, virtualization, containerization (Docker/K8s), and serverless."),
        ("CS305", "High Performance Computing", "CSE", 3, 7, "OpenMP, MPI, GPU parallel programming with CUDA, and cluster architecture."),
        ("CS401", "Big Data Analytics", "CSE", 3, 7, "Hadoop ecosystem, Spark processing, MapReduce, and distributed streaming."),
        ("CS402", "Software Architecture and Design Patterns", "CSE", 3, 8, "Creational, structural, behavioral patterns, microservices, and clean architecture."),

        # --- ARTIFICIAL INTELLIGENCE & DATA SCIENCE (AI&DS) ---
        ("AI101", "Python for Data Science", "AI&DS", 4, 2, "Python syntax, NumPy, Pandas, Matplotlib, and exploratory data analysis."),
        ("AI201", "Foundations of Artificial Intelligence", "AI&DS", 4, 4, "Informed search, heuristic evaluation, adversarial games, and knowledge graphs."),
        ("AI202", "Applied Statistics for Data Science", "AI&DS", 4, 3, "Regression analysis, ANOVA, Bayesian inference, and statistical modeling."),
        ("AI301", "Machine Learning", "AI&DS", 4, 5, "Supervised & unsupervised learning, decision trees, SVM, regularization, and ensemble methods."),
        ("AI302", "Deep Learning", "AI&DS", 4, 6, "Multilayer perceptrons, CNNs, RNNs, backpropagation, and PyTorch frameworks."),
        ("AI303", "Natural Language Processing", "AI&DS", 3, 6, "Tokenization, TF-IDF, Word2Vec, Transformers, BERT, and LLM foundations."),
        ("AI304", "Computer Vision", "AI&DS", 3, 6, "Image filtering, edge detection, object detection (YOLO), and image segmentation."),
        ("AI305", "Data Mining and Warehousing", "AI&DS", 3, 5, "ETL pipelines, star schemas, association rules, and clustering techniques."),
        ("AI401", "Reinforcement Learning", "AI&DS", 3, 7, "Markov decision processes, Q-learning, policy gradients, and actor-critic methods."),
        ("AI402", "Generative AI and Large Language Models", "AI&DS", 3, 7, "Diffusion models, attention mechanisms, fine-tuning, RAG, and prompt engineering."),
        ("AI403", "AI Ethics and Governance", "AI&DS", 2, 8, "Fairness, accountability, bias mitigation, explainable AI, and privacy law."),

        # --- CYBER SECURITY (CYS) ---
        ("CY101", "Introduction to Information Security", "Cyber Security", 3, 3, "CIA triad, security policies, authentication protocols, and access control models."),
        ("CY201", "Cryptography and Network Security", "Cyber Security", 4, 4, "Symmetric/asymmetric ciphers, RSA, AES, digital signatures, and hash functions."),
        ("CY202", "Ethical Hacking and Penetration Testing", "Cyber Security", 3, 5, "Reconnaissance, vulnerability scanning, exploit frameworks (Metasploit), and reporting."),
        ("CY301", "Network Security Protocols", "Cyber Security", 4, 6, "Firewalls, IPSec, TLS/SSL, intrusion detection systems, and zero trust architecture."),
        ("CY302", "Web Application Security", "Cyber Security", 3, 5, "OWASP Top 10 vulnerabilities, SQL injection, XSS, CSRF, and secure coding practices."),
        ("CY303", "Digital Forensics and Incident Response", "Cyber Security", 3, 6, "Evidence acquisition, disk forensics, memory analysis, and chain of custody."),
        ("CY304", "Malware Analysis and Reverse Engineering", "Cyber Security", 3, 7, "Static and dynamic analysis, disassemblers, sandboxing, and obfuscation techniques."),
        ("CY401", "Cyber Threat Intelligence", "Cyber Security", 3, 7, "STIX/TAXII standards, MITRE ATT&CK framework, and threat hunting strategies."),
        ("CY402", "Cloud Security and DevSecOps", "Cyber Security", 3, 8, "Cloud compliance, IAM policies, container security, and CI/CD security scanning."),

        # --- INFORMATION TECHNOLOGY (IT) ---
        ("IT101", "Web Technology Fundamentals", "Information Technology", 3, 2, "HTML5, CSS3, JavaScript, DOM manipulation, and responsive web design."),
        ("IT201", "Full Stack Web Development", "Information Technology", 4, 4, "MERN/MEAN stack, REST APIs, asynchronous programming, and state management."),
        ("IT202", "Mobile Application Development", "Information Technology", 3, 5, "Android SDK, Kotlin/Flutter, mobile UI design, and SQLite integration."),
        ("IT203", "Data Warehousing and Business Intelligence", "Information Technology", 3, 5, "Dimensional modeling, OLAP cubes, PowerBI dashboards, and reporting tools."),
        ("IT301", "Enterprise Java Programming", "Information Technology", 4, 5, "Servlets, JSP, Spring Boot, Hibernate ORM, and enterprise bean architecture."),
        ("IT302", "DevOps and Continuous Integration", "Information Technology", 3, 6, "Git workflows, Jenkins, Docker containers, Kubernetes, and Ansible automation."),
        ("IT303", "Internet of Things (IoT) Systems", "Information Technology", 3, 6, "Microcontrollers, MQTT protocols, sensor interfacing, and edge computing."),
        ("IT401", "Service Oriented Architecture", "Information Technology", 3, 7, "Microservices, SOAP/REST standards, API gateways, and message brokers."),
        ("IT402", "Virtual Reality and Augmented Reality", "Information Technology", 3, 8, "Unity 3D engine, spatial computing, tracking algorithms, and immersive UX."),

        # --- ELECTRONICS AND COMMUNICATION ENGINEERING (ECE) ---
        ("EC101", "Electronic Devices and Circuits", "ECE", 4, 2, "PN junctions, BJT, FET, MOSFET characteristics, and biasing circuits."),
        ("EC102", "Digital Logic Design", "ECE", 4, 3, "Boolean algebra, Karnaugh maps, combinational circuits, flip-flops, and counters."),
        ("EC201", "Signals and Systems", "ECE", 4, 3, "Continuous and discrete-time signals, LTI systems, convolution, and Z-transforms."),
        ("EC202", "Analog Integrated Circuits", "ECE", 4, 4, "Operational amplifiers, filters, multivibrators, PLL, and voltage regulators."),
        ("EC203", "Electromagnetic Fields and Waves", "ECE", 4, 4, "Maxwell's equations, wave propagation, Poynting theorem, and transmission lines."),
        ("EC204", "Digital Signal Processing", "ECE", 4, 5, "DFT, FFT algorithms, IIR/FIR filter design, and DSP processor architecture."),
        ("EC301", "VLSI Design", "ECE", 4, 6, "CMOS logic, layout rules, FPGA architecture, and Verilog HDL synthesis."),
        ("EC302", "Communication Systems", "ECE", 4, 5, "AM, FM, PM, digital modulation (ASK, FSK, PSK, QAM), and noise analysis."),
        ("EC303", "Microprocessors and Microcontrollers", "ECE", 4, 5, "Intel 8086, ARM Cortex, assembly programming, and peripheral interfacing."),
        ("EC304", "Wireless and Cellular Communication", "ECE", 3, 6, "4G LTE, 5G NR architecture, fading channels, MIMO, and beamforming."),
        ("EC401", "Embedded System Design", "ECE", 3, 7, "RTOS concepts, device drivers, low-power optimization, and bus protocols."),
        ("EC402", "Radar and Optical Communication", "ECE", 3, 7, "Radar range equations, optical fibers, optical amplifiers, and WDM systems."),

        # --- ELECTRICAL AND ELECTRONICS ENGINEERING (EEE) ---
        ("EE201", "Electric Circuit Theory", "EEE", 4, 3, "Mesh and nodal analysis, network theorems, transient analysis, and three-phase circuits."),
        ("EE202", "Electrical Machines I", "EEE", 4, 3, "DC generators, DC motors, transformers, and magnetic circuits."),
        ("EE203", "Electrical Machines II", "EEE", 4, 4, "Synchronous generators, synchronous motors, and three-phase induction machines."),
        ("EE204", "Power Systems I - Generation & Transmission", "EEE", 4, 4, "Transmission line parameters, corona, underground cables, and load flow."),
        ("EE301", "Control Systems Engineering", "EEE", 4, 5, "Transfer functions, root locus, Bode plots, Nyquist criterion, and state-space models."),
        ("EE302", "Power Electronics", "EEE", 4, 5, "Thyristors, inverters, buck-boost converters, and PWM control techniques."),
        ("EE303", "Power Systems II - Analysis & Protection", "EEE", 4, 6, "Fault analysis, protective relays, circuit breakers, and grid stability."),
        ("EE304", "Electric Drives and Control", "EEE", 3, 6, "DC/AC drive characteristics, closed-loop speed control, and EV drive trains."),
        ("EE401", "Smart Grid and Renewable Energy Systems", "EEE", 3, 7, "Solar PV, wind energy integration, microgrids, and smart metering."),
        ("EE402", "High Voltage Engineering", "EEE", 3, 7, "Breakdown mechanisms, impulse testing, overvoltage protection, and insulators."),

        # --- MECHANICAL ENGINEERING (MECH) ---
        ("ME201", "Engineering Mechanics", "MECH", 4, 2, "Statics, dynamics, equilibrium of rigid bodies, and friction analysis."),
        ("ME202", "Strength of Materials", "MECH", 4, 3, "Stress, strain, Mohr's circle, shear force diagrams, and bending stresses."),
        ("ME203", "Fluid Mechanics and Machinery", "MECH", 4, 3, "Bernoulli equation, Navier-Stokes, boundary layer, pumps, and turbines."),
        ("ME204", "Manufacturing Technology", "MECH", 3, 3, "Casting, metal forming, welding processes, and conventional machining."),
        ("ME205", "Thermodynamics", "MECH", 4, 3, "First and second laws of thermodynamics, entropy, and thermodynamic cycles."),
        ("ME301", "Kinematics and Dynamics of Machinery", "MECH", 4, 4, "Linkages, cams, gears, balancing of rotating masses, and vibrations."),
        ("ME302", "Thermal Engineering and Heat Transfer", "MECH", 4, 5, "Conduction, convection, radiation, heat exchangers, and IC engines."),
        ("ME303", "Design of Machine Elements", "MECH", 4, 5, "Shafts, gears, bearings, springs, and fatigue failure theories."),
        ("ME304", "CAD/CAM and CIM", "MECH", 3, 6, "Parametric solid modeling, CNC programming, and flexible manufacturing systems."),
        ("ME401", "Automobile Engineering", "MECH", 3, 6, "Vehicle chassis, transmission systems, suspension, and electric vehicle layout."),
        ("ME402", "Robotics and Automation", "MECH", 3, 7, "Forward/inverse kinematics, trajectory planning, actuators, and robotic vision."),
        ("ME403", "Finite Element Analysis", "MECH", 3, 7, "1D/2D element formulation, stiffness matrices, and structural/thermal FEA."),

        # --- CIVIL ENGINEERING (CIVIL) ---
        ("CE101", "Surveying and Geomatics", "Civil Engineering", 4, 2, "Chain surveying, leveling, theodolite, total station, and GPS principles."),
        ("CE201", "Mechanics of Solids", "Civil Engineering", 4, 3, "Beams, torsional stresses, column buckling, and deflection calculations."),
        ("CE202", "Fluid Mechanics and Hydraulic Engineering", "Civil Engineering", 4, 3, "Pipe flow, open channel flow, hydraulic jumps, and dimensional analysis."),
        ("CE203", "Building Materials and Construction", "Civil Engineering", 3, 3, "Concrete technology, brick masonry, foundation types, and green buildings."),
        ("CE204", "Structural Analysis I", "Civil Engineering", 4, 4, "Determinate structures, slope-deflection method, moment distribution, and influence lines."),
        ("CE301", "Structural Analysis II", "Civil Engineering", 4, 5, "Matrix flexibility/stiffness methods, plastic analysis, and space trusses."),
        ("CE302", "Design of Reinforced Concrete Structures", "Civil Engineering", 4, 5, "Limit state design of beams, slabs, columns, and isolated footings."),
        ("CE303", "Soil Mechanics and Geotechnical Engineering", "Civil Engineering", 4, 5, "Soil classification, effective stress, consolidation, shear strength, and settlement."),
        ("CE304", "Transportation and Highway Engineering", "Civil Engineering", 3, 6, "Geometric highway design, pavement materials, traffic engineering, and signals."),
        ("CE305", "Environmental Engineering and Water Treatment", "Civil Engineering", 3, 6, "Water demand forecasting, water treatment units, sewer design, and sludge handling."),
        ("CE401", "Design of Steel Structures", "Civil Engineering", 4, 6, "Tension members, compression members, bolted/welded connections, and plate girders."),
        ("CE402", "Foundation Engineering", "Civil Engineering", 3, 7, "Shallow foundations, pile groups, well foundations, and soil improvement."),

        # --- COMPUTER APPLICATIONS (MCA) ---
        ("CA101", "Programming with Python and Data Handling", "Computer Applications", 4, 1, "Scripting, file I/O, regex, and data handling libraries."),
        ("CA102", "Data Structures with Python", "Computer Applications", 4, 2, "Linear and non-linear data structures with practical implementation."),
        ("CA103", "Relational Database Management Systems", "Computer Applications", 4, 2, "Database schema design, SQL, triggers, procedures, and transactions."),
        ("CA201", "Object Oriented Software Development", "Computer Applications", 4, 3, "Design patterns, Java OOP, unit testing, and version control."),
        ("CA202", "Web Systems and Cloud Applications", "Computer Applications", 4, 3, "Full stack architecture, cloud deployments, and web services."),
        ("CA203", "Mobile Computing and Applications", "Computer Applications", 3, 4, "Mobile UX, Android development, and hybrid frameworks."),
        ("CA301", "Enterprise Data Analytics", "Computer Applications", 3, 4, "Business intelligence, visualization, data warehousing, and forecasting."),
    ]

    # Insert Courses into Database
    cursor.executemany("""
        INSERT OR IGNORE INTO courses (course_code, course_name, department, credits, semester, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, courses_data)
    conn.commit()

    # Create mapping of course_code -> course_id
    cursor.execute("SELECT course_code, course_id FROM courses")
    code_to_id = {row[0]: row[1] for row in cursor.fetchall()}

    # 2. DEFINE PREREQUISITE EDGES (prereq_code -> target_code)
    # Course B requires Course A  => (target_code, prereq_code)
    prereq_pairs = [
        # --- Common Foundation Prerequisites ---
        ("MA102", "MA101"),  # Math 2 requires Math 1
        ("MA201", "MA102"),  # Transforms requires Math 2
        ("MA202", "MA102"),  # Probability requires Math 2
        ("MA204", "MA102"),  # Linear Algebra requires Math 2
        ("CS101", "CS100"),  # C++ requires Basic Programming

        # --- CSE Prerequisite Tree ---
        ("CS102", "CS101"),  # OOP requires C++
        ("CS104", "CS102"),  # Data Structures requires OOP
        ("CS104", "MA203"),  # Data Structures also requires Discrete Math (Type 3)
        ("CS105", "CS104"),  # DBMS requires Data Structures
        ("CS106", "EE101"),  # Computer Org requires Basic EE
        ("CS201", "CS104"),  # Algorithms requires Data Structures (Type 2)
        ("CS202", "CS106"),  # OS requires Computer Org
        ("CS202", "CS104"),  # OS requires Data Structures (Type 3)
        ("CS203", "CS102"),  # Software Engineering requires OOP
        ("CS204", "MA203"),  # Theory of Computation requires Discrete Math
        ("CS205", "CS104"),  # Networks requires Data Structures
        ("CS301", "CS204"),  # Compiler Design requires Theory of Computation
        ("CS301", "CS104"),  # Compiler Design requires Data Structures
        ("CS302", "CS105"),  # Advanced DBMS requires DBMS
        ("CS303", "CS202"),  # Distributed Computing requires OS
        ("CS303", "CS205"),  # Distributed Computing requires Networks
        ("CS304", "CS202"),  # Cloud Computing requires OS
        ("CS304", "CS205"),  # Cloud Computing requires Networks
        ("CS305", "CS201"),  # HPC requires Algorithms
        ("CS305", "CS106"),  # HPC requires Computer Architecture
        ("CS401", "CS105"),  # Big Data requires DBMS
        ("CS401", "CS201"),  # Big Data requires Algorithms
        ("CS402", "CS203"),  # Software Architecture requires Software Engineering

        # --- AI & DS Prerequisite Tree (Type 2, 3, 4 examples) ---
        ("AI101", "CS100"),  # Python for DS requires Basic Programming
        ("AI201", "CS104"),  # Foundations of AI requires Data Structures
        ("AI201", "AI101"),  # Foundations of AI requires Python for DS
        ("AI202", "MA202"),  # Applied Stats requires Probability & Stats
        # Type 4: Machine Learning requires 4 foundational prerequisites!
        ("AI301", "AI101"),  # ML requires Python
        ("AI301", "CS104"),  # ML requires Data Structures
        ("AI301", "MA202"),  # ML requires Probability & Stats
        ("AI301", "MA204"),  # ML requires Linear Algebra
        # Deep Learning requires ML + Algorithms
        ("AI302", "AI301"),  # Deep Learning requires Machine Learning
        ("AI302", "CS201"),  # Deep Learning requires Algorithms
        ("AI303", "AI301"),  # NLP requires Machine Learning
        ("AI304", "AI301"),  # Computer Vision requires Machine Learning
        ("AI305", "CS105"),  # Data Mining requires DBMS
        ("AI401", "AI301"),  # Reinforcement Learning requires Machine Learning
        ("AI402", "AI302"),  # GenAI & LLMs requires Deep Learning
        ("AI402", "AI303"),  # GenAI & LLMs requires NLP
        ("AI403", "AI201"),  # AI Ethics requires Foundations of AI

        # --- Cyber Security Prerequisite Tree ---
        ("CY101", "CS100"),  # Intro InfoSec requires Basic Programming
        ("CY201", "MA203"),  # Cryptography requires Discrete Math
        ("CY201", "CY101"),  # Cryptography requires Intro InfoSec
        ("CY202", "CS205"),  # Ethical Hacking requires Networks
        ("CY202", "CY101"),  # Ethical Hacking requires InfoSec
        ("CY301", "CS205"),  # Network Security Protocols requires Networks
        ("CY301", "CY201"),  # Network Security Protocols requires Cryptography
        ("CY302", "IT101"),  # Web App Security requires Web Tech
        ("CY302", "CY101"),  # Web App Security requires InfoSec
        ("CY303", "CY202"),  # Digital Forensics requires Ethical Hacking
        ("CY304", "CS106"),  # Malware Analysis requires Computer Architecture
        ("CY304", "CY202"),  # Malware Analysis requires Ethical Hacking
        ("CY401", "CY301"),  # Threat Intel requires Network Security Protocols
        ("CY402", "CS304"),  # Cloud Security requires Cloud Computing
        ("CY402", "CY301"),  # Cloud Security requires Network Security

        # --- Information Technology Prerequisite Tree ---
        ("IT101", "CS100"),  # Web Tech requires Basic Programming
        ("IT201", "IT101"),  # Full Stack requires Web Tech
        ("IT201", "CS105"),  # Full Stack requires DBMS
        ("IT202", "CS102"),  # Mobile App requires OOP
        ("IT203", "CS105"),  # Data Warehousing requires DBMS
        ("IT301", "CS102"),  # Enterprise Java requires OOP
        ("IT301", "CS105"),  # Enterprise Java requires DBMS
        ("IT302", "CS202"),  # DevOps requires OS
        ("IT302", "CS205"),  # DevOps requires Networks
        ("IT303", "EE101"),  # IoT requires Basic EE
        ("IT303", "CS205"),  # IoT requires Networks
        ("IT401", "IT201"),  # SOA requires Full Stack
        ("IT402", "CS104"),  # VR/AR requires Data Structures

        # --- ECE Prerequisite Tree ---
        ("EC101", "PH101"),  # Devices requires Physics
        ("EC102", "EE101"),  # Digital Logic requires Basic EE
        ("EC201", "MA102"),  # Signals & Systems requires Math 2
        ("EC202", "EC101"),  # Analog IC requires Electronic Devices
        ("EC203", "PH101"),  # Electromagnetics requires Physics
        ("EC203", "MA102"),  # Electromagnetics requires Math 2
        ("EC204", "EC201"),  # DSP requires Signals & Systems
        ("EC301", "EC102"),  # VLSI requires Digital Logic
        ("EC301", "EC101"),  # VLSI requires Electronic Devices
        ("EC302", "EC201"),  # Communication Systems requires Signals & Systems
        ("EC303", "EC102"),  # Microprocessors requires Digital Logic
        ("EC304", "EC302"),  # Wireless requires Communication Systems
        ("EC401", "EC303"),  # Embedded Systems requires Microprocessors
        ("EC402", "EC203"),  # Optical Comm requires Electromagnetics

        # --- EEE Prerequisite Tree ---
        ("EE201", "EE101"),  # Circuit Theory requires Basic EE
        ("EE201", "MA102"),  # Circuit Theory requires Math 2
        ("EE202", "EE201"),  # Machines I requires Circuit Theory
        ("EE203", "EE202"),  # Machines II requires Machines I
        ("EE204", "EE201"),  # Power Systems I requires Circuit Theory
        ("EE301", "MA201"),  # Control Systems requires Transforms
        ("EE301", "EE201"),  # Control Systems requires Circuit Theory
        ("EE302", "EC101"),  # Power Electronics requires Electronic Devices
        ("EE302", "EE201"),  # Power Electronics requires Circuit Theory
        ("EE303", "EE204"),  # Power Systems II requires Power Systems I
        ("EE304", "EE203"),  # Drives requires Machines II
        ("EE304", "EE302"),  # Drives requires Power Electronics
        ("EE401", "EE204"),  # Smart Grid requires Power Systems I
        ("EE402", "EE204"),  # High Voltage requires Power Systems I

        # --- Mechanical Engineering Prerequisite Tree ---
        ("ME201", "PH101"),  # Engineering Mechanics requires Physics
        ("ME202", "ME201"),  # Strength of Materials requires Engineering Mechanics
        ("ME203", "ME201"),  # Fluid Mechanics requires Engineering Mechanics
        ("ME203", "MA102"),  # Fluid Mechanics requires Math 2
        ("ME204", "ME101"),  # Manufacturing Tech requires Engineering Graphics
        ("ME205", "CH101"),  # Thermodynamics requires Chemistry
        ("ME205", "MA102"),  # Thermodynamics requires Math 2
        ("ME301", "ME201"),  # Kinematics requires Engineering Mechanics
        ("ME302", "ME205"),  # Thermal Engineering requires Thermodynamics
        ("ME303", "ME202"),  # Machine Design requires Strength of Materials
        ("ME303", "ME301"),  # Machine Design requires Kinematics
        ("ME304", "ME101"),  # CAD/CAM requires Engineering Graphics
        ("ME401", "ME302"),  # Automobile requires Thermal Engineering
        ("ME402", "ME301"),  # Robotics requires Kinematics
        ("ME402", "EE101"),  # Robotics requires Basic EE
        ("ME403", "ME202"),  # FEA requires Strength of Materials
        ("ME403", "MA204"),  # FEA requires Linear Algebra

        # --- Civil Engineering Prerequisite Tree ---
        ("CE101", "ME101"),  # Surveying requires Engineering Graphics
        ("CE201", "ME201"),  # Mechanics of Solids requires Engineering Mechanics
        ("CE202", "ME201"),  # Hydraulic Engineering requires Engineering Mechanics
        ("CE202", "MA102"),  # Hydraulic Engineering requires Math 2
        ("CE203", "CH101"),  # Building Materials requires Chemistry
        ("CE204", "CE201"),  # Structural Analysis I requires Mechanics of Solids
        ("CE301", "CE204"),  # Structural Analysis II requires Structural Analysis I
        ("CE302", "CE204"),  # Concrete Structures requires Structural Analysis I
        ("CE303", "CE201"),  # Soil Mechanics requires Mechanics of Solids
        ("CE304", "CE101"),  # Highway Engineering requires Surveying
        ("CE305", "CH101"),  # Environmental Eng requires Chemistry
        ("CE305", "CE202"),  # Environmental Eng requires Hydraulic Engineering
        ("CE401", "CE204"),  # Steel Structures requires Structural Analysis I
        ("CE402", "CE303"),  # Foundation Eng requires Soil Mechanics

        # --- Computer Applications (MCA) Prerequisite Tree ---
        ("CA102", "CA101"),  # DS with Python requires Prog with Python
        ("CA103", "CA101"),  # RDBMS requires Prog with Python
        ("CA201", "CA102"),  # OOP requires DS with Python
        ("CA202", "CA103"),  # Web Systems requires RDBMS
        ("CA203", "CA201"),  # Mobile Computing requires OOP
        ("CA301", "CA103"),  # Enterprise Data Analytics requires RDBMS
        ("CA301", "CA102"),  # Enterprise Data Analytics requires DS with Python
    ]

    # Insert Prerequisites into Database
    prereq_records = []
    for target_code, prereq_code in prereq_pairs:
        if target_code in code_to_id and prereq_code in code_to_id:
            prereq_records.append((code_to_id[target_code], code_to_id[prereq_code]))

    cursor.executemany("""
        INSERT OR IGNORE INTO prerequisites (course_id, prerequisite_course_id)
        VALUES (?, ?)
    """, prereq_records)
    conn.commit()

    # 3. DEFINE SAMPLE STUDENTS (15 Sample Students across Departments)
    students_data = [
        ("STU001", "Rahul Kumar", "rahul.kumar@university.edu", "student123", "CSE", 4, 2, "+91 9876543210"),
        ("STU002", "Priya Sharma", "priya.sharma@university.edu", "student123", "AI&DS", 6, 3, "+91 9876543211"),
        ("STU003", "Arun Kumar", "arun.kumar@university.edu", "student123", "ECE", 5, 3, "+91 9876543212"),
        ("STU004", "Sneha Patel", "sneha.patel@university.edu", "student123", "Information Technology", 3, 2, "+91 9876543213"),
        ("STU005", "Vikram Singh", "vikram.singh@university.edu", "student123", "MECH", 4, 2, "+91 9876543214"),
        ("STU006", "Ananya Roy", "ananya.roy@university.edu", "student123", "Civil Engineering", 5, 3, "+91 9876543215"),
        ("STU007", "Rohan Verma", "rohan.verma@university.edu", "student123", "EEE", 4, 2, "+91 9876543216"),
        ("STU008", "Kavita Nair", "kavita.nair@university.edu", "student123", "Cyber Security", 6, 3, "+91 9876543217"),
        ("STU009", "Amit Joshi", "amit.joshi@university.edu", "student123", "Computer Applications", 3, 2, "+91 9876543218"),
        ("STU010", "Pooja Reddy", "pooja.reddy@university.edu", "student123", "CSE", 2, 1, "+91 9876543219"),
        ("STU011", "Karthik Iyer", "karthik.iyer@university.edu", "student123", "AI&DS", 4, 2, "+91 9876543220"),
        ("STU012", "Neha Gupta", "neha.gupta@university.edu", "student123", "Information Technology", 5, 3, "+91 9876543221"),
        ("STU013", "Manoj Das", "manoj.das@university.edu", "student123", "ECE", 3, 2, "+91 9876543222"),
        ("STU014", "Divya Rao", "divya.rao@university.edu", "student123", "MECH", 2, 1, "+91 9876543223"),
        ("STU015", "Suresh Babu", "suresh.babu@university.edu", "student123", "Civil Engineering", 3, 2, "+91 9876543224"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO students (student_id, name, email, password, department, semester, year, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, students_data)
    conn.commit()

    # 4. DEFINE COMPLETED COURSES FOR SAMPLE STUDENTS
    # Gives realistic academic history
    completed_plans = {
        # STU001 (Rahul Kumar - CSE Sem 4): Has completed Sem 1, 2, and parts of Sem 3
        # Completed: MA101, PH101, CS100, EN101, MA102, EE101, CS101, CS102, MA203, CS104
        # Note: CS104 is completed, so CS201 (Algorithms) and CS105 (DBMS) are ELIGIBLE!
        "STU001": [
            ("MA101", "A+", "2024-12-15"),
            ("PH101", "A", "2024-12-16"),
            ("CS100", "S", "2024-12-18"),
            ("EN101", "A+", "2024-12-20"),
            ("MA102", "A", "2025-05-10"),
            ("EE101", "B+", "2025-05-12"),
            ("CS101", "S", "2025-05-15"),
            ("CS102", "A+", "2025-05-18"),
            ("MA203", "A", "2025-12-10"),
            ("CS104", "S", "2025-12-12"),
            ("CS106", "A", "2025-12-15"),
        ],
        # STU002 (Priya Sharma - AI&DS Sem 6): Has completed up to Sem 5
        "STU002": [
            ("MA101", "S", "2023-12-15"),
            ("PH101", "A+", "2023-12-16"),
            ("CS100", "S", "2023-12-18"),
            ("MA102", "A+", "2024-05-10"),
            ("AI101", "S", "2024-05-15"),
            ("CS101", "A+", "2024-05-18"),
            ("CS102", "A", "2024-12-10"),
            ("MA203", "A+", "2024-12-12"),
            ("CS104", "S", "2024-12-15"),
            ("MA202", "S", "2025-05-10"),
            ("MA204", "A+", "2025-05-12"),
            ("AI201", "S", "2025-05-15"),
            ("CS201", "S", "2025-05-18"),
            ("AI301", "S", "2025-12-10"),  # Machine Learning Completed! Deep Learning is now eligible
        ],
        # STU003 (Arun Kumar - ECE Sem 5): Completed Sem 1, 2, 3, 4
        "STU003": [
            ("MA101", "A", "2024-05-10"),
            ("PH101", "S", "2024-05-12"),
            ("EE101", "A+", "2024-05-15"),
            ("MA102", "A+", "2024-12-10"),
            ("EC101", "S", "2024-12-12"),
            ("EC102", "A+", "2024-12-15"),
            ("EC201", "A", "2025-05-10"),
            ("EC202", "B+", "2025-05-12"),
            ("EC203", "A", "2025-05-15"),
            ("MA201", "A+", "2025-05-18"),
        ],
        # STU004 (Sneha Patel - IT Sem 3)
        "STU004": [
            ("MA101", "A", "2025-05-10"),
            ("CS100", "A+", "2025-05-12"),
            ("EN101", "S", "2025-05-15"),
            ("MA102", "B+", "2025-12-10"),
            ("IT101", "A+", "2025-12-12"),
            ("CS101", "A", "2025-12-15"),
        ],
        # STU008 (Kavita Nair - Cyber Security Sem 6)
        "STU008": [
            ("CS100", "A+", "2023-12-15"),
            ("MA101", "A", "2023-12-16"),
            ("CS101", "A+", "2024-05-10"),
            ("CS102", "A", "2024-05-15"),
            ("CY101", "S", "2024-12-10"),
            ("CS104", "A+", "2024-12-15"),
            ("MA203", "A", "2024-12-18"),
            ("CY201", "S", "2025-05-10"),
            ("CS205", "A+", "2025-05-15"),
            ("CY202", "S", "2025-12-10"),
            ("CY301", "S", "2025-12-15"),
        ],
        # STU010 (Pooja Reddy - CSE Sem 2)
        "STU010": [
            ("MA101", "A+", "2025-12-15"),
            ("PH101", "A", "2025-12-16"),
            ("CS100", "S", "2025-12-18"),
            ("EN101", "A", "2025-12-20"),
        ],
    }

    completion_records = []
    month_lookup = {
        "2023-12": "December 2023",
        "2024-05": "May 2024",
        "2024-12": "December 2024",
        "2025-05": "May 2025",
        "2025-12": "December 2025",
    }
    for stu_id, items in completed_plans.items():
        for c_code, grade, comp_date in items:
            if c_code in code_to_id:
                comp_month = month_lookup.get(comp_date[:7], "May 2025")
                completion_records.append((stu_id, code_to_id[c_code], grade, "Completed", comp_date, comp_month))

    cursor.executemany("""
        INSERT OR IGNORE INTO completed_courses (student_id, course_id, grade, completion_status, completed_on, completed_month)
        VALUES (?, ?, ?, ?, ?, ?)
    """, completion_records)
    conn.commit()

    # 5. DEFINE SAMPLE ENROLLMENTS (Running Courses with Teacher Approval)
    enrollment_plans = [
        # Rahul Kumar (STU001) - 3 Approved Running Courses + 1 Pending Approval
        ("STU001", "CS201", "2026-01-10", 4, "Approved", "Approved", "Dr. K. Raman (Faculty Advisor)", "Prerequisites (CS104) verified. Approved."),
        ("STU001", "CS105", "2026-01-10", 4, "Approved", "Approved", "Dr. K. Raman (Faculty Advisor)", "Prerequisites (CS104) verified. Approved."),
        ("STU001", "CS202", "2026-01-11", 4, "Approved", "Approved", "Dr. K. Raman (Faculty Advisor)", "Prerequisites (CS104, CS106) verified. Approved."),
        ("STU001", "CS203", "2026-01-15", 4, "Pending Teacher Approval", "Pending Teacher Approval", "Dr. K. Raman (Faculty Advisor)", "Submitted for advisor review"),

        # Priya Sharma (STU002 - AI&DS)
        ("STU002", "AI302", "2026-01-12", 6, "Approved", "Approved", "Dr. M. Sangeetha (HOD AI&DS)", "Approved for Semester 6 Deep Learning."),
        ("STU002", "AI303", "2026-01-12", 6, "Approved", "Approved", "Dr. M. Sangeetha (HOD AI&DS)", "Approved for NLP specialization."),
        
        # Arun Kumar (STU003 - ECE)
        ("STU003", "EC204", "2026-01-14", 5, "Approved", "Approved", "Prof. R. Venkatesh (ECE Advisor)", "Signals & Systems cleared. Approved."),
        ("STU003", "EC302", "2026-01-14", 5, "Approved", "Approved", "Prof. R. Venkatesh (ECE Advisor)", "Approved."),
    ]

    enroll_records = []
    for stu_id, c_code, en_date, sem, status, app_status, fac_name, remarks in enrollment_plans:
        if c_code in code_to_id:
            enroll_records.append((stu_id, code_to_id[c_code], en_date, sem, status, app_status, fac_name, remarks))

    cursor.executemany("""
        INSERT OR IGNORE INTO enrollments (student_id, course_id, enrollment_date, semester, status, approval_status, faculty_name, faculty_remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, enroll_records)
    conn.commit()

    # 6. DEFINE ATTENDANCE RECORDS FOR APPROVED RUNNING COURSES
    attendance_data = [
        # Rahul Kumar (STU001) running courses:
        ("STU001", "CS201", 40, 36, 90.0, "2026-09-01"), # Eligible (90%)
        ("STU001", "CS105", 40, 34, 85.0, "2026-09-01"), # Eligible (85%)
        ("STU001", "CS202", 40, 29, 72.5, "2026-09-01"), # Shortage warning! (72.5% < 75%)
        # Priya Sharma (STU002):
        ("STU002", "AI302", 40, 38, 95.0, "2026-09-01"),
        ("STU002", "AI303", 40, 37, 92.5, "2026-09-01"),
        # Arun Kumar (STU003):
        ("STU003", "EC204", 40, 35, 87.5, "2026-09-01"),
        ("STU003", "EC302", 40, 31, 77.5, "2026-09-01"),
    ]
    att_records = []
    for s_id, c_code, tot, att, pct, dt in attendance_data:
        if c_code in code_to_id:
            att_records.append((s_id, code_to_id[c_code], tot, att, pct, dt))

    cursor.executemany("""
        INSERT OR IGNORE INTO attendance (student_id, course_id, total_classes, attended_classes, attendance_percentage, last_updated)
        VALUES (?, ?, ?, ?, ?, ?)
    """, att_records)
    conn.commit()

    # 7. DEFINE SAMPLE BACKLOGS / ARREARS
    backlog_data = [
        # Arun Kumar (STU003 - ECE Sem 5) has 1 active backlog from Semester 1
        ("STU003", "PH101", 1, "F", "2024-2025", 1, "Active Backlog", "Unpaid"),
        # Rohan Verma (STU007 - EEE Sem 4) has 1 active backlog in Math 1
        ("STU007", "MA101", 1, "F", "2024-2025", 2, "Active Backlog", "Paid (Receipt: REC-2026-B102)"),
    ]
    backlog_records = []
    for s_id, c_code, sem, gr, ac_yr, att_cnt, st, fee_st in backlog_data:
        if c_code in code_to_id:
            backlog_records.append((s_id, code_to_id[c_code], sem, gr, ac_yr, att_cnt, st, fee_st))

    cursor.executemany("""
        INSERT OR IGNORE INTO backlogs (student_id, course_id, semester, grade, academic_year, attempt_count, status, exam_fee_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, backlog_records)
    conn.commit()

    # 8. DEFINE ANNOUNCEMENTS & NOTIFICATIONS POSTED BY ADMIN
    notifications_data = [
        ("End-Semester Theory & Practical Examination Schedule (Autumn 2026)", 
         "Exam",
         "The End-Semester Theory and Practical examinations for all B.Tech and MCA programmes will commence from 15th October 2026. Detailed timetable has been published on the examination portal. Hall tickets can be downloaded 7 days prior to exams by students maintaining minimum 75% attendance.",
         "Office of the Controller of Examinations",
         "2026-09-01 10:00",
         "Urgent"),
        
        ("University Holiday Notification: Gandhi Jayanti & Autumn Break",
         "Holiday",
         "The University will remain closed from 2nd October to 4th October 2026 on account of Gandhi Jayanti and Autumn Festival break. Regular academic sessions and laboratory practicals will resume on Monday, 5th October 2026.",
         "Registrar Academic Administration",
         "2026-08-28 14:30",
         "High"),

        ("Course Enrollment & Supplementary Examination Registration Deadline",
         "Academic",
         "All undergraduate students must finalize course registrations for the ongoing semester. Registrations are routed to Department Faculty Advisors for approval. Last date to submit backlog supplementary examination fees is 25th September 2026.",
         "Dean of Academic Affairs",
         "2026-08-25 09:15",
         "High"),

        ("National 24-Hour Hackathon 'CODE-NEXUS 2026' Announcement",
         "General",
         "The Department of Computer Science and Engineering is organizing 'CODE-NEXUS 2026' National Hackathon on 22nd October 2026. Cash pool of Rs. 1,50,000 for top winning AI and Systems software prototypes. Register via student council.",
         "CSE Department Council",
         "2026-08-20 16:00",
         "Normal")
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO notifications (title, category, message, posted_by, posted_date, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    """, notifications_data)
    conn.commit()

    conn.close()
    print(f"Database seeded successfully with {len(courses_data)} courses, attendance, backlogs, and notifications.")


if __name__ == "__main__":
    from database import DB_PATH, init_database
    init_database(DB_PATH)
    seed_database(DB_PATH)
