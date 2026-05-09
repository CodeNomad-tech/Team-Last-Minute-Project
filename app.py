import os
import sqlite3
import uuid
from flask import Flask, request, redirect, session, render_template
import datetime

app = Flask(__name__)
app.secret_key = 'kafumbwe_secret_key_123'

# Inject year into all templates globally
@app.context_processor
def inject_year():
    return {'year': datetime.datetime.now().year}

DB_PATH = "gradesystem.db"

def parse_datetime(value):
    if isinstance(value, datetime.datetime) or value is None:
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(value, fmt)
        except (TypeError, ValueError):
            continue
    return None

def normalize_datetime_rows(rows, indexes):
    normalized = []
    for row in rows:
        item = list(row)
        for index in indexes:
            if index < len(item):
                item[index] = parse_datetime(item[index])
        normalized.append(tuple(item))
    return normalized

def table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def add_column_if_missing(cursor, table_name, column_name, column_sql):
    if column_name not in table_columns(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")

def migrate_db(conn):
    cursor = conn.cursor()
    add_column_if_missing(cursor, "TeacherProfile", "SolanaWallet", "SolanaWallet TEXT")
    add_column_if_missing(cursor, "FeesPayment", "PaymentMethod", "PaymentMethod TEXT DEFAULT 'manual'")
    add_column_if_missing(cursor, "FeesPayment", "SolanaWallet", "SolanaWallet TEXT")
    add_column_if_missing(cursor, "FeesPayment", "SolanaSignature", "SolanaSignature TEXT")
    add_column_if_missing(cursor, "FeesPayment", "SolanaCluster", "SolanaCluster TEXT DEFAULT 'devnet'")
    add_column_if_missing(cursor, "FeesPayment", "PaymentSessionID", "PaymentSessionID TEXT")
    add_column_if_missing(cursor, "MobileMoneyTransaction", "BlockchainNetwork", "BlockchainNetwork TEXT")
    add_column_if_missing(cursor, "MobileMoneyTransaction", "WalletPublicKey", "WalletPublicKey TEXT")
    add_column_if_missing(cursor, "MobileMoneyTransaction", "SolanaSignature", "SolanaSignature TEXT")
    add_column_if_missing(cursor, "MobileMoneyTransaction", "SolanaCluster", "SolanaCluster TEXT DEFAULT 'devnet'")
    add_column_if_missing(cursor, "MobileMoneyTransaction", "PaymentSessionID", "PaymentSessionID TEXT")

# ==========================================
# DATABASE INITIALIZATION AND SEEDING
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Teachers (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT UNIQUE NOT NULL,
        Password TEXT NOT NULL,
        FullName TEXT,
        Role TEXT DEFAULT 'teacher'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TeacherProfile (
        ProfileID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER UNIQUE NOT NULL,
        Bio TEXT,
        PhoneNumber TEXT,
        MobileMoneyID TEXT,
        CommunityReputation INTEGER DEFAULT 0,
        TotalFeesBalance REAL DEFAULT 0,
        ProfileCreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        LastUpdated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (UserID) REFERENCES Teachers(UserID) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FeesPayment (
        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER NOT NULL,
        PaymentAmount REAL NOT NULL,
        PaymentDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        PaymentDescription TEXT,
        PaymentStatus TEXT DEFAULT 'pending',
        TransactionReference TEXT,
        FOREIGN KEY (UserID) REFERENCES Teachers(UserID) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MobileMoneyTransaction (
        TransactionID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER NOT NULL,
        TransactionType TEXT NOT NULL,
        Amount REAL NOT NULL,
        Recipient TEXT,
        SenderID TEXT,
        TransactionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        Status TEXT DEFAULT 'completed',
        TransactionReference TEXT,
        Notes TEXT,
        FOREIGN KEY (UserID) REFERENCES Teachers(UserID) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CommunityEndorsement (
        EndorsementID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INTEGER NOT NULL,
        EndorserName TEXT NOT NULL,
        EndorsementText TEXT NOT NULL,
        EndorsementScore INTEGER DEFAULT 5,
        EndorsementDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        Verified INTEGER DEFAULT 0,
        FOREIGN KEY (UserID) REFERENCES Teachers(UserID) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Class (
        ClassID INTEGER PRIMARY KEY AUTOINCREMENT,
        ClassName TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Student (
        StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
        ExamNumber TEXT UNIQUE NOT NULL,
        Name TEXT NOT NULL,
        ClassID INTEGER,
        FOREIGN KEY (ClassID) REFERENCES Class(ClassID) ON DELETE SET NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Results (
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

    migrate_db(conn)

    cursor.execute("SELECT COUNT(*) FROM Teachers")
    if cursor.fetchone()[0] > 0:
        conn.commit()
        conn.close()
        print("Database Ready.")
        return

    staff = [
        ('Ms Mpongwe', 'pass123', 'Ms. Martha Mpongwe', 'teacher'),
        ('Mr Zulu', 'M.zulu', 'Mr. Brighton Zulu', 'teacher'),
        ('Madam Kalenga', 'M.kay', 'Madam S. Kalenga', 'teacher'),
        ('Mr Sakala', 'pass123', 'Mr. James Sakala', 'teacher'),
        ('admin', 'admin123', 'System Administrator', 'teacher'),
        ('pupil1', 'pass123', 'Student Account 1', 'pupil')
    ]
    cursor.executemany("INSERT INTO Teachers (Username, Password, FullName, Role) VALUES (?, ?, ?, ?)", staff)

    # Create profiles for teachers
    profiles = [
        (1, 'Experienced educator with 15 years in the field', '+260-XXX-XXXX', 'MTN260123456789', 45),
        (2, 'Dedicated science teacher passionate about student development', '+260-XXX-XXXX', 'AIRTEL260987654321', 38),
        (3, 'Mathematics specialist and community advocate', '+260-XXX-XXXX', 'ZESCO260555666777', 52),
        (4, 'History and Social Studies teacher', '+260-XXX-XXXX', 'MTN260111222333', 40),
    ]
    cursor.executemany("""
        INSERT INTO TeacherProfile (UserID, Bio, PhoneNumber, MobileMoneyID, CommunityReputation) 
        VALUES (?, ?, ?, ?, ?)
    """, profiles)

    # Add sample fees payments
    fees = [
        (1, 150.00, 'School Fees - Term 1'),
        (1, 75.50, 'Facility Maintenance Fee'),
        (2, 150.00, 'School Fees - Term 1'),
        (3, 150.00, 'School Fees - Term 1'),
    ]
    cursor.executemany("""
        INSERT INTO FeesPayment (UserID, PaymentAmount, PaymentDescription, PaymentStatus) 
        VALUES (?, ?, ?, 'paid')
    """, fees)

    # Add sample mobile money transactions
    transactions = [
        (1, 'transfer', 100.00, 'School Account', 'MTN260123456789', 'completed', 'REF001'),
        (1, 'deposit', 250.00, None, 'MTN260123456789', 'completed', 'REF002'),
        (2, 'transfer', 50.00, 'Community Fund', 'AIRTEL260987654321', 'completed', 'REF003'),
        (3, 'withdrawal', 75.00, None, 'ZESCO260555666777', 'completed', 'REF004'),
    ]
    cursor.executemany("""
        INSERT INTO MobileMoneyTransaction (UserID, TransactionType, Amount, Recipient, SenderID, Status, TransactionReference) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    # Add sample community endorsements
    endorsements = [
        (1, 'Mr. Phiri', 'Outstanding teacher who goes above and beyond for the students', 5),
        (1, 'Community Leader', 'Highly respected and trusted member of the community', 5),
        (2, 'Parent Association', 'Excellent engagement with parents and consistent support', 4),
        (3, 'School Board', 'Demonstrates exceptional leadership and dedication', 5),
    ]
    cursor.executemany("""
        INSERT INTO CommunityEndorsement (UserID, EndorserName, EndorsementText, EndorsementScore, Verified) 
        VALUES (?, ?, ?, ?, 1)
    """, endorsements)

    grades = [('Form 1',), ('Form 2',), ('Form 3',), ('Form 4',), ('Form 5',)]
    cursor.executemany("INSERT INTO Class (ClassName) VALUES (?)", grades)

    pupils = [
        ('001', 'Alinase Nyirenda', 1),
        ('2026', 'Jane Phiri', 1),
        ('002', 'Bob Chisenga', 2),
        ('2002', 'Zack Tembo', 2),
        ('1709', 'Jimmy Sakala', 3),
        ('2020', 'Charlie Sakala', 3),
        ('2023', 'James Sakala', 4),
        ('008', 'Leo Lungu', 4),
        ('2050', 'Kennedy Bwalya', 5),
        ('1999', 'Ben Kapiri', 5)
    ]
    cursor.executemany("INSERT INTO Student (ExamNumber, Name, ClassID) VALUES (?, ?, ?)", pupils)

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
# ROUTES
# ==========================================

@app.route('/')
def render_home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '')
        pw = request.form.get('password', '')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Username, Role FROM Teachers WHERE Username=? AND Password=?", (user, pw))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            session['user_id'] = row[0]
            session['username'] = row[1]
            session['role'] = row[2]
            return redirect("/dashboard")
        else:
            return render_template('login.html', error=True)

    error = request.args.get('error') == '1'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

@app.route('/dashboard')
def render_dashboard():
    if not session.get('role'):
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Student")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM Class")
    total_classes = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(Score) FROM Results")
    avg_score = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM Results WHERE Score < 50")
    at_risk_count = cursor.fetchone()[0]

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

    return render_template('dashboard.html', 
        total_students=total_students, 
        total_classes=total_classes, 
        avg_score=avg_score, 
        at_risk_count=at_risk_count, 
        subject_stats=subject_stats, 
        top_performers=top_performers
    )

@app.route('/teacher')
def render_teacher_entry():
    if session.get('role') != 'teacher':
        return render_template('error.html', message="Access Denied"), 403

    conn = sqlite3.connect(DB_PATH)
    classes = conn.execute("SELECT ClassID, ClassName FROM Class").fetchall()
    conn.close()

    return render_template('teacher_entry.html', classes=classes)

@app.route('/show_recent_results')
def render_recent_results():
    if not session.get('role'): return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT StudentID, Name, ExamNumber FROM Student ORDER BY Name")
    students = cursor.fetchall()

    student_id = request.args.get('student_id', type=int)

    sel_name = ""
    sel_exam = ""
    rows = []

    if student_id:
        cursor.execute("SELECT Name, ExamNumber FROM Student WHERE StudentID = ?", (student_id,))
        srow = cursor.fetchone()
        if srow:
            sel_name, sel_exam = srow
        
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

    conn.close()

    return render_template('recent_results.html', 
        students=students, 
        student_id=student_id, 
        sel_name=sel_name, 
        sel_exam=sel_exam, 
        rows=rows, 
        session_role=session.get('role')
    )

@app.route('/view_results')
def render_pupil_search():
    exam_number = request.args.get('exam_number')
    class_id = request.args.get('class_id')

    conn = sqlite3.connect(DB_PATH)
    classes = conn.execute("SELECT ClassID, ClassName FROM Class").fetchall()

    student = None
    recs = []
    avg = 0
    error_msg = None

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
            
            if recs:
                total = sum(rec[1] for rec in recs)
                avg = total / len(recs)
        else:
            error_msg = "No student found with those details."

    conn.close()

    return render_template('view_results.html', 
        classes=classes, 
        student=student, 
        recs=recs, 
        avg=avg, 
        error_msg=error_msg
    )

@app.route('/manage_students')
def render_manage_students():
    if session.get('role') != 'teacher': return render_template('error.html', message="Unauthorized"), 403
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.StudentID, s.Name, s.ExamNumber, c.ClassName 
        FROM Student s 
        LEFT JOIN Class c ON s.ClassID = c.ClassID
    """)
    students = cursor.fetchall()
    
    classes = cursor.execute("SELECT ClassID, ClassName FROM Class").fetchall()
    conn.close()

    return render_template('manage_students.html', students=students, classes=classes)

@app.route('/teacher/edit_student')
def render_edit_student():
    if session.get('role') != 'teacher': return render_template('error.html', message="Access Denied"), 403
    
    student_id = request.args.get('student_id')
    if not student_id: return redirect("/manage_students")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT StudentID, Name, ExamNumber, ClassID FROM Student WHERE StudentID=?", (student_id,))
    student = cursor.fetchone()
    
    cursor.execute("SELECT ResultID, Subject, Score, Term FROM Results WHERE StudentID=?", (student_id,))
    results = cursor.fetchall()
    
    conn.close()
    return render_template('edit_student.html', student=student, results=results)

# DECENTRALIZED PROFILE ROUTES
@app.route('/profile')
def render_teacher_profile():
    if not session.get('user_id'): return redirect("/login")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    user_id = session.get('user_id')
    
    # Get teacher info
    cursor.execute("SELECT UserID, Username, FullName FROM Teachers WHERE UserID=?", (user_id,))
    teacher = cursor.fetchone()
    
    # Get profile
    cursor.execute("""
        SELECT ProfileID, UserID, Bio, PhoneNumber, MobileMoneyID, CommunityReputation,
               ProfileCreatedDate, LastUpdated, SolanaWallet
        FROM TeacherProfile WHERE UserID=?
    """, (user_id,))
    profile = cursor.fetchone()
    
    if not profile:
        cursor.execute("""
            INSERT INTO TeacherProfile (UserID) VALUES (?)
        """, (user_id,))
        conn.commit()
        cursor.execute("""
            SELECT ProfileID, UserID, Bio, PhoneNumber, MobileMoneyID, CommunityReputation,
                   ProfileCreatedDate, LastUpdated, SolanaWallet
            FROM TeacherProfile WHERE UserID=?
        """, (user_id,))
        profile = cursor.fetchone()
    
    # Get fees summary
    cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN PaymentStatus='paid' THEN 1 ELSE 0 END) as paid,
               SUM(CASE WHEN PaymentStatus='pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN PaymentStatus='paid' THEN PaymentAmount ELSE 0 END) as total_paid
        FROM FeesPayment WHERE UserID=?
    """, (user_id,))
    fees_summary = cursor.fetchone()
    
    # Get recent transactions
    cursor.execute("""
        SELECT TransactionID, TransactionType, Amount, TransactionDate, Status 
        FROM MobileMoneyTransaction WHERE UserID=? 
        ORDER BY TransactionDate DESC LIMIT 5
    """, (user_id,))
    recent_transactions = normalize_datetime_rows(cursor.fetchall(), [3])
    
    # Get endorsements
    cursor.execute("""
        SELECT EndorsementID, EndorserName, EndorsementScore, EndorsementDate 
        FROM CommunityEndorsement WHERE UserID=? 
        ORDER BY EndorsementDate DESC LIMIT 3
    """, (user_id,))
    endorsements = normalize_datetime_rows(cursor.fetchall(), [3])
    
    avg_reputation = 0
    if endorsements:
        cursor.execute("SELECT AVG(EndorsementScore) FROM CommunityEndorsement WHERE UserID=?", (user_id,))
        avg_reputation = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return render_template('profile.html', 
                         teacher=teacher, 
                         profile=profile,
                         fees_summary=fees_summary,
                         recent_transactions=recent_transactions,
                         endorsements=endorsements,
                         avg_reputation=avg_reputation)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_teacher_profile():
    if not session.get('user_id'): return redirect("/login")
    
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        bio = request.form.get('bio', '')
        phone = request.form.get('phone', '')
        mobile_money_id = request.form.get('mobile_money_id', '')
        solana_wallet = request.form.get('solana_wallet', '')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE TeacherProfile 
            SET Bio=?, PhoneNumber=?, MobileMoneyID=?, SolanaWallet=?, LastUpdated=CURRENT_TIMESTAMP
            WHERE UserID=?
        """, (bio, phone, mobile_money_id, solana_wallet, user_id))
        
        conn.commit()
        conn.close()
        
        return redirect("/profile")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT UserID, Username, FullName FROM Teachers WHERE UserID=?", (user_id,))
    teacher = cursor.fetchone()
    
    cursor.execute("""
        SELECT ProfileID, UserID, Bio, PhoneNumber, MobileMoneyID, CommunityReputation,
               ProfileCreatedDate, LastUpdated, SolanaWallet
        FROM TeacherProfile WHERE UserID=?
    """, (user_id,))
    profile = cursor.fetchone()
    
    if not profile:
        cursor.execute("INSERT INTO TeacherProfile (UserID) VALUES (?)", (user_id,))
        conn.commit()
        cursor.execute("""
            SELECT ProfileID, UserID, Bio, PhoneNumber, MobileMoneyID, CommunityReputation,
                   ProfileCreatedDate, LastUpdated, SolanaWallet
            FROM TeacherProfile WHERE UserID=?
        """, (user_id,))
        profile = cursor.fetchone()
    if profile:
        profile = list(profile)
        profile[6] = parse_datetime(profile[6])
        profile[7] = parse_datetime(profile[7])
        profile = tuple(profile)
    
    conn.close()
    
    return render_template('edit_profile.html', teacher=teacher, profile=profile)

@app.route('/profile/fees')
def view_fees():
    if not session.get('user_id'): return redirect("/login")
    
    user_id = session.get('user_id')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT FullName FROM Teachers WHERE UserID=?", (user_id,))
    teacher = cursor.fetchone()
    
    cursor.execute("""
        SELECT PaymentID, PaymentAmount, PaymentDate, PaymentDescription, PaymentStatus, TransactionReference,
               PaymentMethod, SolanaWallet, SolanaSignature, SolanaCluster, PaymentSessionID
        FROM FeesPayment 
        WHERE UserID=? 
        ORDER BY PaymentDate DESC
    """, (user_id,))
    fees = normalize_datetime_rows(cursor.fetchall(), [2])
    
    # Calculate summary
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN PaymentStatus='paid' THEN PaymentAmount ELSE 0 END) as total_paid,
            SUM(CASE WHEN PaymentStatus='pending' THEN PaymentAmount ELSE 0 END) as total_pending,
            COUNT(*) as total_payments,
            SUM(CASE WHEN SolanaSignature IS NOT NULL AND SolanaSignature != '' THEN 1 ELSE 0 END) as onchain_payments
        FROM FeesPayment WHERE UserID=?
    """, (user_id,))
    summary = cursor.fetchone() or (0, 0, 0, 0)
    
    conn.close()
    
    return render_template('fees_management.html', teacher=teacher, fees=fees, summary=summary)

@app.route('/profile/mobile_money')
def view_mobile_money():
    if not session.get('user_id'): return redirect("/login")
    
    user_id = session.get('user_id')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT FullName, MobileMoneyID FROM Teachers t LEFT JOIN TeacherProfile p ON t.UserID=p.UserID WHERE t.UserID=?", (user_id,))
    teacher = cursor.fetchone()
    
    cursor.execute("""
        SELECT TransactionID, TransactionType, Amount, Recipient, SenderID, TransactionDate, Status,
               TransactionReference, Notes, BlockchainNetwork, WalletPublicKey, SolanaSignature,
               SolanaCluster, PaymentSessionID
        FROM MobileMoneyTransaction 
        WHERE UserID=? 
        ORDER BY TransactionDate DESC
    """, (user_id,))
    transactions = normalize_datetime_rows(cursor.fetchall(), [5])
    
    # Calculate statistics
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN TransactionType='transfer' THEN Amount ELSE 0 END) as total_transferred,
            SUM(CASE WHEN TransactionType='deposit' THEN Amount ELSE 0 END) as total_deposited,
            SUM(CASE WHEN TransactionType='withdrawal' THEN Amount ELSE 0 END) as total_withdrawn,
            COUNT(*) as total_transactions,
            SUM(CASE WHEN SolanaSignature IS NOT NULL AND SolanaSignature != '' THEN 1 ELSE 0 END) as onchain_transactions
        FROM MobileMoneyTransaction WHERE UserID=?
    """, (user_id,))
    stats = cursor.fetchone() or (0, 0, 0, 0, 0)
    
    conn.close()
    
    return render_template('mobile_money.html', teacher=teacher, transactions=transactions, stats=stats)

@app.route('/profile/endorsements')
def view_endorsements():
    if not session.get('user_id'): return redirect("/login")
    
    user_id = session.get('user_id')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT FullName FROM Teachers WHERE UserID=?", (user_id,))
    teacher = cursor.fetchone()
    
    cursor.execute("""
        SELECT EndorsementID, EndorserName, EndorsementScore, EndorsementText, EndorsementDate, Verified
        FROM CommunityEndorsement 
        WHERE UserID=? 
        ORDER BY EndorsementDate DESC
    """, (user_id,))
    endorsements = normalize_datetime_rows(cursor.fetchall(), [4])
    
    # Calculate stats
    cursor.execute("""
        SELECT 
            AVG(EndorsementScore) as avg_score,
            COUNT(*) as total_endorsements,
            COALESCE(SUM(CASE WHEN Verified=1 THEN 1 ELSE 0 END), 0) as verified_count
        FROM CommunityEndorsement WHERE UserID=?
    """, (user_id,))
    stats = cursor.fetchone() or (0, 0, 0)
    
    conn.close()
    
    return render_template('endorsements.html', teacher=teacher, endorsements=endorsements, stats=stats)

# POST ENDPOINTS
@app.route('/teacher/add_results', methods=['POST'])
def handle_add_results():
    exam = request.form.get('exam_number', '')
    name = request.form.get('name', '')
    cid = request.form.get('class_id', '')
    term = request.form.get('term', '')
    subjects = request.form.getlist('subject[]')
    scores = request.form.getlist('score[]')
    tid = session.get('user_id')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT StudentID FROM Student WHERE ExamNumber=?", (exam,))
    row = cursor.fetchone()
    if row:
        sid = row[0]
    else:
        cursor.execute("INSERT INTO Student (ExamNumber, Name, ClassID) VALUES (?, ?, ?)", (exam, name, cid))
        sid = cursor.lastrowid
        
    for subj, score in zip(subjects, scores):
        cursor.execute("INSERT INTO Results (StudentID, Subject, Score, Term, TeacherID) VALUES (?, ?, ?, ?, ?)",
                       (sid, subj, score, term, tid))
    
    conn.commit()
    conn.close()
    return redirect("/show_recent_results")

@app.route('/teacher/edit_result', methods=['POST'])
def handle_edit_results():
    rids = request.form.getlist('result_id[]')
    scores = request.form.getlist('score[]')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for rid, sc in zip(rids, scores):
        cursor.execute("UPDATE Results SET Score=? WHERE ResultID=?", (sc, rid))
    conn.commit()
    conn.close()
    return redirect("/show_recent_results")

@app.route('/admin/add_student', methods=['POST'])
def handle_add_student():
    name = request.form.get('name', '')
    exam = request.form.get('exam_number', '')
    cid = request.form.get('class_id', '')
    
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO Student (Name, ExamNumber, ClassID) VALUES (?, ?, ?)", (name, exam, cid))
        conn.commit()
    except:
        pass
    finally:
        conn.close()
    return redirect("/manage_students")

@app.route('/admin/delete_student', methods=['POST'])
def handle_delete_student():
    sid = request.form.get('student_id')
    if sid:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM Student WHERE StudentID=?", (sid,))
        conn.commit()
        conn.close()
    return redirect("/manage_students")

@app.route('/teacher/delete_result', methods=['POST'])
def handle_delete_result():
    rid = request.form.get('result_id')
    if rid:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM Results WHERE ResultID=?", (rid,))
        conn.commit()
        conn.close()
    return redirect("/show_recent_results")

# DECENTRALIZED PROFILE POST ENDPOINTS
@app.route('/profile/add_fees', methods=['POST'])
def add_fees_payment():
    if not session.get('user_id'): return redirect("/login")
    
    user_id = session.get('user_id')
    amount = request.form.get('amount', 0)
    description = request.form.get('description', '')
    status = request.form.get('status', 'pending')
    reference = request.form.get('reference', '')
    payment_method = request.form.get('payment_method', 'manual')
    solana_wallet = request.form.get('solana_wallet', '')
    solana_signature = request.form.get('solana_signature', '')
    solana_cluster = request.form.get('solana_cluster', 'devnet')
    payment_session_id = request.form.get('payment_session_id') or f"fee-{uuid.uuid4().hex[:12]}"
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO FeesPayment (
                UserID, PaymentAmount, PaymentDescription, PaymentStatus, TransactionReference,
                PaymentMethod, SolanaWallet, SolanaSignature, SolanaCluster, PaymentSessionID
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, amount, description, status, reference, payment_method,
            solana_wallet, solana_signature, solana_cluster, payment_session_id
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding fees: {e}")
    
    return redirect("/profile/fees")

@app.route('/profile/add_transaction', methods=['POST'])
def add_mobile_money_transaction():
    if not session.get('user_id'): return redirect("/login")
    
    user_id = session.get('user_id')
    trans_type = request.form.get('transaction_type', '')
    amount = request.form.get('amount', 0)
    recipient = request.form.get('recipient', '')
    sender_id = request.form.get('sender_id', '')
    status = request.form.get('status', 'completed')
    reference = request.form.get('reference', '')
    notes = request.form.get('notes', '')
    blockchain_network = request.form.get('blockchain_network', '')
    wallet_public_key = request.form.get('wallet_public_key', '')
    solana_signature = request.form.get('solana_signature', '')
    solana_cluster = request.form.get('solana_cluster', 'devnet')
    payment_session_id = request.form.get('payment_session_id') or f"momo-{uuid.uuid4().hex[:12]}"
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO MobileMoneyTransaction (
                UserID, TransactionType, Amount, Recipient, SenderID, Status,
                TransactionReference, Notes, BlockchainNetwork, WalletPublicKey,
                SolanaSignature, SolanaCluster, PaymentSessionID
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, trans_type, amount, recipient, sender_id, status, reference, notes,
            blockchain_network, wallet_public_key, solana_signature, solana_cluster,
            payment_session_id
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding transaction: {e}")
    
    return redirect("/profile/mobile_money")

@app.route('/profile/add_endorsement', methods=['POST'])
def add_community_endorsement():
    if not session.get('user_id'): return redirect("/login")
    
    user_id = session.get('user_id')
    endorser_name = request.form.get('endorser_name', '')
    endorsement_text = request.form.get('endorsement_text', '')
    score = request.form.get('score', 5)
    
    try:
        score = int(score)
        if score < 1: score = 1
        if score > 5: score = 5
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO CommunityEndorsement (UserID, EndorserName, EndorsementText, EndorsementScore)
            VALUES (?, ?, ?, ?)
        """, (user_id, endorser_name, endorsement_text, score))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error adding endorsement: {e}")
    
    return redirect("/profile/endorsements")

def run_server():
    PORT = int(os.environ.get("PORT", 3004))
    print("-" * 50)
    print("KAFUMBWE GRADE BOOK SYSTEM (FLASK)")
    print("-" * 50)
    print(f"Flask Server starting on port {PORT}...")
    print(f"Access the system via: http://localhost:{PORT}")
    print("Default Login: admin / admin123")
    print("-" * 50)
    app.run(port=PORT, host="0.0.0.0", debug=True)

init_db()

if __name__ == "__main__":
    run_server()
