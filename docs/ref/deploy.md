# Glynk 部署信息

> 此文件记录生产实例的部署细节。不要提交敏感信息到 git。

## 服务器

- 地址: `dell@ijiaodui.com`
- SSH: `ssh -p 32001 dell@ijiaodui.com`（公钥登录）
- 路径: `/mnt/tracker/Glynk`

## 端口映射

服务器有端口转发（宿主机内部端口 → 外部可访问端口）：

| 宿主机端口 | 外部端口 | 服务 |
|-----------|---------|------|
| 22333 | 32007 | Nginx (HTTP API) |
| 22233 | 32006 | PostgreSQL |
| 22238 | 32005 | CD Webhook |

## Docker 容器

| 容器 | 内部端口 | 宿主机端口 |
|------|---------|-----------|
| glynk-postgres-1 | 5432 | 22233 |
| glynk-api-1 | 5000 | (内部，通过 nginx) |
| glynk-nginx-1 | 80 | 22333 |
| glynk-dev-1 | 8888 | 22238 |

## 外部访问

- API: `http://ijiaodui.com:32007`
- CD Webhook: `http://ijiaodui.com:32005/webhook`
- PostgreSQL: `ijiaodui.com:32006`

## CD (持续部署)

GitHub Webhook 配置:
- URL: `http://ijiaodui.com:32005/webhook`
- Secret: (见服务器 .env)
- Events: push

## 数据目录

```
/mnt/tracker/Glynk/
├── Glynk-data/
│   ├── html/           # HTML 内容文件
│   ├── uploads/        # 临时上传
│   └── postgres/       # PostgreSQL 数据
```
