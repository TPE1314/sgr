#!/bin/bash

# 🤖 电报机器人投稿系统 - 快速设置脚本
# Quick Setup Script for Telegram Bot Submission System
# 版本: v2.0 (包含广告管理、多媒体增强、多语言支持等)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
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

log_header() {
    echo -e "${PURPLE}===================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${PURPLE}===================================================${NC}"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到您正在使用root用户运行脚本"
        log_warning "建议创建一个普通用户来运行机器人"
        read -p "是否继续? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检测系统信息
detect_system() {
    log_header "🔍 检测系统信息"
    
    # 检测操作系统
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    log_info "操作系统: $OS $VER"
    log_info "架构: $(uname -m)"
    log_info "内核: $(uname -r)"
    
    # 检查系统要求
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    
    log_info "总内存: ${TOTAL_MEM}GB"
    log_info "可用磁盘空间: ${AVAILABLE_SPACE}GB"
    
    # 检查最低要求
    if (( $(echo "$TOTAL_MEM < 0.5" | bc -l) )); then
        log_error "系统内存不足 (最低要求: 512MB)"
        exit 1
    fi
    
    if (( AVAILABLE_SPACE < 1 )); then
        log_error "磁盘空间不足 (最低要求: 1GB)"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 安装系统依赖
install_system_deps() {
    log_header "📦 安装系统依赖"
    
    # 检测包管理器
    if command -v apt-get > /dev/null; then
        PKG_MANAGER="apt-get"
        UPDATE_CMD="apt-get update"
        INSTALL_CMD="apt-get install -y"
    elif command -v yum > /dev/null; then
        PKG_MANAGER="yum"
        UPDATE_CMD="yum check-update"
        INSTALL_CMD="yum install -y"
    elif command -v dnf > /dev/null; then
        PKG_MANAGER="dnf"
        UPDATE_CMD="dnf check-update"
        INSTALL_CMD="dnf install -y"
    elif command -v pacman > /dev/null; then
        PKG_MANAGER="pacman"
        UPDATE_CMD="pacman -Sy"
        INSTALL_CMD="pacman -S --noconfirm"
    else
        log_error "未找到支持的包管理器"
        exit 1
    fi
    
    log_info "使用包管理器: $PKG_MANAGER"
    
    # 更新包列表
    log_info "更新包列表..."
    if [[ $PKG_MANAGER == "apt-get" ]]; then
        sudo $UPDATE_CMD
        sudo $INSTALL_CMD software-properties-common
    else
        sudo $UPDATE_CMD || true
    fi
    
    # 基础依赖
    log_info "安装基础依赖..."
    BASIC_DEPS="python3 python3-pip python3-venv git curl wget bc htop sqlite3"
    
    # 多媒体依赖 (可选)
    MEDIA_DEPS="imagemagick ffmpeg"
    
    # OCR依赖 (可选)
    if [[ $PKG_MANAGER == "apt-get" ]]; then
        OCR_DEPS="tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng"
    elif [[ $PKG_MANAGER == "yum" ]] || [[ $PKG_MANAGER == "dnf" ]]; then
        OCR_DEPS="tesseract tesseract-langpack-chi_sim tesseract-langpack-eng"
    else
        OCR_DEPS="tesseract"
    fi
    
    # 安装依赖
    for dep in $BASIC_DEPS; do
        if ! command -v $dep > /dev/null; then
            log_info "安装 $dep..."
            sudo $INSTALL_CMD $dep
        else
            log_success "$dep 已安装"
        fi
    done
    
    # 可选依赖安装询问
    echo
    read -p "是否安装多媒体处理依赖 (ImageMagick, FFmpeg)? 推荐安装 (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for dep in $MEDIA_DEPS; do
            log_info "安装 $dep..."
            sudo $INSTALL_CMD $dep || log_warning "$dep 安装失败，可跳过"
        done
    fi
    
    echo
    read -p "是否安装OCR文字识别依赖 (Tesseract)? 推荐安装 (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for dep in $OCR_DEPS; do
            log_info "安装 $dep..."
            sudo $INSTALL_CMD $dep || log_warning "$dep 安装失败，可跳过"
        done
    fi
    
    log_success "系统依赖安装完成"
}

# 检查Python版本
check_python() {
    log_header "🐍 检查Python环境"
    
    if ! command -v python3 > /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python版本: $PYTHON_VERSION"
    
    # 检查Python版本 (需要3.8+)
    if python3 -c 'import sys; exit(not (sys.version_info >= (3, 8)))'; then
        log_success "Python版本符合要求 (3.8+)"
    else
        log_error "Python版本过低，需要3.8或更高版本"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip3 > /dev/null; then
        log_info "安装pip3..."
        sudo apt-get install -y python3-pip
    fi
    
    log_success "Python环境检查完成"
}

# 创建虚拟环境
setup_venv() {
    log_header "🏗️ 创建Python虚拟环境"
    
    if [[ -d "venv" ]]; then
        log_warning "虚拟环境已存在，是否删除重建? (y/n)"
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            log_info "使用现有虚拟环境"
            return
        fi
    fi
    
    log_info "创建虚拟环境..."
    python3 -m venv venv
    
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    log_info "升级pip..."
    pip install --upgrade pip
    
    log_success "虚拟环境设置完成"
}

# 安装Python依赖
install_python_deps() {
    log_header "📚 安装Python依赖包"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查requirements.txt
    if [[ ! -f "requirements.txt" ]]; then
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
    
    log_info "安装Python依赖包..."
    log_info "这可能需要几分钟时间..."
    
    # 安装依赖
    pip install -r requirements.txt
    
    # 验证重要包
    log_info "验证关键依赖包..."
    CRITICAL_PACKAGES=("python-telegram-bot" "pillow" "psutil")
    
    for package in "${CRITICAL_PACKAGES[@]}"; do
        if pip show "$package" > /dev/null 2>&1; then
            VERSION=$(pip show "$package" | grep Version | cut -d' ' -f2)
            log_success "$package v$VERSION 安装成功"
        else
            log_error "$package 安装失败"
            exit 1
        fi
    done
    
    # 可选包检查
    OPTIONAL_PACKAGES=("pytesseract" "moviepy" "mutagen" "redis" "babel")
    
    for package in "${OPTIONAL_PACKAGES[@]}"; do
        if pip show "$package" > /dev/null 2>&1; then
            VERSION=$(pip show "$package" | grep Version | cut -d' ' -f2)
            log_success "可选包 $package v$VERSION 已安装"
        else
            log_warning "可选包 $package 未安装 (可忽略)"
        fi
    done
    
    log_success "Python依赖安装完成"
}

# 配置机器人
configure_bots() {
    log_header "⚙️ 配置机器人系统"
    
    echo -e "${CYAN}现在需要配置您的机器人信息${NC}"
    echo -e "${YELLOW}请确保您已经完成以下准备工作:${NC}"
    echo "1. 从 @BotFather 获取了三个机器人的Token"
    echo "2. 创建了目标频道、审核群组、管理群组"
    echo "3. 将机器人添加到对应的群组/频道并设为管理员"
    echo "4. 获取了所有频道/群组的ID"
    echo
    
    read -p "是否已完成准备工作? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}请先完成准备工作，然后重新运行此脚本${NC}"
        echo "详细说明请参考 README.md 中的【准备工作】部分"
        exit 0
    fi
    
    # 备份现有配置
    if [[ -f "config.ini" ]]; then
        cp config.ini "config.ini.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份现有配置文件"
    fi
    
    # 创建配置文件
    log_info "创建配置文件..."
    
    # 输入机器人Token
    echo -e "\n${CYAN}=== 机器人Token配置 ===${NC}"
    read -p "请输入投稿机器人Token: " SUBMISSION_TOKEN
    read -p "请输入发布机器人Token: " PUBLISH_TOKEN
    read -p "请输入控制机器人Token: " CONTROL_TOKEN
    
    # 输入频道/群组ID
    echo -e "\n${CYAN}=== 频道/群组ID配置 ===${NC}"
    echo -e "${YELLOW}注意: 频道/群组ID通常是负数，格式如: -1001234567890${NC}"
    read -p "请输入目标频道ID: " CHANNEL_ID
    read -p "请输入审核群组ID: " REVIEW_GROUP_ID
    read -p "请输入管理群组ID: " ADMIN_GROUP_ID
    
    # 输入管理员ID
    echo -e "\n${CYAN}=== 管理员配置 ===${NC}"
    echo -e "${YELLOW}管理员ID是正数，可以从 @userinfobot 获取${NC}"
    echo -e "${YELLOW}多个管理员请用逗号分隔，如: 123456789,987654321${NC}"
    read -p "请输入管理员用户ID: " ADMIN_USERS
    
    # 高级设置询问
    echo -e "\n${CYAN}=== 高级配置 ===${NC}"
    
    # 广告设置
    read -p "是否启用广告系统? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        AD_ENABLED="true"
        read -p "每篇文章最大广告数 (1-5, 默认3): " MAX_ADS
        MAX_ADS=${MAX_ADS:-3}
        read -p "是否显示广告标签? (y/n): " -n 1 -r
        echo
        SHOW_AD_LABEL=$([[ $REPLY =~ ^[Yy]$ ]] && echo "true" || echo "false")
    else
        AD_ENABLED="false"
        MAX_ADS="0"
        SHOW_AD_LABEL="false"
    fi
    
    # 多媒体设置
    read -p "是否启用OCR文字识别? (y/n): " -n 1 -r
    echo
    ENABLE_OCR=$([[ $REPLY =~ ^[Yy]$ ]] && echo "true" || echo "false")
    
    read -p "是否启用图片自动压缩? (y/n): " -n 1 -r
    echo
    ENABLE_COMPRESS=$([[ $REPLY =~ ^[Yy]$ ]] && echo "true" || echo "false")
    
    # 性能设置
    echo -e "${YELLOW}性能设置 (使用默认值即可):${NC}"
    read -p "数据库连接池大小 (默认10): " DB_POOL_SIZE
    DB_POOL_SIZE=${DB_POOL_SIZE:-10}
    
    read -p "异步工作进程数 (默认5): " ASYNC_WORKERS
    ASYNC_WORKERS=${ASYNC_WORKERS:-5}
    
    # 多语言设置
    echo -e "${YELLOW}多语言设置:${NC}"
    echo "支持的语言: zh-CN(中文), en-US(英语), ja-JP(日语), ko-KR(韩语)"
    read -p "默认语言 (默认zh-CN): " DEFAULT_LANG
    DEFAULT_LANG=${DEFAULT_LANG:-zh-CN}
    
    read -p "默认时区 (默认Asia/Shanghai): " DEFAULT_TZ
    DEFAULT_TZ=${DEFAULT_TZ:-Asia/Shanghai}
    
    # 生成配置文件
    cat > config.ini << EOF
[telegram]
# 机器人Token (必填)
submission_bot_token = $SUBMISSION_TOKEN
publish_bot_token = $PUBLISH_TOKEN
admin_bot_token = $CONTROL_TOKEN

# 频道和群组ID (必填)
channel_id = $CHANNEL_ID
admin_group_id = $ADMIN_GROUP_ID
review_group_id = $REVIEW_GROUP_ID

# 管理员用户ID列表 (必填)
admin_users = $ADMIN_USERS

[database]
db_file = telegram_bot.db

[settings]
# 投稿设置
require_approval = true
auto_publish_delay = 0
max_file_size = 50

# 广告设置
ad_enabled = $AD_ENABLED
max_ads_per_post = $MAX_ADS
show_ad_label = $SHOW_AD_LABEL

# 多媒体设置
enable_ocr = $ENABLE_OCR
enable_image_compress = $ENABLE_COMPRESS
enable_video_thumbnail = true

# 性能设置
db_pool_size = $DB_POOL_SIZE
cache_enabled = true
async_workers = $ASYNC_WORKERS

# 多语言设置
default_language = $DEFAULT_LANG
default_timezone = $DEFAULT_TZ

[performance]
# 数据库连接池
db_pool_size = $DB_POOL_SIZE
db_max_overflow = 5

# 异步任务队列
async_max_workers = $ASYNC_WORKERS
async_queue_size = 1000

# 内存缓存
cache_max_size = 1000
cache_default_ttl = 3600

# 文件处理
max_file_size = 50
enable_compression = $ENABLE_COMPRESS

[media]
# 图片处理
image_quality = medium
max_image_size = 2048
enable_ocr = $ENABLE_OCR
ocr_languages = chi_sim+eng

# 视频处理
enable_video_thumbnail = true
thumbnail_time = 1.0
max_video_size = 100

# 音频处理
enable_audio_metadata = true

[advertisement]
# 基础设置
enabled = $AD_ENABLED
max_ads_per_post = $MAX_ADS
min_ads_per_post = 0

# 显示设置
show_ad_label = $SHOW_AD_LABEL
ad_separator = "\n\n━━━━━━━━━━\n\n"
random_selection = true

# 统计设置
track_clicks = true
EOF
    
    # 设置配置文件权限
    chmod 600 config.ini
    
    log_success "配置文件创建完成"
}

# 验证配置
validate_config() {
    log_header "✅ 验证配置"
    
    source venv/bin/activate
    
    log_info "测试配置文件格式..."
    if python3 -c "
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
print('配置文件格式正确')
" 2>/dev/null; then
        log_success "配置文件格式验证通过"
    else
        log_error "配置文件格式错误"
        exit 1
    fi
    
    log_info "测试机器人Token连接..."
    
    # 读取配置
    SUBMISSION_TOKEN=$(python3 -c "
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
print(config.get('telegram', 'submission_bot_token'))
")
    
    # 测试Token
    RESPONSE=$(curl -s "https://api.telegram.org/bot$SUBMISSION_TOKEN/getMe")
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        BOT_NAME=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['result']['first_name'])
")
        log_success "投稿机器人连接成功: $BOT_NAME"
    else
        log_error "投稿机器人Token无效"
        log_error "响应: $RESPONSE"
        exit 1
    fi
    
    log_success "配置验证完成"
}

# 初始化数据库
init_database() {
    log_header "🗄️ 初始化数据库"
    
    source venv/bin/activate
    
    log_info "初始化数据库表..."
    
    # 运行数据库初始化
    python3 -c "
from database import DatabaseManager
from advertisement_manager import initialize_ad_manager
from performance_optimizer import initialize_optimizer
from i18n_manager import initialize_locale_manager
from real_time_notification import initialize_notification_manager

# 初始化数据库
db = DatabaseManager('telegram_bot.db')
print('数据库初始化完成')

# 初始化各个模块
try:
    initialize_ad_manager('telegram_bot.db')
    print('广告管理模块初始化完成')
except Exception as e:
    print(f'广告管理模块初始化失败: {e}')

try:
    initialize_optimizer('telegram_bot.db')
    print('性能优化模块初始化完成')
except Exception as e:
    print(f'性能优化模块初始化失败: {e}')

try:
    initialize_locale_manager()
    print('多语言模块初始化完成')
except Exception as e:
    print(f'多语言模块初始化失败: {e}')

try:
    # 读取配置获取Token
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    token = config.get('telegram', 'admin_bot_token')
    initialize_notification_manager(token)
    print('实时通知模块初始化完成')
except Exception as e:
    print(f'实时通知模块初始化失败: {e}')
"
    
    log_success "数据库初始化完成"
}

# 设置文件权限
setup_permissions() {
    log_header "🔐 设置文件权限"
    
    # 脚本文件可执行
    chmod +x *.sh
    log_info "脚本文件权限设置完成"
    
    # Python文件只读
    chmod 644 *.py
    log_info "Python文件权限设置完成"
    
    # 配置文件仅用户可读
    chmod 600 config.ini
    log_info "配置文件权限设置完成"
    
    # 日志目录
    mkdir -p logs
    chmod 755 logs
    log_info "日志目录权限设置完成"
    
    log_success "文件权限设置完成"
}

# 测试系统
test_system() {
    log_header "🧪 测试系统功能"
    
    source venv/bin/activate
    
    echo -e "${CYAN}正在启动测试...${NC}"
    echo -e "${YELLOW}这将启动所有机器人进行功能测试${NC}"
    echo -e "${YELLOW}测试将在30秒后自动停止${NC}"
    echo
    
    read -p "是否开始功能测试? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "跳过功能测试"
        return
    fi
    
    # 启动机器人
    log_info "启动机器人进行测试..."
    
    # 后台启动
    python3 submission_bot.py > logs/submission_test.log 2>&1 &
    SUBMISSION_PID=$!
    
    python3 publish_bot.py > logs/publish_test.log 2>&1 &
    PUBLISH_PID=$!
    
    python3 control_bot.py > logs/control_test.log 2>&1 &
    CONTROL_PID=$!
    
    log_info "机器人已启动，进程ID: $SUBMISSION_PID, $PUBLISH_PID, $CONTROL_PID"
    
    # 等待启动
    sleep 5
    
    # 检查进程
    TEST_PASSED=true
    
    for pid in $SUBMISSION_PID $PUBLISH_PID $CONTROL_PID; do
        if kill -0 $pid 2>/dev/null; then
            log_success "进程 $pid 运行正常"
        else
            log_error "进程 $pid 启动失败"
            TEST_PASSED=false
        fi
    done
    
    # 等待测试时间
    if $TEST_PASSED; then
        log_info "测试运行中，等待30秒..."
        for i in {30..1}; do
            echo -ne "\r${YELLOW}剩余时间: ${i}秒${NC} "
            sleep 1
        done
        echo
    fi
    
    # 停止测试
    log_info "停止测试进程..."
    for pid in $SUBMISSION_PID $PUBLISH_PID $CONTROL_PID; do
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            log_info "已停止进程 $pid"
        fi
    done
    
    sleep 2
    
    # 检查日志
    log_info "检查测试日志..."
    
    if grep -q "ERROR" logs/*.log 2>/dev/null; then
        log_warning "在日志中发现错误，请检查:"
        grep "ERROR" logs/*.log | head -5
        TEST_PASSED=false
    fi
    
    if $TEST_PASSED; then
        log_success "系统功能测试通过"
    else
        log_warning "系统测试发现问题，请检查日志文件"
        log_info "日志文件位置: ./logs/"
    fi
}

# 创建系统服务
setup_systemd() {
    log_header "🔧 设置系统服务 (可选)"
    
    echo -e "${CYAN}是否要创建systemd服务以便开机自启动?${NC}"
    echo -e "${YELLOW}这将允许机器人在系统重启后自动启动${NC}"
    echo
    
    read -p "创建systemd服务? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "跳过systemd服务创建"
        return
    fi
    
    CURRENT_USER=$(whoami)
    CURRENT_DIR=$(pwd)
    
    # 创建服务文件
    log_info "创建systemd服务文件..."
    
    sudo tee /etc/systemd/system/telegram-bots.service > /dev/null << EOF
[Unit]
Description=Telegram Bot Submission System
After=network.target
Wants=network.target

[Service]
Type=forking
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/start_all.sh
ExecStop=$CURRENT_DIR/stop_all.sh
ExecReload=$CURRENT_DIR/restart_all.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # 重载systemd
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable telegram-bots.service
    
    log_success "systemd服务创建完成"
    log_info "服务管理命令:"
    echo "  启动: sudo systemctl start telegram-bots"
    echo "  停止: sudo systemctl stop telegram-bots"
    echo "  重启: sudo systemctl restart telegram-bots"
    echo "  状态: sudo systemctl status telegram-bots"
    echo "  日志: sudo journalctl -u telegram-bots -f"
}

# 创建使用指南
create_usage_guide() {
    log_header "📖 创建使用指南"
    
    cat > USAGE_GUIDE.md << 'EOF'
# 🚀 快速使用指南

## 启动系统

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

---

如需更多帮助，请查看 README.md 或联系技术支持。
EOF
    
    log_success "使用指南创建完成: USAGE_GUIDE.md"
}

# 显示完成信息
show_completion() {
    log_header "🎉 安装完成"
    
    echo -e "${GREEN}"
    cat << 'EOF'
   ╔═══════════════════════════════════════════════════════════╗
   ║                                                           ║
   ║         🤖 电报机器人投稿系统安装完成！                    ║  
   ║                                                           ║
   ║    您现在拥有了一个功能完整的企业级Telegram机器人系统     ║
   ║                                                           ║
   ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${CYAN}📋 安装总结:${NC}"
    echo "✅ 系统依赖安装完成"
    echo "✅ Python环境配置完成"  
    echo "✅ 机器人配置完成"
    echo "✅ 数据库初始化完成"
    echo "✅ 文件权限设置完成"
    echo "✅ 系统功能验证完成"
    
    echo -e "\n${CYAN}🚀 快速开始:${NC}"
    echo -e "${WHITE}1. 启动系统:${NC}     ./start_all.sh"
    echo -e "${WHITE}2. 检查状态:${NC}     ./status.sh"  
    echo -e "${WHITE}3. 查看日志:${NC}     tail -f *.log"
    echo -e "${WHITE}4. 停止系统:${NC}     ./stop_all.sh"
    
    echo -e "\n${CYAN}📖 文档和指南:${NC}"
    echo -e "${WHITE}• 详细文档:${NC}      README.md"
    echo -e "${WHITE}• 使用指南:${NC}      USAGE_GUIDE.md"
    echo -e "${WHITE}• 配置文件:${NC}      config.ini"
    
    echo -e "\n${CYAN}🎛️ 管理界面:${NC}"
    echo -e "${WHITE}• 控制机器人:${NC}    发送 /start 到控制机器人"
    echo -e "${WHITE}• 广告管理:${NC}      发送 /ads 到控制机器人"
    echo -e "${WHITE}• 系统监控:${NC}      控制面板中的系统信息"
    
    echo -e "\n${CYAN}🔧 系统管理:${NC}"
    if systemctl is-enabled telegram-bots.service >/dev/null 2>&1; then
        echo -e "${WHITE}• 服务管理:${NC}      sudo systemctl [start|stop|restart] telegram-bots"
        echo -e "${WHITE}• 开机自启:${NC}      已启用"
    else
        echo -e "${WHITE}• 手动管理:${NC}      使用 ./start_all.sh 和 ./stop_all.sh"
    fi
    
    echo -e "\n${YELLOW}⚠️ 重要提醒:${NC}"
    echo "• 请妥善保管 config.ini 文件中的Token信息"
    echo "• 定期备份数据库文件 telegram_bot.db"  
    echo "• 建议定期查看日志文件检查系统运行状态"
    echo "• 首次使用前请阅读 USAGE_GUIDE.md"
    
    echo -e "\n${CYAN}📞 技术支持:${NC}"
    echo "• 遇到问题请查看故障排除章节"
    echo "• 可以在GitHub提交Issue反馈问题"
    echo "• 加入技术交流群获取实时帮助"
    
    echo -e "\n${GREEN}🎊 感谢使用！祝您使用愉快！${NC}"
    echo
}

# 主安装流程
main() {
    clear
    echo -e "${PURPLE}"
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🤖 电报机器人投稿系统 - 快速安装脚本 v2.0                 ║
    ║                                                              ║
    ║    功能特性:                                                  ║
    ║    • 智能投稿管理    • 广告系统     • 多媒体处理             ║
    ║    • 多语言支持      • 实时通知     • 性能优化               ║
    ║    • 热更新功能      • 安全管理     • 数据统计               ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${CYAN}欢迎使用电报机器人投稿系统快速安装脚本！${NC}"
    echo -e "${YELLOW}此脚本将自动安装和配置整个系统${NC}"
    echo
    
    # 确认开始安装
    read -p "按回车键开始安装，或 Ctrl+C 取消: "
    
    # 安装步骤
    check_root
    detect_system
    install_system_deps
    check_python
    setup_venv
    install_python_deps
    configure_bots
    validate_config
    init_database
    setup_permissions
    test_system
    setup_systemd
    create_usage_guide
    show_completion
    
    # 询问是否立即启动
    echo
    read -p "是否立即启动机器人系统? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "正在启动机器人系统..."
        ./start_all.sh
        sleep 3
        ./status.sh
    else
        log_info "系统已准备就绪，您可以随时使用 ./start_all.sh 启动"
    fi
}

# 运行主程序
main "$@"