from io import BytesIO
from pathlib import Path
from typing import Optional
from datetime import datetime
import re

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl import load_workbook
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .database import Base, SessionLocal, engine
from .models import AdmissionResult, ApplicationChoice, CandidateProfile, Notice, Score, User

app = FastAPI(title="Admission System API (Insecure Demo)")

# Frontend dev server and static file usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginIn(BaseModel):
    username: str
    password: str


class ChoiceIn(BaseModel):
    candidate_id: int
    batch: str
    university: str
    major: str
    priority: int


class ScoreIn(BaseModel):
    candidate_id: int
    subject: str
    score: int
    total_score: int


class AdmissionIn(BaseModel):
    candidate_id: int
    university: str
    major: str
    status: str


class NoticeIn(BaseModel):
    title: str
    content: str


class ScoreBatchIn(BaseModel):
    candidate_id: int
    chinese: int = 0
    math: int = 0
    foreign_language: int = 0
    comprehensive: int = 0


class CandidateCreateIn(BaseModel):
    username: str
    password: str
    exam_no: str
    name: str
    id_card: str
    phone: str


class CandidateProfileUpdateIn(BaseModel):
    exam_no: str
    name: str
    id_card: str
    phone: str


class MeProfileUpdateIn(BaseModel):
    exam_no: str
    name: str
    id_card: str
    phone: str


class RegisterIn(BaseModel):
    username: str
    password: str
    name: str
    id_card: str
    phone: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        value = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]{4,20}$", value):
            raise ValueError("用户名需为 4-20 位字母/数字/下划线")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度至少 6 位")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("姓名不能为空")
        return value

    @field_validator("id_card")
    @classmethod
    def validate_id_card(cls, v: str) -> str:
        value = v.strip().upper()
        if not re.match(r"^\d{17}[\dX]$", value):
            raise ValueError("身份证号格式不正确")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        value = v.strip()
        if not re.match(r"^1\d{10}$", value):
            raise ValueError("手机号格式不正确")
        return value


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(username="admin", password="admin123", role="admin")
            alice = User(username="alice", password="123456", role="candidate")
            bob = User(username="bob", password="123456", role="candidate")
            carol = User(username="carol", password="123456", role="candidate")
            dave = User(username="dave", password="123456", role="candidate")
            erin = User(username="erin", password="123456", role="candidate")
            db.add_all([admin, alice, bob, carol, dave, erin])
            db.flush()

            p1 = CandidateProfile(
                user_id=alice.id,
                exam_no="20260001",
                name="Alice",
                id_card="110101199901010001",
                phone="13800000001",
            )
            p2 = CandidateProfile(
                user_id=bob.id,
                exam_no="20260002",
                name="Bob",
                id_card="110101199902020002",
                phone="13800000002",
            )
            p3 = CandidateProfile(
                user_id=carol.id,
                exam_no="20260003",
                name="Carol",
                id_card="110101199903030003",
                phone="13800000003",
            )
            p4 = CandidateProfile(
                user_id=dave.id,
                exam_no="20260004",
                name="Dave",
                id_card="110101199904040004",
                phone="13800000004",
            )
            p5 = CandidateProfile(
                user_id=erin.id,
                exam_no="20260005",
                name="Erin",
                id_card="110101199905050005",
                phone="13800000005",
            )
            db.add_all([p1, p2, p3, p4, p5])
            db.flush()

            db.add_all(
                [
                    ApplicationChoice(
                        candidate_id=p1.id, batch="本科一批", university="示例大学", major="计算机科学", priority=1
                    ),
                    ApplicationChoice(
                        candidate_id=p2.id, batch="本科一批", university="东海理工大学", major="软件工程", priority=1
                    ),
                    ApplicationChoice(
                        candidate_id=p3.id, batch="本科一批", university="江城大学", major="信息安全", priority=1
                    ),
                    ApplicationChoice(
                        candidate_id=p4.id, batch="本科二批", university="华北学院", major="网络工程", priority=1
                    ),
                    ApplicationChoice(
                        candidate_id=p5.id, batch="本科一批", university="南方科技学院", major="数据科学", priority=1
                    ),
                    Score(candidate_id=p1.id, subject="综合", score=620, total_score=620),
                    Score(candidate_id=p2.id, subject="综合", score=598, total_score=598),
                    Score(candidate_id=p3.id, subject="综合", score=645, total_score=645),
                    Score(candidate_id=p4.id, subject="综合", score=575, total_score=575),
                    Score(candidate_id=p5.id, subject="综合", score=611, total_score=611),
                    AdmissionResult(
                        candidate_id=p1.id, university="示例大学", major="计算机科学", status="admitted"
                    ),
                    Notice(title="欢迎", content="欢迎使用系统", creator_id=admin.id),
                    Notice(
                        title="填报提醒",
                        content="本科一批志愿填报截止时间为 2026-06-30 18:00",
                        creator_id=admin.id,
                    ),
                    Notice(
                        title="成绩复核通知",
                        content="如对成绩有异议，请在 3 个工作日内提交申请。",
                        creator_id=admin.id,
                    ),
                ]
            )
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def get_current_user(user_id: Optional[int]) -> Optional[User]:
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def upsert_subject_score(db, candidate_id: int, subject: str, value: int) -> None:
    row = (
        db.query(Score)
        .filter(Score.candidate_id == candidate_id, Score.subject == subject)
        .order_by(Score.id.desc())
        .first()
    )
    if row:
        row.score = int(value)
        row.total_score = int(value)
    else:
        db.add(Score(candidate_id=candidate_id, subject=subject, score=int(value), total_score=int(value)))


