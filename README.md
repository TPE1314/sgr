# 电报机器人投稿系统 - Ubuntu 搭建教程

## 📋 系统概述

这是一个完整的电报机器人投稿系统，包含三个机器人：

- **🎯 投稿机器人** (`submission_bot.py`) - 接收用户投稿
- **📢 发布机器人** (`publish_bot.py`) - 审核投稿并发布到频道  
- **🎛️ 控制机器人** (`control_bot.py`) - 管理其他两个机器人

## 🚀 快速开始

### 1. 系统要求

- Ubuntu 18.04+ 
- Python 3.7+
- 至少 512MB RAM
- 至少 1GB 磁盘空间

### 2. 自动安装

```bash
# 克隆项目（如果是从Git仓库）
git clone <your-repo-url>
cd telegram-bot-system

# 或者直接上传所有文件到您的Ubuntu服务器

# 运行自动安装脚本
chmod +x install.sh
./install.sh
```

### 3. 手动安装

如果自动安装失败，可以手动执行以下步骤：

```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装Python和依赖
sudo apt install -y python3 python3-pip python3-venv git curl wget bc htop

# 安装Python包
pip3 install -r requirements.txt

# 设置脚本权限
chmod +x *.sh
```

## ⚙️ 配置步骤

### 1. 创建电报机器人

