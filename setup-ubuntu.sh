#!/bin/bash

# 电报多管理员客服系统 - Ubuntu一键部署脚本
# 支持 Ubuntu 20.04/22.04 LTS
# 执行方式: curl -sSL https://raw.githubusercontent.com/yourrepo/bot/main/setup-ubuntu.sh | sudo bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo bash $0"
        exit 1
    fi
}

# 检查Ubuntu版本
check_ubuntu_version() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法检测操作系统版本"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "此脚本仅支持Ubuntu系统"
        exit 1
    fi
    
    if [[ "$VERSION_ID" != "20.04" && "$VERSION_ID" != "22.04" ]]; then
        log_warning "此脚本主要针对Ubuntu 20.04/22.04 LTS优化，当前版本: $VERSION_ID"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "检测到Ubuntu $VERSION_ID"
}

# 更新系统
update_system() {
    log_info "更新系统包列表..."
    apt update -y
    
    log_info "升级系统包..."
    apt upgrade -y
    
    log_success "系统更新完成"
}

# 安装基础依赖
install_basic_deps() {
    log_info "安装基础依赖包..."
    
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "基础依赖安装完成"
}

# 安装Redis
install_redis() {
    log_info "安装Redis服务器..."
    
    # 添加Redis官方仓库
    curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
    
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/redis.list
    
    apt update -y
    apt install -y redis
    
    # 配置Redis
    cat > /etc/redis/redis.conf << EOF
# Redis配置文件
bind 127.0.0.1
port 6379
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF
    
    # 启动Redis服务
    systemctl enable redis-server
    systemctl start redis-server
    
    log_success "Redis安装完成并已启动"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 安装Python包
    python3 -m pip install \
        aiogram==3.0.0 \
        redis==4.5.5 \
        aiofiles==23.2.1 \
        apscheduler==3.10.4 \
        pillow==10.0.1 \
        opencv-python==4.8.1.78 \
        pytesseract==0.3.10 \
        moviepy==1.0.3 \
        mutagen==1.47.0 \
        psutil==5.9.6 \
        requests==2.31.0 \
        python-dotenv==1.0.0
    
    log_success "Python依赖安装完成"
}

# 创建系统用户
create_system_user() {
    log_info "创建系统用户..."
    
    if ! id "telebot" &>/dev/null; then
        useradd -r -s /bin/false -d /opt/telebot telebot
        log_success "创建用户 telebot"
    else
        log_info "用户 telebot 已存在"
    fi
    
    # 创建必要的目录
    mkdir -p /opt/telebot/{logs,uploads,backups,config}
    mkdir -p /var/log/telebot
    mkdir -p /tmp/telebot
    
    # 设置权限
    chown -R telebot:telebot /opt/telebot
    chown -R telebot:telebot /var/log/telebot
    chown -R telebot:telebot /tmp/telebot
    
    log_success "系统用户和目录创建完成"
}

# 部署应用文件
deploy_application() {
    log_info "部署应用程序..."
    
    # 复制应用文件
    cp bot.py /opt/telebot/
    cp config.ini /opt/telebot/config/
    
    # 设置权限
    chown telebot:telebot /opt/telebot/bot.py
    chown telebot:telebot /opt/telebot/config/config.ini
    chmod +x /opt/telebot/bot.py
    
    log_success "应用程序部署完成"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."
    
    cat > /etc/systemd/system/telebot.service << EOF
[Unit]
Description=Telegram Multi-Admin Support Bot
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=telebot
Group=telebot
WorkingDirectory=/opt/telebot
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/telebot
ExecStart=/usr/bin/python3 /opt/telebot/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telebot

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/telebot /var/log/telebot /tmp/telebot

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable telebot
    
    log_success "systemd服务创建完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 检查ufw是否安装
    if command -v ufw &> /dev/null; then
        # 允许SSH
        ufw allow ssh
        
        # 允许HTTP/HTTPS (如果需要webhook)
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # 允许Redis (仅本地)
        ufw allow from 127.0.0.1 to any port 6379
        
        # 启用防火墙
        ufw --force enable
        
        log_success "防火墙配置完成"
    else
        log_warning "ufw未安装，跳过防火墙配置"
    fi
}

