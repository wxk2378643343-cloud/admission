# Admission Insecure Demo (Vue + FastAPI 前后端分离)

本项目用于高校招生录取系统漏洞研究演示，刻意保留安全缺陷，仅限教学与论文实验。

## 1. 项目结构

- `backend/app/` FastAPI 后端（仅 API）
- `data/db/` 数据库文件目录
- `frontend/` Vue3 + Vite 前端
- `doc/` 方案文档

## 2. 启动后端

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

后端地址：`http://127.0.0.1:8000`  
默认 SQLite：`data/db/admission.db`

## 3. 启动前端

新开一个 PowerShell 窗口：

```powershell
cd frontend
npm install
npm run dev
```

前端地址：`http://127.0.0.1:5173`

## 4. 默认账号

- 管理员：`admin / admin123`
- 考生：`alice / 123456`
- 考生：`bob / 123456`

## 5. 预留漏洞点（用于论文复现）

1. SQL 注入
- 文件：`backend/app/main.py`
- 位置：`POST /api/login`
- 说明：拼接 SQL 登录校验

2. 越权访问（IDOR）
- 文件：`backend/app/main.py`
- 位置：`GET /api/profile/{profile_id}`
- 说明：只校验登录，不校验资源归属

3. 存储型 XSS
- 文件：`frontend/src/App.vue`
- 位置：公告渲染 `v-html="n.content"`
- 说明：后端不清洗，前端直接渲染 HTML

4. 暴力破解风险
- 文件：`backend/app/main.py`
- 位置：`POST /api/login`
- 说明：无验证码、无失败锁定、无限尝试

5. Excel 导入表达式执行风险（新增）
- 文件：`backend/app/main.py`
- 位置：`POST /api/scores/import`
- 说明：对 `=...` 单元格内容执行 `eval`，可导致代码执行风险（仅实验环境）

## 6. 演示顺序建议

1. 正常业务：登录 -> 查看考生 -> 新增志愿 -> 发布录取 -> 公告发布
2. SQL 注入：登录框构造注入 payload
3. 越权：普通考生读取其它 profile id
4. XSS：公告写入脚本后在前端触发
