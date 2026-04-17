from math import ceil
import base64
import hashlib
import hmac
import html
import json
import os
import secrets
import sqlite3
import time

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database import get_conn, init_db


app = FastAPI(title="Admission Secure API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

TOKEN_TTL_SECONDS = 8 * 60 * 60
TOKEN_SECRET = os.environ.get("ADMISSION_TOKEN_SECRET", "dev-admission-token-secret-change-me")

STUDENT_STATUSES = {"未审核", "待录取", "已录取", "未录取"}
SCORE_STATUSES = {"未审核", "待录取"}
ADMISSION_RESULTS = {"待定", "录取", "未录取"}
PUBLISH_STATUSES = {"未发布", "已发布"}
LOCKED_STUDENT_STATUSES = {"已录取", "未录取"}


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RegisterBody(BaseModel):
    student_no: str = Field(min_length=3, max_length=32)
    name: str = Field(min_length=1, max_length=32)
    gender: str = Field(pattern="^(男|女)$")
    password: str = Field(min_length=6, max_length=128)


class StudentAdminBody(BaseModel):
    student_no: str = Field(min_length=3, max_length=32)
    name: str = Field(min_length=1, max_length=32)
    gender: str = Field(pattern="^(男|女)$")


class PlanBody(BaseModel):
    year: int = Field(ge=2020, le=2100)
    batch: str = Field(min_length=1, max_length=32)
    college: str = Field(min_length=1, max_length=64)
    major: str = Field(min_length=1, max_length=64)
    quota: int = Field(ge=0, le=10000)


class NoticeBody(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=5000)
    publisher: str = Field(min_length=1, max_length=64)
    created_at: str = Field(min_length=1, max_length=64)


class PasswordBody(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class AdminResetPasswordBody(BaseModel):
    user_id: int
    new_password: str = Field(min_length=6, max_length=128)


class ProfileBody(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class ScoreBody(BaseModel):
    chinese_score: int = Field(ge=0, le=150)
    math_score: int = Field(ge=0, le=150)
    foreign_score: int = Field(ge=0, le=150)
    comprehensive_score: int = Field(ge=0, le=300)
    status: str


class ChoiceBody(BaseModel):
    plan_id: int
    choice_order: int = Field(ge=1, le=5)


class AdmissionReviewBody(BaseModel):
    student_id: int
    choice_id: int | None = None
    result: str
    publish_status: str


def hash_password(password: str, salt: str | None = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    encoded = base64.b64encode(digest).decode()
    return f"pbkdf2_sha256${salt}${encoded}"


def verify_password(password: str, stored: str):
    if not stored.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(password, stored)
    _, salt, encoded = stored.split("$", 2)
    return hmac.compare_digest(hash_password(password, salt), f"pbkdf2_sha256${salt}${encoded}")


def migrate_passwords():
    conn = get_conn()
    rows = conn.execute("SELECT id, password FROM users").fetchall()
    for row in rows:
        if not row["password"].startswith("pbkdf2_sha256$"):
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(row["password"]), row["id"]))
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup_event():
    init_db()
    migrate_passwords()


def fetch_all(sql: str, params: tuple = ()):
    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(sql: str, params: tuple = ()):
    conn = get_conn()
    row = conn.execute(sql, params).fetchone()
    conn.close()
    return dict(row) if row else None


def execute_sql(sql: str, params: tuple = ()):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    lastrowid = cursor.lastrowid
    conn.close()
    return lastrowid


def paged(sql: str, params: tuple, page: int, page_size: int):
    data = fetch_all(sql, params)
    total = len(data)
    page_count = max(1, ceil(total / page_size))
    start = (page - 1) * page_size
    return {
        "items": data[start : start + page_size],
        "page": page,
        "page_size": page_size,
        "total": total,
        "page_count": page_count,
    }


def make_token(user: dict):
    payload = {
        "user": user,
        "exp": int(time.time() + TOKEN_TTL_SECONDS),
        "nonce": secrets.token_urlsafe(12),
    }
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode().rstrip("=")
    signature = hmac.new(TOKEN_SECRET.encode(), payload_b64.encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{payload_b64}.{signature_b64}"


def decode_token(token: str):
    try:
        payload_b64, signature_b64 = token.split(".", 1)
        expected = hmac.new(TOKEN_SECRET.encode(), payload_b64.encode(), hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode(signature_b64 + "=" * (-len(signature_b64) % 4))
        if not hmac.compare_digest(expected, actual):
            return None
        payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4))
        payload = json.loads(payload_json.decode())
    except (ValueError, json.JSONDecodeError, TypeError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    user = payload.get("user")
    if not isinstance(user, dict):
        return None
    return user


def current_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return decode_token(token)


def ensure_admin(authorization: str | None):
    user = current_user(authorization)
    if not user or user["role"] != "admin":
        return None, {"success": False, "message": "forbidden"}
    return user, None


def ensure_student(authorization: str | None):
    user = current_user(authorization)
    if not user or user["role"] != "student":
        return None, {"success": False, "message": "forbidden"}
    return user, None


def normalize_student_status(status: str):
    return {"审核中": "未审核", "待审核": "未审核", "已审核": "待录取"}.get(status, status)


def sanitize_text(value: str):
    return html.escape(value, quote=True)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/login")
def login(body: LoginBody):
    user = fetch_one("SELECT id, username, password, role, name FROM users WHERE username = ?", (body.username,))
    if not user or not verify_password(body.password, user["password"]):
        return {"success": False, "message": "用户名或密码错误"}
    safe_user = {"id": user["id"], "username": user["username"], "role": user["role"], "name": user["name"]}
    return {"success": True, "user": safe_user, "token": make_token(safe_user)}


@app.post("/api/logout")
def logout(authorization: str | None = Header(default=None)):
    return {"success": True}


@app.post("/api/register")
def register(body: RegisterBody):
    if fetch_one("SELECT id FROM users WHERE username = ?", (body.student_no,)):
        return {"success": False, "message": "该学号已注册"}
    if fetch_one("SELECT id FROM students WHERE student_no = ?", (body.student_no,)):
        return {"success": False, "message": "该学号已存在"}
    user_id = execute_sql(
        "INSERT INTO users (username, password, role, name) VALUES (?, ?, 'student', ?)",
        (body.student_no, hash_password(body.password), body.name),
    )
    execute_sql(
        """
        INSERT INTO students (
          user_id, student_no, name, gender, score, chinese_score, math_score,
          foreign_score, comprehensive_score, major, choice_major, status
        ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, '', '', '未审核')
        """,
        (user_id, body.student_no, body.name, body.gender),
    )
    return {"success": True, "message": "注册成功，请登录"}


@app.get("/api/admin/stats")
def admin_stats(authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    return {
        "student_count": fetch_one("SELECT COUNT(*) AS total FROM students")["total"],
        "plan_count": fetch_one("SELECT COUNT(*) AS total FROM plans")["total"],
        "admission_count": fetch_one("SELECT COUNT(*) AS total FROM admissions")["total"],
        "notice_count": fetch_one("SELECT COUNT(*) AS total FROM notices")["total"],
    }


@app.get("/api/admin/dashboard/charts")
def admin_dashboard_charts(authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    return {
        "status": fetch_all("SELECT status AS name, COUNT(*) AS value FROM students GROUP BY status ORDER BY value DESC"),
        "results": fetch_all("SELECT result AS name, COUNT(*) AS value FROM admissions GROUP BY result ORDER BY value DESC"),
        "majors": fetch_all(
            """
            SELECT plans.major, plans.quota, COUNT(admissions.id) AS admitted
            FROM plans
            LEFT JOIN admissions ON admissions.major = plans.major AND admissions.result = '录取'
            GROUP BY plans.id, plans.major, plans.quota
            ORDER BY plans.id
            """
        ),
        "scores": fetch_all(
            """
            SELECT CASE
              WHEN score >= 600 THEN '600+'
              WHEN score >= 550 THEN '550-599'
              WHEN score >= 500 THEN '500-549'
              ELSE '500以下'
            END AS name, COUNT(*) AS value
            FROM students GROUP BY name ORDER BY MIN(score) DESC
            """
        ),
        "latest_notices": fetch_all("SELECT * FROM notices ORDER BY id DESC LIMIT 4"),
        "tasks": {
            "pending_students": fetch_one("SELECT COUNT(*) AS total FROM students WHERE status IN ('未审核', '待录取')")["total"],
            "unpublished_admissions": fetch_one("SELECT COUNT(*) AS total FROM admissions WHERE publish_status != '已发布'")["total"],
            "open_plans": fetch_one("SELECT COUNT(*) AS total FROM plans")["total"],
        },
    }


@app.get("/api/admin/students")
def get_students(keyword: str = "", page: int = 1, page_size: int = 5, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    like = f"%{keyword}%"
    return paged(
        "SELECT * FROM students WHERE name LIKE ? OR student_no LIKE ? OR major LIKE ? ORDER BY id DESC",
        (like, like, like),
        page,
        page_size,
    )


@app.post("/api/admin/students")
def create_student(body: StudentAdminBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    if fetch_one("SELECT id FROM users WHERE username = ?", (body.student_no,)):
        return {"success": False, "message": "该学号账号已存在"}
    user_id = execute_sql(
        "INSERT INTO users (username, password, role, name) VALUES (?, ?, 'student', ?)",
        (body.student_no, hash_password("123456"), body.name),
    )
    student_id = execute_sql(
        """
        INSERT INTO students (
          user_id, student_no, name, gender, score, chinese_score, math_score,
          foreign_score, comprehensive_score, major, choice_major, status
        ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, '', '', '未审核')
        """,
        (user_id, body.student_no, body.name, body.gender),
    )
    return {"success": True, "id": student_id}


@app.put("/api/admin/students/{student_id}")
def update_student(student_id: int, body: StudentAdminBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    current = fetch_one("SELECT * FROM students WHERE id = ?", (student_id,))
    if not current:
        return {"success": False, "message": "学生不存在"}
    if fetch_one("SELECT id FROM students WHERE student_no = ? AND id != ?", (body.student_no, student_id)):
        return {"success": False, "message": "该学号已存在"}
    execute_sql("UPDATE students SET student_no = ?, name = ?, gender = ? WHERE id = ?", (body.student_no, body.name, body.gender, student_id))
    if current["user_id"]:
        execute_sql("UPDATE users SET username = ?, name = ? WHERE id = ?", (body.student_no, body.name, current["user_id"]))
    return {"success": True}


@app.delete("/api/admin/students/{student_id}")
def delete_student(student_id: int, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    execute_sql("DELETE FROM students WHERE id = ?", (student_id,))
    return {"success": True}


@app.post("/api/admin/reset-password")
def admin_reset_password(body: AdminResetPasswordBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    if not fetch_one("SELECT id FROM users WHERE id = ?", (body.user_id,)):
        return {"success": False, "message": "用户不存在"}
    execute_sql("UPDATE users SET password = ? WHERE id = ?", (hash_password(body.new_password), body.user_id))
    return {"success": True, "message": "密码重置成功"}


@app.get("/api/admin/scores")
def get_scores(keyword: str = "", page: int = 1, page_size: int = 8, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    like = f"%{keyword}%"
    return paged(
        """
        SELECT id, student_no, name, gender, score, chinese_score, math_score,
               foreign_score, comprehensive_score, status
        FROM students WHERE name LIKE ? OR student_no LIKE ?
        ORDER BY score DESC, id DESC
        """,
        (like, like),
        page,
        page_size,
    )


@app.put("/api/admin/scores/{student_id}")
def update_score(student_id: int, body: ScoreBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    status = normalize_student_status(body.status)
    if status not in SCORE_STATUSES:
        return {"success": False, "message": "成绩管理只能设置未审核或待录取"}
    total = body.chinese_score + body.math_score + body.foreign_score + body.comprehensive_score
    execute_sql(
        """
        UPDATE students
        SET chinese_score = ?, math_score = ?, foreign_score = ?, comprehensive_score = ?,
            score = ?, status = ?
        WHERE id = ?
        """,
        (body.chinese_score, body.math_score, body.foreign_score, body.comprehensive_score, total, status, student_id),
    )
    return {"success": True}


@app.get("/api/admin/choices")
def get_admin_choices(keyword: str = "", page: int = 1, page_size: int = 8, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    like = f"%{keyword}%"
    return paged(
        """
        SELECT students.id, students.student_no, students.name, students.score, students.status,
               COUNT(student_choices.id) AS choice_count,
               GROUP_CONCAT(student_choices.choice_order || '. ' || student_choices.batch || ' / ' ||
                            student_choices.college || ' / ' || student_choices.major, '\n') AS choices_text
        FROM students
        LEFT JOIN student_choices ON student_choices.student_id = students.id
        WHERE students.name LIKE ? OR students.student_no LIKE ?
        GROUP BY students.id
        ORDER BY students.score DESC, students.id DESC
        """,
        (like, like),
        page,
        page_size,
    )


@app.get("/api/admin/students/{student_id}/choices")
def get_admin_student_choices(student_id: int, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    return fetch_all("SELECT * FROM student_choices WHERE student_id = ? ORDER BY choice_order", (student_id,))


@app.get("/api/admin/plans")
def get_plans(keyword: str = "", page: int = 1, page_size: int = 5, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    like = f"%{keyword}%"
    return paged("SELECT * FROM plans WHERE college LIKE ? OR major LIKE ? ORDER BY id DESC", (like, like), page, page_size)


@app.post("/api/admin/plans")
def create_plan(body: PlanBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    return {"success": True, "id": execute_sql("INSERT INTO plans (year, batch, college, major, quota) VALUES (?, ?, ?, ?, ?)", (body.year, body.batch, body.college, body.major, body.quota))}


@app.put("/api/admin/plans/{plan_id}")
def update_plan(plan_id: int, body: PlanBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    execute_sql("UPDATE plans SET year = ?, batch = ?, college = ?, major = ?, quota = ? WHERE id = ?", (body.year, body.batch, body.college, body.major, body.quota, plan_id))
    return {"success": True}


@app.delete("/api/admin/plans/{plan_id}")
def delete_plan(plan_id: int, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    execute_sql("DELETE FROM plans WHERE id = ?", (plan_id,))
    return {"success": True}


@app.get("/api/admin/admission-review")
def get_admission_review(keyword: str = "", page: int = 1, page_size: int = 8, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    like = f"%{keyword}%"
    return paged(
        """
        SELECT students.id AS student_id, students.student_no, students.name, students.score,
               students.status, students.major AS admitted_major,
               COUNT(student_choices.id) AS choice_count, admissions.id AS admission_id,
               admissions.result AS admission_result, admissions.publish_status,
               admissions.choice_id, admissions.batch, admissions.college, admissions.major
        FROM students
        LEFT JOIN student_choices ON student_choices.student_id = students.id
        LEFT JOIN admissions ON admissions.student_id = students.id
        WHERE students.name LIKE ? OR students.student_no LIKE ? OR students.major LIKE ?
        GROUP BY students.id
        ORDER BY students.score DESC, students.id DESC
        """,
        (like, like, like),
        page,
        page_size,
    )


@app.post("/api/admin/admission-review")
def save_admission_review(body: AdmissionReviewBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    if body.result not in ADMISSION_RESULTS or body.publish_status not in PUBLISH_STATUSES:
        return {"success": False, "message": "录取结果或发布状态不合法"}
    student = fetch_one("SELECT * FROM students WHERE id = ?", (body.student_id,))
    if not student:
        return {"success": False, "message": "学生不存在"}
    existing = fetch_one("SELECT * FROM admissions WHERE student_id = ?", (body.student_id,))
    if existing and existing["publish_status"] == "已发布" and existing["result"] != "待定":
        return {"success": False, "message": "已发布的最终录取结果不可再修改"}

    choice = None
    if body.result == "录取":
        if not body.choice_id:
            return {"success": False, "message": "录取时必须选择一个志愿"}
        choice = fetch_one("SELECT * FROM student_choices WHERE id = ? AND student_id = ?", (body.choice_id, body.student_id))
        if not choice:
            return {"success": False, "message": "志愿不存在或不属于该学生"}
        batch, college, major, status, choice_id = choice["batch"], choice["college"], choice["major"], "已录取", choice["id"]
    elif body.result == "未录取":
        batch, college, major, status, choice_id = "", "", "", "未录取", None
    else:
        batch, college, major, status, choice_id = "", "", "", "待录取", None

    if existing:
        execute_sql(
            """
            UPDATE admissions
            SET choice_id = ?, student_name = ?, batch = ?, college = ?, major = ?,
                result = ?, publish_status = ?
            WHERE id = ?
            """,
            (choice_id, student["name"], batch, college, major, body.result, body.publish_status, existing["id"]),
        )
    else:
        execute_sql(
            """
            INSERT INTO admissions (student_id, choice_id, student_name, batch, college, major, result, publish_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (body.student_id, choice_id, student["name"], batch, college, major, body.result, body.publish_status),
        )
    execute_sql("UPDATE students SET status = ?, major = ? WHERE id = ?", (status, major, body.student_id))
    return {"success": True}


@app.get("/api/admin/notices")
def get_notices_admin(keyword: str = "", page: int = 1, page_size: int = 5, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    like = f"%{keyword}%"
    return paged("SELECT * FROM notices WHERE title LIKE ? OR content LIKE ? ORDER BY id DESC", (like, like), page, page_size)


@app.post("/api/admin/notices")
def create_notice(body: NoticeBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    notice_id = execute_sql(
        "INSERT INTO notices (title, content, publisher, created_at) VALUES (?, ?, ?, ?)",
        (sanitize_text(body.title), sanitize_text(body.content), sanitize_text(body.publisher), body.created_at),
    )
    return {"success": True, "id": notice_id}


@app.put("/api/admin/notices/{notice_id}")
def update_notice(notice_id: int, body: NoticeBody, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    execute_sql(
        "UPDATE notices SET title = ?, content = ?, publisher = ?, created_at = ? WHERE id = ?",
        (sanitize_text(body.title), sanitize_text(body.content), sanitize_text(body.publisher), body.created_at, notice_id),
    )
    return {"success": True}


@app.delete("/api/admin/notices/{notice_id}")
def delete_notice(notice_id: int, authorization: str | None = Header(default=None)):
    _, blocked = ensure_admin(authorization)
    if blocked:
        return blocked
    execute_sql("DELETE FROM notices WHERE id = ?", (notice_id,))
    return {"success": True}


def current_student(authorization: str | None):
    user, blocked = ensure_student(authorization)
    if blocked:
        return None, blocked
    student = fetch_one("SELECT students.* FROM students WHERE user_id = ?", (user["id"],))
    if not student:
        return None, {"success": False, "message": "学生不存在"}
    return student, None


@app.get("/api/student/profile")
def student_profile(authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    return blocked or student


@app.get("/api/student/admission")
def student_admission(authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    if blocked:
        return blocked
    return fetch_one("SELECT * FROM admissions WHERE student_id = ?", (student["id"],))


@app.get("/api/student/score")
def student_score(authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    if blocked:
        return blocked
    rank = fetch_one("SELECT COUNT(*) + 1 AS rank FROM students WHERE score > ?", (student["score"],))["rank"]
    total = fetch_one("SELECT COUNT(*) AS total FROM students")["total"]
    return {**student, "rank": rank, "total": total}


@app.get("/api/student/plans")
def student_plans(authorization: str | None = Header(default=None)):
    _, blocked = ensure_student(authorization)
    if blocked:
        return blocked
    return fetch_all("SELECT * FROM plans ORDER BY year DESC, batch, college, major")


@app.get("/api/student/choices")
def student_choices(authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    if blocked:
        return blocked
    return {
        "student": student,
        "items": fetch_all("SELECT * FROM student_choices WHERE student_id = ? ORDER BY choice_order", (student["id"],)),
        "locked": student["status"] in LOCKED_STUDENT_STATUSES,
    }


@app.post("/api/student/choices")
def create_choice(body: ChoiceBody, authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    if blocked:
        return blocked
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}
    count = fetch_one("SELECT COUNT(*) AS total FROM student_choices WHERE student_id = ?", (student["id"],))["total"]
    if count >= 5:
        return {"success": False, "message": "最多只能填报5个志愿"}
    plan = fetch_one("SELECT * FROM plans WHERE id = ?", (body.plan_id,))
    if not plan:
        return {"success": False, "message": "招生计划不存在"}
    order_value = min(max(body.choice_order, 1), count + 1)
    for row in fetch_all("SELECT id, choice_order FROM student_choices WHERE student_id = ? AND choice_order >= ? ORDER BY choice_order DESC", (student["id"], order_value)):
        execute_sql("UPDATE student_choices SET choice_order = ? WHERE id = ?", (row["choice_order"] + 1, row["id"]))
    execute_sql(
        """
        INSERT INTO student_choices (student_id, plan_id, choice_order, batch, college, major, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, '已提交', datetime('now', 'localtime'))
        """,
        (student["id"], plan["id"], order_value, plan["batch"], plan["college"], plan["major"]),
    )
    execute_sql("UPDATE students SET choice_major = ? WHERE id = ? AND choice_major = ''", (plan["major"], student["id"]))
    return {"success": True}


@app.put("/api/student/choices/{choice_id}")
def update_choice(choice_id: int, body: ChoiceBody, authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    if blocked:
        return blocked
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}
    plan = fetch_one("SELECT * FROM plans WHERE id = ?", (body.plan_id,))
    if not plan:
        return {"success": False, "message": "招生计划不存在"}
    execute_sql(
        "UPDATE student_choices SET plan_id = ?, batch = ?, college = ?, major = ? WHERE id = ? AND student_id = ?",
        (plan["id"], plan["batch"], plan["college"], plan["major"], choice_id, student["id"]),
    )
    return {"success": True}


@app.delete("/api/student/choices/{choice_id}")
def delete_choice(choice_id: int, authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    if blocked:
        return blocked
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}
    execute_sql("DELETE FROM student_choices WHERE id = ? AND student_id = ?", (choice_id, student["id"]))
    rows = fetch_all("SELECT id FROM student_choices WHERE student_id = ? ORDER BY choice_order", (student["id"],))
    for index, row in enumerate(rows, start=1):
        execute_sql("UPDATE student_choices SET choice_order = ? WHERE id = ?", (index, row["id"]))
    return {"success": True}


@app.put("/api/student/choices/{choice_id}/order")
def move_choice(choice_id: int, direction: str, authorization: str | None = Header(default=None)):
    student, blocked = current_student(authorization)
    if blocked:
        return blocked
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}
    current = fetch_one("SELECT * FROM student_choices WHERE id = ? AND student_id = ?", (choice_id, student["id"]))
    if not current:
        return {"success": False, "message": "志愿不存在"}
    target_order = current["choice_order"] - 1 if direction == "up" else current["choice_order"] + 1
    target = fetch_one("SELECT * FROM student_choices WHERE student_id = ? AND choice_order = ?", (student["id"], target_order))
    if target:
        execute_sql("UPDATE student_choices SET choice_order = ? WHERE id = ?", (target["choice_order"], current["id"]))
        execute_sql("UPDATE student_choices SET choice_order = ? WHERE id = ?", (current["choice_order"], target["id"]))
    return {"success": True}


@app.get("/api/student/notices")
def student_notices(authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"success": False, "message": "forbidden"}
    return fetch_all("SELECT * FROM notices ORDER BY id DESC")


@app.get("/api/student/notices/{notice_id}")
def student_notice_detail(notice_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"success": False, "message": "forbidden"}
    return fetch_one("SELECT * FROM notices WHERE id = ?", (notice_id,))


@app.post("/api/student/password")
def change_password(body: PasswordBody, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"success": False, "message": "forbidden"}
    db_user = fetch_one("SELECT id, password FROM users WHERE id = ?", (user["id"],))
    if not db_user or not verify_password(body.old_password, db_user["password"]):
        return {"success": False, "message": "原密码错误"}
    execute_sql("UPDATE users SET password = ? WHERE id = ?", (hash_password(body.new_password), user["id"]))
    return {"success": True, "message": "密码修改成功"}


@app.put("/api/profile")
def update_profile(body: ProfileBody, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    if not user:
        return {"success": False, "message": "forbidden"}
    execute_sql("UPDATE users SET name = ? WHERE id = ?", (body.name, user["id"]))
    if user["role"] == "student":
        execute_sql("UPDATE students SET name = ? WHERE user_id = ?", (body.name, user["id"]))
    updated = fetch_one("SELECT id, username, role, name FROM users WHERE id = ?", (user["id"],))
    user.update(updated)
    return {"success": True, "user": updated}


@app.exception_handler(sqlite3.Error)
def sqlite_exception_handler(_, exc: sqlite3.Error):
    return JSONResponse(status_code=500, content={"success": False, "message": "database error"})
