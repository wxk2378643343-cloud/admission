from math import ceil
import sqlite3

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database import get_conn, init_db


app = FastAPI(title="Admission Vulnerable API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginBody(BaseModel):
    username: str
    password: str


class RegisterBody(BaseModel):
    student_no: str
    name: str
    gender: str
    password: str


class StudentAdminBody(BaseModel):
    student_no: str
    name: str
    gender: str


class PlanBody(BaseModel):
    year: int
    batch: str
    college: str
    major: str
    quota: int


class AdmissionBody(BaseModel):
    student_id: int
    student_name: str
    batch: str
    major: str
    result: str
    publish_status: str


class NoticeBody(BaseModel):
    title: str
    content: str
    publisher: str
    created_at: str


class PasswordBody(BaseModel):
    user_id: int
    old_password: str
    new_password: str


class AdminResetPasswordBody(BaseModel):
    user_id: int
    new_password: str


class ProfileBody(BaseModel):
    user_id: int
    name: str


class ScoreBody(BaseModel):
    chinese_score: int
    math_score: int
    foreign_score: int
    comprehensive_score: int
    status: str


class ChoiceBody(BaseModel):
    user_id: int
    plan_id: int
    choice_order: int


class AdmissionReviewBody(BaseModel):
    student_id: int
    choice_id: int | None = None
    result: str
    publish_status: str


STUDENT_STATUSES = {"未审核", "待录取", "已录取", "未录取"}
SCORE_STATUSES = {"未审核", "待录取"}
ADMISSION_RESULTS = {"待定", "录取", "未录取"}
PUBLISH_STATUSES = {"未发布", "已发布"}
LOCKED_STUDENT_STATUSES = {"已录取", "未录取"}


@app.on_event("startup")
def startup_event():
    init_db()


def fetch_all(sql: str):
    conn = get_conn()
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_one(sql: str):
    conn = get_conn()
    row = conn.execute(sql).fetchone()
    conn.close()
    return dict(row) if row else None


def execute_sql(sql: str):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    lastrowid = cursor.lastrowid
    conn.close()
    return lastrowid


def paged(sql: str, page: int, page_size: int):
    data = fetch_all(sql)
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


def ensure_admin(x_role: str | None):
    if x_role != "admin":
        return {"message": "forbidden"}
    return None


@app.get("/api/health")
def health():
    return {"status": "ok"}


def normalize_student_status(status: str):
    mapping = {
        "审核中": "未审核",
        "待审核": "未审核",
        "已审核": "待录取",
    }
    return mapping.get(status, status)


@app.post("/api/login")
def login(body: LoginBody):
    sql = (
        "SELECT id, username, role, name FROM users "
        f"WHERE username = '{body.username}' AND password = '{body.password}'"
    )
    user = fetch_one(sql)
    if not user:
      return {"success": False, "message": "用户名或密码错误"}
    return {"success": True, "user": user}


@app.post("/api/register")
def register(body: RegisterBody):
    exists = fetch_one(
        f"SELECT id FROM users WHERE username = '{body.student_no}'"
    )
    if exists:
        return {"success": False, "message": "该学号已注册"}

    student_exists = fetch_one(
        f"SELECT id FROM students WHERE student_no = '{body.student_no}'"
    )
    if student_exists:
        return {"success": False, "message": "该学号已存在"}

    user_id = execute_sql(
        "INSERT INTO users (username, password, role, name) "
        f"VALUES ('{body.student_no}', '{body.password}', 'student', '{body.name}')"
    )
    execute_sql(
        "INSERT INTO students ("
        "user_id, student_no, name, gender, score, chinese_score, math_score, "
        "foreign_score, comprehensive_score, major, choice_major, status"
        ") "
        f"VALUES ({user_id}, '{body.student_no}', '{body.name}', '{body.gender}', "
        "0, 0, 0, 0, 0, '', '', '未审核')"
    )
    return {"success": True, "message": "注册成功，请登录"}


@app.get("/api/admin/stats")
def admin_stats(x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    return {
        "student_count": fetch_one("SELECT COUNT(*) AS total FROM students")["total"],
        "plan_count": fetch_one("SELECT COUNT(*) AS total FROM plans")["total"],
        "admission_count": fetch_one("SELECT COUNT(*) AS total FROM admissions")["total"],
        "notice_count": fetch_one("SELECT COUNT(*) AS total FROM notices")["total"],
    }


@app.get("/api/admin/dashboard/charts")
def admin_dashboard_charts(x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked

    status_rows = fetch_all(
        "SELECT status AS name, COUNT(*) AS value FROM students GROUP BY status ORDER BY value DESC"
    )
    result_rows = fetch_all(
        "SELECT result AS name, COUNT(*) AS value FROM admissions GROUP BY result ORDER BY value DESC"
    )
    major_rows = fetch_all(
        """
        SELECT plans.major, plans.quota, COUNT(admissions.id) AS admitted
        FROM plans
        LEFT JOIN admissions
          ON admissions.major = plans.major AND admissions.result IN ('录取', '已录取')
        GROUP BY plans.id, plans.major, plans.quota
        ORDER BY plans.id
        """
    )
    score_rows = fetch_all(
        """
        SELECT
          CASE
            WHEN score >= 600 THEN '600+'
            WHEN score >= 550 THEN '550-599'
            WHEN score >= 500 THEN '500-549'
            ELSE '500以下'
          END AS name,
          COUNT(*) AS value
        FROM students
        GROUP BY name
        ORDER BY MIN(score) DESC
        """
    )
    latest_notices = fetch_all("SELECT * FROM notices ORDER BY id DESC LIMIT 4")

    return {
        "status": status_rows,
        "results": result_rows,
        "majors": major_rows,
        "scores": score_rows,
        "latest_notices": latest_notices,
        "tasks": {
            "pending_students": fetch_one(
                "SELECT COUNT(*) AS total FROM students WHERE status IN ('审核中', '未审核', '待录取')"
            )["total"],
            "unpublished_admissions": fetch_one(
                "SELECT COUNT(*) AS total FROM admissions WHERE publish_status != '已发布'"
            )["total"],
            "open_plans": fetch_one("SELECT COUNT(*) AS total FROM plans")["total"],
        },
    }


@app.get("/api/admin/students")
def get_students(
    keyword: str = "",
    page: int = 1,
    page_size: int = 5,
    x_role: str | None = Header(default=None),
):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "SELECT * FROM students "
        f"WHERE name LIKE '%{keyword}%' OR student_no LIKE '%{keyword}%' "
        f"OR major LIKE '%{keyword}%' ORDER BY id DESC"
    )
    return paged(sql, page, page_size)


@app.post("/api/admin/students")
def create_student(body: StudentAdminBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    exists = fetch_one(f"SELECT id FROM users WHERE username = '{body.student_no}'")
    if exists:
        return {"success": False, "message": "该学号账号已存在"}
    user_id = execute_sql(
        "INSERT INTO users (username, password, role, name) "
        f"VALUES ('{body.student_no}', '123456', 'student', '{body.name}')"
    )
    sql = (
        "INSERT INTO students ("
        "user_id, student_no, name, gender, score, chinese_score, math_score, "
        "foreign_score, comprehensive_score, major, choice_major, status"
        ") "
        f"VALUES ({user_id}, '{body.student_no}', '{body.name}', '{body.gender}', "
        "0, 0, 0, 0, 0, '', '', '未审核')"
    )
    student_id = execute_sql(sql)
    return {"id": student_id}


@app.put("/api/admin/students/{student_id}")
def update_student(student_id: int, body: StudentAdminBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    current = fetch_one(f"SELECT * FROM students WHERE id = {student_id}")
    if not current:
        return {"success": False, "message": "学生不存在"}
    exists = fetch_one(
        f"SELECT id FROM students WHERE student_no = '{body.student_no}' AND id != {student_id}"
    )
    if exists:
        return {"success": False, "message": "该学号已存在"}
    sql = (
        "UPDATE students SET "
        f"student_no = '{body.student_no}', name = '{body.name}', gender = '{body.gender}' "
        f"WHERE id = {student_id}"
    )
    execute_sql(sql)
    if current["user_id"]:
        execute_sql(
            f"UPDATE users SET username = '{body.student_no}', name = '{body.name}' "
            f"WHERE id = {current['user_id']}"
        )
    return {"success": True}


@app.delete("/api/admin/students/{student_id}")
def delete_student(student_id: int, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    execute_sql(f"DELETE FROM students WHERE id = {student_id}")
    return {"success": True}


@app.post("/api/admin/reset-password")
def admin_reset_password(body: AdminResetPasswordBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    if not body.new_password:
        return {"success": False, "message": "新密码不能为空"}
    user = fetch_one(f"SELECT id FROM users WHERE id = {body.user_id}")
    if not user:
        return {"success": False, "message": "用户不存在"}
    execute_sql(
        f"UPDATE users SET password = '{body.new_password}' WHERE id = {body.user_id}"
    )
    return {"success": True, "message": "密码重置成功"}


@app.get("/api/admin/scores")
def get_scores(
    keyword: str = "",
    page: int = 1,
    page_size: int = 8,
    x_role: str | None = Header(default=None),
):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "SELECT id, student_no, name, gender, score, chinese_score, math_score, "
        "foreign_score, comprehensive_score, status FROM students "
        f"WHERE name LIKE '%{keyword}%' OR student_no LIKE '%{keyword}%' "
        "ORDER BY score DESC, id DESC"
    )
    return paged(sql, page, page_size)


@app.put("/api/admin/scores/{student_id}")
def update_score(student_id: int, body: ScoreBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    status = normalize_student_status(body.status)
    if status not in SCORE_STATUSES:
        return {"success": False, "message": "成绩管理只能设置未审核或待录取"}
    total_score = (
        body.chinese_score
        + body.math_score
        + body.foreign_score
        + body.comprehensive_score
    )
    execute_sql(
        "UPDATE students SET "
        f"chinese_score = {body.chinese_score}, math_score = {body.math_score}, "
        f"foreign_score = {body.foreign_score}, comprehensive_score = {body.comprehensive_score}, "
        f"score = {total_score}, status = '{status}' WHERE id = {student_id}"
    )
    return {"success": True}


@app.get("/api/admin/choices")
def get_admin_choices(
    keyword: str = "",
    page: int = 1,
    page_size: int = 8,
    x_role: str | None = Header(default=None),
):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "SELECT students.id, students.student_no, students.name, students.score, students.status, "
        "COUNT(student_choices.id) AS choice_count, "
        "GROUP_CONCAT(student_choices.choice_order || '. ' || student_choices.batch || ' / ' || "
        "student_choices.college || ' / ' || student_choices.major, '\n') AS choices_text "
        "FROM students "
        "LEFT JOIN student_choices ON student_choices.student_id = students.id "
        f"WHERE students.name LIKE '%{keyword}%' OR students.student_no LIKE '%{keyword}%' "
        "GROUP BY students.id "
        "ORDER BY students.score DESC, students.id DESC"
    )
    return paged(sql, page, page_size)


@app.get("/api/admin/students/{student_id}/choices")
def get_admin_student_choices(student_id: int, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    return fetch_all(
        f"SELECT * FROM student_choices WHERE student_id = {student_id} ORDER BY choice_order"
    )


@app.get("/api/admin/plans")
def get_plans(
    keyword: str = "",
    page: int = 1,
    page_size: int = 5,
    x_role: str | None = Header(default=None),
):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "SELECT * FROM plans "
        f"WHERE college LIKE '%{keyword}%' OR major LIKE '%{keyword}%' ORDER BY id DESC"
    )
    return paged(sql, page, page_size)


@app.post("/api/admin/plans")
def create_plan(body: PlanBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "INSERT INTO plans (year, batch, college, major, quota) "
        f"VALUES ({body.year}, '{body.batch}', '{body.college}', '{body.major}', {body.quota})"
    )
    return {"id": execute_sql(sql)}


@app.put("/api/admin/plans/{plan_id}")
def update_plan(plan_id: int, body: PlanBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "UPDATE plans SET "
        f"year = {body.year}, batch = '{body.batch}', college = '{body.college}', "
        f"major = '{body.major}', quota = {body.quota} WHERE id = {plan_id}"
    )
    execute_sql(sql)
    return {"success": True}


@app.delete("/api/admin/plans/{plan_id}")
def delete_plan(plan_id: int, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    execute_sql(f"DELETE FROM plans WHERE id = {plan_id}")
    return {"success": True}


@app.get("/api/admin/admission-review")
def get_admission_review(
    keyword: str = "",
    page: int = 1,
    page_size: int = 8,
    x_role: str | None = Header(default=None),
):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "SELECT students.id AS student_id, students.student_no, students.name, students.score, "
        "students.status, students.major AS admitted_major, "
        "COUNT(student_choices.id) AS choice_count, admissions.id AS admission_id, "
        "admissions.result AS admission_result, admissions.publish_status, "
        "admissions.choice_id, admissions.batch, admissions.college, admissions.major "
        "FROM students "
        "LEFT JOIN student_choices ON student_choices.student_id = students.id "
        "LEFT JOIN admissions ON admissions.student_id = students.id "
        f"WHERE students.name LIKE '%{keyword}%' OR students.student_no LIKE '%{keyword}%' "
        "OR students.major LIKE '%{keyword}%' "
        "GROUP BY students.id "
        "ORDER BY students.score DESC, students.id DESC"
    )
    return paged(sql, page, page_size)


@app.post("/api/admin/admission-review")
def save_admission_review(body: AdmissionReviewBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked

    student = fetch_one(f"SELECT * FROM students WHERE id = {body.student_id}")
    if not student:
        return {"success": False, "message": "学生不存在"}
    if body.result not in ADMISSION_RESULTS:
        return {"success": False, "message": "录取结果不合法"}
    if body.publish_status not in PUBLISH_STATUSES:
        return {"success": False, "message": "发布状态不合法"}
    existing = fetch_one(f"SELECT * FROM admissions WHERE student_id = {body.student_id}")
    if existing and existing["publish_status"] == "已发布" and existing["result"] != "待定":
        return {"success": False, "message": "已发布的最终录取结果不可再修改"}

    choice = None
    if body.result == "录取":
        if not body.choice_id:
            return {"success": False, "message": "录取时必须选择一个志愿"}
        choice = fetch_one(
            f"SELECT * FROM student_choices WHERE id = {body.choice_id} AND student_id = {body.student_id}"
        )
        if not choice:
            return {"success": False, "message": "志愿不存在或不属于该学生"}
        batch = choice["batch"]
        college = choice["college"]
        major = choice["major"]
        status = "已录取"
    elif body.result == "未录取":
        batch = ""
        college = ""
        major = ""
        status = "未录取"
    else:
        batch = ""
        college = ""
        major = ""
        status = "待录取"

    choice_id_value = choice["id"] if choice else "NULL"
    if existing:
        execute_sql(
            "UPDATE admissions SET "
            f"choice_id = {choice_id_value}, student_name = '{student['name']}', "
            f"batch = '{batch}', college = '{college}', major = '{major}', "
            f"result = '{body.result}', publish_status = '{body.publish_status}' "
            f"WHERE id = {existing['id']}"
        )
    else:
        execute_sql(
            "INSERT INTO admissions (student_id, choice_id, student_name, batch, college, major, result, publish_status) "
            f"VALUES ({body.student_id}, {choice_id_value}, '{student['name']}', "
            f"'{batch}', '{college}', '{major}', '{body.result}', '{body.publish_status}')"
        )

    execute_sql(
        f"UPDATE students SET status = '{status}', major = '{major}' WHERE id = {body.student_id}"
    )
    return {"success": True}


@app.get("/api/admin/admissions")
def get_admissions(
    keyword: str = "",
    page: int = 1,
    page_size: int = 5,
    x_role: str | None = Header(default=None),
):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "SELECT * FROM admissions "
        f"WHERE student_name LIKE '%{keyword}%' OR major LIKE '%{keyword}%' "
        f"OR batch LIKE '%{keyword}%' OR publish_status LIKE '%{keyword}%' ORDER BY id DESC"
    )
    return paged(sql, page, page_size)


@app.post("/api/admin/admissions")
def create_admission(body: AdmissionBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "INSERT INTO admissions (student_id, student_name, batch, major, result, publish_status) "
        f"VALUES ({body.student_id}, '{body.student_name}', '{body.batch}', "
        f"'{body.major}', '{body.result}', '{body.publish_status}')"
    )
    return {"id": execute_sql(sql)}


@app.put("/api/admin/admissions/{admission_id}")
def update_admission(admission_id: int, body: AdmissionBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "UPDATE admissions SET "
        f"student_id = {body.student_id}, student_name = '{body.student_name}', "
        f"batch = '{body.batch}', major = '{body.major}', result = '{body.result}', "
        f"publish_status = '{body.publish_status}' WHERE id = {admission_id}"
    )
    execute_sql(sql)
    return {"success": True}


@app.delete("/api/admin/admissions/{admission_id}")
def delete_admission(admission_id: int, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    execute_sql(f"DELETE FROM admissions WHERE id = {admission_id}")
    return {"success": True}


@app.get("/api/admin/notices")
def get_notices_admin(
    keyword: str = "",
    page: int = 1,
    page_size: int = 5,
    x_role: str | None = Header(default=None),
):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "SELECT * FROM notices "
        f"WHERE title LIKE '%{keyword}%' OR content LIKE '%{keyword}%' ORDER BY id DESC"
    )
    return paged(sql, page, page_size)


@app.post("/api/admin/notices")
def create_notice(body: NoticeBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "INSERT INTO notices (title, content, publisher, created_at) "
        f"VALUES ('{body.title}', '{body.content}', '{body.publisher}', '{body.created_at}')"
    )
    return {"id": execute_sql(sql)}


@app.put("/api/admin/notices/{notice_id}")
def update_notice(notice_id: int, body: NoticeBody, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    sql = (
        "UPDATE notices SET "
        f"title = '{body.title}', content = '{body.content}', publisher = '{body.publisher}', "
        f"created_at = '{body.created_at}' WHERE id = {notice_id}"
    )
    execute_sql(sql)
    return {"success": True}


@app.delete("/api/admin/notices/{notice_id}")
def delete_notice(notice_id: int, x_role: str | None = Header(default=None)):
    blocked = ensure_admin(x_role)
    if blocked:
        return blocked
    execute_sql(f"DELETE FROM notices WHERE id = {notice_id}")
    return {"success": True}


@app.get("/api/student/profile")
def student_profile(user_id: int):
    sql = (
        "SELECT students.* FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {user_id}"
    )
    return fetch_one(sql)


@app.get("/api/student/admission")
def student_admission(user_id: int):
    student = fetch_one(
        "SELECT students.* FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {user_id}"
    )
    if not student:
        return None
    return fetch_one(f"SELECT * FROM admissions WHERE student_id = {student['id']}")


@app.get("/api/student/score")
def student_score(user_id: int):
    student = fetch_one(
        "SELECT students.student_no, students.name, students.score, students.chinese_score, "
        "students.math_score, students.foreign_score, students.comprehensive_score, "
        "students.choice_major, students.major, students.status FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {user_id}"
    )
    if not student:
        return None
    rank_row = fetch_one(
        f"SELECT COUNT(*) + 1 AS rank FROM students WHERE score > {student['score']}"
    )
    total_row = fetch_one("SELECT COUNT(*) AS total FROM students")
    return {
        **student,
        "rank": rank_row["rank"],
        "total": total_row["total"],
    }


@app.get("/api/student/plans")
def student_plans():
    return fetch_all("SELECT * FROM plans ORDER BY year DESC, batch, college, major")


@app.get("/api/student/choices")
def student_choices(user_id: int):
    student = fetch_one(
        "SELECT students.* FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {user_id}"
    )
    if not student:
        return {"student": None, "items": [], "locked": True}
    items = fetch_all(
        f"SELECT * FROM student_choices WHERE student_id = {student['id']} ORDER BY choice_order"
    )
    return {
        "student": student,
        "items": items,
        "locked": student["status"] in LOCKED_STUDENT_STATUSES,
    }


@app.post("/api/student/choices")
def create_choice(body: ChoiceBody):
    student = fetch_one(
        "SELECT students.* FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {body.user_id}"
    )
    if not student:
        return {"success": False, "message": "学生不存在"}
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}

    count = fetch_one(
        f"SELECT COUNT(*) AS total FROM student_choices WHERE student_id = {student['id']}"
    )["total"]
    if count >= 5:
        return {"success": False, "message": "最多只能填报5个志愿"}

    plan = fetch_one(f"SELECT * FROM plans WHERE id = {body.plan_id}")
    if not plan:
        return {"success": False, "message": "招生计划不存在"}

    order_value = min(max(body.choice_order, 1), count + 1)
    existing = fetch_all(
        f"SELECT id, choice_order FROM student_choices WHERE student_id = {student['id']} "
        f"AND choice_order >= {order_value} ORDER BY choice_order DESC"
    )
    for row in existing:
        execute_sql(
            f"UPDATE student_choices SET choice_order = {row['choice_order'] + 1} WHERE id = {row['id']}"
        )

    execute_sql(
        "INSERT INTO student_choices (student_id, plan_id, choice_order, batch, college, major, status, created_at) "
        f"VALUES ({student['id']}, {plan['id']}, {order_value}, '{plan['batch']}', "
        f"'{plan['college']}', '{plan['major']}', '已提交', datetime('now', 'localtime'))"
    )
    execute_sql(
        f"UPDATE students SET choice_major = '{plan['major']}' WHERE id = {student['id']} AND choice_major = ''"
    )
    return {"success": True}


@app.put("/api/student/choices/{choice_id}")
def update_choice(choice_id: int, body: ChoiceBody):
    student = fetch_one(
        "SELECT students.* FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {body.user_id}"
    )
    if not student:
        return {"success": False, "message": "学生不存在"}
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}
    plan = fetch_one(f"SELECT * FROM plans WHERE id = {body.plan_id}")
    if not plan:
        return {"success": False, "message": "招生计划不存在"}
    execute_sql(
        f"UPDATE student_choices SET plan_id = {plan['id']}, batch = '{plan['batch']}', "
        f"college = '{plan['college']}', major = '{plan['major']}' "
        f"WHERE id = {choice_id} AND student_id = {student['id']}"
    )
    return {"success": True}


@app.delete("/api/student/choices/{choice_id}")
def delete_choice(choice_id: int, user_id: int):
    student = fetch_one(
        "SELECT students.* FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {user_id}"
    )
    if not student:
        return {"success": False, "message": "学生不存在"}
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}
    execute_sql(f"DELETE FROM student_choices WHERE id = {choice_id} AND student_id = {student['id']}")
    rows = fetch_all(
        f"SELECT id FROM student_choices WHERE student_id = {student['id']} ORDER BY choice_order"
    )
    for index, row in enumerate(rows, start=1):
        execute_sql(f"UPDATE student_choices SET choice_order = {index} WHERE id = {row['id']}")
    return {"success": True}


@app.put("/api/student/choices/{choice_id}/order")
def move_choice(choice_id: int, user_id: int, direction: str):
    student = fetch_one(
        "SELECT students.* FROM students "
        f"LEFT JOIN users ON users.id = students.user_id WHERE users.id = {user_id}"
    )
    if not student:
        return {"success": False, "message": "学生不存在"}
    if student["status"] in LOCKED_STUDENT_STATUSES:
        return {"success": False, "message": "已完成录取结果后不可修改志愿"}
    current = fetch_one(
        f"SELECT * FROM student_choices WHERE id = {choice_id} AND student_id = {student['id']}"
    )
    if not current:
        return {"success": False, "message": "志愿不存在"}
    target_order = current["choice_order"] - 1 if direction == "up" else current["choice_order"] + 1
    target = fetch_one(
        f"SELECT * FROM student_choices WHERE student_id = {student['id']} AND choice_order = {target_order}"
    )
    if not target:
        return {"success": True}
    execute_sql(f"UPDATE student_choices SET choice_order = {target['choice_order']} WHERE id = {current['id']}")
    execute_sql(f"UPDATE student_choices SET choice_order = {current['choice_order']} WHERE id = {target['id']}")
    return {"success": True}


@app.get("/api/student/notices")
def student_notices():
    return fetch_all("SELECT * FROM notices ORDER BY id DESC")


@app.get("/api/student/notices/{notice_id}")
def student_notice_detail(notice_id: int):
    return fetch_one(f"SELECT * FROM notices WHERE id = {notice_id}")


@app.post("/api/student/password")
def change_password(body: PasswordBody):
    user = fetch_one(
        f"SELECT * FROM users WHERE id = {body.user_id} AND password = '{body.old_password}'"
    )
    if not user:
        return {"success": False, "message": "原密码错误"}
    execute_sql(
        f"UPDATE users SET password = '{body.new_password}' WHERE id = {body.user_id}"
    )
    return {"success": True, "message": "密码修改成功"}


@app.put("/api/profile")
def update_profile(body: ProfileBody):
    execute_sql(f"UPDATE users SET name = '{body.name}' WHERE id = {body.user_id}")
    execute_sql(f"UPDATE students SET name = '{body.name}' WHERE user_id = {body.user_id}")
    user = fetch_one(
        f"SELECT id, username, role, name FROM users WHERE id = {body.user_id}"
    )
    return {"success": True, "user": user}


@app.get("/api/debug/users")
def debug_users():
    return fetch_all("SELECT id, username, password, role, name FROM users ORDER BY id")


@app.exception_handler(sqlite3.Error)
def sqlite_exception_handler(_, exc: sqlite3.Error):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": str(exc)},
    )
