# Admission 修订版

该版本包含招生管理的 Vue 前端与 FastAPI 后端，使用 SQLite 保存本地演示数据。

## 启动

1. 在 `secure_version/backend/` 创建并激活 Python 虚拟环境，运行 `python -m pip install -r requirements.txt`。
2. 在同一目录运行 `python -m uvicorn main:app --reload`。API 使用本机 8000 端口，启动时初始化本地数据库。
3. 在 `secure_version/frontend/` 运行 `npm ci`，再运行 `npm run dev`，打开 `http://localhost:5173`。

前端的 API 地址定义在 [src/api.js](frontend/src/api.js)。首次登录和录入请使用本地演示数据。修订内容见 [修复说明](doc/修复说明.md)。
