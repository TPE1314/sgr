# 🚀 电报多管理员客服系统

一个功能强大的电报多管理员客服系统，支持多用户同时与单管理员实时对话，具备富媒体处理、智能路由、负载均衡等企业级功能。

## ✨ 核心特性

- 🔥 **高并发支持**: 支持50+用户同时与单管理员对话
- 🎯 **智能路由**: 自动分配会话，负载均衡
- 📱 **富媒体支持**: 图片、视频、文档、语音全支持
- 🚀 **一键部署**: Ubuntu系统一键安装部署
- 📊 **实时监控**: 内置监控面板和性能指标
- 🔒 **安全可靠**: 病毒扫描、内容过滤、权限管理
- 🌐 **多语言**: 支持国际化
- 📈 **可扩展**: 模块化设计，易于扩展

## 🏗️ 系统架构

```
用户 → 会话路由 → 管理员分配 → 消息处理 → 媒体处理 → 存储
  ↓
Redis缓存 ← 数据库 ← 日志记录 ← 监控统计
```

## 📋 系统要求

- **操作系统**: Ubuntu 20.04/22.04 LTS (推荐)
- **Python**: 3.10+
- **内存**: 最低 2GB，推荐 4GB+
- **存储**: 最低 10GB，推荐 20GB+
- **网络**: 稳定的互联网连接

## 🚀 快速开始

### 方法1: 一键部署 (推荐)

```bash
# 下载并执行部署脚本
curl -sSL https://raw.githubusercontent.com/yourrepo/bot/main/setup-ubuntu.sh | sudo bash
```

### 方法2: 手动安装

```bash
# 1. 克隆项目
git clone https://github.com/yourrepo/telegram-support-bot.git
cd telegram-support-bot

# 2. 快速启动
chmod +x quick_start.sh
./quick_start.sh
```

### 方法3: Docker部署

```bash
# 构建镜像
docker build -t telebot .

# 运行容器
docker run -d --name telebot \
  -e BOT_TOKEN=your_token \
  -v $(pwd)/config:/opt/telebot/config \
  telebot
```

## ⚙️ 配置说明

### 1. 获取机器人Token

1. 在Telegram中联系 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 获取API Token

### 2. 编辑配置文件

```bash
sudo telebot-cli config
```

在 `config.ini` 中设置：

```ini
[BOT]
token = YOUR_BOT_TOKEN_HERE

[ADMINS]
support_team = 123456789,987654321
max_sessions_per_admin = 50
```

### 3. 启动服务

```bash
# 启动服务
sudo telebot-cli start

# 查看状态
sudo telebot-cli status

# 实时监控
sudo telebot-cli monitor
```

## 📱 使用方法

### 用户端

1. 在Telegram中搜索你的机器人
2. 发送 `/start` 开始会话
3. 发送消息、图片、视频等
4. 等待客服回复

### 管理员端

1. 在 `config.ini` 中添加管理员ID
2. 管理员会收到用户消息通知
3. 支持多会话标签式管理
4. 实时查看会话状态和统计

## 🔧 管理命令

```bash
# 服务管理
telebot-cli start      # 启动服务
telebot-cli stop       # 停止服务
telebot-cli restart    # 重启服务
telebot-cli status     # 查看状态

# 监控和日志
telebot-cli monitor    # 实时监控面板
telebot-cli logs       # 查看日志
telebot-cli logs --follow  # 实时日志

# 维护操作
telebot-cli backup     # 手动备份
telebot-cli config     # 编辑配置
telebot-cli update     # 更新系统
```

## 📊 性能测试

### 压力测试

```bash
# 设置环境变量
export BOT_TOKEN="your_bot_token"

# 运行压力测试
python3 stress_test.py --users 50 --duration 300
```

### 性能指标

| 场景 | 延迟 | 资源消耗 | 并发用户 |
|------|------|----------|----------|
| 1:1会话 | <100ms | 50MB RAM | 1 |
| 10:1并发 | <200ms | 200MB RAM | 10 |
| 50:1并发 | <500ms | 800MB RAM | 50 |
| 100:1并发 | <1s | 1.5GB RAM | 100 |

## 🏗️ 项目结构

```
telegram-support-bot/
├── bot.py                 # 主程序
├── config.ini             # 配置文件
├── requirements.txt        # Python依赖
├── setup-ubuntu.sh        # Ubuntu一键部署脚本
├── quick_start.sh         # 快速启动脚本
├── stress_test.py         # 压力测试脚本
├── uploads/               # 上传文件目录
├── logs/                  # 日志目录
├── backups/               # 备份目录
└── README.md              # 项目说明
```

## 🔌 扩展功能

### 1. GPT-4集成

```ini
[INTEGRATIONS]
enable_gpt4 = true
openai_api_key = your-api-key
```

### 2. 翻译服务

```ini
[INTEGRATIONS]
enable_translation = true
translation_api_key = your-api-key
```

### 3. 情感分析

```ini
[INTEGRATIONS]
enable_sentiment_analysis = true
sentiment_api_key = your-api-key
```

### 4. S3存储

```ini
[MEDIA]
enable_s3_storage = true
s3_endpoint = your-s3-endpoint
s3_access_key = your-access-key
s3_secret_key = your-secret-key
```

## 🐛 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   sudo telebot-cli logs
   sudo systemctl status telebot
   ```

2. **Redis连接失败**
   ```bash
   sudo systemctl status redis-server
   sudo systemctl restart redis-server
   ```

3. **权限问题**
   ```bash
   sudo chown -R telebot:telebot /opt/telebot
   sudo chmod +x /opt/telebot/bot.py
   ```

4. **配置文件错误**
   ```bash
   sudo telebot-cli config
   # 检查配置文件语法
   ```

### 日志位置

- 应用日志: `/var/log/telebot/telebot.log`
- 系统日志: `journalctl -u telebot`
- 备份日志: `/var/log/telebot/backup.log`

## 📈 监控和维护

### 系统监控

```bash
# 实时监控
sudo telebot-cli monitor

# 查看资源使用
htop
iotop
nethogs
```

### 自动备份

- 数据库每日自动备份
- 备份文件保留30天
- 支持手动备份: `sudo telebot-cli backup`

### 日志轮转

- 日志文件自动轮转
- 支持日志压缩
- 可配置保留天数

## 🔒 安全特性

- 文件病毒扫描
- 内容过滤
- 权限管理
- 防火墙配置
- 系统用户隔离
- 日志审计

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送分支: `git push origin feature/AmazingFeature`
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 技术支持

- 📧 邮箱: support@example.com
- 💬 讨论组: [Telegram Group](https://t.me/your_support_group)
- 📖 文档: [Wiki](https://github.com/yourrepo/bot/wiki)
- 🐛 问题反馈: [Issues](https://github.com/yourrepo/bot/issues)

## 🙏 致谢

感谢以下开源项目的支持：

- [aiogram](https://github.com/aiogram/aiogram) - 异步Telegram Bot框架
- [Redis](https://redis.io/) - 高性能缓存数据库
- [SQLite](https://www.sqlite.org/) - 轻量级数据库
- [Ubuntu](https://ubuntu.com/) - 优秀的Linux发行版

---

⭐ 如果这个项目对你有帮助，请给它一个星标！