# SQLBot 开发与部署指南

## 📋 项目概览

**SQLBot** 是一款基于大模型和 RAG 的智能问数系统，采用前后端分离架构。

### 技术栈

#### 后端 (Backend)
- **框架**: FastAPI (Python 3.11)
- **数据库**: PostgreSQL (主数据库) + pgvector (向量存储)
- **ORM**: SQLModel + Alembic (数据库迁移)
- **AI框架**: LangChain, LangGraph, LlamaIndex
- **依赖管理**: uv (现代化 Python 包管理器)
- **端口**: 
  - 8000: 主应用 API
  - 8001: MCP Server (Model Context Protocol)

#### 前端 (Frontend)
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **构建工具**: Vite
- **状态管理**: Pinia
- **国际化**: Vue I18n
- **图表**: AntV G2, AntV S2, AntV X6

#### 图表渲染服务 (G2-SSR)
- **运行时**: Node.js
- **进程管理**: PM2
- **端口**: 3000 (内部服务)
- **功能**: 服务端图表渲染 (柱状图、折线图、饼图等)

#### 数据库
- **PostgreSQL**: 5432 端口
- **扩展**: pgvector (向量相似度搜索)

---

## 🛠️ 本地开发环境搭建 (WSL)

### 前置要求

```bash
# 1. 安装必要的系统依赖
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm postgresql-client git curl

# 2. 安装 uv (Python 包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 3. 安装 Node.js 18+ (如果版本过低)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 数据库准备

你有两个选择：

#### 选项 1: 使用本地 PostgreSQL

```bash
# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib

# 启动服务
sudo service postgresql start

# 创建数据库和用户
sudo -u postgres psql
```

```sql
CREATE USER root WITH PASSWORD 'Password123@pg';
CREATE DATABASE sqlbot OWNER root;
\c sqlbot
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

#### 选项 2: 使用 Docker PostgreSQL (推荐)

```bash
docker run -d \
  --name sqlbot-postgres \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=Password123@pg \
  -e POSTGRES_DB=sqlbot \
  -p 5432:5432 \
  -v ./data/postgresql:/var/lib/postgresql/data \
  ankane/pgvector:latest
```

### 后端开发环境

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/WSL
# 或 .venv\Scripts\activate  # Windows

# 3. 安装依赖 (CPU版本)
uv sync --extra cpu

# 4. 配置环境变量
# 在项目根目录创建 .env 文件
cd ..
cat > .env << 'EOF'
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sqlbot
POSTGRES_USER=root
POSTGRES_PASSWORD=Password123@pg

# 项目配置
PROJECT_NAME=SQLBot
DEFAULT_PWD=SQLBot@123456
SECRET_KEY=your-secret-key-here-change-in-production

# CORS 配置
BACKEND_CORS_ORIGINS=http://localhost,http://localhost:5173,http://localhost:8000

# 日志配置
LOG_LEVEL=DEBUG
SQL_DEBUG=True

# 缓存配置
CACHE_TYPE=memory

# 文件上传路径
UPLOAD_DIR=./data/file

# MCP 配置
SERVER_IMAGE_HOST=http://localhost:8001/images/
EOF

# 5. 运行数据库迁移
cd backend
alembic upgrade head

# 6. 启动后端服务
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端开发环境

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install
# 或使用国内镜像
npm install --registry=https://registry.npmmirror.com

# 3. 启动开发服务器
npm run dev

# 前端将运行在 http://localhost:5173
```

### G2-SSR 图表服务

```bash
# 1. 进入 g2-ssr 目录
cd g2-ssr

# 2. 安装依赖
npm install

# 3. 启动服务
node app.js
# 或使用 PM2
npm install -g pm2
pm2 start app.js --name g2-ssr

# 服务运行在 http://localhost:3000
```

### MCP Server (可选)

```bash
# 在后端目录，另开一个终端
cd backend
source .venv/bin/activate
uvicorn main:mcp_app --host 0.0.0.0 --port 8001 --reload
```

### 访问应用

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MCP Server**: http://localhost:8001

默认登录信息：
- 用户名: `admin`
- 密码: `SQLBot@123456`

---

## 🐳 生产环境部署 (分离式部署)

### 架构设计

```
┌─────────────────┐
│   Nginx/Caddy   │ (前端静态文件 + 反向代理)
│   Port: 80/443  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼────┐ ┌─▼──────────┐
│ 前端    │ │  后端容器   │
│ 静态文件│ │  Port: 8000│
└────────┘ │  Port: 8001│
           └─────┬──────┘
                 │
         ┌───────▼────────┐
         │  PostgreSQL    │
         │  Port: 5432    │
         │  (独立服务器)   │
         └────────────────┘
```

### 1. 数据库服务器部署

```bash
# 在数据库服务器上 (假设 IP: 192.168.1.100)

# 使用 Docker 部署 PostgreSQL
docker run -d \
  --name sqlbot-postgres \
  --restart unless-stopped \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=YourStrongPassword123! \
  -e POSTGRES_DB=sqlbot \
  -p 5432:5432 \
  -v /data/postgresql:/var/lib/postgresql/data \
  ankane/pgvector:latest

