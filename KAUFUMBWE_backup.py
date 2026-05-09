import os
import sqlite3
import http.server
import socketserver
import urllib.parse
import datetime
import json

# ==========================================
# DATABASE INITIALIZATION AND SEEDING
# ==========================================

def init_db():
    """
    Initializes the SQLite database with extended schema 
    and comprehensive sample data.
    """
    conn = sqlite3.connect("gradesystem.db")
    cursor = conn.cursor()

    # Drop existing tables to ensure a clean prototype state
    cursor.executescript("""
    DROP TABLE IF EXISTS Results;
    DROP TABLE IF EXISTS Student;
    DROP TABLE IF EXISTS Class;
    DROP TABLE IF EXISTS Teachers;
    """)

    # Create Teachers table - Stores login credentials and roles
    cursor.execute("""
    CREATE TABLE Teachers (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT UNIQUE NOT NULL,
        Password TEXT NOT NULL,
        FullName TEXT,
        Role TEXT DEFAULT 'teacher' -- 'teacher' or 'pupil'
    );
    """)

    # Create Classes table - Defines school structure
    cursor.execute("""
    CREATE TABLE Class (
        ClassID INTEGER PRIMARY KEY AUTOINCREMENT,
        ClassName TEXT UNIQUE NOT NULL
    );
    """)

    # Create Students table - Links to Class
    cursor.execute("""
    CREATE TABLE Student (
        StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
        ExamNumber TEXT UNIQUE NOT NULL,
        Name TEXT NOT NULL,
        ClassID INTEGER,
        FOREIGN KEY (ClassID) REFERENCES Class(ClassID) ON DELETE SET NULL
    );
    """)

    # Create Results table - The core data repository
    cursor.execute("""
    CREATE TABLE Results (
        ResultID INTEGER PRIMARY KEY AUTOINCREMENT,
        StudentID INTEGER NOT NULL,
        Subject TEXT NOT NULL,
        Score INTEGER CHECK(Score >= 0 AND Score <= 100),
        Term TEXT NOT NULL,
        TeacherID INTEGER,
        DateAdded DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (StudentID) REFERENCES Student(StudentID) ON DELETE CASCADE,
        FOREIGN KEY (TeacherID) REFERENCES Teachers(UserID) ON DELETE SET NULL
    );
    """)

    # --- INSERT SAMPLE DATA ---
    
    # Teachers
    staff = [
        ('Ms Mpongwe', 'pass123', 'Ms. Martha Mpongwe', 'teacher'),
        ('Mr Zulu', 'M.zulu', 'Mr. Brighton Zulu', 'teacher'),
        ('Madam Kalenga', 'M.kay', 'Madam S. Kalenga', 'teacher'),
        ('Mr Sakala', 'pass123', 'Mr. James Sakala', 'teacher'),
        ('admin', 'admin123', 'System Administrator', 'teacher'),
        ('pupil1', 'pass123', 'Student Account 1', 'pupil')
    ]
    cursor.executemany("INSERT INTO Teachers (Username, Password, FullName, Role) VALUES (?, ?, ?, ?)", staff)

    # Classes
    grades = [('Form 1',), ('Form 2',), ('Form 3',), ('Form 4',), ('Form 5',)]
    cursor.executemany("INSERT INTO Class (ClassName) VALUES (?)", grades)

    # Students
    pupils = [
        ('001', 'Alice Mumba', 1),
        ('2026', 'Jane Phiri', 1),
        ('002', 'Bob Chisenga', 2),
        ('2002', 'Zack Tembo', 2),
        ('1709', 'Jimmy Sakala', 3),
        ('2020', 'Charlie Sakala', 3),
        ('2023', 'James Sakala', 4),
        ('008', 'Dee Lungu', 4),
        ('2050', 'Kennedy Bwalya', 5),
        ('1999', 'Ben Kapiri', 5)
    ]
    cursor.executemany("INSERT INTO Student (ExamNumber, Name, ClassID) VALUES (?, ?, ?)", pupils)

    # Initial Results
    results_data = [
        (1, 'Mathematics', 85, 'Term 1', 1),
        (1, 'English', 78, 'Term 1', 2),
        (2, 'Mathematics', 92, 'Term 1', 1),
        (2, 'English', 88, 'Term 1', 3),
        (5, 'Science', 65, 'Term 1', 4),
        (5, 'Social Studies', 72, 'Term 1', 1)
    ]
    cursor.executemany("INSERT INTO Results (StudentID, Subject, Score, Term, TeacherID) VALUES (?, ?, ?, ?, ?)", results_data)

    conn.commit()
    conn.close()
    print("Database Initialized Successfully.")

