可以通过以下命令连接到服务器；通过公钥登陆，已经配置好了：
`ssh -p 32001 dell@ijiaodui.com`

所在路径：
`/mnt/tracker/Resonote/Resonote`

现有的部署在docker中运行；新的部署可能也需要在docker中运行，因为登陆的账号有docker权限，但是可能缺少一些配置宿主机的权限。

因为一些长期的可能失败的定时任务，现在部署的数据库中又可能有垃圾数据（一般是来自RSS的），来自EPUB的数据应该是优质的可以继承的。