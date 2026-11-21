# Admission 招生管理系统

![Vue 3](https://img.shields.io/badge/Vue%203-2563EB?style=flat-square)
![Vite](https://img.shields.io/badge/Vite-0F766E?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-334155?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-B45309?style=flat-square)

## 📌 项目简介

面向学生与管理人员，涵盖招生信息展示、学生业务和后台管理。

本仓库供**网络安全学习**使用。 `vulnerable_version/` 是有漏洞的历史对照版本，`secure_version/` 是针对课程示例做过修复的版本。可以对照两套源码，理解防护措施和代码变更。

## 🏗️ 系统架构

- 两个版本分别包含 Vue 前端、FastAPI 后端和各自的本地数据库。
- 前端负责用户交互，后端提供业务 API，SQLite 保存各版本的演示数据。

## 📁 项目结构

| 路径 | 用途 |
| --- | --- |
| [`secure_version/frontend`](secure_version/frontend) | 修订版 Web 界面 |
| [`secure_version/backend`](secure_version/backend) | 修订版 API 与数据库逻辑 |
| [`vulnerable_version`](vulnerable_version) | 用于防御性对照的历史源码 |

## 🚀 如何启动

本地演示使用修订版。先启动后端，再在各自的前端目录运行 `npm ci` 和 `npm run dev`。具体环境和后端命令见[修订版安装与运行说明](secure_version/README.md)。

| 入口 | 默认地址 |
| --- | --- |
| API | `http://127.0.0.1:8000` |
| Web | `http://localhost:5173` |

演示数据和数据库按版本分开保存。相关资料见[修订记录](secure_version/doc/修复说明.md)。