# ==========================================
# UI COMPONENTS AND STYLING
# ==========================================

def get_html_header(title="KAFUMBWE GRADE BOOK"):
    """
    Returns the CSS and Header portion of the HTML.
    This UI Kit is designed to be modern and responsive.
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            :root {{
                --primary: #2c3e50;
                --secondary: #34495e;
                --accent: #27ae60;
                --danger: #e74c3c;
                --light: #ecf0f1;
                --dark: #2c3e50;
                --shadow: 0 4px 15px rgba(0,0,0,0.1);
            }}

            body {{
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%);
                margin: 0;
                padding: 0;
                color: var(--dark);
                min-height: 100vh;
            }}

            .top-nav {{
                background: var(--primary);
                color: white;
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: var(--shadow);
            }}

            .top-nav a {{
                color: white;
                text-decoration: none;
                margin-left: 20px;
                font-weight: 500;
            }}

            .container {{
                max-width: 1100px;
                margin: 40px auto;
                background: rgba(255, 255, 255, 0.95);
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.15);
            }}

            h1, h2, h3 {{
                color: var(--primary);
            }}

            .welcome-hero {{
                text-align: center;
                padding: 20px 0;
            }}

            .welcome-image {{
                width: 150px;
                height: 150px;
                background: #fff;
                border-radius: 50%;
                padding: 10px;
                box-shadow: var(--shadow);
                margin-bottom: 20px;
                border: 4px solid var(--accent);
            }}

            /* Dashboard Cards */
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}

            .card {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                border-left: 5px solid var(--accent);
                transition: transform 0.3s ease;
            }}

            .card:hover {{ transform: translateY(-5px); }}

            .card.at-risk {{ border-left-color: var(--danger); }}

            .card h4 {{ margin: 0; color: #7f8c8d; font-size: 0.9rem; text-transform: uppercase; }}
            .card p {{ margin: 10px 0 0; font-size: 1.8rem; font-weight: bold; }}

            /* Form Elements */
            form {{
                margin-top: 20px;
            }}

            .form-group {{
                margin-bottom: 15px;
            }}

            label {{
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
            }}

            input[type="text"], input[type="password"], input[type="number"], select {{
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                box-sizing: border-box;
                font-size: 1rem;
                transition: border-color 0.3s;
            }}

            input:focus, select:focus {{
                border-color: var(--accent);
                outline: none;
            }}

            .btn {{
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                text-decoration: none;
                display: inline-block;
                transition: opacity 0.3s;
                font-size: 1rem;
            }}

            .btn:hover {{ opacity: 0.9; }}

            .btn-primary {{ background: var(--accent); color: white; }}
            .btn-secondary {{ background: var(--secondary); color: white; }}
            .btn-danger {{ background: var(--danger); color: white; }}

            /* Table Styling */
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 25px 0;
                background: white;
                border-radius: 8px;
                overflow: hidden;
            }}

            th {{
                background: var(--primary);
                color: white;
                padding: 15px;
                text-align: left;
            }}

            td {{
                padding: 15px;
                border-bottom: 1px solid #eee;
            }}

            tr:hover {{ background: #f9f9f9; }}

            /* Footer and Copyright */
            footer {{
                text-align: center;
                margin-top: 50px;
                padding: 20px;
                color: var(--primary);
                font-size: 0.9rem;
            }}

            .copyright {{
                font-weight: bold;
                margin-bottom: 5px;
            }}

            .dev-tag {{
                font-size: 0.75rem;
                opacity: 0.7;
            }}

            /* Responsive Table Wrapper */
            .table-responsive {{
                overflow-x: auto;
            }}

            /* Notification Badge */
            .badge {{
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: bold;
            }}
            .badge-pass {{ background: #d4edda; color: #155724; }}
            .badge-fail {{ background: #f8d7da; color: #721c24; }}

        </style>
    </head>
    <body>
    """

def get_html_footer():
    """
    Dynamic footer with dynamic year for the copyright notice.
    """
    year = datetime.datetime.now().year
    return f"""
        </div> <!-- End Container -->
        
        <footer>
            <div class="copyright">
                &copy; {year} KAFUMBWE GRADE BOOK SYSTEM. All Rights Reserved.
            </div>
            <div class="dev-tag">
                Official School Management Portal | Version 3.0.1
            </div>
            <div style="margin-top:10px;">
                <small>Developed for Kafumbwe Secondary School Excellence Initiatives</small>
            </div>
        </footer>
    </body>
    </html>
    """

