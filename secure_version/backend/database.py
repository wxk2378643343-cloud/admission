from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "admission.db"


def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT,
            name TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            student_no TEXT,
            name TEXT,
            gender TEXT,
            score INTEGER,
            major TEXT,
            choice_major TEXT,
            status TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            batch TEXT,
            college TEXT,
            major TEXT,
            quota INTEGER
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            student_name TEXT,
            batch TEXT,
            major TEXT,
            result TEXT,
            publish_status TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            publisher TEXT,
            created_at TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS student_choices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            plan_id INTEGER,
            choice_order INTEGER,
            batch TEXT,
            college TEXT,
            major TEXT,
            status TEXT,
            created_at TEXT
        )
        """
    )

    student_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(students)").fetchall()
    }
    score_columns = {
        "chinese_score": "INTEGER DEFAULT 0",
        "math_score": "INTEGER DEFAULT 0",
        "foreign_score": "INTEGER DEFAULT 0",
        "comprehensive_score": "INTEGER DEFAULT 0",
    }
    for column, definition in score_columns.items():
        if column not in student_columns:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {column} {definition}")

    admission_columns = {
        row["name"] for row in cursor.execute("PRAGMA table_info(admissions)").fetchall()
    }
    admission_extra_columns = {
        "choice_id": "INTEGER",
        "college": "TEXT DEFAULT ''",
    }
    for column, definition in admission_extra_columns.items():
        if column not in admission_columns:
            cursor.execute(f"ALTER TABLE admissions ADD COLUMN {column} {definition}")

    user_count = cursor.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if user_count == 0:
        cursor.executescript(
            """
            INSERT INTO users (username, password, role, name) VALUES
            ('admin', '123456', 'admin', '管理员'),
            ('2026001', '123456', 'student', '张三'),
            ('2026002', '123456', 'student', '李四');

            INSERT INTO students (
                user_id, student_no, name, gender, score, chinese_score, math_score,
                foreign_score, comprehensive_score, major, choice_major, status
            ) VALUES
            (2, '2026001', '张三', '男', 612, 128, 140, 136, 208, '计算机科学与技术', '软件工程', '已录取'),
            (3, '2026002', '李四', '女', 587, 121, 132, 129, 205, '信息管理与信息系统', '电子商务', '审核中');

            INSERT INTO plans (year, batch, college, major, quota) VALUES
            (2026, '本科一批', '信息工程学院', '计算机科学与技术', 120),
            (2026, '本科一批', '管理学院', '信息管理与信息系统', 80),
            (2026, '本科二批', '商学院', '电子商务', 60);

            INSERT INTO admissions (student_id, choice_id, student_name, batch, college, major, result, publish_status) VALUES
            (1, 1, '张三', '本科一批', '信息工程学院', '计算机科学与技术', '录取', '已发布'),
            (2, 3, '李四', '本科一批', '管理学院', '信息管理与信息系统', '待定', '未发布');

            INSERT INTO notices (title, content, publisher, created_at) VALUES
            ('2026年招生录取工作安排', '请各位考生按时登录系统查询录取状态。', '招生办公室', '2026-04-17 09:00:00'),
            ('本科一批录取结果发布时间', '本科一批录取结果预计于4月20日18:00统一开放查询。', '招生办公室', '2026-04-17 09:10:00');
            """
        )

    choice_count = cursor.execute("SELECT COUNT(*) AS count FROM student_choices").fetchone()["count"]
    if choice_count == 0:
        cursor.executescript(
            """
            INSERT INTO student_choices (student_id, plan_id, choice_order, batch, college, major, status, created_at) VALUES
            (1, 1, 1, '本科一批', '信息工程学院', '计算机科学与技术', '已提交', '2026-04-17 10:00:00'),
            (1, 3, 2, '本科二批', '商学院', '电子商务', '已提交', '2026-04-17 10:02:00'),
            (2, 2, 1, '本科一批', '管理学院', '信息管理与信息系统', '已提交', '2026-04-17 10:05:00'),
            (2, 3, 2, '本科二批', '商学院', '电子商务', '已提交', '2026-04-17 10:06:00');
            """
        )

    cursor.execute(
        """
        UPDATE students
        SET
            chinese_score = CASE WHEN score = 612 THEN 128 WHEN score = 587 THEN 121 ELSE chinese_score END,
            math_score = CASE WHEN score = 612 THEN 140 WHEN score = 587 THEN 132 ELSE math_score END,
            foreign_score = CASE WHEN score = 612 THEN 136 WHEN score = 587 THEN 129 ELSE foreign_score END,
            comprehensive_score = CASE WHEN score = 612 THEN 208 WHEN score = 587 THEN 205 ELSE comprehensive_score END
        WHERE chinese_score = 0 AND math_score = 0 AND foreign_score = 0 AND comprehensive_score = 0
        """
    )
    cursor.execute("UPDATE students SET status = '未审核' WHERE status IN ('审核中', '待审核')")
    cursor.execute("UPDATE students SET status = '待录取' WHERE status = '已审核'")
    cursor.execute("UPDATE admissions SET result = '录取' WHERE result = '已录取'")
    cursor.execute("UPDATE admissions SET result = '待定' WHERE result = '待审核'")

    conn.commit()
    conn.close()
