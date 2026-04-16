可以通过以下命令连接到服务器；通过公钥登陆，已经配置好了：
`ssh -p 32001 dell@ijiaodui.com`

所在路径：
`/mnt/tracker/Resonote/Resonote`

在docker中运行，先已停止；新的部署可能也需要在docker中运行，因为登陆的账号有docker权限，但是可能缺少一些配置宿主机的权限。

服务器端口转发

```
22334->32002 # dev ssh
22335->32003 # frp (用于连接本地PC做mineru解析；服务器宿主机：~/frp_0.52.3_linux_amd64)
22237->32004 # Milvus gRPC
22238->32005 # dev Webhook Server (CD)
22233->32006 # PostgreSQL
22333->32007 # nginx
22234->32008 # neo4j Bolt
22337->?     # frp
```