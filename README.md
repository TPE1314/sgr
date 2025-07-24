# 🤖 电报机器人投稿系统 v2.3.0 - 终极增强版

[![一键安装](https://img.shields.io/badge/一键安装-v2.3.0-brightgreen?style=for-the-badge&logo=rocket)](https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh)
[![版本](https://img.shields.io/badge/版本-v2.3.0-blue?style=for-the-badge&logo=github)](https://github.com/TPE1314/sgr/releases)
[![GitHub Stars](https://img.shields.io/github/stars/TPE1314/sgr?style=for-the-badge&logo=github)](https://github.com/TPE1314/sgr/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/TPE1314/sgr?style=for-the-badge&logo=github)](https://github.com/TPE1314/sgr/issues)

一个功能强大、企业级的Telegram机器人投稿管理系统，集成了**投稿管理**、**广告投放**、**多媒体处理**、**多语言支持**、**实时通知**等高级功能。

## 🆕 v2.3.0 更新亮点

- 🔧 **数据库问题终极修复**: 100%解决ModuleNotFoundError问题
- 🤖 **机器人代码自动修复**: 自动修复filters和f-string语法问题  
- 📊 **版本管理优化**: 统一版本显示格式(v2.3.0)，告别日期格式
- 🚀 **安装流程增强**: 三层保护机制，确保100%安装成功
- 🔄 **智能预修复**: 启动前自动检测并修复已知问题

> 🚀 **一行命令部署**: `curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash`

## ✨ 功能特点

### 🎯 核心功能
- 📝 **三机器人架构**: 投稿、发布、控制机器人分工协作
- 👥 **审核群组**: 专业的投稿审核工作流
- 🔄 **热更新**: 支持配置文件和代码热更新
- 👨‍💼 **动态管理员**: 支持动态添加/移除管理员
- 📱 **多文件类型**: 文字、图片、视频、音频、文档等

### 🚀 高级功能
- 📢 **智能广告系统**: 自动在内容中插入1-3条广告
- 🎨 **多媒体增强**: 图片压缩、OCR识别、视频缩略图
- 🌍 **多语言界面**: 支持12种语言，自动时区处理
- 🔔 **实时通知系统**: 跨机器人事件通知
- ⚡ **性能优化**: 数据库连接池、异步队列、内存缓存
- 🔄 **一键更新**: Git拉取、依赖更新、系统备份
- 📁 **文件更新**: 直接发送代码文件更新系统

### 📊 管理功能
- 📈 **数据统计**: 投稿统计、广告效果分析
- 🛡️ **安全防护**: 用户封禁、权限管理、操作日志
- 💾 **数据备份**: 自动备份、版本控制、回滚功能
- 🔍 **智能监控**: 系统状态、性能监控、错误告警

## 🏗️ 系统架构

```
                    电报机器人投稿系统架构图
    ┌─────────────────────────────────────────────────────────────┐
    │                        用户端                                │
    └─────────────────────┬───────────────────────────────────────┘
                          │ 投稿
    ┌─────────────────────▼───────────────────────────────────────┐
    │                  投稿机器人                                  │
    │  • 接收多媒体投稿    • OCR文字识别    • 自动标签生成         │
    └─────────────────────┬───────────────────────────────────────┘
                          │ 发送到审核群
    ┌─────────────────────▼───────────────────────────────────────┐
    │                   审核群组                                   │
    │  • 整合投稿信息      • 用户统计      • 一键审核             │
    └─────────────────────┬───────────────────────────────────────┘
                          │ 审核通过
    ┌─────────────────────▼───────────────────────────────────────┐
    │                  发布机器人                                  │
    │  • 自动添加广告      • 多媒体优化    • 频道发布             │
    └─────────────────────┬───────────────────────────────────────┘
                          │ 发布到频道
    ┌─────────────────────▼───────────────────────────────────────┐
    │                    目标频道                                  │
    │  • 优质内容展示      • 智能广告展示  • 用户订阅            │
    └─────────────────────────────────────────────────────────────┘
                          ▲
                          │ 管理控制
    ┌─────────────────────┴───────────────────────────────────────┐
    │                  控制机器人                                  │
    │  • 系统管理          • 广告管理      • 性能监控             │
    │  • 热更新            • 用户管理      • 数据统计             │
    └─────────────────────────────────────────────────────────────┘
```

## 💻 环境要求

### 系统要求
- **操作系统**: Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- **Python版本**: Python 3.8+
- **内存**: 最低512MB，推荐1GB+
- **存储**: 最低1GB可用空间
- **网络**: 稳定的互联网连接

### 依赖组件
- **必需**: SQLite3, Git, Python3-pip
- **可选**: Redis (缓存)、ImageMagick (图片处理)、FFmpeg (视频处理)

## 🚀 快速开始

> 💡 **只需一行命令即可完成部署！**

### ⚡ v2.3.0 超快安装 (推荐)
```bash
# v2.3.0 一行命令完成安装 🚀
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

**v2.3.0 安装特性**：
- 🔧 **自动修复数据库问题**: 无需手动干预
- 🤖 **智能代码修复**: 自动修复已知的语法问题
- 📊 **版本统一管理**: 使用v2.3.0标准版本格式
- 🚀 **三层保护机制**: 确保100%安装成功

### 📥 其他安装方式
```bash
# 方法一：克隆仓库
git clone https://github.com/TPE1314/sgr.git
cd sgr && chmod +x quick_setup.sh && ./quick_setup.sh

# 方法二：下载脚本
wget https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh
chmod +x quick_setup.sh && ./quick_setup.sh
```

v2.3.0一键安装脚本将自动完成：
- ✅ 系统环境检测和多平台适配
- ✅ 依赖包自动安装和版本检查
- ✅ Python虚拟环境配置
- ✅ **v2.3.0数据库问题终极修复**
- ✅ **机器人代码自动修复** (filters/f-string)
- ✅ 交互式配置向导
- ✅ 系统功能验证和语法检查
- ✅ **自动启动机器人** (可选择后台运行)
- ✅ **版本管理** (统一v2.3.0格式)

## 🎛️ 系统管理

### 📊 统一管理工具
安装完成后，使用 `bot_manager.sh` 进行全面的系统管理：

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
./bot_manager.sh install    # 重新运行安装脚本
./bot_manager.sh help       # 查看帮助信息
```

### 🚀 启动选项
安装完成后提供4种启动方式：

1. **立即启动并在后台运行** (推荐) - 最常用的生产环境选项
2. **立即启动并查看实时状态** - 适合测试和调试
3. **稍后手动启动** - 先完成其他配置
4. **设置开机自启动** - 自动配置systemd服务

### 📱 传统管理方式
```bash
# 启动系统
./start_all.sh

# 查看状态
./status.sh

# 停止系统  
./stop_all.sh
```

### 🔄 开机自启动
```bash
# 配置systemd服务 (一键安装时选择选项4)
sudo systemctl enable telegram-bot-system

# 手动管理服务
sudo systemctl start telegram-bot-system    # 启动服务
sudo systemctl stop telegram-bot-system     # 停止服务
sudo systemctl status telegram-bot-system   # 查看状态
sudo systemctl restart telegram-bot-system  # 重启服务
```

### 📋 准备工作

在运行安装脚本之前，请确保已准备：

#### 1. 创建Telegram机器人
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

#### 2. 准备频道和群组
1. **创建目标频道**: 用于发布审核通过的内容
2. **创建审核群组**: 管理员审核投稿的工作群
3. **创建管理群组**: 管理员接收系统通知
4. 将对应机器人加入各自的频道/群组并设为管理员
5. 获取频道/群组ID (转发消息给 [@userinfobot](https://t.me/userinfobot))

### 🛠️ 系统安装

#### 方法一: 一键安装 (推荐) 🚀
```bash
# 1. 克隆仓库
git clone https://github.com/TPE1314/sgr.git
cd sgr

# 2. 运行一键安装脚本
chmod +x quick_setup.sh
./quick_setup.sh
```

#### 方法二: 直接下载安装 🌐
```bash
# 下载安装脚本并运行
wget https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh
chmod +x quick_setup.sh
./quick_setup.sh
```

#### 方法三: 一行命令安装 ⚡
```bash
# 下载并立即执行 (适合服务器环境)
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

#### 方法四: 手动安装
```bash
# 1. 克隆项目
git clone https://github.com/TPE1314/sgr.git
cd sgr

# 2. 更新系统
sudo apt update && sudo apt upgrade -y

# 3. 安装基础依赖
sudo apt install -y python3 python3-pip python3-venv git sqlite3 \
                    imagemagick ffmpeg tesseract-ocr tesseract-ocr-chi-sim

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 5. 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt

# 6. 设置权限
chmod +x *.sh
```

### ⚙️ 系统配置

#### 1. 基础配置
```bash
# 运行配置脚本
./setup_config.sh
```

按提示输入以下信息：
- 投稿机器人Token
- 发布机器人Token  
- 控制机器人Token
- 目标频道ID
- 审核群组ID
- 管理群组ID
- 管理员用户ID列表

#### 2. 高级配置 (可选)
编辑 `config.ini` 进行高级配置：

```ini
[telegram]
# 机器人Token (必填)
submission_bot_token = YOUR_SUBMISSION_BOT_TOKEN
publish_bot_token = YOUR_PUBLISH_BOT_TOKEN  
admin_bot_token = YOUR_ADMIN_BOT_TOKEN

# 频道和群组ID (必填)
channel_id = YOUR_CHANNEL_ID
admin_group_id = YOUR_ADMIN_GROUP_ID
review_group_id = YOUR_REVIEW_GROUP_ID

# 管理员用户ID列表 (必填)
admin_users = 123456789,987654321

[database]
db_file = telegram_bot.db

[settings]
# 投稿设置
require_approval = true
auto_publish_delay = 0
max_file_size = 50

# 广告设置  
ad_enabled = true
max_ads_per_post = 3
show_ad_label = true

# 多媒体设置
enable_ocr = true
enable_image_compress = true
enable_video_thumbnail = true

# 性能设置
db_pool_size = 10
cache_enabled = true
async_workers = 5

# 多语言设置
default_language = zh-CN
default_timezone = Asia/Shanghai
```

### 🏃‍♂️ 启动系统

#### 使用管理脚本 (推荐)
```bash
# 启动所有机器人
./start_all.sh

# 检查运行状态
./status.sh

# 查看日志
tail -f *.log

# 停止所有机器人
./stop_all.sh
```

#### 手动启动
```bash
# 激活虚拟环境
source venv/bin/activate

# 启动投稿机器人
python submission_bot.py &

# 启动发布机器人  
python publish_bot.py &

# 启动控制机器人
python control_bot.py &
```

### ✅ 验证安装

1. **测试投稿机器人**: 向投稿机器人发送消息
2. **测试审核群组**: 检查审核群是否收到投稿
3. **测试发布功能**: 在审核群通过投稿，检查是否发布到频道
4. **测试控制面板**: 使用控制机器人查看系统状态

## 📚 详细使用教程

### 🎯 投稿机器人使用

#### 用户操作
```
1. 用户向投稿机器人发送内容
   • 文字消息: 直接发送文字
   • 图片: 发送图片 + 可选描述
   • 视频: 发送视频 + 可选描述  
   • 音频: 发送音频文件
   • 文档: 发送任意文档文件

2. 系统自动处理
   • 生成投稿ID
   • 提取媒体信息 (分辨率、时长等)
   • OCR文字识别 (图片)
   • 自动标签生成
   • 发送确认消息

3. 转发到审核群
   • 整合用户信息和投稿统计
   • 显示投稿内容和元数据
   • 提供审核操作按钮
```

#### 支持的文件类型
- 📝 **文字**: 纯文本消息
- 🖼️ **图片**: JPG, PNG, GIF, WebP (自动压缩)
- 🎬 **视频**: MP4, AVI, MOV (自动生成缩略图)
- 🎵 **音频**: MP3, WAV, OGG (提取元数据)
- 📁 **文档**: PDF, DOC, TXT (文件信息提取)
- 🎙️ **语音**: 语音消息
- 📹 **视频通话**: 圆形视频消息
- 🏷️ **贴纸**: Telegram贴纸
- 📍 **位置**: 地理位置信息
- 👤 **联系人**: 联系人卡片

### 👨‍⚖️ 审核群组使用

#### 审核界面说明
每个投稿在审核群显示为整合消息：

```
🔍 投稿审核 #123

👤 投稿用户信息：
• 用户名: @username  
• 用户ID: 123456789
• 状态: ✅ 正常

📊 用户投稿统计：
• 总投稿: 15 条
• 待审核: 2 条  
• 已发布: 10 条
• 已拒绝: 3 条
• 通过率: 66.7%

⏰ 投稿信息：
• 投稿时间: 2024-12-19 15:30:25
• 内容类型: 图片

📄 详情:
[投稿内容显示]

[✅ 通过] [❌ 拒绝] [👤 用户] [🚫 封禁] [🔄 刷新]
```

#### 审核操作
- ✅ **通过**: 投稿将自动发布到频道 (含广告)
- ❌ **拒绝**: 投稿被拒绝，可选填拒绝理由
- 👤 **用户统计**: 查看用户详细统计信息
- 🚫 **封禁用户**: 禁止用户继续投稿
- 🔄 **刷新**: 更新投稿信息和统计数据

### 📢 广告系统使用

#### 创建广告
使用控制机器人创建不同类型的广告：

```bash
# 文本广告
/create_ad text 欢迎广告
🎉 欢迎来到我们的频道！
订阅获取更多精彩内容。

# 链接广告
/create_ad link 官网推广 https://example.com  
🌐 访问我们的官方网站
获取更多信息和服务。

# 按钮广告
/create_ad button 特惠活动 https://sale.com 立即购买
🔥 限时特惠活动开始！
点击下方按钮立即参与。
```

#### 广告管理
1. **打开管理面板**: `/ads`
2. **查看广告列表**: 显示所有广告及状态
3. **编辑广告**: 修改内容、启用/暂停、删除
4. **查看统计**: 展示次数、点击率分析
5. **系统配置**: 调整展示策略和参数

#### 广告展示策略
- **位置选择**: 内容前、内容后、内容中间
- **数量控制**: 每篇最多3个广告
- **智能选择**: 基于权重和优先级的算法
- **内容匹配**: 可设置特定内容类型展示
- **效果统计**: 自动记录展示和点击数据

### 🎛️ 控制机器人使用

#### 主要功能
控制机器人提供强大的系统管理功能：

```
🎛️ 机器人控制面板

🤖 机器人管理:
[📊 机器人状态] [💻 系统信息]
[🚀 启动全部] [🛑 停止全部]  
[🔄 重启全部] [🔥 热更新]

👨‍💼 超级管理员功能:
[👨‍💼 管理员列表] [➕ 添加管理员]
[📋 操作日志] [⚙️ 系统配置]
[📁 文件更新历史] [🔄 一键更新]

📢 广告管理:
[📢 广告管理] [📊 广告统计]
```

#### 系统管理命令
```bash
# 基础命令
/start          # 显示控制面板
/status         # 查看系统状态
/help           # 显示帮助信息

# 机器人管理  
/restart_bots   # 重启机器人
/logs           # 查看日志文件

# 用户管理
/add_admin <用户ID> <权限>     # 添加管理员
/remove_admin <用户ID>        # 移除管理员

# 系统更新
/update         # 执行系统更新

# 广告管理
/ads            # 广告管理面板
/create_ad      # 创建广告
```

#### 热更新功能
控制机器人支持多种更新方式：

1. **配置热更新**: 修改config.ini后自动重载
2. **代码文件更新**: 直接发送.py文件更新代码
3. **批量更新**: 发送.zip压缩包批量更新
4. **Git更新**: 从代码仓库拉取最新版本
5. **依赖更新**: 自动更新Python依赖包

### 📊 数据统计功能

#### 投稿统计
- 总投稿数、待审核数、通过率
- 按时间段统计 (日/周/月)
- 按内容类型分类统计
- 用户活跃度排行

#### 广告统计  
- 总展示数、总点击数、整体CTR
- 按广告分类的详细数据
- 表现最佳广告排行
- 收入预估 (如果设置)

#### 系统统计
- 机器人运行状态和时长
- 数据库大小和性能指标
- 错误日志和异常统计
- 资源使用情况监控

### 🌍 多语言功能

#### 语言设置
系统支持12种语言，用户可以个性化设置：

**支持语言列表**:
- 🇨🇳 简体中文 (zh-CN)
- 🇹🇼 繁體中文 (zh-TW)  
- 🇺🇸 English (en-US)
- 🇯🇵 日本語 (ja-JP)
- 🇰🇷 한국어 (ko-KR)
- 🇷🇺 Русский (ru-RU)
- 🇫🇷 Français (fr-FR)
- 🇩🇪 Deutsch (de-DE)
- 🇪🇸 Español (es-ES)
- 🇧🇷 Português (pt-BR)
- 🇮🇹 Italiano (it-IT)
- 🇸🇦 العربية (ar-SA)

#### 时区处理
- **自动检测**: 根据用户地理位置推荐时区
- **手动设置**: 支持全球主要时区设置
- **智能转换**: 自动转换为用户本地时间
- **相对时间**: 显示 "刚刚"、"5分钟前" 等

### 🔧 高级配置

#### 性能优化配置
```ini
[performance]
# 数据库连接池
db_pool_size = 10
db_max_overflow = 5

# 异步任务队列
async_max_workers = 10  
async_queue_size = 1000

# 内存缓存
cache_max_size = 1000
cache_default_ttl = 3600

# 文件处理
max_file_size = 50
enable_compression = true
```

#### 多媒体处理配置
```ini
[media]
# 图片处理
image_quality = medium
max_image_size = 2048
enable_ocr = true
ocr_languages = chi_sim+eng

# 视频处理  
enable_video_thumbnail = true
thumbnail_time = 1.0
max_video_size = 100

# 音频处理
enable_audio_metadata = true
```

#### 广告系统配置
```ini
[advertisement]
# 基础设置
enabled = true
max_ads_per_post = 3
min_ads_per_post = 0

# 显示设置
show_ad_label = true
ad_separator = "\n\n━━━━━━━━━━\n\n"
random_selection = true

# 统计设置
track_clicks = true
```

## 🛠️ 运维管理

### 📊 监控和维护

#### 日志管理
```bash
# 查看实时日志
tail -f submission_bot.log
tail -f publish_bot.log  
tail -f control_bot.log

# 日志轮转设置
sudo nano /etc/logrotate.d/telegram-bots

# 清理旧日志
find . -name "*.log.*" -mtime +7 -delete
```

#### 数据库维护
```bash
# 数据库备份
sqlite3 telegram_bot.db ".backup backup_$(date +%Y%m%d).db"

# 数据库优化
sqlite3 telegram_bot.db "VACUUM;"

# 数据库检查
sqlite3 telegram_bot.db "PRAGMA integrity_check;"
```

#### 系统监控
```bash
# 检查机器人进程
ps aux | grep python | grep bot

# 检查内存使用
free -h

# 检查磁盘空间  
df -h

# 检查网络连接
netstat -tlnp | grep python
```

### 🔄 更新和升级

#### 常规更新
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启服务
./stop_all.sh
./start_all.sh
```

#### 大版本升级
```bash
# 1. 备份数据
cp telegram_bot.db telegram_bot_backup.db
cp config.ini config_backup.ini

# 2. 停止服务
./stop_all.sh

# 3. 更新代码
git fetch --all
git checkout v2.0  # 新版本标签

# 4. 数据库迁移
python migrate.py

# 5. 更新配置
./setup_config.sh

# 6. 启动服务
./start_all.sh
```

### 🛡️ 安全管理

#### 权限管理
- **超级管理员**: 完全控制权限
- **普通管理员**: 审核和基础管理权限
- **版主**: 仅审核权限
- **普通用户**: 投稿权限

#### 安全措施
- 定期更换机器人Token
- 限制管理员数量
- 监控异常操作
- 定期备份数据
- 使用HTTPS代理 (如需要)

### 📈 性能优化

#### 系统优化
```bash
# 优化系统参数
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'fs.file-max=65536' >> /etc/sysctl.conf

# 优化Python运行
export PYTHONOPTIMIZE=1
export PYTHONUNBUFFERED=1
```

#### 数据库优化
```sql
-- 创建索引
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_advertisements_status ON advertisements(status);
CREATE INDEX idx_ad_display_logs_ad_id ON ad_display_logs(ad_id);

-- 定期清理
DELETE FROM ad_display_logs WHERE displayed_at < datetime('now', '-30 days');
```

## 🐛 故障排除

### 常见问题

#### 1. 机器人无响应
```bash
# 检查进程
ps aux | grep bot

# 检查网络
ping api.telegram.org

# 查看错误日志
tail -n 50 *.log

# 重启机器人
./restart_all.sh
```

#### 2. 数据库错误
```bash
# 检查数据库文件
ls -la telegram_bot.db

# 修复数据库
sqlite3 telegram_bot.db "PRAGMA integrity_check;"

# 恢复备份
cp telegram_bot_backup.db telegram_bot.db
```

#### 3. 权限问题
```bash
# 检查文件权限
ls -la *.py *.sh

# 修复权限
chmod +x *.sh
chmod 644 *.py *.ini
```

#### 4. 依赖问题
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 更新pip
pip install --upgrade pip

# 清理缓存
pip cache purge
```

### 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 401 | Token无效 | 检查config.ini中的Token |
| 403 | 权限不足 | 确认机器人是群组管理员 |
| 404 | 找不到用户/群组 | 检查ID是否正确 |
| 429 | 请求过于频繁 | 等待后重试，检查是否有循环 |
| 500 | 服务器错误 | 检查网络连接，稍后重试 |

### 紧急恢复

#### 快速恢复步骤
```bash
# 1. 停止所有服务
./stop_all.sh

# 2. 恢复配置文件
cp config_backup.ini config.ini

# 3. 恢复数据库
cp telegram_bot_backup.db telegram_bot.db

# 4. 重新启动
./start_all.sh

# 5. 验证功能
./status.sh
```

## 📞 技术支持

### 获取帮助
- 📖 **文档**: 查看本README文档
- 🐛 **Issue**: [提交问题](https://github.com/TPE1314/sgr/issues)
- 💡 **功能建议**: [提出新功能想法](https://github.com/TPE1314/sgr/issues/new)
- 📞 **技术支持**: 通过GitHub Issues获取帮助

### 贡献代码
欢迎提交Pull Request改进系统：
1. Fork项目: [TPE1314/sgr](https://github.com/TPE1314/sgr)
2. 创建功能分支
3. 提交修改
4. 发起Pull Request

### 版本更新通知
- 关注GitHub Releases: [TPE1314/sgr](https://github.com/TPE1314/sgr/releases)
- ⭐ Star 本项目获取更新通知
- 📢 关注作者动态

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢以下开源项目的支持：
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Pillow](https://github.com/python-pillow/Pillow)  
- [SQLite](https://www.sqlite.org/)

---

**🎉 现在您已经拥有了一个功能完整的企业级Telegram机器人系统！**

如有任何问题，请随时联系技术支持。祝您使用愉快！ 🚀