@app.get("/")
def root():
    return {"message": "Admission API running", "docs": "/docs"}


@app.post("/api/login")
def login(payload: LoginIn):
    db = SessionLocal()
    try:
        # intentionally vulnerable to SQL injection for dissertation demonstration
        sql = f"SELECT id, username, role FROM user WHERE username = '{payload.username}' AND password = '{payload.password}'"
        row = db.execute(text(sql)).first()
        if not row:
            raise HTTPException(status_code=401, detail="账号或密码错误")
        return {"id": row.id, "username": row.username, "role": row.role}
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="系统异常")
    finally:
        db.close()


@app.post("/api/register")
def register(payload: RegisterIn):
    db = SessionLocal()
    try:
        existed_user = db.query(User).filter(User.username == payload.username).first()
        if existed_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        existed_id_card = db.query(CandidateProfile).filter(CandidateProfile.id_card == payload.id_card).first()
        if existed_id_card:
            raise HTTPException(status_code=400, detail="身份证号已存在")

        new_user = User(username=payload.username, password=payload.password, role="candidate")
        db.add(new_user)
        db.flush()

        profile = CandidateProfile(
            user_id=new_user.id,
            exam_no="PENDING",
            name=payload.name,
            id_card=payload.id_card,
            phone=payload.phone,
        )
        db.add(profile)
        db.flush()

        year = datetime.now().year
        id_suffix = payload.id_card[-4:]
        profile.exam_no = f"{year}{id_suffix}{profile.id:05d}"

        db.commit()
        return {"message": "ok", "exam_no": profile.exam_no}
    finally:
        db.close()


@app.get("/api/me")
def me(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return {"id": user.id, "username": user.username, "role": user.role}


@app.get("/api/me/profile")
def my_profile(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="当前账号没有考生档案")
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "exam_no": profile.exam_no,
            "name": profile.name,
            "id_card": profile.id_card,
            "phone": profile.phone,
        }
    finally:
        db.close()


