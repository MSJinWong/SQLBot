---
type: always_apply
description: SQLBot 项目的开发约定、代码风格、依赖与测试规范
---

# SQLBot Rules & Guidelines

## 1. 项目与架构概览

- 本仓库是 **SQLBot**：基于大模型 + RAG 的智能问数系统。
- 架构：
  - 后端：FastAPI (Python 3.11) + SQLModel + Alembic + PostgreSQL/pgvector + LangChain / LangGraph / LlamaIndex。
  - 前端：Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue I18n。
  - 图表渲染服务：`g2-ssr`（Node.js + G2 SSR + PM2）。
  - 数据库：PostgreSQL + pgvector。
- 部署方式：本地开发 & 生产环境部署详见 `DEVELOPMENT_DEPLOYMENT_GUIDE.md`。

## 2. 通用原则

- **遵守 License**：不得替换或修改 SQLBot 的 Logo 和版权信息；衍生作品需遵守 GPLv3 的开源义务（详见根目录 `LICENSE` 和 `README.md`）。
- **尊重现有结构**：新增代码优先按现有目录结构和模块边界组织，不要创建“第二套架构”。
- **配置统一走环境变量**：
  - 所有运行时配置通过 `.env` 和 `common.core.config.settings` 读取。
  - 禁止在代码中硬编码密码、密钥、数据库连接等敏感信息。
- **国际化优先**：
  - 前端文案通过 Vue I18n 管理，避免在组件中直接硬编码字符串。
  - 后端返回给用户展示的文本遵循现有 locales / 文案体系。
- **命令执行策略（给 Agent 用）**：
  - 可直接执行：测试（`pytest`）、静态检查（`mypy`、`ruff`）、前端 lint（`npm run lint`）、前端构建（`npm run build`）。
  - 需要用户明确确认：安装/升级依赖、`docker build` / `docker-compose up -d`、`alembic upgrade`、重置密码脚本、数据库导入导出等有副作用的命令。

## 3. 后端（FastAPI / Python）规范

### 3.1 代码风格 & 静态检查

- Python 版本固定为 **3.11**，按此版本特性编写代码。
- 所有新函数、方法必须添加**完整类型注解**，兼容 `pyproject.toml` 中的 **mypy strict** 设置。
- 使用 `ruff` 作为格式化 + lint 工具：
  - 格式化：`ruff format .`
  - 检查 & 修复：`ruff check --fix .`
- 导入顺序遵循：标准库 → 第三方库 → 项目内部模块，并保持与现有文件一致。

### 3.2 目录与模块组织

- 后端代码位于 `backend/`：
  - 业务逻辑按域拆分在 `backend/apps/**` 下。
  - API 入口为 `apps.api.api_router`，新增接口时应注册到合适的 router 中。
- 典型拆分方式：
  - 模型：`apps.<domain>.models` 或现有 models 模块。
  - 业务逻辑：`apps.<domain>.crud` / `service`。
  - 路由：`apps.<domain>.router`，在 `apps.api` 中统一挂载。
- `backend/main.py` 只做应用初始化（迁移、缓存、CORS、MCP、日志等），不要在其中写业务逻辑。

### 3.3 API 设计

- 使用 **APIRouter** 定义路由，路径统一挂在 `settings.API_V1_STR`（如 `/api/v1`）下，避免硬编码前缀。
- 请求/响应：
  - 优先使用 **Pydantic 模型** 作为请求体和响应体，避免裸 `dict`。
  - 列表、分页、通用响应结构尽量复用现有模型和封装。
- 权限与认证：
  - 使用 `apps.system.middleware.auth.TokenMiddleware` 和现有认证机制，避免自建一套新的认证/权限系统。

### 3.4 数据库与迁移

- 统一通过 **SQLModel + Alembic** 管理数据库结构。
- 修改表结构的流程：
  1. 更新 SQLModel 模型。
  2. 执行 `alembic revision --autogenerate -m "描述"`，检查生成迁移脚本。
  3. 确认无误后执行 `alembic upgrade head`。
- 不在业务代码中绕过迁移系统直接执行破坏性 DDL（例如 `ALTER TABLE`），除非有充分注释和强理由。

### 3.5 缓存、嵌入与启动流程

- 启动流程在 `backend/main.py` 的 `lifespan` 中集中维护，包括：
  - 数据库迁移：`run_migrations()`。
  - 缓存初始化：`init_sqlbot_cache()`。
  - 动态 CORS：`init_dynamic_cors(app)`。
  - 嵌入初始化：术语、训练数据、表 & 数据源。
  - `sqlbot_xpack` 相关缓存清理和模型信息加密。
- 新增需要在启动阶段执行的任务：
  - 尽量通过独立函数封装，并在 `lifespan` 中调用。
  - 避免每个请求里重复执行昂贵初始化逻辑。

### 3.6 日志与错误处理

- 日志统一通过 `SQLBotLogUtil` 记录，避免直接使用 `print()`。
- 日志级别由环境变量 `LOG_LEVEL` 控制，新日志合理选择 DEBUG / INFO / WARNING / ERROR。
- 错误处理：
  - 复用 `common.core.response_middleware.ResponseMiddleware` 与 `exception_handler`，保持错误响应格式一致。
  - 对于业务可预期错误，推荐使用统一的业务错误封装，而不是裸抛 `Exception`。

## 4. 前端（Vue 3 + TS + Vite）规范

### 4.1 代码风格

- 所有新逻辑使用 **TypeScript**：
  - `.vue` 文件中使用 `<script setup lang="ts">`。
