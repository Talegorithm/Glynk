# Glynk 部署信息

> 此文件记录生产实例的部署细节。不要提交敏感信息到 git。

## 架构概览

```
浏览器 → CDN (腾讯云, brainow.link) → 前端服务器 (Nginx + 静态文件)
                                         ├── /api/*  → 后端服务器 (Docker API)
                                         ├── /media/* → 后端服务器 (直接文件)
                                         └── /*      → SPA (index.html)
```

## 本地开发（连远程数据）

通过已有端口转发直连服务器 DB 和文件，无需 SSH 隧道：

```bash
export POSTGRES_HOST=ijiaodui.com
export POSTGRES_PORT=32006
export REMOTE_FILE_BASE=http://ijiaodui.com:32007
export GLYNK_TOKEN=glk_xxx   # ingestion 要写远程文件时需要；必须在服务器白名单里
uvicorn glynk.main:app --reload --port 8000
```

- `REMOTE_FILE_BASE` 启用 `RemoteFileStore`（`glynk/storage/file_store.py`）：
  - 读：HTTP GET `/media/{unit_id}/{filename}`，带 LRU 缓存
  - 写：HTTP PUT `/api/internal/files/{unit_id}/{filename}`（ingestion 用），需 `GLYNK_TOKEN` 在服务器 `GLYNK_WRITE_ALLOWED_TOKENS` 白名单里
- 不设 `REMOTE_FILE_BASE` 时默认走 `LocalFileStore`（本地磁盘），生产环境零影响
- Auth token 和线上共用同一个 DB，账号通用
- 服务器白名单 env：`GLYNK_WRITE_ALLOWED_TOKENS=glk_aaa,glk_bbb`（逗号分隔，不在名单内的 token 调 `/api/internal/files` → 403）

---

## 后端服务器

- 地址: `dell@ijiaodui.com`
- SSH: `ssh -p 32001 dell@ijiaodui.com`（公钥登录）
- 路径: `/mnt/tracker/Glynk`

### 端口映射

| 宿主机端口 | 外部端口 | 服务 |
|-----------|---------|------|
| 22333 | 32007 | Nginx (HTTP API) |
| 22233 | 32006 | PostgreSQL |
| 22238 | 32005 | CD Webhook |

### Docker 容器

| 容器 | 内部端口 | 宿主机端口 |
|------|---------|-----------|
| glynk-postgres-1 | 5432 | 22233 |
| glynk-api-1 | 5000 | (内部，通过 nginx) |
| glynk-nginx-1 | 80 | 22333 |
| glynk-dev-1 | 8888 | 22238 |

### 手动部署后端

GitHub 连接不稳定，通常需要手动 scp 更新的文件：

```bash
# 上传改动的文件
scp -P 32001 glynk/path/to/file.py dell@ijiaodui.com:/mnt/tracker/Glynk/glynk/path/to/file.py

# 重建 API 容器
ssh -p 32001 dell@ijiaodui.com 'cd /mnt/tracker/Glynk && docker-compose up -d --force-recreate api'
```

### 数据目录

```
/mnt/tracker/Glynk/
├── .env                # Azure OpenAI key 等（docker-compose 自动读取）
├── Glynk-data/
│   ├── html/           # HTML 内容文件 + 图片（从 Resonote library_media 迁移）
│   ├── uploads/        # 临时上传
│   └── postgres/       # PostgreSQL 数据
```

Resonote 旧数据仍在 `/mnt/tracker/Resonote/Resonote-data/`，图片已复制到 Glynk。

## 前端服务器

- 地址: `root@62.234.45.192`
- SSH: `ssh -i dev.pem root@62.234.45.192`（dev.pem 在本地项目根目录，已 gitignore）
- 路径: `/root/Glynk`
- 部署目录: `/var/www/glynk`
- 域名: `brainow.link`（临时复用，新域名备案中）

### Nginx 配置

配置文件: `/etc/nginx/conf.d/brainow.conf`（源文件: `glynk-web/cd/nginx.conf`）

关键代理规则：
- `/api/media/*` → `ijiaodui.com:32007/media/*`（旧数据 HTML 中的图片路径）
- `/media/*` → `ijiaodui.com:32007/media/*`（新数据图片路径）
- `/api/*` → `ijiaodui.com:32007/api/*`（API，禁用缓存）
- `/*` → SPA fallback

### CD (自动部署)

GitHub Webhook → `http://62.234.45.192:8888/webhook` → 自动 git pull + npm build + deploy

**注意**：前端服务器连 GitHub 不稳定，自动部署经常因 git fetch 超时失败。失败时手动部署：

```bash
# 本地构建
cd glynk-web && npm run build

# 上传到服务器
scp -i dev.pem -r dist/* root@62.234.45.192:/var/www/glynk/

# 刷新 CDN
ssh -i dev.pem root@62.234.45.192 "cd /root/Glynk/glynk-web/cd && node purge-cdn.cjs"
```

### CDN (腾讯云)

- 域名: `brainow.link` + `www.brainow.link`
- HTTPS: CDN 处理，Nginx 只 HTTP
- 刷新生效: 5-10 分钟
- **注意**: 确认 `/api/` 路径在 CDN 控制台设置为不缓存

### Webhook 服务管理

```bash
# 启停
bash /root/Glynk/glynk-web/cd/start_webhook.sh
bash /root/Glynk/glynk-web/cd/stop_webhook.sh

# 日志
tail -50 /root/webhook_frontend.log
```

## 部署文件说明

所有部署脚本在 `glynk-web/cd/` 目录下（已 gitignore，不在公开仓库中）：

| 文件 | 用途 |
|------|------|
| `nginx.conf` | Nginx 配置源文件 |
| `deploy_frontend.sh` | 自动部署脚本（webhook 调用） |
| `webhook_server_frontend.py` | GitHub Webhook 接收服务 |
| `start_webhook.sh` / `stop_webhook.sh` | Webhook 服务管理 |
| `purge-cdn.cjs` | CDN 缓存刷新（需要 tencentcloud-sdk-nodejs） |

后端部署文件同样 gitignore：`docker-compose.yml`、`env/`

## 已知问题

- 前端服务器 GitHub 连接不稳定，自动部署常失败
- pgvector 向量索引不支持 3072 维（IVFFlat/HNSW 均限制 2000 维），当前使用暴力扫描
- CDN 可能缓存 API 的 404 响应，需在腾讯云控制台确认 `/api/` 不缓存规则
- 翻译功能前端 UI 存在但后端未完整实现