@app.put("/api/me/profile")
def my_profile_update(payload: MeProfileUpdateIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="当前账号没有考生档案")
        profile.exam_no = payload.exam_no
        profile.name = payload.name
        profile.id_card = payload.id_card
        profile.phone = payload.phone
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.get("/api/profiles")
def profiles(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        rows = db.query(CandidateProfile).all()
        return [
            {
                "id": p.id,
                "user_id": p.user_id,
                "exam_no": p.exam_no,
                "name": p.name,
                "id_card": p.id_card,
                "phone": p.phone,
            }
            for p in rows
        ]
    finally:
        db.close()


@app.post("/api/profiles")
def profile_create(payload: CandidateCreateIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        existed = db.query(User).filter(User.username == payload.username).first()
        if existed:
            raise HTTPException(status_code=400, detail="用户名已存在")

        new_user = User(username=payload.username, password=payload.password, role="candidate")
        db.add(new_user)
        db.flush()
        profile = CandidateProfile(
            user_id=new_user.id,
            exam_no=payload.exam_no,
            name=payload.name,
            id_card=payload.id_card,
            phone=payload.phone,
        )
        db.add(profile)
        db.commit()
        return {"message": "ok", "profile_id": profile.id}
    finally:
        db.close()


@app.post("/api/profiles/import")
async def profile_import(file: UploadFile = File(...), user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 文件")

    content = await file.read()
    db = SessionLocal()
    try:
        wb = load_workbook(filename=BytesIO(content), data_only=False)
        ws = wb.active
        imported = 0
        # Header: username | password | exam_no | name | id_card | phone
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            username = str(row[0]).strip()
            password = str(row[1] or "123456").strip()
            exam_no = str(row[2] or "").strip()
            name = str(row[3] or "").strip()
            id_card = str(row[4] or "").strip()
            phone = str(row[5] or "").strip()

            if db.query(User).filter(User.username == username).first():
                continue

            new_user = User(username=username, password=password, role="candidate")
            db.add(new_user)
            db.flush()
            db.add(
                CandidateProfile(
                    user_id=new_user.id,
                    exam_no=exam_no,
                    name=name,
                    id_card=id_card,
                    phone=phone,
                )
            )
            imported += 1

        db.commit()
        return {"message": "ok", "imported": imported}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"导入失败: {exc}")
    finally:
        db.close()


@app.put("/api/profiles/{profile_id}")
def profile_update(profile_id: int, payload: CandidateProfileUpdateIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        row = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="考生不存在")
        row.exam_no = payload.exam_no
        row.name = payload.name
        row.id_card = payload.id_card
        row.phone = payload.phone
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.get("/api/profile/{profile_id}")
def profile_detail(profile_id: int, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        # intentionally insecure: no ownership authorization check (IDOR)
        p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="考生不存在")
        return {
            "id": p.id,
            "user_id": p.user_id,
            "exam_no": p.exam_no,
            "name": p.name,
            "id_card": p.id_card,
            "phone": p.phone,
        }
    finally:
        db.close()


@app.get("/api/choices")
def choice_list(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        rows = db.query(ApplicationChoice).all()
        return [
            {
                "id": c.id,
                "candidate_id": c.candidate_id,
                "batch": c.batch,
                "university": c.university,
                "major": c.major,
                "priority": c.priority,
            }
            for c in rows
        ]
    finally:
        db.close()


@app.post("/api/choices")
def choice_create(payload: ChoiceIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "candidate":
        raise HTTPException(status_code=403, detail="仅考生可操作")

    db = SessionLocal()
    try:
        my_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if not my_profile:
            raise HTTPException(status_code=403, detail="考生档案不存在")
        if payload.candidate_id != my_profile.id:
            raise HTTPException(status_code=403, detail="仅可填报自己的志愿")
        latest_admission = (
            db.query(AdmissionResult)
            .filter(AdmissionResult.candidate_id == my_profile.id)
            .order_by(AdmissionResult.id.desc())
            .first()
        )
        if latest_admission and latest_admission.status == "admitted":
            raise HTTPException(status_code=400, detail="已录取后不可新增志愿")
        if payload.priority not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="志愿优先级仅支持 1-3")

        existed_count = db.query(ApplicationChoice).filter(ApplicationChoice.candidate_id == my_profile.id).count()
        if existed_count >= 3:
            raise HTTPException(status_code=400, detail="最多仅可填报 3 个志愿")
        duplicated_priority = (
            db.query(ApplicationChoice)
            .filter(
                ApplicationChoice.candidate_id == my_profile.id,
                ApplicationChoice.priority == payload.priority,
            )
            .first()
        )
        if duplicated_priority:
            raise HTTPException(status_code=400, detail="该优先级已使用，请选择其他优先级")

        row = ApplicationChoice(**payload.model_dump())
        db.add(row)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.put("/api/choices/{choice_id}")
def choice_update(choice_id: int, payload: ChoiceIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "candidate":
        raise HTTPException(status_code=403, detail="仅考生可操作")

    db = SessionLocal()
    try:
        my_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if not my_profile:
            raise HTTPException(status_code=403, detail="考生档案不存在")
        if payload.candidate_id != my_profile.id:
            raise HTTPException(status_code=403, detail="仅可修改自己的志愿")
        latest_admission = (
            db.query(AdmissionResult)
            .filter(AdmissionResult.candidate_id == my_profile.id)
            .order_by(AdmissionResult.id.desc())
            .first()
        )
        if latest_admission and latest_admission.status == "admitted":
            raise HTTPException(status_code=400, detail="已录取后不可编辑志愿")
        if payload.priority not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="志愿优先级仅支持 1-3")

        row = db.query(ApplicationChoice).filter(ApplicationChoice.id == choice_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="志愿不存在")
        if row.candidate_id != my_profile.id:
            raise HTTPException(status_code=403, detail="仅可修改自己的志愿")
        duplicated_priority = (
            db.query(ApplicationChoice)
            .filter(
                ApplicationChoice.candidate_id == my_profile.id,
                ApplicationChoice.priority == payload.priority,
                ApplicationChoice.id != choice_id,
            )
            .first()
        )
        if duplicated_priority:
            raise HTTPException(status_code=400, detail="该优先级已使用，请选择其他优先级")
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.get("/api/scores")
def score_list(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        rows = db.query(Score).all()
        return [
            {
                "id": s.id,
                "candidate_id": s.candidate_id,
                "subject": s.subject,
                "score": s.score,
                "total_score": s.total_score,
            }
            for s in rows
        ]
    finally:
        db.close()


@app.post("/api/scores")
def score_create(payload: ScoreIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        row = Score(**payload.model_dump())
        db.add(row)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.post("/api/scores/batch")
def score_batch_upsert(payload: ScoreBatchIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        exists_profile = db.query(CandidateProfile).filter(CandidateProfile.id == payload.candidate_id).first()
        if not exists_profile:
            raise HTTPException(status_code=404, detail="考生不存在")

        upsert_subject_score(db, payload.candidate_id, "语文", payload.chinese)
        upsert_subject_score(db, payload.candidate_id, "数学", payload.math)
        upsert_subject_score(db, payload.candidate_id, "外语", payload.foreign_language)
        upsert_subject_score(db, payload.candidate_id, "综合", payload.comprehensive)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.get("/api/scores/template")
def score_template_export(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        profiles = db.query(CandidateProfile).order_by(CandidateProfile.id.asc()).all()
        scores = db.query(Score).all()
        latest_by_candidate_subject = {}
        for s in scores:
            key = (s.candidate_id, s.subject)
            old = latest_by_candidate_subject.get(key)
            if old is None or s.id > old.id:
                latest_by_candidate_subject[key] = s

        wb = Workbook()
        ws = wb.active
        ws.title = "scores_template"
        ws.append(["candidate_id", "name", "exam_no", "语文", "数学", "外语", "综合"])
        for p in profiles:
            ws.append(
                [
                    p.id,
                    p.name,
                    p.exam_no,
                    (latest_by_candidate_subject.get((p.id, "语文")).score if latest_by_candidate_subject.get((p.id, "语文")) else ""),
                    (latest_by_candidate_subject.get((p.id, "数学")).score if latest_by_candidate_subject.get((p.id, "数学")) else ""),
                    (latest_by_candidate_subject.get((p.id, "外语")).score if latest_by_candidate_subject.get((p.id, "外语")) else ""),
                    (latest_by_candidate_subject.get((p.id, "综合")).score if latest_by_candidate_subject.get((p.id, "综合")) else ""),
                ]
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=scores_template.xlsx"},
        )
    finally:
        db.close()


@app.post("/api/scores/import-template")
async def score_import_template(file: UploadFile = File(...), user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 文件")

    content = await file.read()
    db = SessionLocal()
    try:
        wb = load_workbook(filename=BytesIO(content), data_only=True)
        ws = wb.active
        imported = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            candidate_id = int(row[0])
            chinese = int(row[3] or 0)
            math = int(row[4] or 0)
            foreign = int(row[5] or 0)
            comprehensive = int(row[6] or 0)

            profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_id).first()
            if not profile:
                continue

            upsert_subject_score(db, candidate_id, "语文", chinese)
            upsert_subject_score(db, candidate_id, "数学", math)
            upsert_subject_score(db, candidate_id, "外语", foreign)
            upsert_subject_score(db, candidate_id, "综合", comprehensive)
            imported += 1

        db.commit()
        return {"message": "ok", "imported": imported}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"导入失败: {exc}")
    finally:
        db.close()


@app.put("/api/scores/{score_id}")
def score_update(score_id: int, payload: ScoreIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        row = db.query(Score).filter(Score.id == score_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="成绩不存在")
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.post("/api/scores/import")
async def score_import(file: UploadFile = File(...), user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx 文件")

    content = await file.read()
    db = SessionLocal()
    try:
        wb = load_workbook(filename=BytesIO(content), data_only=False)
        ws = wb.active
        imported = 0
        # Header: candidate_id | subject | score | total_score_or_expr
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue
            candidate_id = int(row[0])
            subject = str(row[1] or "")
            score_value = int(row[2] or 0)
            total_raw = row[3]

            if isinstance(total_raw, str) and total_raw.startswith("="):
                # intentionally insecure for dissertation demonstration:
                # executes arbitrary expression from imported cell.
                total_score = int(eval(total_raw[1:]))
            else:
                total_score = int(total_raw or score_value)

            db.add(
                Score(
                    candidate_id=candidate_id,
                    subject=subject,
                    score=score_value,
                    total_score=total_score,
                )
            )
            imported += 1

        db.commit()
        return {"message": "ok", "imported": imported}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"导入失败: {exc}")
    finally:
        db.close()


@app.get("/api/admissions")
def admission_list(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        rows = db.query(AdmissionResult).all()
        return [
            {
                "id": a.id,
                "candidate_id": a.candidate_id,
                "university": a.university,
                "major": a.major,
                "status": a.status,
            }
            for a in rows
        ]
    finally:
        db.close()


@app.get("/api/admission-board")
def admission_board(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        choices = db.query(ApplicationChoice).all()
        admissions = db.query(AdmissionResult).all()
        profiles = db.query(CandidateProfile).all()

        profile_map = {p.id: p for p in profiles}

        # group all choices by candidate, and keep first choice as default display
        choices_by_candidate = {}
        choice_by_candidate = {}
        for c in choices:
            if c.candidate_id not in choices_by_candidate:
                choices_by_candidate[c.candidate_id] = []
            choices_by_candidate[c.candidate_id].append(c)
            old = choice_by_candidate.get(c.candidate_id)
            if old is None or c.priority < old.priority:
                choice_by_candidate[c.candidate_id] = c

        for cid, rows in choices_by_candidate.items():
            rows.sort(key=lambda x: x.priority)

        # pick latest admission row for each candidate
        admission_by_candidate = {}
        for a in admissions:
            old = admission_by_candidate.get(a.candidate_id)
            if old is None or a.id > old.id:
                admission_by_candidate[a.candidate_id] = a

        candidate_ids = sorted(choice_by_candidate.keys())
        if user.role == "candidate":
            my_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
            if not my_profile:
                return []
            candidate_ids = [cid for cid in candidate_ids if cid == my_profile.id]

        rows = []
        for cid in candidate_ids:
            p = profile_map.get(cid)
            c = choice_by_candidate.get(cid)
            a = admission_by_candidate.get(cid)
            if not p or not c:
                continue
            candidate_choices = choices_by_candidate.get(cid, [])
            rows.append(
                {
                    "candidate_id": cid,
                    "name": p.name,
                    "exam_no": p.exam_no,
                    "choice_university": c.university,
                    "choice_major": c.major,
                    "choices": [
                        {
                            "id": item.id,
                            "batch": item.batch,
                            "university": item.university,
                            "major": item.major,
                            "priority": item.priority,
                        }
                        for item in candidate_choices
                    ],
                    "admission_id": a.id if a else None,
                    "university": a.university if a else c.university,
                    "major": a.major if a else c.major,
                    "status": a.status if a else None,
                }
            )
        return rows
    finally:
        db.close()


@app.post("/api/admissions")
def admission_create(payload: AdmissionIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        choice_exists = (
            db.query(ApplicationChoice)
            .filter(ApplicationChoice.candidate_id == payload.candidate_id)
            .first()
        )
        if not choice_exists:
            raise HTTPException(status_code=400, detail="该考生尚未填报志愿，不能录取")

        if payload.status not in ["pending", "admitted", "rejected"]:
            raise HTTPException(status_code=403, detail="状态仅支持拟录取/录取/拒绝")

        row = AdmissionResult(**payload.model_dump())
        db.add(row)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.put("/api/admissions/{admission_id}")
def admission_update(admission_id: int, payload: AdmissionIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        choice_exists = (
            db.query(ApplicationChoice)
            .filter(ApplicationChoice.candidate_id == payload.candidate_id)
            .first()
        )
        if not choice_exists:
            raise HTTPException(status_code=400, detail="该考生尚未填报志愿，不能录取")

        if payload.status not in ["pending", "admitted", "rejected"]:
            raise HTTPException(status_code=403, detail="状态仅支持拟录取/录取/拒绝")

        row = db.query(AdmissionResult).filter(AdmissionResult.id == admission_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="录取记录不存在")
        for key, value in payload.model_dump().items():
            setattr(row, key, value)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.get("/api/notices")
def notice_list(user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    db = SessionLocal()
    try:
        rows = db.query(Notice).order_by(Notice.id.desc()).all()
        return [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "creator_id": n.creator_id,
            }
            for n in rows
        ]
    finally:
        db.close()


@app.post("/api/notices")
def notice_create(payload: NoticeIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        # intentionally insecure for XSS demonstration: content stored/rendered without sanitization
        row = Notice(title=payload.title, content=payload.content, creator_id=user.id)
        db.add(row)
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()


@app.put("/api/notices/{notice_id}")
def notice_update(notice_id: int, payload: NoticeIn, user_id: Optional[int] = None):
    user = get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可操作")

    db = SessionLocal()
    try:
        row = db.query(Notice).filter(Notice.id == notice_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="公告不存在")
        row.title = payload.title
        row.content = payload.content
        db.commit()
        return {"message": "ok"}
    finally:
        db.close()