def get_nav(session):
    """
    Generates navigation based on user session.
    """
    if not session:
        return ""
    
    role_badge = f'<span class="badge badge-pass" style="margin-left:10px;">{session["role"].upper()}</span>'
    
    nav = f"""
    <div class="top-nav">
        <div><strong>KAFUMBWE PORTAL</strong> {role_badge}</div>
        <div>
            <a href="/dashboard">Dashboard</a>
    """
    
    if session['role'] == 'teacher':
        nav += """
            <a href="/teacher">Add Results</a>
            <a href="/manage_students">Students</a>
            <a href="/show_recent_results">Recent Saved Results</a>
        """
    else:
        nav += '<a href="/view_results">My Results</a>'
        
    nav += """
            <a href="/logout" style="color:#ff7675;">Logout</a>
        </div>
    </div>
    """
    return nav

# ==========================================
# SERVER REQUEST HANDLER
# ==========================================

class GradeSystemHandler(http.server.BaseHTTPRequestHandler):
    # Class-level session storage (Simplified for prototype)
    user_session = {}

    def do_GET(self):
        """
        Handles all page requests.
        """
        url = urllib.parse.urlparse(self.path)
        path = url.path
        params = urllib.parse.parse_qs(url.query)

        if path == "/":
            self.render_home()
        elif path == "/myphoto.jpg":
            try:
                with open("myphoto.", "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "image/jpeg")
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "File not found")
        elif path == "/login":
            self.render_login()
        elif path == "/logout":
            GradeSystemHandler.user_session = {}
            self.redirect("/login")
        elif path == "/dashboard":
            self.render_dashboard()
        elif path == "/teacher":
            self.render_teacher_entry()
        elif path == "/show_recent_results":
            self.render_recent_results(params)
        elif path == "/view_results":
            self.render_pupil_search(params)
        elif path == "/manage_students":
            self.render_manage_students()
        elif path == "/teacher/edit_student":
            self.render_edit_student(params)
        else:
            self.render_error("404 - Page Not Found")

    def do_POST(self):
        """
        Handles all form submissions.
        """
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(post_data)
        
        path = self.path

        if path == "/login":
            self.handle_login(data)
        elif path == "/teacher/add_results":
            self.handle_add_results(data)
        elif path == "/teacher/edit_result":
            self.handle_edit_results(data)
        elif path == "/admin/add_student":
            self.handle_add_student(data)
        elif path == "/admin/delete_student":
            self.handle_delete_student(data)
        elif path == "/teacher/delete_result":
            self.handle_delete_result(data)
        else:
            self.render_error("Invalid Post Action")

    # --- HELPER METHODS ---

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def render_error(self, message):
        html = get_html_header("Error") + f"<h2>Error</h2><p>{message}</p><a href='/'>Back Home</a>" + get_html_footer()
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def send_html(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        full_page = get_html_header() + get_nav(GradeSystemHandler.user_session) + '<div class="container">' + content + '</div>' + get_html_footer()
        self.wfile.write(full_page.encode())

    # --- PAGE RENDERING METHODS ---

    def render_home(self):
        # Placeholder for School Logo
        logo_svg = """
        <svg class="welcome-image" viewBox="0 0 24 24" fill="none" stroke="#27ae60" stroke-width="2">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
            <path d="M6 12v5c3 3 9 3 12 0v-5"/>
        </svg>
        """
        content = f"""
        <style>
            .container {{
                background: url('/myphoto.') no-repeat center center;
                background-size: cover;
                border: none;
                position: relative;
                min-height: 60vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                overflow: hidden;
            }}
            .container::before {{
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0, 0, 0, 0.6); /* Dark overlay for better and professional text contrast */
                z-index: 1;
                border-radius: 15px; /* Matching the container border radius */
            }}
            .welcome-hero {{
                background: transparent;
                padding: 40px;
                margin: 0;
                text-align: center;
                z-index: 2; /* Ensure it stays above the overlay */
                position: relative;
                width: 100%;
            }}
            .welcome-hero h1 {{
                color: #ffffff !important;
                font-size: 2.8rem;
                letter-spacing: 2px;
                margin-bottom: 20px;
                text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.8);
            }}
            .welcome-hero p {{
                color: #e0e0e0 !important;
                font-size: 1.2rem;
                font-weight: 300;
                margin-bottom: 30px;
                text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.8);
            }}
            .welcome-hero small {{
                color: #cccccc !important;
                text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.8);
            }}
            .action-buttons {{
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
                margin-top: 40px;
            }}
            .action-buttons .btn {{
                padding: 15px 35px;
                font-size: 1.1rem;
                border-radius: 50px; /* Pillow-shaped professional buttons */
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .action-buttons .btn:hover {{
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
            }}
            .separator {{
                margin-top: 50px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                padding-top: 20px;
                width: 80%;
                margin-left: auto;
                margin-right: auto;
            }}
        </style>
        <div class="welcome-hero">
            {logo_svg}
            <h1>KAFUMBWE SOLANA GRADE BOOK SYSTEM</h1>
            <p>Welcome to the official academic record management system of Kafumbwe.</p>
            <div class="action-buttons">
                <a href="/login" class="btn btn-primary">Teacher Portal Login</a>
                <a href="/view_results" class="btn btn-secondary">Check Student Results</a>
            </div>
            <div class="separator">
                <p><small style="opacity: 0.8;">Authorized personnel only. Please ensure your credentials are kept secure.</small></p>
                <p><small style="opacity: 0.9; font-weight: bold; letter-spacing: 1px;">-- JJ.SAKALA</small></p>
            </div>
        </div>
        """
        self.send_html(content)

    def render_login(self):
        content = """
        <div style="max-width:400px; margin:0 auto;">
            <h2 style="text-align:center;">Staff Login</h2>
            <form method="post" action="/login">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required placeholder="Enter username">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" id="passInput" required placeholder="Enter password">
                </div>
                <div style="margin:10px 0;">
                    <input type="checkbox" onclick="var x = document.getElementById('passInput'); x.type = x.type === 'password' ? 'text' : 'password';"> Show Password
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;">Sign In</button>
            </form>
            <p style="text-align:center; margin-top:20px;"><a href="/">Back to Landing Page</a></p>
        </div>
        """
        self.send_html(content)

    def render_dashboard(self):
        if not GradeSystemHandler.user_session:
            return self.redirect("/login")

        conn = sqlite3.connect("gradesystem.db")
        cursor = conn.cursor()

        # Aggregate Data
        cursor.execute("SELECT COUNT(*) FROM Student")
        total_students = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM Class")
        total_classes = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(Score) FROM Results")
        avg_score = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM Results WHERE Score < 50")
        at_risk_count = cursor.fetchone()[0]

        # Detailed Stats
        cursor.execute("""
            SELECT Subject, AVG(Score) as avg_score 
            FROM Results 
            GROUP BY Subject 
            ORDER BY avg_score DESC
        """)
        subject_stats = cursor.fetchall()

        cursor.execute("""
            SELECT s.Name, AVG(r.Score) as avg_score
            FROM Student s
            JOIN Results r ON s.StudentID = r.StudentID
            GROUP BY s.StudentID
            ORDER BY avg_score DESC
            LIMIT 3
        """)
        top_performers = cursor.fetchall()

        conn.close()

        subject_html = "".join([f"<tr><td>{s[0]}</td><td>{round(s[1],1)}%</td></tr>" for s in subject_stats])
        top_html = "".join([f"<tr><td>{p[0]}</td><td>{round(p[1],1)}%</td></tr>" for p in top_performers])

        content = f"""
        <h2>Academic Overview</h2>
        <div class="stats-grid">
            <div class="card">
                <h4>Total Pupils</h4>
                <p>{total_students}</p>
            </div>
            <div class="card">
                <h4>Active Classes</h4>
                <p>{total_classes}</p>
            </div>
            <div class="card">
                <h4>System Avg</h4>
                <p>{round(avg_score, 1)}%</p>
            </div>
            <div class="card at-risk">
                <h4>Failing Records</h4>
                <p>{at_risk_count}</p>
            </div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:30px;">
            <div>
                <h3>Subject Performance</h3>
                <table>
                    <thead><tr><th>Subject</th><th>Average</th></tr></thead>
                    <tbody>{subject_html if subject_html else "<tr><td colspan='2'>No data</td></tr>"}</tbody>
                </table>
            </div>
            <div>
                <h3>Honor Roll (Top 3)</h3>
                <table>
                    <thead><tr><th>Name</th><th>Average</th></tr></thead>
                    <tbody>{top_html if top_html else "<tr><td colspan='2'>No data</td></tr>"}</tbody>
                </table>
            </div>
        </div>
        """
        self.send_html(content)

    def render_teacher_entry(self):
        if GradeSystemHandler.user_session.get('role') != 'teacher':
            return self.render_error("Access Denied")

        conn = sqlite3.connect("gradesystem.db")
        classes = conn.execute("SELECT ClassID, ClassName FROM Class").fetchall()
        conn.close()

        class_options = "".join([f'<option value="{c[0]}">{c[1]}</option>' for c in classes])

        content = f"""
        <h2>New Grade Entry</h2>
        <p>Use the form below to register a student and record their academic results.</p>
        
        <form method="post" action="/teacher/add_results">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                <div class="form-group">
                    <label>Exam Number</label>
                    <input type="text" name="exam_number" required placeholder="e.g. EX001">
                </div>
                <div class="form-group">
                    <label>Student Full Name</label>
                    <input type="text" name="name" required placeholder="Full Name">
                </div>
            </div>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                <div class="form-group">
                    <label>Class/Grade</label>
                    <select name="class_id" required>
                        {class_options}
                    </select>
                </div>
                <div class="form-group">
                    <label>Academic Term</label>
                    <select name="term" required>
                        <option>Term 1</option>
                        <option>Term 2</option>
                        <option>Term 3</option>
                    </select>
                </div>
            </div>

            <h3 style="margin-top:30px; border-bottom:1px solid #ddd; padding-bottom:10px;">Subject Scores</h3>
            <div id="score-rows">
                <div style="display:flex; gap:10px; margin-bottom:10px;">
                    <input type="text" name="subject[]" placeholder="Subject Name" required style="flex:2;">
                    <input type="number" name="score[]" placeholder="Score (0-100)" min="0" max="100" required style="flex:1;">
                    <button type="button" onclick="this.parentElement.remove()" class="btn btn-danger">X</button>
                </div>
            </div>
            
            <button type="button" onclick="addScoreRow()" class="btn btn-secondary" style="margin-bottom:20px;">+ Add Another Subject</button>
            <hr>
            <button type="submit" class="btn btn-primary">Save All Records</button>
        </form>

        <script>
            function addScoreRow() {{
                const container = document.getElementById('score-rows');
                const div = document.createElement('div');
                div.style.display = 'flex';
                div.style.gap = '10px';
                div.style.marginBottom = '10px';
                div.innerHTML = `
                    <input type="text" name="subject[]" placeholder="Subject Name" required style="flex:2;">
                    <input type="number" name="score[]" placeholder="Score (0-100)" min="0" max="100" required style="flex:1;">
                    <button type="button" onclick="this.parentElement.remove()" class="btn btn-danger">X</button>
                `;
                container.appendChild(div);
            }}
        </script>
        """
        self.send_html(content)

    def render_recent_results(self, params):
        if not GradeSystemHandler.user_session: return self.redirect("/login")

        conn = sqlite3.connect("gradesystem.db")
        cursor = conn.cursor()

        # Fetch students for selector
        cursor.execute("SELECT StudentID, Name, ExamNumber FROM Student ORDER BY Name")
        students = cursor.fetchall()

        student_id = None
        if params and "student_id" in params and params["student_id"]:
            try:
                student_id = int(params["student_id"][0])
            except Exception:
                student_id = None

        results_html = ""
        header_html = ""
        table_headers = ""

        if student_id:
            cursor.execute("SELECT Name, ExamNumber FROM Student WHERE StudentID = ?", (student_id,))
            srow = cursor.fetchone()
            if srow:
                sel_name, sel_exam = srow
                header_html = f"<h3 style='margin-top:20px;'>Recent Results for <strong>{sel_name}</strong> ({sel_exam})</h3>"
            
            cursor.execute("""
                SELECT r.ResultID, r.Subject, r.Score, r.Term, t.Username, c.ClassName
                FROM Results r
                LEFT JOIN Teachers t ON r.TeacherID = t.UserID
                LEFT JOIN Student s ON r.StudentID = s.StudentID
                LEFT JOIN Class c ON s.ClassID = c.ClassID
                WHERE r.StudentID = ?
                ORDER BY r.ResultID DESC
                LIMIT 50
            """, (student_id,))
            rows = cursor.fetchall()
            if rows:
                for rid, subject, score, term, teacher, class_name in rows:
                    teacher_name = teacher if teacher else "Unknown"
                    badge = "badge-pass" if score >= 50 else "badge-fail"
                    del_form = f"""
                    <form method="post" action="/teacher/delete_result" style="display:inline; margin:0;" onsubmit="return confirm('Delete this result?')">
                        <input type="hidden" name="result_id" value="{rid}">
                        <button type="submit" class="btn btn-danger" style="padding:4px 8px; font-size:0.8rem; height:auto; margin:0;">Del</button>
                    </form>
                    """
                    results_html += f"<tr><td>{subject}</td><td><span class='badge {badge}'>{score}%</span></td><td>{term}</td><td>{class_name}</td><td>{teacher_name}</td><td>{del_form}</td></tr>"
            else:
                results_html = "<tr><td colspan='6' style='padding:15px; text-align:center;'>No results for this pupil yet.</td></tr>"
            table_headers = "<th>Subject</th><th>Score</th><th>Term</th><th>Class</th><th>Submitted By</th><th>Action</th>"

        # Build student selector
        options_html = "<option value=''>-- All Pupils --</option>"
        for sid, name, exam in students:
            sel = " selected" if student_id and sid == student_id else ""
            options_html += f"<option value='{sid}'{sel}>{name} ({exam})</option>"

        # Build pupil cards
        students_cards_html = ""
        if students:
            students_cards_html += "<div style='display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:20px; margin-top:0px;'>"
            role = GradeSystemHandler.user_session.get('role') if GradeSystemHandler.user_session else None
            for sid, name, exam in students:
                students_cards_html += (
                    "<div style='background:#eaf4fe; padding:20px; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.06);'>"
                    f"<h4 style='margin:0 0 10px 0; color:#1976d2; font-size:1.1rem;'>Check Results for {name}</h4>"
                    f"<p style='margin:0 0 15px 0; color:#555;'>Exam: {exam}</p>"
                    f"<a href='/show_recent_results?student_id={sid}' style='display:inline-block; padding:8px 16px; background:#2196F3; color:#fff; text-decoration:none; border-radius:6px; margin-right:8px; font-weight:bold;'>View</a>"
                    + (f"<a href='/teacher/edit_student?student_id={sid}' style='display:inline-block; padding:8px 16px; background:#ff9800; color:#fff; text-decoration:none; border-radius:6px; font-weight:bold;'>Edit</a>" if role == 'teacher' else "")
                    + "</div>"
                )
            students_cards_html += "</div>"
        
        conn.close()

        table_css = ""
        if student_id:
            table_css = f"""
            <div style="margin-top:20px;" class="table-responsive">
                {header_html}
                <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                    <thead><tr style="background-color:#f2f2f2;">{table_headers}</tr></thead>
                    <tbody>{results_html}</tbody>
                </table>
            </div>
            """

        content = f"""
        <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 30px; flex-wrap:wrap; gap:20px;'>
            <div style="display:flex; gap:10px;">
                <a href="/dashboard" class="btn" style="background:#2196F3; color:#fff; padding:10px 15px; font-weight:bold; border-radius:4px;">Back to Teacher Dashboard</a>
                <a href="/show_recent_results" class="btn" style="background:#9e9e9e; color:#fff; padding:10px 15px; font-weight:bold; border-radius:4px;">Show All</a>
            </div>
            <div style="background:#fff; padding:20px; border-radius:8px; box-shadow:0 2px 5px rgba(0,0,0,0.1); min-width:250px;">
                <form method='get' action='/show_recent_results' style='margin:0;'>
                    <label style='font-weight:600; display:block; margin-bottom:10px; color:#555;'>Filter by Pupil:</label>
                    <select name='student_id' style='padding:10px; border-radius:6px; border:1px solid #ccc; width:100%; background:#fff;' onchange='this.form.submit()'>
                        {options_html}
                    </select>
                    <noscript><button type="submit" class="btn btn-primary" style="margin-top:10px;">View</button></noscript>
                </form>
            </div>
        </div>
        
        {students_cards_html}

        {table_css}

        <div style="margin-top: 40px; text-align: left;">
            <a href="/logout" class="btn" style="background:#f44336; color:#fff; font-weight:bold; padding:10px 20px; border-radius:4px;">Logout</a>
        </div>
        """
        self.send_html(content)

    def render_pupil_search(self, params):
        exam_number = params.get('exam_number', [None])[0]
        class_id = params.get('class_id', [None])[0]

        conn = sqlite3.connect("gradesystem.db")
        classes = conn.execute("SELECT ClassID, ClassName FROM Class").fetchall()
        class_options = "".join([f'<option value="{c[0]}">{c[1]}</option>' for c in classes])

        result_view = ""
        if exam_number and class_id:
            cursor = conn.cursor()
            cursor.execute("SELECT StudentID, Name FROM Student WHERE ExamNumber=? AND ClassID=?", (exam_number, class_id))
            student = cursor.fetchone()
            
            if student:
                sid, sname = student
                cursor.execute("""
                    SELECT Subject, Score, Term, t.FullName 
                    FROM Results r
                    LEFT JOIN Teachers t ON r.TeacherID = t.UserID
                    WHERE StudentID = ? ORDER BY Term ASC
                """, (sid,))
                recs = cursor.fetchall()
                
                rows = ""
                total = 0
                for rec in recs:
                    total += rec[1]
                    badge = "badge-pass" if rec[1] >= 50 else "badge-fail"
                    rows += f"<tr><td>{rec[0]}</td><td><span class='badge {badge}'>{rec[1]}</span></td><td>{rec[2]}</td><td>{rec[3]}</td></tr>"
                
                avg = total / len(recs) if recs else 0
                result_view = f"""
                <div style="background:#fff; padding:20px; border-radius:10px; margin-top:30px; border:1px solid #ddd;">
                    <h3>Report for {sname}</h3>
                    <table>
                        <thead><tr><th>Subject</th><th>Score</th><th>Term</th><th>Instructor</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                    <p style="font-weight:bold; font-size:1.2rem;">Cumulative Average: {round(avg, 1)}%</p>
                </div>
                """
            else:
                result_view = "<p style='color:red; margin-top:20px;'>No student found with those details.</p>"

        conn.close()

        content = f"""
        <h2>Student Result Inquiry</h2>
        <p>Enter your examination number and select your current grade to view your performance report.</p>
        <form method="get" action="/view_results">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
                <div class="form-group">
                    <label>Examination Number</label>
                    <input type="text" name="exam_number" required placeholder="e.g. 1709">
                </div>
                <div class="form-group">
                    <label>Your Class</label>
                    <select name="class_id" required>
                        <option value="">-- Choose --</option>
                        {class_options}
                    </select>
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Retrieve Results</button>
        </form>
        {result_view}
        """
        self.send_html(content)

    def render_manage_students(self):
        if GradeSystemHandler.user_session.get('role') != 'teacher': return self.render_error("Unauthorized")
        
        conn = sqlite3.connect("gradesystem.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.StudentID, s.Name, s.ExamNumber, c.ClassName 
            FROM Student s 
            LEFT JOIN Class c ON s.ClassID = c.ClassID
        """)
        students = cursor.fetchall()
        
        classes = cursor.execute("SELECT ClassID, ClassName FROM Class").fetchall()
        class_opts = "".join([f'<option value="{c[0]}">{c[1]}</option>' for c in classes])
        
        rows = ""
        for s in students:
            rows += f"""
            <tr>
                <td>{s[1]}</td>
                <td>{s[2]}</td>
                <td>{s[3]}</td>
                <td>
                    <a href="/teacher/edit_student?student_id={s[0]}" class="btn btn-secondary" style="padding:5px 10px; font-size:0.8rem;">Edit</a>
                    <form method="post" action="/admin/delete_student" style="display:inline;">
                        <input type="hidden" name="student_id" value="{s[0]}">
                        <button type="submit" class="btn btn-danger" style="padding:5px 10px; font-size:0.8rem;">Delete</button>
                    </form>
                </td>
            </tr>
            """
            
        content = f"""
        <h2>Student Directory</h2>
        <div style="display:grid; grid-template-columns: 2fr 1fr; gap:30px;">
            <div>
                <table>
                    <thead><tr><th>Name</th><th>Exam #</th><th>Class</th><th>Action</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
            <div style="background:#f1f2f6; padding:20px; border-radius:10px;">
                <h3>Student</h3>
                <form method="post" action="/admin/add_student">
                    <div class="form-group"><label>Full Name</label><input type="text" name="name" required></div>
                    <div class="form-group"><label>Exam ID</label><input type="text" name="exam_number" required></div>
                    <div class="form-group"><label>Class</label><select name="class_id">{class_opts}</select></div>
                    <button type="submit" class="btn btn-primary" style="width:100%;">Register Student</button>
                </form>
            </div>
        </div>
        """
        conn.close()
        self.send_html(content)

    def render_edit_student(self, params):
        if GradeSystemHandler.user_session.get('role') != 'teacher': return self.render_error("Access Denied")
        
        student_id = params.get('student_id', [None])[0]
        if not student_id: return self.redirect("/manage_students")
        
        conn = sqlite3.connect("gradesystem.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT StudentID, Name, ExamNumber, ClassID FROM Student WHERE StudentID=?", (student_id,))
        s = cursor.fetchone()
        
        cursor.execute("SELECT ResultID, Subject, Score, Term FROM Results WHERE StudentID=?", (student_id,))
        results = cursor.fetchall()
        
        res_rows = ""
        for r in results:
            res_rows += f"""
            <div style="display:flex; gap:10px; margin-bottom:10px; align-items:center;">
                <input type="hidden" name="result_id[]" value="{r[0]}">
                <span style="flex:2;">{r[1]} ({r[3]})</span>
                <input type="number" name="score[]" value="{r[2]}" min="0" max="100" style="flex:1;">
            </div>
            """
            
        content = f"""
        <h2>Correction Portal: {s[1]}</h2>
        <form method="post" action="/teacher/edit_result">
            <input type="hidden" name="student_id" value="{s[0]}">
            <h3>Update Scores</h3>
            {res_rows if res_rows else "<p>No results recorded for this student.</p>"}
            <hr>
            <button type="submit" class="btn btn-primary">Apply Changes</button>
            <a href="/manage_students" class="btn btn-secondary">Cancel</a>
        </form>
        """
        conn.close()
        self.send_html(content)

    # --- POST HANDLER LOGIC ---

    def handle_login(self, data):
        user = data.get('username', [''])[0]
        pw = data.get('password', [''])[0]
        
        conn = sqlite3.connect("gradesystem.db")
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Username, Role FROM Teachers WHERE Username=? AND Password=?", (user, pw))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            GradeSystemHandler.user_session = {
                'user_id': row[0],
                'username': row[1],
                'role': row[2]
            }
            self.redirect("/dashboard")
        else:
            self.redirect("/login?error=1")

    def handle_add_results(self, data):
        exam = data.get('exam_number', [''])[0]
        name = data.get('name', [''])[0]
        cid = data.get('class_id', [''])[0]
        term = data.get('term', [''])[0]
        subjects = data.get('subject[]', [])
        scores = data.get('score[]', [])
        tid = GradeSystemHandler.user_session.get('user_id')

        conn = sqlite3.connect("gradesystem.db")
        cursor = conn.cursor()
        
        # Upsert Student
        cursor.execute("SELECT StudentID FROM Student WHERE ExamNumber=?", (exam,))
        row = cursor.fetchone()
        if row:
            sid = row[0]
        else:
            cursor.execute("INSERT INTO Student (ExamNumber, Name, ClassID) VALUES (?, ?, ?)", (exam, name, cid))
            sid = cursor.lastrowid
            
        # Add Results
        for subj, score in zip(subjects, scores):
            cursor.execute("INSERT INTO Results (StudentID, Subject, Score, Term, TeacherID) VALUES (?, ?, ?, ?, ?)",
                           (sid, subj, score, term, tid))
        
        conn.commit()
        conn.close()
        self.redirect("/show_recent_results")

    def handle_edit_results(self, data):
        rids = data.get('result_id[]', [])
        scores = data.get('score[]', [])
        
        conn = sqlite3.connect("gradesystem.db")
        cursor = conn.cursor()
        for rid, sc in zip(rids, scores):
            cursor.execute("UPDATE Results SET Score=? WHERE ResultID=?", (sc, rid))
        conn.commit()
        conn.close()
        self.redirect("/show_recent_results")

    def handle_add_student(self, data):
        name = data.get('name', [''])[0]
        exam = data.get('exam_number', [''])[0]
        cid = data.get('class_id', [''])[0]
        
        conn = sqlite3.connect("gradesystem.db")
        try:
            conn.execute("INSERT INTO Student (Name, ExamNumber, ClassID) VALUES (?, ?, ?)", (name, exam, cid))
            conn.commit()
        except:
            pass
        finally:
            conn.close()
        self.redirect("/manage_students")

    def handle_delete_student(self, data):
        sid = data.get('student_id', [None])[0]
        if sid:
            conn = sqlite3.connect("gradesystem.db")
            conn.execute("DELETE FROM Student WHERE StudentID=?", (sid,))
            conn.commit()
            conn.close()
        self.redirect("/manage_students")

    def handle_delete_result(self, data):
        rid = data.get('result_id', [None])[0]
        if rid:
            conn = sqlite3.connect("gradesystem.db")
            conn.execute("DELETE FROM Results WHERE ResultID=?", (rid,))
            conn.commit()
            conn.close()
        self.redirect("/show_recent_results")

# ==========================================
# MAIN EXECUTION THREAD
# ==========================================

def run_server():
    """
    Main entry point for the Grade Book System.
    """
    # Create DB if it doesn't exist or re-seed it
    init_db()
    
    PORT = int(os.environ.get("PORT", 3004))
    
    print("-" * 50)
    print("KAFUMBWE GRADE BOOK SYSTEM")
    print("-" * 50)
    print(f"Server starting on port {PORT}...")
    print(f"Access the system via: http://localhost:{3004}")
    print("Default Login: admin / admin123")
    print("-" * 50)

    try:
        with socketserver.TCPServer(("", PORT), GradeSystemHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    run_server()