- 优先使用 **Composition API**，与现有组件风格保持一致。
- 使用 ESLint + Prettier：
  - 检查：`npm run lint`。
  - 不随意在文件中关闭 ESLint 规则，确有需要须加说明注释。

### 4.2 组件与状态管理

- UI 组件优先使用 **Element Plus** / `element-plus-secondary`。
- 全局状态统一使用 **Pinia** 管理，避免事件总线或随机全局单例。
- 组件职责划分：
  - 容器组件负责数据获取和状态管理。
  - 展示组件保持无副作用、方便复用。

### 4.3 网络请求与接口约定

- 使用已有 Axios 封装访问后端：
  - 接口基地址通过 `VITE_API_BASE_URL` 配置。
  - 复用已有拦截器与异常处理逻辑，保持统一的错误提示体验。
- 与后端接口的约定：
  - 路径、请求体、响应结构必须与 FastAPI 中的 Pydantic 模型对齐。
  - 修改后端接口时，需同步更新前端调用方并考虑兼容性。

### 4.4 国际化与文案

- 所有用户可见文本通过 Vue I18n 管理：
  - 避免在组件内直接硬编码中文/英文。
  - 新增 i18n key 时遵循现有命名规则和层级结构。
- 时间与数字格式使用 `dayjs` 等统一工具处理，不在组件内写散乱的格式化逻辑。

### 4.5 构建与静态资源

- 日常命令：
  - 开发：`npm run dev`
  - 构建：`npm run build`
  - 预览：`npm run preview`
- 静态资源（图片、字体等）：
  - 放在约定目录（`public` / `assets`），避免硬编码外部 URL。
  - 部署通过 Nginx 或其他静态服务器提供，遵循指南中的 Nginx 示例配置。

## 5. G2-SSR 图表服务

- `g2-ssr` 负责服务端图表渲染（Node.js + `@antv/g2-ssr` + `node-canvas` + PM2）。
- 修改或新增图表类型时：
  - 优先扩展 `g2-ssr/charts` 中的既有模式，保持配置结构一致。
  - 本地使用 `node app.js` 验证功能与性能，再纳入正式流程。
- 生产环境推荐使用 PM2：
  - 启动命令：`pm2 start app.js --name g2-ssr`。
  - 保持端口与 `DEVELOPMENT_DEPLOYMENT_GUIDE.md` 中描述一致（默认 3000）。

## 6. 测试与质量保证

### 6.1 后端测试

- 测试框架：**pytest**。
- 新增功能应配套新增或补充相应测试用例（单元测试或集成测试）。
- 常用命令（在 `backend/` 下）：
  - 运行测试：`pytest`
  - 类型检查：`mypy .`
  - 格式化 & lint：`ruff format . && ruff check --fix .`
- 尽量使用独立测试数据库或事务回滚策略，避免污染实际数据。

### 6.2 前端质量检查

- 在 `frontend/` 下：
  - Lint：`npm run lint`
  - 构建检查：`npm run build`
- 如增加前端单元测试，推荐集中使用统一测试框架（例如 Vitest），不要在每个组件零散引入不同方案。

## 7. 依赖与环境管理

### 7.1 Python / 后端依赖（uv）

- 依赖管理统一使用 **uv**：
  - 创建虚拟环境：`uv venv`。
  - 安装依赖（CPU 版本）：`uv sync --extra cpu`。
- 新增或升级后端依赖：
  - 修改 `backend/pyproject.toml` 中的 `dependencies`，遵循现有版本约束风格（`>=,<` 或精确 pin）。
  - 执行 `uv sync` 更新锁定文件，**不要手工编辑锁文件**。
  - 对 LangChain、LlamaIndex 等 AI 相关依赖谨慎升级，注意兼容性。

### 7.2 Node / 前端与 G2-SSR 依赖

- 前端和 G2-SSR 统一使用 **npm** 管理：
  - 安装依赖：`npm install`（可按需使用国内镜像）。
- 新增前端依赖时：
  - 优先复用现有库（Element Plus、AntV 系列、dayjs 等）。
  - 对体积较大的库评估对前端包大小与性能的影响。

### 7.3 环境变量与配置

- 环境变量含义详见 `DEVELOPMENT_DEPLOYMENT_GUIDE.md`（如 `POSTGRES_SERVER`、`DEFAULT_PWD`、`LOG_LEVEL` 等）。
- 约定：
  - 本地开发在项目根目录 `.env` 中配置；生产通过容器环境变量或配置文件注入。
  - 不将 `.env`、生产密码、密钥等敏感文件提交到版本控制。

## 8. 针对 Auggie CLI / Agent 的使用建议

- 在对本项目进行复杂变更前，Agent 应：
  - 先阅读或引用 `DEVELOPMENT_DEPLOYMENT_GUIDE.md` 和根目录 `README.md`，理解当前架构与约束。
  - 概述要修改的模块、运行的命令，并在执行有副作用的操作前征求用户确认。
- 完成代码修改后优先执行：
  - 后端：`pytest`、`mypy .`、`ruff format . && ruff check --fix .`。
  - 前端（如有改动）：`npm run build`、`npm run lint`。
- 对涉及数据库结构变更、部署脚本、数据迁移的请求：
  - 明确提示风险，给出迁移与回滚方案，避免直接在生产环境执行破坏性操作。
- 始终遵守本规则文件中关于依赖管理、国际化、日志与错误处理的约定，避免引入与现有架构风格冲突的实现方式。