# 创建定时备份任务
create_backup_cron() {
    log_info "创建定时备份任务..."
    
    # 创建备份脚本
    cat > /opt/telebot/backup.sh << 'EOF'
#!/bin/bash
# 备份脚本

BACKUP_DIR="/opt/telebot/backups"
DB_FILE="/opt/telebot/telebot.db"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份数据库
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_DIR/telebot_$DATE.db"
    gzip "$BACKUP_DIR/telebot_$DATE.db"
    echo "数据库备份完成: telebot_$DATE.db.gz"
fi

# 清理旧备份 (保留30天)
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete

echo "备份完成: $(date)"
EOF
    
    chmod +x /opt/telebot/backup.sh
    chown telebot:telebot /opt/telebot/backup.sh
    
    # 添加到crontab
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/telebot/backup.sh >> /var/log/telebot/backup.log 2>&1") | crontab -
    
    log_success "定时备份任务创建完成"
}

# 创建管理工具
create_management_tool() {
    log_info "创建管理工具..."
    
    cat > /usr/local/bin/telebot-cli << 'EOF'
#!/bin/bash
# 电报机器人管理工具

BOT_SERVICE="telebot"
BOT_DIR="/opt/telebot"
LOG_FILE="/var/log/telebot/telebot.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 显示帮助信息
show_help() {
    echo "电报多管理员客服系统 - 管理工具"
    echo ""
    echo "用法: telebot-cli [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  start     启动机器人服务"
    echo "  stop      停止机器人服务"
    echo "  restart   重启机器人服务"
    echo "  status    查看服务状态"
    echo "  logs      查看日志"
    echo "  monitor   实时监控面板"
    echo "  backup    手动备份"
    echo "  config    编辑配置文件"
    echo "  update    更新系统"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  telebot-cli start"
    echo "  telebot-cli monitor"
    echo "  telebot-cli logs --follow"
}

# 检查服务状态
check_service_status() {
    if systemctl is-active --quiet $BOT_SERVICE; then
        echo -e "${GREEN}✓${NC} 服务运行中"
        return 0
    else
        echo -e "${RED}✗${NC} 服务未运行"
        return 1
    fi
}

# 启动服务
start_service() {
    echo "启动机器人服务..."
    systemctl start $BOT_SERVICE
    sleep 2
    check_service_status
}

# 停止服务
stop_service() {
    echo "停止机器人服务..."
    systemctl stop $BOT_SERVICE
    sleep 2
    check_service_status
}

# 重启服务
restart_service() {
    echo "重启机器人服务..."
    systemctl restart $BOT_SERVICE
    sleep 2
    check_service_status
}

# 查看服务状态
show_status() {
    echo "=== 服务状态 ==="
    systemctl status $BOT_SERVICE --no-pager -l
    
    echo ""
    echo "=== 系统资源 ==="
    echo "内存使用: $(free -h | grep Mem | awk '{print $3"/"$2}')"
    echo "磁盘使用: $(df -h / | tail -1 | awk '{print $5}')"
    echo "CPU负载: $(uptime | awk -F'load average:' '{print $2}')"
    
    echo ""
    echo "=== 网络连接 ==="
    netstat -tlnp | grep :6379 || echo "Redis未运行"
}

# 查看日志
show_logs() {
    local follow=false
    
    # 检查是否使用--follow选项
    if [[ "$*" == *"--follow"* ]]; then
        follow=true
    fi
    
    if [ "$follow" = true ]; then
        echo "实时日志 (按Ctrl+C退出)..."
        tail -f $LOG_FILE
    else
        echo "最近100行日志:"
        tail -n 100 $LOG_FILE
    fi
}

# 实时监控面板
show_monitor() {
    echo "=== 实时监控面板 ==="
    echo "按Ctrl+C退出监控"
    echo ""
    
    while true; do
        clear
        echo "=== 电报机器人实时监控 ==="
        echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        
        # 服务状态
        echo "服务状态:"
        if systemctl is-active --quiet $BOT_SERVICE; then
            echo -e "  ${GREEN}✓ 机器人服务运行中${NC}"
        else
            echo -e "  ${RED}✗ 机器人服务未运行${NC}"
        fi
        
        if systemctl is-active --quiet redis-server; then
            echo -e "  ${GREEN}✓ Redis服务运行中${NC}"
        else
            echo -e "  ${RED}✗ Redis服务未运行${NC}"
        fi
        
        echo ""
        
        # 系统资源
        echo "系统资源:"
        echo "  内存: $(free -h | grep Mem | awk '{print $3"/"$2 " (" $3/$2*100 "%)"}')"
        echo "  磁盘: $(df -h / | tail -1 | awk '{print $3"/"$2 " (" $5 ")"}')"
        echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
        
        echo ""
        
        # 进程信息
        echo "进程信息:"
        ps aux | grep -E "(bot.py|redis)" | grep -v grep | head -5 | while read line; do
            pid=$(echo $line | awk '{print $2}')
            cpu=$(echo $line | awk '{print $3}')
            mem=$(echo $line | awk '{print $4}')
            cmd=$(echo $line | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
            echo "  PID:$pid CPU:${cpu}% MEM:${mem}% $cmd"
        done
        
        echo ""
        echo "按Ctrl+C退出监控"
        
        sleep 5
    done
}

# 手动备份
manual_backup() {
    echo "执行手动备份..."
    /opt/telebot/backup.sh
}

# 编辑配置文件
edit_config() {
    echo "编辑配置文件..."
    if command -v nano &> /dev/null; then
        nano $BOT_DIR/config/config.ini
    elif command -v vim &> /dev/null; then
        vim $BOT_DIR/config/config.ini
    else
        echo "未找到编辑器，请手动编辑: $BOT_DIR/config/config.ini"
    fi
}

# 更新系统
update_system() {
    echo "更新系统..."
    apt update -y
    apt upgrade -y
    
    echo "更新Python依赖..."
    python3 -m pip install --upgrade aiogram redis aiofiles
    
    echo "重启服务..."
    systemctl restart $BOT_SERVICE
    
    echo "更新完成"
}

# 主逻辑
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    monitor)
        show_monitor
        ;;
    backup)
        manual_backup
        ;;
    config)
        edit_config
        ;;
    update)
        update_system
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "未知命令: $1"
        echo "使用 'telebot-cli help' 查看帮助信息"
        exit 1
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/telebot-cli
    
    log_success "管理工具创建完成"
}

# 创建requirements.txt
create_requirements() {
    log_info "创建requirements.txt..."
    
    cat > /opt/telebot/requirements.txt << EOF
# 电报多管理员客服系统依赖
aiogram==3.0.0
redis==4.5.5
aiofiles==23.2.1
apscheduler==3.10.4
pillow==10.0.1
opencv-python==4.8.1.78
pytesseract==0.3.10
moviepy==1.0.3
mutagen==1.47.0
psutil==5.9.6
requests==2.31.0
python-dotenv==1.0.0
EOF
    
    chown telebot:telebot /opt/telebot/requirements.txt
    
    log_success "requirements.txt创建完成"
}

# 创建README文件
create_readme() {
    log_info "创建README文件..."
    
    cat > /opt/telebot/README.md << 'EOF'
# 电报多管理员客服系统

## 系统概述
这是一个支持多用户同时与单管理员实时对话的电报客服系统，具备富媒体处理、智能路由、负载均衡等功能。

## 快速开始

### 1. 配置机器人
编辑配置文件：
```bash
sudo telebot-cli config
```

在 `config.ini` 中设置你的机器人Token：
```ini
[BOT]
token = YOUR_BOT_TOKEN_HERE
```

### 2. 启动服务
```bash
sudo telebot-cli start
```

### 3. 查看状态
```bash
sudo telebot-cli status
```

### 4. 实时监控
```bash
sudo telebot-cli monitor
```

## 管理命令

- `telebot-cli start` - 启动服务
- `telebot-cli stop` - 停止服务
- `telebot-cli restart` - 重启服务
- `telebot-cli status` - 查看状态
- `telebot-cli logs` - 查看日志
- `telebot-cli monitor` - 实时监控
- `telebot-cli backup` - 手动备份
- `telebot-cli config` - 编辑配置
- `telebot-cli update` - 更新系统

## 文件结构
```
/opt/telebot/
├── bot.py              # 主程序
├── config/
│   └── config.ini      # 配置文件
├── logs/               # 日志目录
├── uploads/            # 上传文件目录
├── backups/            # 备份目录
└── requirements.txt    # Python依赖
```

## 日志文件
- 应用日志: `/var/log/telebot/telebot.log`
- 系统日志: `journalctl -u telebot`

## 故障排除

### 服务无法启动
1. 检查配置文件: `sudo telebot-cli config`
2. 查看日志: `sudo telebot-cli logs`
3. 检查权限: `ls -la /opt/telebot/`

### Redis连接失败
1. 检查Redis服务: `sudo systemctl status redis-server`
2. 重启Redis: `sudo systemctl restart redis-server`

## 技术支持
如有问题，请查看日志文件或联系技术支持。
EOF
    
    chown telebot:telebot /opt/telebot/README.md
    
    log_success "README文件创建完成"
}

# 最终配置和启动
final_setup() {
    log_info "执行最终配置..."
    
    # 设置环境变量
    echo "export TELEBOT_HOME=/opt/telebot" >> /etc/environment
    echo "export PATH=\$PATH:/opt/telebot" >> /etc/environment
    
    # 创建日志轮转配置
    cat > /etc/logrotate.d/telebot << EOF
/var/log/telebot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 telebot telebot
    postrotate
        systemctl reload telebot > /dev/null 2>&1 || true
    endscript
}
EOF
    
    # 启动服务
    log_info "启动机器人服务..."
    systemctl start telebot
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if systemctl is-active --quiet telebot; then
        log_success "机器人服务启动成功"
    else
        log_error "机器人服务启动失败"
        systemctl status telebot --no-pager -l
    fi
    
    log_success "部署完成！"
}

# 显示完成信息
show_completion_info() {
    echo ""
    echo "=========================================="
    echo "🎉 电报多管理员客服系统部署完成！"
    echo "=========================================="
    echo ""
    echo "📁 安装目录: /opt/telebot"
    echo "🔧 管理工具: telebot-cli"
    echo "📊 监控面板: telebot-cli monitor"
    echo "📝 配置文件: /opt/telebot/config/config.ini"
    echo ""
    echo "🚀 下一步操作:"
    echo "1. 编辑配置文件设置机器人Token:"
    echo "   sudo telebot-cli config"
    echo ""
    echo "2. 启动服务:"
    echo "   sudo telebot-cli start"
    echo ""
    echo "3. 查看状态:"
    echo "   sudo telebot-cli status"
    echo ""
    echo "4. 实时监控:"
    echo "   sudo telebot-cli monitor"
    echo ""
    echo "📚 更多信息请查看: /opt/telebot/README.md"
    echo ""
    echo "⚠️  重要提醒:"
    echo "- 请务必在配置文件中设置正确的机器人Token"
    echo "- 定期检查日志和系统状态"
    echo "- 建议启用防火墙保护系统安全"
    echo ""
}

# 主函数
main() {
    echo "🚀 开始部署电报多管理员客服系统..."
    echo "=========================================="
    echo ""
    
    # 执行部署步骤
    check_root
    check_ubuntu_version
    update_system
    install_basic_deps
    install_redis
    install_python_deps
    create_system_user
    deploy_application
    create_systemd_service
    configure_firewall
    create_backup_cron
    create_management_tool
    create_requirements
    create_readme
    final_setup
    
    # 显示完成信息
    show_completion_info
}

# 执行主函数
main "$@"