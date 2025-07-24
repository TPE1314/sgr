# 📦 安装教程

## 🚀 快速开始

### 前置要求
- Linux系统 (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- Python 3.8+
- 至少512MB内存和1GB磁盘空间
- sudo权限

### 📥 获取项目

#### 方法一：Git克隆 (推荐)
```bash
git clone https://github.com/TPE1314/sgr.git
cd sgr
```

#### 方法二：下载ZIP包
```bash
# 下载并解压ZIP包
wget https://github.com/TPE1314/sgr/archive/main.zip
unzip main.zip
cd sgr-main
```

#### 方法三：直接下载安装脚本
```bash
# 仅下载安装脚本 (最小化下载)
wget https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh
chmod +x quick_setup.sh
./quick_setup.sh
```

#### 方法四：一行命令安装
```bash
# 最快安装方式 (适合VPS/服务器)
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

## ⚡ 一键安装

### 🎯 使用一键安装脚本 (推荐)
```bash
# 1. 确保已进入项目目录
cd sgr

# 2. 给脚本执行权限
chmod +x quick_setup.sh

# 3. 运行一键安装
./quick_setup.sh
```

一键安装脚本会自动完成：
- ✅ 系统环境检测
- ✅ 依赖包自动安装
- ✅ Python环境配置
- ✅ 交互式配置向导
- ✅ 系统功能验证
- ✅ **自动启动机器人** (4种启动选项)

### 🚀 启动选项
安装完成后会提供以下启动方式：

1. **立即启动并在后台运行** (推荐)
   - 最适合生产环境
   - 系统自动在后台运行
   - 断开SSH连接后继续运行

2. **立即启动并查看实时状态**
   - 适合测试和调试
   - 可以看到实时运行状态
   - 按Ctrl+C退出监控

3. **稍后手动启动**
   - 先完成其他配置
   - 使用 `./bot_manager.sh start` 启动

4. **设置开机自启动**
   - 自动配置systemd服务
   - 服务器重启后自动启动
   - 进程监控和自动重启

### 🔧 手动安装

如果一键安装失败，可以选择手动安装：

#### 1. 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git sqlite3 \
                    imagemagick ffmpeg tesseract-ocr tesseract-ocr-chi-sim

# CentOS/RHEL
sudo yum install -y python3 python3-pip git sqlite ImageMagick ffmpeg \
                    tesseract tesseract-langpack-chi_sim

# Arch Linux
sudo pacman -S python python-pip git sqlite imagemagick ffmpeg \
               tesseract tesseract-data-chi_sim
```

#### 2. 创建Python环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装Python依赖
pip install -r requirements.txt
```

#### 3. 设置权限
```bash
chmod +x *.sh
chmod 600 config.ini  # 配置文件创建后
```

## ⚙️ 配置系统

### 🤖 创建Telegram机器人

1. 与 [@BotFather](https://t.me/BotFather) 对话
2. 创建三个机器人：
   ```
   /newbot
   投稿机器人名称 (如: MySubmissionBot)
   投稿机器人用户名 (如: my_submission_bot)
   
   /newbot  
   发布机器人名称 (如: MyPublishBot)
   发布机器人用户名 (如: my_publish_bot)
   
   /newbot
   控制机器人名称 (如: MyControlBot) 
   控制机器人用户名 (如: my_control_bot)
   ```
3. 保存三个机器人的Token

### 📢 创建频道和群组

1. **创建目标频道**: 用于发布审核通过的内容
2. **创建审核群组**: 管理员审核投稿的工作群
3. **创建管理群组**: 管理员接收系统通知
4. 将对应机器人加入各自的频道/群组并设为管理员
5. 获取频道/群组ID (转发消息给 [@userinfobot](https://t.me/userinfobot))

### 🔧 配置文件设置

#### 使用配置脚本 (推荐)
```bash
./setup_config.sh
```

#### 手动编辑配置
```bash
cp config.ini.example config.ini
nano config.ini
```

配置示例：
```ini
[telegram]
submission_bot_token = 1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
publish_bot_token = 1234567890:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
admin_bot_token = 1234567890:CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

channel_id = -1001234567890
admin_group_id = -1001234567891
review_group_id = -1001234567892

admin_users = 123456789,987654321

[database]
db_file = telegram_bot.db

[settings]
require_approval = true
auto_publish_delay = 0
max_file_size = 50
ad_enabled = true
max_ads_per_post = 3
show_ad_label = true
```

## 🚀 启动系统

### 🎛️ 统一管理工具 (推荐)
使用 `bot_manager.sh` 进行全面的系统管理：

```bash
# 🚀 基本操作
./bot_manager.sh start      # 启动所有机器人
./bot_manager.sh stop       # 停止所有机器人
./bot_manager.sh restart    # 重启所有机器人
./bot_manager.sh status     # 查看系统状态

# 📊 监控和日志
./bot_manager.sh monitor    # 实时监控状态 (3秒刷新)
./bot_manager.sh logs       # 查看最近日志
./bot_manager.sh logs -f    # 实时查看日志

# 🔧 系统维护
./bot_manager.sh backup     # 备份配置和数据
./bot_manager.sh restore    # 恢复配置
./bot_manager.sh update     # 更新系统
./bot_manager.sh help       # 查看帮助信息
```

### 📱 传统管理方式
```bash
# 启动所有机器人
./start_all.sh

# 检查运行状态
./status.sh

# 查看日志
tail -f logs/*.log

# 停止系统
./stop_all.sh
```

### 📊 系统状态示例
```
📊 电报机器人状态监控
==========================

🤖 机器人状态：
--------------------
📝 投稿机器人: 运行中 (PID: 12345, 内存: 25.3MB, CPU: 0.2%)
  📝 日志活跃 (最后更新: 2分钟前)

📢 发布机器人: 运行中 (PID: 12346, 内存: 28.1MB, CPU: 0.1%)
  📝 日志活跃 (最后更新: 1分钟前)

🎛️ 控制机器人: 运行中 (PID: 12347, 内存: 32.5MB, CPU: 0.3%)
  📝 日志活跃 (最后更新: 3分钟前)
```

## ✅ 验证安装

### 1. 测试投稿机器人
- 向投稿机器人发送测试消息
- 检查是否收到确认消息

### 2. 测试审核群组
- 查看审核群是否收到投稿通知
- 测试审核按钮功能

### 3. 测试发布功能
- 在审核群通过一个投稿
- 检查是否正确发布到频道

### 4. 测试控制面板
- 向控制机器人发送 `/start`
- 检查控制面板功能

## 🔧 系统服务 (可选)

### 设置开机自启动
```bash
# 创建systemd服务
sudo nano /etc/systemd/system/telegram-bots.service
```

服务文件内容：
```ini
[Unit]
Description=Telegram Bot Submission System
After=network.target

[Service]
Type=forking
User=your-username
WorkingDirectory=/path/to/sgr
ExecStart=/path/to/sgr/start_all.sh
ExecStop=/path/to/sgr/stop_all.sh
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

#### 1. 安装脚本失败
```bash
# 检查错误日志
cat logs/install_error_*.log

# 手动安装依赖
sudo apt install -y python3-dev build-essential

# 重新运行安装
./quick_setup.sh
```

#### 2. Python依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 清除缓存重新安装
pip cache purge
pip install -r requirements.txt --force-reinstall
```

#### 3. 机器人无响应
```bash
# 检查进程
ps aux | grep python

# 检查网络连接
ping api.telegram.org

# 重启机器人
./restart_all.sh
```

#### 4. 配置问题
```bash
# 验证配置文件
python3 -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print('配置文件正确')"

# 测试Token
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

### 日志分析
```bash
# 查看错误日志
grep -i error *.log

# 查看最近日志
tail -n 100 *.log

# 实时监控日志
tail -f *.log | grep -i error
```

## 📈 性能优化

### 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化Python性能
export PYTHONOPTIMIZE=1
export PYTHONUNBUFFERED=1
```

### 数据库优化
```bash
# 定期清理日志
sqlite3 telegram_bot.db "DELETE FROM ad_display_logs WHERE displayed_at < datetime('now', '-30 days');"

# 优化数据库
sqlite3 telegram_bot.db "VACUUM;"
```

## 🔄 更新系统

### 更新代码
```bash
# 停止系统
./stop_all.sh

# 拉取最新代码
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启系统
./start_all.sh
```

### 版本检查
```bash
# 查看当前版本
git log --oneline -1

# 查看可用更新
git fetch
git log HEAD..origin/main --oneline
```

## 📞 获取帮助

如果遇到问题，请：

1. 📖 查看 [README.md](https://github.com/TPE1314/sgr/blob/main/README.md) 详细文档
2. 📋 查看 [USAGE_GUIDE.md](https://github.com/TPE1314/sgr/blob/main/USAGE_GUIDE.md) 使用指南
3. 🐛 提交 [Issue](https://github.com/TPE1314/sgr/issues) 反馈问题
4. 💡 提出 [功能建议](https://github.com/TPE1314/sgr/issues/new)
5. ⭐ Star [项目仓库](https://github.com/TPE1314/sgr) 支持项目

---

**项目地址**: https://github.com/TPE1314/sgr  
**作者**: TPE1314  
**许可证**: MIT License