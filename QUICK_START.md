# ⚡ 快速开始

## 🚀 3步完成部署

### 1. 获取项目
```bash
# 方法一：克隆仓库 (推荐)
git clone https://github.com/TPE1314/sgr.git
cd sgr

# 方法二：直接下载脚本
wget https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh
```

### 2. 一键安装
```bash
# 方法一：运行安装脚本
chmod +x quick_setup.sh
./quick_setup.sh

# 方法二：一行命令安装
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### 3. 启动系统

#### 🎯 自动启动 (推荐)
安装完成后会提供4种启动选项：
1. **立即启动并在后台运行** (推荐) ← 选择此项即自动运行！
2. 立即启动并查看实时状态
3. 稍后手动启动
4. 设置开机自启动

#### 📱 手动管理
```bash
# 使用统一管理工具
./bot_manager.sh start      # 启动系统
./bot_manager.sh status     # 查看状态
./bot_manager.sh monitor    # 实时监控

# 传统方式
./start_all.sh              # 启动所有机器人
./status.sh                 # 查看状态
```

## 📋 准备工作

安装前请准备：
- 3个Telegram机器人Token (从 [@BotFather](https://t.me/BotFather) 获取)
- 3个群组/频道ID (从 [@userinfobot](https://t.me/userinfobot) 获取)
- 管理员用户ID

## 📖 详细文档

- 📦 [完整安装教程](INSTALL.md)
- 📚 [详细文档](README.md)
- 🔧 [使用指南](USAGE_GUIDE.md)

## 🆘 需要帮助？

- 🐛 [提交Issue](https://github.com/TPE1314/sgr/issues)
- ⭐ [Star项目](https://github.com/TPE1314/sgr)

---
**项目地址**: https://github.com/TPE1314/sgr