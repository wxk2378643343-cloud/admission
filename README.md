# Admission 招生管理系统

本仓库收录招生管理系统的两个独立实现。应用由 Web 前端、Python API 和 SQLite 数据层组成。

| 路径 | 内容 |
| --- | --- |
| [修订版](secure_version/) | 日常阅读和本地演示入口 |
| [修订版说明](secure_version/README.md) | 环境要求、应用启动和功能说明 |
| `vulnerable_version/` | 供防御性对照审阅的历史实现 |

## 本地使用

从修订版 README 开始，在对应的前、后端目录分别安装依赖。前端使用自己的锁文件管理依赖。首次使用前查看修订版的配置与数据库说明，使用本地测试数据。两个版本的目录、依赖和数据库应各自独立。

安全修订的背景和变更说明见 [修订记录](secure_version/doc/修复说明.md)。


在 `secure_version/backend/` 中按版本文档安装依赖后，启动入口为 `uvicorn main:app --reload`。接着在 `secure_version/frontend/` 运行 `npm ci` 和 `npm run dev`。