# 配置 PostgreSQL 允许远程连接
docker exec -it sqlbot-postgres bash
echo "host all all 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf
echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf
exit

# 重启容器
docker restart sqlbot-postgres

# 配置防火墙
sudo ufw allow 5432/tcp
```

### 2. 后端服务器部署 (容器化)

#### 方式 A: 使用官方镜像

```bash
# 在后端服务器上 (假设 IP: 192.168.1.101)

# 创建配置文件
mkdir -p /opt/sqlbot/config
cat > /opt/sqlbot/config/.env << 'EOF'
# 数据库配置 (指向独立数据库服务器)
POSTGRES_SERVER=192.168.1.100
POSTGRES_PORT=5432
POSTGRES_DB=sqlbot
POSTGRES_USER=root
POSTGRES_PASSWORD=YourStrongPassword123!

# 项目配置
PROJECT_NAME=SQLBot
DEFAULT_PWD=SQLBot@123456
SECRET_KEY=your-production-secret-key-change-this

# CORS 配置 (添加你的前端域名)
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 日志配置
LOG_LEVEL=INFO
SQL_DEBUG=False

# 缓存配置 (生产环境建议使用 Redis)
CACHE_TYPE=memory
# CACHE_REDIS_URL=redis://192.168.1.102:6379/0

# MCP 配置
SERVER_IMAGE_HOST=https://yourdomain.com/mcp/images/
EOF

# 运行容器 (不包含数据库)
docker run -d \
  --name sqlbot-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 8001:8001 \
  --env-file /opt/sqlbot/config/.env \
  -e POSTGRES_SERVER=192.168.1.100 \
  -v /opt/sqlbot/data/excel:/opt/sqlbot/data/excel \
  -v /opt/sqlbot/data/file:/opt/sqlbot/data/file \
  -v /opt/sqlbot/data/images:/opt/sqlbot/images \
  -v /opt/sqlbot/logs:/opt/sqlbot/app/logs \
  dataease/sqlbot:latest
```

#### 方式 B: 自己构建后端镜像

创建专用的后端 Dockerfile:

```bash
# 在项目根目录创建 Dockerfile.backend
cat > Dockerfile.backend << 'EOF'
FROM registry.cn-qingdao.aliyuncs.com/dataease/sqlbot-base:latest AS builder

ENV PYTHONUNBUFFERED=1
ENV SQLBOT_HOME=/opt/sqlbot
ENV APP_HOME=${SQLBOT_HOME}/app
ENV PYTHONPATH=${SQLBOT_HOME}/app
ENV PATH="${APP_HOME}/.venv/bin:$PATH"

RUN mkdir -p ${APP_HOME}
WORKDIR ${APP_HOME}

# 安装依赖
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra cpu --frozen

# 复制应用代码
COPY backend ${APP_HOME}

# G2-SSR 构建
FROM registry.cn-qingdao.aliyuncs.com/dataease/sqlbot-base:latest AS ssr-builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3 pkg-config \
    libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY g2-ssr/app.js g2-ssr/package.json /app/