1. 联系 [@BotFather](https://t.me/BotFather) 创建三个机器人：
   ```
   /newbot
   ```
   - 投稿机器人 (例如: YourSubmissionBot)
   - 发布机器人 (例如: YourPublishBot)  
   - 控制机器人 (例如: YourControlBot)

2. 保存每个机器人的token

### 2. 创建频道和群组

1. **创建发布频道**
   - 创建一个新频道用于发布内容
   - 将发布机器人添加为管理员
   - 获取频道ID (可以转发频道消息到 [@userinfobot](https://t.me/userinfobot))

2. **创建审核群组**
   - 创建一个新群组用于审核投稿
   - 将发布机器人添加为管理员
   - 获取群组ID

3. **获取管理员用户ID**
   - 发送任意消息给 [@userinfobot](https://t.me/userinfobot) 获取您的用户ID

### 3. 编辑配置文件

编辑 `config.ini` 文件：

```bash
nano config.ini
```

填入实际的配置信息：

```ini
[telegram]
# 在这里填入你的机器人tokens
submission_bot_token = 1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
publish_bot_token = 1234567890:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
admin_bot_token = 1234567890:CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

# 频道和群组ID (注意：ID通常是负数，需要加-)
channel_id = -1001234567890
admin_group_id = -1001234567890
review_group_id = -1001234567890

# 管理员用户ID列表 (用逗号分隔)
admin_users = 123456789,987654321

[database]
db_file = telegram_bot.db

[settings]
# 是否需要管理员审核
require_approval = true
# 自动发布延迟时间(秒)
auto_publish_delay = 0
```

**重要提示：**
- Token格式：`数字:字母数字组合`
- 频道/群组ID通常是负数，格式：`-1001xxxxxxxxx`
- 用户ID是正数，格式：`xxxxxxxxx`

## 🎮 使用方法

### 启动系统

```bash
# 启动所有机器人
./start_all.sh

# 查看运行状态
./status.sh

# 查看日志
tail -f *.log
```

### 停止系统

```bash
# 停止所有机器人
./stop_all.sh
```

### 重启系统

```bash
# 重启所有机器人
./stop_all.sh
sleep 3
./start_all.sh
```

## 📱 机器人使用指南

### 投稿机器人使用

用户可以：
- 发送 `/start` 开始使用
- 直接发送文字、图片、视频、文档等内容进行投稿
- 使用 `/status` 查看投稿统计
- 使用 `/help` 获取帮助

### 发布机器人（审核功能）

管理员可以：
- 在审核群中看到新投稿
- 点击 ✅ 批准投稿（自动发布到频道）
- 点击 ❌ 拒绝投稿
- 点击 📊 查看用户统计
- 点击 🚫 封禁用户

### 控制机器人

管理员可以：
- 发送 `/start` 打开控制面板
- 使用 `/status` 查看机器人状态
- 使用 `/start_bots` 启动所有机器人
- 使用 `/stop_bots` 停止所有机器人
- 使用 `/restart_bots` 重启所有机器人
- 使用 `/logs` 查看日志
- 使用 `/system` 查看系统信息

## 🔧 管理命令

### 日常管理

```bash
# 查看机器人状态
./status.sh

# 实时监控（每5秒刷新）
watch -n 5 ./status.sh

# 查看日志
tail -f submission_bot.log
tail -f publish_bot.log  
tail -f control_bot.log

# 查看系统资源
htop
```

### 数据库管理

```bash
# 备份数据库
cp telegram_bot.db telegram_bot.db.backup

# 查看数据库内容（需要安装sqlite3）
sudo apt install sqlite3
sqlite3 telegram_bot.db
.tables
.quit
```

### 开机自启动（可选）

创建systemd服务：

```bash
# 创建服务文件
sudo nano /etc/systemd/system/telegram-bots.service
```

内容：
```ini
[Unit]
Description=Telegram Bots Service
After=network.target

[Service]
Type=forking
User=your-username
WorkingDirectory=/path/to/your/bot/directory
ExecStart=/path/to/your/bot/directory/start_all.sh
ExecStop=/path/to/your/bot/directory/stop_all.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bots.service
sudo systemctl start telegram-bots.service
```

## 🛠️ 故障排除

### 常见问题

1. **机器人无法启动**
   ```bash
   # 检查依赖
   pip3 show python-telegram-bot psutil
   
   # 检查配置文件
   python3 -c "from config_manager import ConfigManager; print('配置文件正常')"
   ```

2. **权限问题**
   ```bash
   # 检查文件权限
   ls -la *.py *.sh
   
   # 重新设置权限
   chmod +x *.sh
   chmod 644 *.py
   ```

3. **网络连接问题**
   ```bash
   # 测试网络连接
   curl -s https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

4. **数据库问题**
   ```bash
   # 检查数据库文件
   ls -la telegram_bot.db
   
   # 重新初始化（注意：会清空数据）
   rm telegram_bot.db
   python3 -c "from database import DatabaseManager; DatabaseManager('telegram_bot.db')"
   ```

### 日志查看

```bash
# 查看错误日志
grep -i error *.log

# 查看警告日志  
grep -i warning *.log

# 查看最新日志
tail -n 50 *.log
```

## 📊 监控与维护

### 性能监控

```bash
# 查看系统资源
./status.sh

# 查看进程详情
ps aux | grep python3

# 查看内存使用
free -h

# 查看磁盘使用
df -h
```

### 定期维护

建议每周执行：

```bash
# 备份数据库
cp telegram_bot.db "backup_$(date +%Y%m%d_%H%M%S).db"

# 清理旧日志（保留最近7天）
find . -name "*.log" -mtime +7 -delete

# 检查系统更新
sudo apt update && sudo apt list --upgradable
```

## 🔐 安全建议

1. **保护配置文件**
   ```bash
   chmod 600 config.ini
   ```

2. **定期更新**
   ```bash
   pip3 install --upgrade python-telegram-bot
   ```

3. **监控日志**
   - 定期检查错误日志
   - 关注异常登录尝试

4. **备份重要数据**
   - 定期备份数据库
   - 保存配置文件副本

## 📞 支持与帮助

如果遇到问题：

1. 查看本文档的故障排除部分
2. 检查日志文件中的错误信息
3. 确认配置文件格式正确
4. 验证网络连接正常

## 📝 更新日志

- v1.0.0 - 初始版本
  - 三个机器人完整功能
  - 审核群组支持
  - 完整的管理界面

## 📄 许可证

请根据您的需要添加适当的许可证信息。

---

🎉 **恭喜！您的电报机器人投稿系统已搭建完成！**