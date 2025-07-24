# 🚀 一键安装指南

> 💡 **安装完成后支持自动启动机器人并在后台运行**，选择 "1) 立即启动并在后台运行" 即可！

## ⚡ 超快安装 (推荐)

### 方式1: 一行命令安装
```bash
# 适合服务器/VPS环境，最快安装方式
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### 方式2: 下载后安装
```bash
# 下载安装脚本
wget https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh

# 设置执行权限
chmod +x quick_setup.sh

# 运行安装
./quick_setup.sh
```

### 方式3: 克隆仓库安装
```bash
# 克隆完整项目
git clone https://github.com/TPE1314/sgr.git
cd sgr

# 运行安装脚本
chmod +x quick_setup.sh
./quick_setup.sh
```

## 🌐 国内用户加速

### 使用镜像加速 (中国大陆用户)
```bash
# 使用GitHub镜像 (如果GitHub访问困难)
curl -fsSL https://mirror.ghproxy.com/https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash

# 或使用GitCode镜像
wget https://gitcode.net/TPE1314/sgr/-/raw/main/quick_setup.sh
chmod +x quick_setup.sh
./quick_setup.sh
```

### 使用代理安装
```bash
# 如果有代理服务器
export https_proxy=http://your-proxy:port
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

## 🎯 不同环境安装

### Ubuntu/Debian 系统
```bash
# 更新系统包列表
sudo apt update

# 一键安装
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### CentOS/RHEL 系统
```bash
# 更新系统包
sudo yum update -y

# 一键安装
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### Arch Linux 系统
```bash
# 更新系统
sudo pacman -Syu

# 一键安装
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

## 🔧 自定义安装

### 指定安装目录
```bash
# 下载到指定目录
mkdir -p /opt/telegram-bots
cd /opt/telegram-bots
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### 静默安装模式
```bash
# 使用预设配置静默安装 (开发中)
export SILENT_INSTALL=true
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

## 📱 移动设备安装

### Android (Termux)
```bash
# 安装基础依赖
pkg update && pkg install python git wget curl

# 一键安装
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### iOS (iSH)
```bash
# 安装依赖
apk add python3 git wget curl

# 一键安装
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

## 🐳 容器化安装

### Docker 一键部署
```bash
# 使用Docker运行 (开发中)
docker run -d --name telegram-bots \
  -v $(pwd)/config:/app/config \
  tpe1314/sgr:latest
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  telegram-bots:
    image: tpe1314/sgr:latest
    container_name: telegram-bots
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    restart: unless-stopped
```

## ☁️ 云服务器快速部署

### 腾讯云 CVM
```bash
# 登录云服务器后执行
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### 阿里云 ECS
```bash
# 登录ECS实例后执行
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### AWS EC2
```bash
# SSH连接EC2后执行
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

### 华为云 ECS
```bash
# 登录华为云服务器后执行
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

## 🛡️ 安全安装

### 验证脚本完整性
```bash
# 下载脚本并验证
wget https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh
wget https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh.sha256

# 验证文件完整性 (可选)
sha256sum -c quick_setup.sh.sha256

# 查看脚本内容 (推荐)
less quick_setup.sh

# 确认无误后执行
chmod +x quick_setup.sh
./quick_setup.sh
```

### 离线安装包
```bash
# 下载完整项目包
wget https://github.com/TPE1314/sgr/archive/main.zip
unzip main.zip
cd sgr-main

# 运行离线安装
chmod +x quick_setup.sh
./quick_setup.sh
```

## 🔄 更新安装

### 更新到最新版本
```bash
# 进入项目目录
cd sgr

# 拉取最新代码
git pull origin main

# 重新运行安装脚本
./quick_setup.sh
```

### 强制重新安装
```bash
# 删除旧版本
rm -rf sgr/

# 重新安装
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash
```

## 🆘 安装故障排除

### 网络连接问题
```bash
# 测试GitHub连接
curl -I https://github.com

# 测试raw.githubusercontent.com连接
curl -I https://raw.githubusercontent.com

# 使用代理或镜像
export https_proxy=http://proxy:port
```

### 权限问题
```bash
# 确保有执行权限
chmod +x quick_setup.sh

# 检查sudo权限
sudo -v
```

### Python环境问题
```bash
# 检查Python版本
python3 --version

# 手动安装Python (Ubuntu)
sudo apt install -y python3 python3-pip python3-venv
```

## 🚀 安装完成后

### 🎯 自动启动选项
安装完成后，脚本会提供4种启动方式：

1. **立即启动并在后台运行** (推荐)
   - 💡 最适合生产环境
   - 🔄 系统自动在后台运行
   - 🌐 断开SSH连接后继续运行

2. **立即启动并查看实时状态**
   - 🔍 适合测试和调试
   - 📊 可以看到实时运行状态
   - ⌨️ 按Ctrl+C退出监控

3. **稍后手动启动**
   - ⏰ 先完成其他配置
   - 🎛️ 使用 `./bot_manager.sh start` 启动

4. **设置开机自启动**
   - 🔧 自动配置systemd服务
   - 🔄 服务器重启后自动启动
   - 🛡️ 进程监控和自动重启

### 🎛️ 系统管理
```bash
# 统一管理工具
./bot_manager.sh start      # 启动系统
./bot_manager.sh status     # 查看状态
./bot_manager.sh monitor    # 实时监控
./bot_manager.sh logs -f    # 实时日志
./bot_manager.sh help       # 帮助信息
```

## 📞 获取支持

如果安装过程中遇到问题：

1. 📖 查看 [完整安装教程](INSTALL.md)
2. 🐛 提交 [Issue](https://github.com/TPE1314/sgr/issues)
3. 💡 查看 [常见问题](README.md#故障排除)
4. ⭐ Star [项目](https://github.com/TPE1314/sgr) 获取更新

---

**项目地址**: https://github.com/TPE1314/sgr  
**一键安装**: `curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash`