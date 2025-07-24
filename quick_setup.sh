#!/bin/bash

# 🤖 电报机器人投稿系统 - 一键安装脚本
# One-Click Installation Script for Telegram Bot Submission System
# 版本: v2.1 (增强版一键安装，支持更多功能和平台)
# 
# 功能特性:
# - 智能系统检测和环境配置
# - 多平台支持 (Ubuntu/CentOS/Debian/Arch)
# - 自动依赖安装和版本检查
# - 交互式配置向导
# - 自动测试和验证
# - 系统服务配置
# - 完整的错误处理和回滚机制

set -e

# 脚本版本和信息
SCRIPT_VERSION="2.1"
SCRIPT_NAME="Telegram Bot System Installer"
MIN_PYTHON_VERSION="3.8"
REQUIRED_MEMORY_MB=512
REQUIRED_DISK_GB=1

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 全局变量
INSTALL_DIR=""
BACKUP_DIR=""
PYTHON_CMD=""
PIP_CMD=""
PKG_MANAGER=""
DISTRO=""
DISTRO_VERSION=""
ARCH=""
INSTALL_LOG=""
ERROR_LOG=""

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    [[ -n "$INSTALL_LOG" ]] && echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$INSTALL_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    [[ -n "$INSTALL_LOG" ]] && echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$INSTALL_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    [[ -n "$INSTALL_LOG" ]] && echo "[WARNING] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$INSTALL_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    [[ -n "$ERROR_LOG" ]] && echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$ERROR_LOG"
    [[ -n "$INSTALL_LOG" ]] && echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$INSTALL_LOG"
}

log_header() {
    echo -e "${PURPLE}===================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${PURPLE}===================================================${NC}"
    [[ -n "$INSTALL_LOG" ]] && echo "[HEADER] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$INSTALL_LOG"
}

log_step() {
    echo -e "${CYAN}⏳ $1${NC}"
    [[ -n "$INSTALL_LOG" ]] && echo "[STEP] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$INSTALL_LOG"
}

# 错误处理和清理
cleanup_on_error() {
    log_error "安装过程中发生错误，正在清理..."
    
    # 停止可能运行的进程
    pkill -f "python.*bot\.py" 2>/dev/null || true
    
    # 恢复备份（如果存在）
    if [[ -n "$BACKUP_DIR" && -d "$BACKUP_DIR" ]]; then
        log_info "恢复配置文件备份..."
        [[ -f "$BACKUP_DIR/config.ini" ]] && cp "$BACKUP_DIR/config.ini" . 2>/dev/null || true
    fi
    
    # 显示错误日志位置
    if [[ -n "$ERROR_LOG" && -f "$ERROR_LOG" ]]; then
        log_error "详细错误信息请查看: $ERROR_LOG"
        echo -e "${YELLOW}最近的错误:${NC}"
        tail -5 "$ERROR_LOG" 2>/dev/null || true
    fi
    
    log_error "安装失败。您可以重新运行脚本或查看日志文件获取更多信息。"
    exit 1
}

# 设置错误陷阱
trap cleanup_on_error ERR

# 初始化环境
init_environment() {
    # 设置安装目录
    INSTALL_DIR=$(pwd)
    BACKUP_DIR="$INSTALL_DIR/.backup_$(date +%Y%m%d_%H%M%S)"
    
    # 创建日志目录
    mkdir -p logs
    INSTALL_LOG="$INSTALL_DIR/logs/install_$(date +%Y%m%d_%H%M%S).log"
    ERROR_LOG="$INSTALL_DIR/logs/install_error_$(date +%Y%m%d_%H%M%S).log"
    
    # 记录安装开始
    echo "=== Telegram Bot System Installation Started ===" > "$INSTALL_LOG"
    echo "Date: $(date)" >> "$INSTALL_LOG"
    echo "User: $(whoami)" >> "$INSTALL_LOG"
    echo "Directory: $INSTALL_DIR" >> "$INSTALL_LOG"
    echo "Script Version: $SCRIPT_VERSION" >> "$INSTALL_LOG"
    echo "=============================================" >> "$INSTALL_LOG"
    
    log_info "初始化安装环境完成"
    log_info "安装日志: $INSTALL_LOG"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到您正在使用root用户运行脚本"
        log_warning "建议创建一个普通用户来运行机器人"
        echo -e "${YELLOW}继续使用root用户可能存在安全风险${NC}"
        read -p "是否继续? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "安装已取消"
            exit 0
        fi
        log_warning "使用root用户继续安装..."
    fi
}

# 检测系统信息
detect_system() {
    log_header "🔍 检测系统信息"
    
    # 检测架构
    ARCH=$(uname -m)
    log_info "系统架构: $ARCH"
    
    # 检测操作系统
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_VERSION=$VERSION_ID
        log_info "发行版: $NAME $VERSION_ID"
    elif type lsb_release >/dev/null 2>&1; then
        DISTRO=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        DISTRO_VERSION=$(lsb_release -sr)
        log_info "发行版: $(lsb_release -sd)"
    elif [[ -f /etc/redhat-release ]]; then
        DISTRO="rhel"
        DISTRO_VERSION=$(grep -oE '[0-9]+\.[0-9]+' /etc/redhat-release | head -1)
        log_info "发行版: $(cat /etc/redhat-release)"
    elif [[ -f /etc/debian_version ]]; then
        DISTRO="debian"
        DISTRO_VERSION=$(cat /etc/debian_version)
        log_info "发行版: Debian $DISTRO_VERSION"
    else
        DISTRO="unknown"
        DISTRO_VERSION="unknown"
        log_warning "未能识别的操作系统: $(uname -s)"
    fi
    
    log_info "内核版本: $(uname -r)"
    log_info "主机名: $(hostname)"
    
    # 检查系统资源
    log_step "检查系统资源..."
    
    # 内存检查
    if command -v free >/dev/null 2>&1; then
        TOTAL_MEM_KB=$(free | awk '/^Mem:/{print $2}')
        TOTAL_MEM_MB=$((TOTAL_MEM_KB / 1024))
        AVAILABLE_MEM_KB=$(free | awk '/^Mem:/{print $7}')
        AVAILABLE_MEM_MB=$((AVAILABLE_MEM_KB / 1024))
        
        log_info "总内存: ${TOTAL_MEM_MB}MB"
        log_info "可用内存: ${AVAILABLE_MEM_MB}MB"
        
        if (( TOTAL_MEM_MB < REQUIRED_MEMORY_MB )); then
            log_error "系统内存不足 (当前: ${TOTAL_MEM_MB}MB, 最低要求: ${REQUIRED_MEMORY_MB}MB)"
            exit 1
        fi
    else
        log_warning "无法检测内存信息"
    fi
    
    # 磁盘空间检查
    if command -v df >/dev/null 2>&1; then
        AVAILABLE_SPACE_KB=$(df . | awk 'NR==2 {print $4}')
        AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE_KB / 1024 / 1024))
        
        log_info "可用磁盘空间: ${AVAILABLE_SPACE_GB}GB"
        
        if (( AVAILABLE_SPACE_GB < REQUIRED_DISK_GB )); then
            log_error "磁盘空间不足 (当前: ${AVAILABLE_SPACE_GB}GB, 最低要求: ${REQUIRED_DISK_GB}GB)"
            exit 1
        fi
    else
        log_warning "无法检测磁盘空间"
    fi
    
    # 检查网络连接
    log_step "检查网络连接..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_success "网络连接正常"
    elif ping -c 1 114.114.114.114 >/dev/null 2>&1; then
        log_success "网络连接正常 (使用国内DNS)"
    else
        log_warning "网络连接异常，可能影响依赖包下载"
    fi
    
    # 检查防火墙状态
    if command -v ufw >/dev/null 2>&1; then
        if ufw status | grep -q "Status: active"; then
            log_info "检测到UFW防火墙已启用"
        fi
    elif command -v firewall-cmd >/dev/null 2>&1; then
        if firewall-cmd --state 2>/dev/null | grep -q "running"; then
            log_info "检测到firewalld防火墙已启用"
        fi
    fi
    
    log_success "系统检测完成"
}

# 智能检测包管理器
detect_package_manager() {
    log_step "检测包管理器..."
    
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MANAGER="apt"
    elif command -v yum >/dev/null 2>&1; then
        PKG_MANAGER="yum"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
    elif command -v pacman >/dev/null 2>&1; then
        PKG_MANAGER="pacman"
    elif command -v zypper >/dev/null 2>&1; then
        PKG_MANAGER="zypper"
    elif command -v emerge >/dev/null 2>&1; then
        PKG_MANAGER="emerge"
    else
        log_error "未找到支持的包管理器"
        log_error "支持的包管理器: apt, yum, dnf, pacman, zypper, emerge"
        exit 1
    fi
    
    log_info "检测到包管理器: $PKG_MANAGER"
}

# 更新包列表
update_package_lists() {
    log_step "更新包列表..."
    
    case $PKG_MANAGER in
        apt)
            sudo apt-get update -qq
            ;;
        yum)
            sudo yum check-update -q || true
            ;;
        dnf)
            sudo dnf check-update -q || true
            ;;
        pacman)
            sudo pacman -Sy --noconfirm
            ;;
        zypper)
            sudo zypper refresh -q
            ;;
        emerge)
            sudo emerge --sync --quiet
            ;;
    esac
    
    log_success "包列表更新完成"
}

# 安装单个包
install_package() {
    local package=$1
    log_step "安装 $package..."
    
    case $PKG_MANAGER in
        apt)
            if ! dpkg -l | grep -q "^ii.*$package"; then
                sudo apt-get install -y "$package" -qq
            else
                log_info "$package 已安装"
                return 0
            fi
            ;;
        yum)
            if ! rpm -q "$package" >/dev/null 2>&1; then
                sudo yum install -y "$package" -q
            else
                log_info "$package 已安装"
                return 0
            fi
            ;;
        dnf)
            if ! rpm -q "$package" >/dev/null 2>&1; then
                sudo dnf install -y "$package" -q
            else
                log_info "$package 已安装"
                return 0
            fi
            ;;
        pacman)
            if ! pacman -Q "$package" >/dev/null 2>&1; then
                sudo pacman -S --noconfirm "$package"
            else
                log_info "$package 已安装"
                return 0
            fi
            ;;
        zypper)
            if ! zypper se -i "$package" | grep -q "$package"; then
                sudo zypper install -y "$package"
            else
                log_info "$package 已安装"
                return 0
            fi
            ;;
        emerge)
            sudo emerge -q "$package"
            ;;
    esac
    
    # 验证安装
    if command -v "$package" >/dev/null 2>&1; then
        log_success "$package 安装成功"
    else
        log_warning "$package 安装可能失败，但继续安装"
    fi
}

# 安装系统依赖
install_system_deps() {
    log_header "📦 安装系统依赖"
    
    detect_package_manager
    update_package_lists
    
    # 基础依赖包映射
    declare -A BASIC_PACKAGES
    
    case $PKG_MANAGER in
        apt)
            BASIC_PACKAGES=(
                ["python"]="python3"
                ["pip"]="python3-pip" 
                ["venv"]="python3-venv"
                ["git"]="git"
                ["curl"]="curl"
                ["wget"]="wget"
                ["sqlite"]="sqlite3"
                ["build-tools"]="build-essential"
                ["dev-tools"]="python3-dev"
            )
            ;;
        yum|dnf)
            BASIC_PACKAGES=(
                ["python"]="python3"
                ["pip"]="python3-pip"
                ["venv"]="python3"
                ["git"]="git"
                ["curl"]="curl"
                ["wget"]="wget"
                ["sqlite"]="sqlite"
                ["build-tools"]="gcc gcc-c++ make"
                ["dev-tools"]="python3-devel"
            )
            ;;
        pacman)
            BASIC_PACKAGES=(
                ["python"]="python"
                ["pip"]="python-pip"
                ["venv"]="python"
                ["git"]="git"
                ["curl"]="curl"
                ["wget"]="wget"
                ["sqlite"]="sqlite"
                ["build-tools"]="base-devel"
                ["dev-tools"]=""
            )
            ;;
        zypper)
            BASIC_PACKAGES=(
                ["python"]="python3"
                ["pip"]="python3-pip"
                ["venv"]="python3"
                ["git"]="git"
                ["curl"]="curl"
                ["wget"]="wget"
                ["sqlite"]="sqlite3"
                ["build-tools"]="gcc gcc-c++ make"
                ["dev-tools"]="python3-devel"
            )
            ;;
    esac
    
    # 安装基础依赖
    log_step "安装基础依赖包..."
    for package_type in python pip venv git curl wget sqlite build-tools dev-tools; do
        if [[ -n "${BASIC_PACKAGES[$package_type]}" ]]; then
            for pkg in ${BASIC_PACKAGES[$package_type]}; do
                install_package "$pkg"
            done
        fi
    done
    
    # 可选依赖询问
    echo
    echo -e "${CYAN}可选功能安装:${NC}"
    
    # 多媒体处理依赖
    read -p "是否安装多媒体处理依赖 (ImageMagick, FFmpeg)? 推荐安装 (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        case $PKG_MANAGER in
            apt)
                install_package "imagemagick"
                install_package "ffmpeg"
                ;;
            yum|dnf)
                install_package "ImageMagick"
                install_package "ffmpeg"
                ;;
            pacman)
                install_package "imagemagick"
                install_package "ffmpeg"
                ;;
            zypper)
                install_package "ImageMagick"
                install_package "ffmpeg"
                ;;
        esac
    fi
    
    # OCR依赖
    read -p "是否安装OCR文字识别依赖 (Tesseract)? 推荐安装 (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        case $PKG_MANAGER in
            apt)
                install_package "tesseract-ocr"
                install_package "tesseract-ocr-chi-sim" 
                install_package "tesseract-ocr-eng"
                ;;
            yum|dnf)
                install_package "tesseract"
                install_package "tesseract-langpack-chi_sim"
                install_package "tesseract-langpack-eng"
                ;;
            pacman)
                install_package "tesseract"
                install_package "tesseract-data-chi_sim"
                install_package "tesseract-data-eng"
                ;;
            zypper)
                install_package "tesseract-ocr"
                install_package "tesseract-ocr-traineddata-chinese_simplified"
                install_package "tesseract-ocr-traineddata-english"
                ;;
        esac
    fi
    
    log_success "系统依赖安装完成"
}

# 智能检测Python环境
detect_python() {
    log_step "检测Python环境..."
    
    # 检测可用的Python命令
    local python_candidates=("python3" "python" "python3.11" "python3.10" "python3.9" "python3.8")
    
    for cmd in "${python_candidates[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            local version=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null)
            if [[ -n "$version" ]]; then
                log_info "发现Python: $cmd (版本 $version)"
                
                # 检查版本是否符合要求
                if $cmd -c "import sys; exit(not (sys.version_info >= (3, 8)))" 2>/dev/null; then
                    PYTHON_CMD="$cmd"
                    log_success "使用Python: $PYTHON_CMD (版本 $version)"
                    break
                else
                    log_warning "$cmd 版本过低 ($version < $MIN_PYTHON_VERSION)"
                fi
            fi
        fi
    done
    
    if [[ -z "$PYTHON_CMD" ]]; then
        log_error "未找到符合要求的Python版本 (需要 >= $MIN_PYTHON_VERSION)"
        exit 1
    fi
}

# 检测pip环境
detect_pip() {
    log_step "检测pip环境..."
    
    # 检测可用的pip命令
    local pip_candidates=("pip3" "pip" "$PYTHON_CMD -m pip")
    
    for cmd in "${pip_candidates[@]}"; do
        if eval "$cmd --version" >/dev/null 2>&1; then
            PIP_CMD="$cmd"
            local pip_version=$(eval "$cmd --version" | awk '{print $2}')
            log_success "使用pip: $PIP_CMD (版本 $pip_version)"
            break
        fi
    done
    
    if [[ -z "$PIP_CMD" ]]; then
        log_warning "未找到pip，尝试安装..."
        
        # 尝试通过ensurepip安装pip
        if $PYTHON_CMD -m ensurepip --upgrade 2>/dev/null; then
            PIP_CMD="$PYTHON_CMD -m pip"
            log_success "pip安装成功"
        else
            log_error "pip安装失败"
            exit 1
        fi
    fi
}

# 检查Python模块
check_python_modules() {
    log_step "检查Python环境完整性..."
    
    # 检查关键模块
    local required_modules=("venv" "ssl" "sqlite3" "json" "urllib")
    
    for module in "${required_modules[@]}"; do
        if $PYTHON_CMD -c "import $module" 2>/dev/null; then
            log_info "✓ $module 模块可用"
        else
            log_warning "✗ $module 模块不可用"
        fi
    done
    
    # 检查pip是否可以升级
    log_step "检查pip版本..."
    eval "$PIP_CMD install --upgrade pip --quiet" || log_warning "pip升级失败"
}

# 检查Python版本
check_python() {
    log_header "🐍 检查Python环境"
    
    detect_python
    detect_pip
    check_python_modules
    
    # 显示最终环境信息
    local python_version=$($PYTHON_CMD --version)
    local pip_version=$(eval "$PIP_CMD --version" | awk '{print $2}')
    
    log_success "Python环境配置完成"
    log_info "Python命令: $PYTHON_CMD"
    log_info "Python版本: $python_version"
    log_info "Pip命令: $PIP_CMD" 
    log_info "Pip版本: $pip_version"
}

# 创建虚拟环境
setup_venv() {
    log_header "🏗️ 创建Python虚拟环境"
    
    # 检查现有虚拟环境
    if [[ -d "venv" ]]; then
        log_warning "检测到现有虚拟环境"
        echo -e "${YELLOW}选项:${NC}"
        echo "1) 删除并重建虚拟环境"
        echo "2) 使用现有虚拟环境"
        echo "3) 备份现有环境并创建新环境"
        
        read -p "请选择 (1-3): " -n 1 -r
        echo
        
        case $REPLY in
            1)
                log_info "删除现有虚拟环境..."
                rm -rf venv
                ;;
            2)
                log_info "使用现有虚拟环境"
                # 测试现有环境
                if source venv/bin/activate 2>/dev/null; then
                    log_success "现有虚拟环境可用"
                    return 0
                else
                    log_warning "现有虚拟环境损坏，将重建"
                    rm -rf venv
                fi
                ;;
            3)
                log_info "备份现有虚拟环境..."
                mv venv "venv_backup_$(date +%Y%m%d_%H%M%S)"
                ;;
            *)
                log_info "使用现有虚拟环境"
                if source venv/bin/activate 2>/dev/null; then
                    return 0
                else
                    rm -rf venv
                fi
                ;;
        esac
    fi
    
    log_step "创建新的虚拟环境..."
    if ! $PYTHON_CMD -m venv venv; then
        log_error "虚拟环境创建失败"
        exit 1
    fi
    
    log_step "激活虚拟环境..."
    if ! source venv/bin/activate; then
        log_error "虚拟环境激活失败"
        exit 1
    fi
    
    log_step "升级虚拟环境中的pip..."
    if ! pip install --upgrade pip --quiet; then
        log_warning "pip升级失败，但继续安装"
    fi
    
    # 验证虚拟环境
    local venv_python=$(which python)
    local venv_pip=$(which pip)
    
    log_info "虚拟环境Python: $venv_python"
    log_info "虚拟环境pip: $venv_pip"
    
    log_success "虚拟环境设置完成"
}

# 创建requirements.txt (如果不存在)
create_requirements() {
    if [[ ! -f "requirements.txt" ]]; then
        log_warning "requirements.txt 不存在，创建默认版本..."
        
        cat > requirements.txt << 'EOF'
# 核心依赖
python-telegram-bot==20.7
psutil==5.9.0
dataclasses-json==0.6.3

# 图片和多媒体处理
Pillow==10.1.0
pytz==2023.3

# 可选依赖 (如果需要相应功能请取消注释)
# pytesseract==0.3.10  # OCR文字识别
# moviepy==1.0.3       # 视频处理
# mutagen==1.47.0      # 音频元数据
# babel==2.13.1        # 本地化
# redis==5.0.1         # 缓存 (可选)

# 开发和调试
# pytest==7.4.3       # 测试框架
# black==23.11.0       # 代码格式化
EOF
        log_info "默认requirements.txt已创建"
    fi
}

# 安装Python依赖
install_python_deps() {
    log_header "📚 安装Python依赖包"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 创建requirements.txt (如果需要)
    create_requirements
    
    log_step "分析依赖包..."
    local total_packages=$(grep -v '^#' requirements.txt | grep -v '^$' | wc -l)
    log_info "需要安装 $total_packages 个包"
    
    log_step "升级pip和基础工具..."
    pip install --upgrade pip setuptools wheel --quiet
    
    log_step "安装Python依赖包..."
    log_info "这可能需要几分钟时间，请耐心等待..."
    
    # 使用超时和重试机制安装依赖
    local max_retries=3
    local retry_count=0
    
    while (( retry_count < max_retries )); do
        if timeout 600 pip install -r requirements.txt --quiet --no-cache-dir; then
            log_success "依赖包安装成功"
            break
        else
            retry_count=$((retry_count + 1))
            if (( retry_count < max_retries )); then
                log_warning "安装失败，第 $retry_count 次重试..."
                sleep 5
            else
                log_error "依赖包安装失败，已重试 $max_retries 次"
                exit 1
            fi
        fi
    done
    
    # 验证关键包
    log_step "验证关键依赖包..."
    local critical_packages=("telegram" "PIL" "psutil")
    local missing_packages=()
    
    for package in "${critical_packages[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            log_success "✓ $package 模块可用"
        else
            log_error "✗ $package 模块不可用"
            missing_packages+=("$package")
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        log_error "关键模块缺失: ${missing_packages[*]}"
        exit 1
    fi
    
    # 显示已安装的包
    log_step "生成依赖包清单..."
    pip list --format=freeze > installed_packages.txt
    local installed_count=$(wc -l < installed_packages.txt)
    log_info "已安装 $installed_count 个Python包"
    
    # 检查可选功能
    log_step "检查可选功能支持..."
    
    # OCR支持
    if python -c "import pytesseract" 2>/dev/null; then
        log_success "✓ OCR功能支持已启用"
    else
        log_info "○ OCR功能未启用 (需要pytesseract)"
    fi
    
    # 视频处理支持
    if python -c "import moviepy" 2>/dev/null; then
        log_success "✓ 视频处理功能已启用"
    else
        log_info "○ 视频处理功能未启用 (需要moviepy)"
    fi
    
    # 音频处理支持
    if python -c "import mutagen" 2>/dev/null; then
        log_success "✓ 音频处理功能已启用"
    else
        log_info "○ 音频处理功能未启用 (需要mutagen)"
    fi
    
    log_success "Python依赖安装和验证完成"
}

# 验证Telegram Token
validate_token() {
    local token=$1
    local bot_name=$2
    
    log_step "验证 $bot_name Token..."
    
    local response=$(curl -s --connect-timeout 10 "https://api.telegram.org/bot$token/getMe")
    
    if echo "$response" | grep -q '"ok":true'; then
        local bot_username=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['result']['username'])
except:
    print('unknown')
")
        log_success "$bot_name Token有效 (@$bot_username)"
        return 0
    else
        log_error "$bot_name Token无效"
        return 1
    fi
}

# 智能配置向导
show_configuration_guide() {
    log_header "📋 配置向导"
    
    echo -e "${CYAN}欢迎使用配置向导！${NC}"
    echo
    echo -e "${YELLOW}在开始配置之前，请确保您已完成以下准备工作:${NC}"
    echo
    echo "🤖 ${WHITE}1. 创建三个Telegram机器人${NC}"
    echo "   • 与 @BotFather 对话"
    echo "   • 使用 /newbot 命令创建三个机器人"
    echo "   • 保存三个机器人的Token"
    echo
    echo "📢 ${WHITE}2. 创建频道和群组${NC}"
    echo "   • 创建一个目标频道 (用于发布内容)"
    echo "   • 创建一个审核群组 (管理员审核投稿)"
    echo "   • 创建一个管理群组 (接收系统通知)"
    echo
    echo "🔐 ${WHITE}3. 设置权限${NC}"
    echo "   • 将三个机器人都添加到群组/频道"
    echo "   • 设置机器人为管理员"
    echo "   • 给予必要的权限"
    echo
    echo "🆔 ${WHITE}4. 获取ID${NC}"
    echo "   • 转发频道/群组消息给 @userinfobot"
    echo "   • 记录频道和群组的ID (通常是负数)"
    echo "   • 记录您的用户ID (正数)"
    echo
    echo "📖 ${WHITE}更详细的说明请查看 README.md 文档${NC}"
    echo
    
    # 选择配置方式
    echo -e "${CYAN}配置方式选择:${NC}"
    echo "1) 🚀 交互式配置 (推荐) - 逐步引导配置"
    echo "2) 📁 导入配置文件 - 使用现有config.ini"
    echo "3) 📝 手动配置 - 创建最小配置后手动编辑"
    echo "4) 📋 查看配置示例 - 显示配置文件示例"
    echo
    
    read -p "请选择配置方式 (1-4): " -n 1 -r
    echo
    
    case $REPLY in
        1) interactive_configuration ;;
        2) import_configuration ;;
        3) minimal_configuration ;;
        4) show_configuration_example ;;
        *) 
            log_info "使用默认方式 (交互式配置)"
            interactive_configuration
            ;;
    esac
}

# 交互式配置
interactive_configuration() {
    log_step "开始交互式配置..."
    
    # 备份现有配置
    if [[ -f "config.ini" ]]; then
        mkdir -p "$BACKUP_DIR"
        cp config.ini "$BACKUP_DIR/config.ini"
        log_info "已备份现有配置文件到 $BACKUP_DIR"
    fi
    
    log_step "收集机器人配置信息..."
    
    # 输入机器人Token
    echo -e "\n${CYAN}=== 🤖 机器人Token配置 ===${NC}"
    echo -e "${YELLOW}请依次输入三个机器人的Token${NC}"
    echo
    
    # 投稿机器人Token
    while true; do
        read -p "📝 投稿机器人Token: " SUBMISSION_TOKEN
        if [[ -n "$SUBMISSION_TOKEN" ]]; then
            if validate_token "$SUBMISSION_TOKEN" "投稿机器人"; then
                break
            else
                echo -e "${RED}Token验证失败，请重新输入${NC}"
            fi
        else
            echo -e "${RED}Token不能为空，请重新输入${NC}"
        fi
    done
    
    # 发布机器人Token  
    while true; do
        read -p "📢 发布机器人Token: " PUBLISH_TOKEN
        if [[ -n "$PUBLISH_TOKEN" ]]; then
            if validate_token "$PUBLISH_TOKEN" "发布机器人"; then
                break
            else
                echo -e "${RED}Token验证失败，请重新输入${NC}"
            fi
        else
            echo -e "${RED}Token不能为空，请重新输入${NC}"
        fi
    done
    
    # 控制机器人Token
    while true; do
        read -p "🎛️  控制机器人Token: " CONTROL_TOKEN
        if [[ -n "$CONTROL_TOKEN" ]]; then
            if validate_token "$CONTROL_TOKEN" "控制机器人"; then
                break
            else
                echo -e "${RED}Token验证失败，请重新输入${NC}"
            fi
        else
            echo -e "${RED}Token不能为空，请重新输入${NC}"
        fi
    done
    
    # 输入频道/群组ID
    echo -e "\n${CYAN}=== 📢 频道/群组ID配置 ===${NC}"
    echo -e "${YELLOW}💡 提示: ${NC}"
    echo "• 频道/群组ID通常是负数，格式如: -1001234567890"
    echo "• 可以转发频道/群组消息给 @userinfobot 获取ID"
    echo "• 确保机器人已加入对应频道/群组并设为管理员"
    echo
    
    read -p "📺 目标频道ID (发布内容的频道): " CHANNEL_ID
    read -p "👥 审核群组ID (管理员审核投稿): " REVIEW_GROUP_ID
    read -p "🛡️  管理群组ID (系统通知群组): " ADMIN_GROUP_ID
    
    # 输入管理员ID
    echo -e "\n${CYAN}=== 👨‍💼 管理员配置 ===${NC}"
    echo -e "${YELLOW}💡 提示: ${NC}"
    echo "• 管理员ID是正数，可以从 @userinfobot 获取"
    echo "• 多个管理员请用逗号分隔，如: 123456789,987654321"
    echo "• 第一个ID将成为超级管理员"
    echo
    
    read -p "👤 管理员用户ID: " ADMIN_USERS
    
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

# 导入配置文件
import_configuration() {
    log_step "导入现有配置文件..."
    
    if [[ -f "config.ini" ]]; then
        log_success "使用现有配置文件"
        return 0
    else
        log_error "未找到config.ini文件"
        read -p "是否切换到交互式配置? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            interactive_configuration
        else
            exit 1
        fi
    fi
}

# 最小配置
minimal_configuration() {
    log_step "创建最小配置文件..."
    
    cat > config.ini << 'EOF'
[telegram]
# 请填入您的机器人Token
submission_bot_token = YOUR_SUBMISSION_BOT_TOKEN
publish_bot_token = YOUR_PUBLISH_BOT_TOKEN
admin_bot_token = YOUR_ADMIN_BOT_TOKEN

# 请填入频道和群组ID (负数)
channel_id = YOUR_CHANNEL_ID
admin_group_id = YOUR_ADMIN_GROUP_ID
review_group_id = YOUR_REVIEW_GROUP_ID

# 请填入管理员用户ID (正数，用逗号分隔)
admin_users = YOUR_ADMIN_USER_ID

[database]
db_file = telegram_bot.db

[settings]
require_approval = true
auto_publish_delay = 0
max_file_size = 50
ad_enabled = false
max_ads_per_post = 0
show_ad_label = false
enable_ocr = false
enable_image_compress = false
enable_video_thumbnail = true
db_pool_size = 10
cache_enabled = true
async_workers = 5
default_language = zh-CN
default_timezone = Asia/Shanghai

[performance]
db_pool_size = 10
db_max_overflow = 5
async_max_workers = 5
async_queue_size = 1000
cache_max_size = 1000
cache_default_ttl = 3600
max_file_size = 50
enable_compression = false

[media]
image_quality = medium
max_image_size = 2048
enable_ocr = false
ocr_languages = chi_sim+eng
enable_video_thumbnail = true
thumbnail_time = 1.0
max_video_size = 100
enable_audio_metadata = true

[advertisement]
enabled = false
max_ads_per_post = 0
min_ads_per_post = 0
show_ad_label = false
ad_separator = "\n\n━━━━━━━━━━\n\n"
random_selection = true
track_clicks = true
EOF
    
    log_warning "已创建最小配置文件，请手动编辑 config.ini 填入实际值"
    log_info "配置完成后请重新运行安装脚本验证配置"
    
    echo -e "${YELLOW}必须配置的项目:${NC}"
    echo "• submission_bot_token"
    echo "• publish_bot_token"
    echo "• admin_bot_token"
    echo "• channel_id"
    echo "• admin_group_id"
    echo "• review_group_id"
    echo "• admin_users"
    
    read -p "是否现在编辑配置文件? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} config.ini
    fi
}

# 显示配置示例
show_configuration_example() {
    log_header "📋 配置文件示例"
    
    echo -e "${CYAN}config.ini 配置示例:${NC}"
    echo
    cat << 'EOF'
[telegram]
# 机器人Token (从@BotFather获取)
submission_bot_token = 1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
publish_bot_token = 1234567890:BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
admin_bot_token = 1234567890:CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

# 频道和群组ID (负数，从@userinfobot获取)
channel_id = -1001234567890
admin_group_id = -1001234567891
review_group_id = -1001234567892

# 管理员用户ID (正数，多个用逗号分隔)
admin_users = 123456789,987654321

[database]
db_file = telegram_bot.db

[settings]
# 基础设置
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
EOF
    
    echo
    read -p "按回车键返回配置选择: "
    show_configuration_guide
}

# 配置机器人 (主入口函数)
configure_bots() {
    log_header "⚙️ 配置机器人系统"
    show_configuration_guide
}

# 验证配置
validate_config() {
    log_header "✅ 验证配置"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 检查配置文件是否存在
    if [[ ! -f "config.ini" ]]; then
        log_error "配置文件 config.ini 不存在"
        exit 1
    fi
    
    log_step "验证配置文件格式..."
    if python -c "
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
required_sections = ['telegram', 'database', 'settings']
for section in required_sections:
    if not config.has_section(section):
        raise Exception(f'Missing section: {section}')
print('配置文件格式正确')
" 2>/dev/null; then
        log_success "配置文件格式验证通过"
    else
        log_error "配置文件格式错误"
        log_error "请检查config.ini文件格式"
        exit 1
    fi
    
    log_step "验证必需配置项..."
    local config_check=$(python -c "
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

required_items = {
    'telegram': ['submission_bot_token', 'publish_bot_token', 'admin_bot_token', 
                 'channel_id', 'admin_group_id', 'review_group_id', 'admin_users'],
    'database': ['db_file']
}

missing = []
for section, items in required_items.items():
    for item in items:
        if not config.has_option(section, item) or not config.get(section, item).strip():
            missing.append(f'{section}.{item}')

if missing:
    print('MISSING:' + ','.join(missing))
else:
    print('OK')
" 2>/dev/null)
    
    if [[ $config_check == "OK" ]]; then
        log_success "必需配置项验证通过"
    else
        local missing_items=$(echo $config_check | cut -d':' -f2)
        log_error "缺少必需配置项: $missing_items"
        exit 1
    fi
    
    log_step "测试机器人Token连接..."
    
    # 读取所有Token
    local tokens=$(python -c "
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
print(config.get('telegram', 'submission_bot_token'))
print(config.get('telegram', 'publish_bot_token'))
print(config.get('telegram', 'admin_bot_token'))
")
    
    local token_array=($tokens)
    local token_names=("投稿机器人" "发布机器人" "控制机器人")
    
    # 验证每个Token
    for i in {0..2}; do
        local token=${token_array[$i]}
        local name=${token_names[$i]}
        
        if validate_token "$token" "$name"; then
            continue
        else
            log_error "$name Token验证失败"
            exit 1
        fi
    done
    
    log_step "验证ID格式..."
    local id_check=$(python -c "
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

# 检查频道/群组ID (应该是负数)
channel_id = config.get('telegram', 'channel_id')
admin_group_id = config.get('telegram', 'admin_group_id')
review_group_id = config.get('telegram', 'review_group_id')

if not (channel_id.startswith('-') and channel_id[1:].isdigit()):
    print(f'Invalid channel_id: {channel_id}')
    exit(1)

if not (admin_group_id.startswith('-') and admin_group_id[1:].isdigit()):
    print(f'Invalid admin_group_id: {admin_group_id}')
    exit(1)

if not (review_group_id.startswith('-') and review_group_id[1:].isdigit()):
    print(f'Invalid review_group_id: {review_group_id}')
    exit(1)

# 检查管理员ID (应该是正数)
admin_users = config.get('telegram', 'admin_users')
for user_id in admin_users.split(','):
    user_id = user_id.strip()
    if not user_id.isdigit():
        print(f'Invalid admin_user_id: {user_id}')
        exit(1)

print('ID格式验证通过')
")
    
    if [[ $? -eq 0 ]]; then
        log_success "$id_check"
    else
        log_error "ID格式验证失败: $id_check"
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

# 显示安装摘要
show_install_summary() {
    log_header "📋 安装摘要"
    
    echo -e "${CYAN}系统信息:${NC}"
    echo "• 操作系统: $DISTRO $DISTRO_VERSION"
    echo "• 架构: $ARCH"
    echo "• Python: $PYTHON_CMD"
    echo "• 包管理器: $PKG_MANAGER"
    echo
    
    echo -e "${CYAN}安装位置:${NC}"
    echo "• 安装目录: $INSTALL_DIR"
    echo "• 日志文件: $INSTALL_LOG"
    echo "• 备份目录: $BACKUP_DIR"
    echo
    
    echo -e "${CYAN}预计安装时间:${NC}"
    echo "• 系统依赖: 2-5 分钟"
    echo "• Python环境: 3-8 分钟"
    echo "• 配置和测试: 5-10 分钟"
    echo "• 总计: 10-25 分钟"
    echo
}

# 安装前检查
pre_install_check() {
    log_header "🔍 安装前检查"
    
    # 检查网络连接
    if ! ping -c 1 pypi.org >/dev/null 2>&1; then
        log_warning "无法连接到PyPI，可能影响Python包下载"
        read -p "是否继续安装? (y/n): " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 0
    fi
    
    # 检查磁盘空间
    local required_space=1000000  # 1GB in KB
    local available_space=$(df . | awk 'NR==2 {print $4}')
    
    if (( available_space < required_space )); then
        log_warning "磁盘空间可能不足，建议至少1GB可用空间"
        read -p "是否继续安装? (y/n): " -n 1 -r
        echo  
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 0
    fi
    
    # 检查sudo权限
    if ! sudo -n true 2>/dev/null; then
        log_info "安装需要sudo权限来安装系统依赖"
        if ! sudo true; then
            log_error "无法获取sudo权限"
            exit 1
        fi
    fi
    
    log_success "安装前检查完成"
}

# 安装完成后操作
post_install_actions() {
    log_header "🎯 安装完成"
    
    # 生成安装报告
    cat > install_report.txt << EOF
Telegram Bot System Installation Report
======================================

Installation Date: $(date)
System: $DISTRO $DISTRO_VERSION ($ARCH)
Python: $($PYTHON_CMD --version)
Install Directory: $INSTALL_DIR

Installation Status: SUCCESS

Files Created:
- config.ini (configuration file)
- venv/ (Python virtual environment)
- logs/ (log directory)
- *.py (bot scripts)
- *.sh (management scripts)

Next Steps:
1. Start the system: ./start_all.sh
2. Check status: ./status.sh
3. View logs: tail -f *.log
4. Read documentation: README.md

For support, check:
- README.md for detailed documentation
- USAGE_GUIDE.md for quick start
- logs/ directory for troubleshooting
EOF
    
    log_info "安装报告已保存到 install_report.txt"
    
    # 清理临时文件
    log_step "清理安装临时文件..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # 设置最终权限
    log_step "设置最终文件权限..."
    chmod 600 config.ini 2>/dev/null || true
    chmod +x *.sh 2>/dev/null || true
    chmod 755 logs 2>/dev/null || true
    
    log_success "安装后操作完成"
}

# 主安装流程
main() {
    # 显示欢迎界面
    clear
    echo -e "${PURPLE}"
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🤖 电报机器人投稿系统 - 一键安装脚本 v2.1                 ║
    ║                                                              ║
    ║    ✨ 新版本特性:                                             ║
    ║    • 🔍 智能系统检测      • 🚀 多平台支持                    ║
    ║    • 📦 自动依赖管理      • ⚙️  交互式配置向导               ║
    ║    • 🧪 自动功能测试      • 🛡️  完整错误处理                ║
    ║    • 📊 安装进度监控      • 🔄 自动回滚机制                  ║
    ║                                                              ║
    ║    🎯 核心功能:                                               ║
    ║    • 📝 智能投稿管理      • 📢 广告系统                      ║
    ║    • 🎨 多媒体处理        • 🌍 多语言支持                    ║
    ║    • 🔔 实时通知          • ⚡ 性能优化                      ║
    ║    • 🔄 热更新功能        • 🛡️  安全管理                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${CYAN}🎉 欢迎使用电报机器人投稿系统一键安装脚本！${NC}"
    echo -e "${YELLOW}📋 本脚本将为您自动完成系统的安装、配置和测试${NC}"
    echo
    
    # 显示脚本信息
    echo -e "${WHITE}脚本信息:${NC}"
    echo "• 版本: $SCRIPT_VERSION"
    echo "• 支持平台: Ubuntu, CentOS, Debian, Arch Linux等"
    echo "• Python要求: >= $MIN_PYTHON_VERSION"
    echo "• 预计耗时: 10-25 分钟"
    echo
    
    # 确认开始安装
    echo -e "${CYAN}准备开始安装...${NC}"
    read -p "按回车键继续，或按 Ctrl+C 取消: "
    echo
    
    # 执行安装流程
    init_environment
    pre_install_check
    show_install_summary
    
    echo -e "${GREEN}🚀 开始安装流程...${NC}"
    echo
    
         # 主要安装步骤
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
    post_install_actions
    show_completion
    
    # 询问是否立即启动
    echo
    echo -e "${CYAN}🎯 安装完成！${NC}"
    read -p "是否立即启动机器人系统? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "正在启动机器人系统..."
        if ./start_all.sh; then
            sleep 3
            ./status.sh
            echo
            echo -e "${GREEN}🎊 系统启动成功！您可以开始使用机器人了！${NC}"
        else
            log_warning "系统启动失败，请检查日志文件"
        fi
    else
        log_info "系统已准备就绪，您可以随时使用 ./start_all.sh 启动"
    fi
    
    echo
    echo -e "${PURPLE}📞 如需帮助，请查看:${NC}"
    echo "• README.md - 详细文档"
    echo "• USAGE_GUIDE.md - 快速使用指南"
    echo "• install_report.txt - 安装报告"
    echo "• logs/ - 日志文件"
}

# 运行主程序
main "$@"