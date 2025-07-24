# 🚀 快速使用指南

## 快速开始

### 📦 获取项目
```bash
# 克隆仓库
git clone https://github.com/TPE1314/sgr.git
cd sgr
```

### ⚡ 一键安装
```bash
# 运行一键安装脚本
chmod +x quick_setup.sh
./quick_setup.sh
```

### 🚀 启动系统
```bash
# 启动所有机器人
./start_all.sh

# 检查运行状态  
./status.sh

# 查看日志
tail -f *.log
```

## 基本使用

### 1. 投稿机器人
- 用户向投稿机器人发送任意内容
- 支持文字、图片、视频、音频、文档等
- 自动转发到审核群组

### 2. 审核群组  
- 管理员在审核群组中审核投稿
- 点击 ✅ 通过投稿
- 点击 ❌ 拒绝投稿
- 点击 👤 查看用户统计
- 点击 🚫 封禁用户

### 3. 控制机器人
- 发送 `/start` 打开控制面板
- 管理机器人状态
- 查看系统信息
- 管理广告系统

## 广告管理

### 创建广告
```bash
# 文本广告
/create_ad text 欢迎广告
🎉 欢迎来到我们的频道！

# 链接广告  
/create_ad link 官网 https://example.com
🌐 访问我们的官方网站

# 按钮广告
/create_ad button 活动 https://sale.com 立即参与
🔥 限时特惠活动！
```

### 管理广告
- 使用 `/ads` 命令打开广告管理面板
- 可以启用/禁用、编辑、删除广告
- 查看广告统计和效果

## 系统管理

### 日常维护
```bash
# 查看系统状态
./status.sh

# 重启所有机器人
./restart_all.sh  

# 查看日志
tail -f submission_bot.log
tail -f publish_bot.log
tail -f control_bot.log

# 备份数据库
cp telegram_bot.db backup_$(date +%Y%m%d).db
```

### 更新系统
```bash
# 拉取最新代码
git pull

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启系统
./stop_all.sh
./start_all.sh
```

## 故障排除

### 机器人无响应
1. 检查进程: `ps aux | grep python`
2. 查看日志: `tail -n 50 *.log`
3. 重启机器人: `./restart_all.sh`

### 配置问题
1. 检查config.ini格式
2. 验证Token有效性
3. 确认频道/群组ID正确

### 权限问题
1. 确认机器人是群组管理员
2. 检查文件权限: `ls -la`
3. 重设权限: `chmod +x *.sh`

## 高级功能

### 多语言设置
- 用户可以设置个人语言偏好
- 支持中文、英语、日语、韩语等12种语言
- 自动时区转换

### 性能监控
- 查看数据库性能
- 监控内存使用
- 异步任务队列状态

### 实时通知
- 系统状态变化通知
- 错误告警通知
- 管理员操作通知

## 获取支持

如需更多帮助，请：
- 📖 查看 [完整文档](https://github.com/TPE1314/sgr/blob/main/README.md)
- 🐛 提交 [Issue](https://github.com/TPE1314/sgr/issues) 
- ⭐ Star [项目仓库](https://github.com/TPE1314/sgr)
- 💡 提出 [功能建议](https://github.com/TPE1314/sgr/issues/new)

---

**项目地址**: https://github.com/TPE1314/sgr