# vulnerable_version

目录结构：

- `frontend`：Vue 前端
- `backend`：FastAPI 后端

启动方式：

1. 后端
   - 进入 `vulnerable_version/backend`
   - 安装依赖：`pip install -r requirements.txt`
   - 启动：`uvicorn main:app --reload`

2. 前端
   - 进入 `vulnerable_version/frontend`
   - 安装依赖：`npm install`
   - 启动：`npm run dev`

默认账号：

- 管理员：`admin / 123456`
- 学生：`2026001 / 123456`

当前版本故意保留了若干不安全实现，用于后续安全版对比，包括：

- 明文密码
- 依赖前端传递角色信息
- SQL 字符串拼接
- 公告详情直接渲染 HTML