COPY g2-ssr/charts/* /app/charts/
RUN npm install

# 运行时镜像 (不包含 PostgreSQL)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SQLBOT_HOME=/opt/sqlbot
ENV PYTHONPATH=${SQLBOT_HOME}/app
ENV PATH="${SQLBOT_HOME}/app/.venv/bin:$PATH"

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wait-for-it nodejs npm \
    libcairo2 libpango-1.0-0 libjpeg62-turbo libgif7 librsvg2-2 \
    && rm -rf /var/lib/apt/lists/*

# 复制应用
COPY --from=builder ${SQLBOT_HOME} ${SQLBOT_HOME}
COPY --from=ssr-builder /app /opt/sqlbot/g2-ssr
COPY g2-ssr/*.ttf /usr/share/fonts/truetype/liberation/

WORKDIR ${SQLBOT_HOME}/app

# 创建启动脚本 (不启动 PostgreSQL)
RUN cat > start-backend.sh << 'SCRIPT'
#!/bin/bash
SSR_PATH=/opt/sqlbot/g2-ssr
APP_PATH=/opt/sqlbot/app
PM2_CMD_PATH=$SSR_PATH/node_modules/pm2/bin/pm2

# 等待数据库就绪
wait-for-it ${POSTGRES_SERVER}:${POSTGRES_PORT} --timeout=120 --strict -- echo "Database ready"

# 运行数据库迁移
cd $APP_PATH
alembic upgrade head

# 启动 G2-SSR
nohup $PM2_CMD_PATH start $SSR_PATH/app.js &

# 启动 MCP Server
nohup uvicorn main:mcp_app --host 0.0.0.0 --port 8001 &

# 启动主应用
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
SCRIPT

RUN chmod +x start-backend.sh

EXPOSE 8000 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["./start-backend.sh"]
EOF

# 构建镜像
docker build -f Dockerfile.backend -t sqlbot-backend:latest .

# 运行
docker run -d \
  --name sqlbot-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -p 8001:8001 \
  --env-file /opt/sqlbot/config/.env \
  -v /opt/sqlbot/data:/opt/sqlbot/data \
  -v /opt/sqlbot/logs:/opt/sqlbot/app/logs \
  sqlbot-backend:latest
```

### 3. 前端服务器部署

```bash
# 在前端服务器上 (假设 IP: 192.168.1.102)

# 1. 构建前端
cd frontend

# 修改生产环境配置
cat > .env.production << 'EOF'
VITE_API_BASE_URL=https://yourdomain.com/api/v1
VITE_APP_TITLE=SQLBot
EOF

# 构建
npm install
npm run build

# 2. 部署到 Nginx
sudo apt install nginx

# 复制构建文件
sudo mkdir -p /var/www/sqlbot
sudo cp -r dist/* /var/www/sqlbot/

# 3. 配置 Nginx
sudo cat > /etc/nginx/sites-available/sqlbot << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # 前端静态文件
    location / {
        root /var/www/sqlbot;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端 API 代理
    location /api/ {
        proxy_pass http://192.168.1.101:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # MCP Server 代理
    location /mcp/ {
        proxy_pass http://192.168.1.101:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /var/www/sqlbot;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/sqlbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 4. 配置 HTTPS (使用 Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 📦 完整的 Docker Compose 部署 (分离式)

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: ankane/pgvector:latest
    container_name: sqlbot-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: YourStrongPassword123!
      POSTGRES_DB: sqlbot
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - sqlbot-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U root -d sqlbot"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 后端服务
  backend:
    image: sqlbot-backend:latest
    container_name: sqlbot-backend
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_SERVER: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: sqlbot
      POSTGRES_USER: root
      POSTGRES_PASSWORD: YourStrongPassword123!
      PROJECT_NAME: SQLBot
      DEFAULT_PWD: SQLBot@123456
      SECRET_KEY: your-production-secret-key
      BACKEND_CORS_ORIGINS: https://yourdomain.com
      LOG_LEVEL: INFO
      CACHE_TYPE: memory
      SERVER_IMAGE_HOST: https://yourdomain.com/mcp/images/
    ports:
      - "8000:8000"
      - "8001:8001"
    volumes:
      - backend_data:/opt/sqlbot/data
      - backend_logs:/opt/sqlbot/app/logs
    networks:
      - sqlbot-network

  # Nginx 前端
  nginx:
    image: nginx:alpine
    container_name: sqlbot-nginx
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    networks:
      - sqlbot-network

volumes:
  postgres_data:
  backend_data:
  backend_logs:

networks:
  sqlbot-network:
    driver: bridge
```

---

## 🔧 常用开发命令

### 后端

```bash
# 数据库迁移
cd backend
alembic revision --autogenerate -m "描述"
alembic upgrade head
alembic downgrade -1

# 运行测试
pytest

# 代码格式化
ruff format .
ruff check --fix .

# 类型检查
mypy .
```

### 前端

```bash
cd frontend

# 开发
npm run dev

# 构建
npm run build

# 预览构建
npm run preview

# 代码检查
npm run lint
```

---

## 📝 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `POSTGRES_SERVER` | 数据库地址 | localhost |
| `POSTGRES_PORT` | 数据库端口 | 5432 |
| `POSTGRES_DB` | 数据库名 | sqlbot |
| `POSTGRES_USER` | 数据库用户 | root |
| `POSTGRES_PASSWORD` | 数据库密码 | Password123@pg |
| `SECRET_KEY` | JWT 密钥 | 自动生成 |
| `DEFAULT_PWD` | 默认密码 | SQLBot@123456 |
| `LOG_LEVEL` | 日志级别 | INFO |
| `CACHE_TYPE` | 缓存类型 | memory |
| `BACKEND_CORS_ORIGINS` | CORS 配置 | - |

---

## 🚀 性能优化建议

### 生产环境

1. **使用 Redis 缓存**: 设置 `CACHE_TYPE=redis` 和 `CACHE_REDIS_URL`
2. **增加 Worker 数量**: `uvicorn main:app --workers 4`
3. **启用 CDN**: 静态资源使用 CDN 加速
4. **数据库优化**: 配置连接池、索引优化
5. **启用 Gzip**: Nginx 配置 gzip 压缩

---

## 📚 更多资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [Docker 文档](https://docs.docker.com/)

---

## ❓ 常见问题

### Q: 如何重置管理员密码？

```bash
docker exec -it sqlbot-backend bash
cd /opt/sqlbot/app
python scripts/reset_admin_password.py
```

### Q: 如何备份数据库？

```bash
docker exec sqlbot-postgres pg_dump -U root sqlbot > backup_$(date +%Y%m%d).sql
```

### Q: 如何查看日志？

```bash
# 后端日志
docker logs -f sqlbot-backend

# 数据库日志
docker logs -f sqlbot-postgres
```

---

**祝你开发顺利！** 🎉

