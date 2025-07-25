#!/bin/bash

# 一键更新脚本 v2.3.0
# 自动更新电报机器人投稿系统

set -e  # 遇到错误立即退出

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

log_header() {
    echo
    echo "========================================"
    echo "$1"
    echo "========================================"
}

# 检查运行环境
check_environment() {
    log_header "检查运行环境"
    
    # 检查是否为root用户
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户运行"
    fi
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_success "Python版本: $PYTHON_VERSION"
    else
        log_error "Python3未安装"
        exit 1
    fi
    
    # 检查Git
    if command -v git &> /dev/null; then
        log_success "Git已安装"
    else
        log_error "Git未安装，请先安装Git"
        exit 1
    fi
    
    # 检查当前目录
    if [[ ! -f "config.ini" && ! -f "config.local.ini" ]]; then
        log_error "当前目录不是项目根目录"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 备份当前系统
backup_system() {
    log_header "备份当前系统"
    
    BACKUP_DIR="backups/update_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份配置文件
    if [[ -f "config.local.ini" ]]; then
        cp config.local.ini "$BACKUP_DIR/"
        log_success "备份配置文件: config.local.ini"
    fi
    
    if [[ -f "config.ini" ]]; then
        cp config.ini "$BACKUP_DIR/"
        log_success "备份配置文件: config.ini"
    fi
    
    # 备份数据库
    if [[ -f "telegram_bot.db" ]]; then
        cp telegram_bot.db "$BACKUP_DIR/"
        log_success "备份数据库: telegram_bot.db"
    fi
    
    # 备份日志文件
    if ls *.log 1> /dev/null 2>&1; then
        cp *.log "$BACKUP_DIR/" 2>/dev/null || true
        log_success "备份日志文件"
    fi
    
    # 备份PID文件
    if [[ -d "pids" ]]; then
        cp -r pids "$BACKUP_DIR/" 2>/dev/null || true
        log_success "备份PID文件"
    fi
    
    echo "$BACKUP_DIR" > .last_backup
    log_success "系统备份完成: $BACKUP_DIR"
}

# 停止所有机器人
stop_bots() {
    log_header "停止所有机器人"
    
    # 使用pkill停止进程
    pkill -f "python.*submission_bot.py" 2>/dev/null && log_success "停止投稿机器人" || log_info "投稿机器人未运行"
    pkill -f "python.*publish_bot.py" 2>/dev/null && log_success "停止发布机器人" || log_info "发布机器人未运行"
    pkill -f "python.*control_bot.py" 2>/dev/null && log_success "停止控制机器人" || log_info "控制机器人未运行"
    
    # 等待进程完全停止
    sleep 3
    
    log_success "所有机器人已停止"
}

# 更新代码
update_code() {
    log_header "更新代码"
    
    # 检查Git状态
    if git status --porcelain | grep -q .; then
        log_warning "检测到未提交的更改"
        
        # 备份本地更改
        git stash push -m "自动备份 $(date +%Y%m%d_%H%M%S)"
        log_success "已暂存本地更改"
    fi
    
    # 获取当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    log_info "当前分支: $CURRENT_BRANCH"
    
    # 拉取最新代码
    log_info "拉取最新代码..."
    if git pull origin "$CURRENT_BRANCH"; then
        log_success "代码更新成功"
    else
        log_error "代码更新失败"
        
        # 尝试重置并强制拉取
        log_warning "尝试强制更新..."
        git fetch origin
        git reset --hard origin/"$CURRENT_BRANCH"
        log_success "强制更新完成"
    fi
    
    # 检查是否有暂存的更改
    if git stash list | grep -q "自动备份"; then
        log_info "发现暂存的本地更改，请手动处理:"
        git stash list | grep "自动备份"
    fi
}

# 更新依赖
update_dependencies() {
    log_header "更新依赖"
    
    # 激活虚拟环境
    if [[ -d "venv" ]]; then
        source venv/bin/activate
        log_success "激活虚拟环境"
    else
        log_warning "虚拟环境不存在，使用系统Python"
    fi
    
    # 更新pip
    python3 -m pip install --upgrade pip
    log_success "更新pip完成"
    
    # 安装/更新依赖
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt --upgrade
        log_success "依赖更新完成"
    else
        log_warning "requirements.txt不存在，跳过依赖更新"
    fi
}

# 修复数据库
fix_database() {
    log_header "修复数据库"
    
    # 运行数据库修复脚本
    if [[ -f "fix_data_sync.py" ]]; then
        python3 fix_data_sync.py
        log_success "数据库修复完成"
    else
        log_warning "数据库修复脚本不存在"
    fi
}

# 修复Markdown问题
fix_markdown() {
    log_header "修复Markdown实体解析问题"
    
    if [[ -f "fix_markdown_entities.py" ]]; then
        python3 fix_markdown_entities.py
        log_success "Markdown修复完成"
    else
        log_warning "Markdown修复脚本不存在"
    fi
}

# 确保投稿机器人只接收私聊
fix_submission_bot_privacy() {
    log_header "确保投稿机器人只接收私聊"
    
    if [[ -f "submission_bot.py" ]]; then
        # 检查是否已经配置了私聊限制
        if grep -q "filters.ChatType.PRIVATE" submission_bot.py; then
            log_success "投稿机器人已配置为只接收私聊"
        else
            log_info "正在配置投稿机器人私聊限制..."
            
            # 备份原文件
            cp submission_bot.py submission_bot.py.backup
            
            # 为CommandHandler添加私聊过滤器
            sed -i 's/CommandHandler("start", self.start_command)/CommandHandler("start", self.start_command, filters=filters.ChatType.PRIVATE)/g' submission_bot.py
            sed -i 's/CommandHandler("status", self.status_command)/CommandHandler("status", self.status_command, filters=filters.ChatType.PRIVATE)/g' submission_bot.py
            sed -i 's/CommandHandler("help", self.help_command)/CommandHandler("help", self.help_command, filters=filters.ChatType.PRIVATE)/g' submission_bot.py
            
            # 为MessageHandler添加私聊过滤器
            sed -i 's/filters\.TEXT & ~filters\.COMMAND/filters.TEXT \& ~filters.COMMAND \& filters.ChatType.PRIVATE/g' submission_bot.py
            sed -i 's/filters\.PHOTO)/filters.PHOTO \& filters.ChatType.PRIVATE)/g' submission_bot.py
            sed -i 's/filters\.VIDEO)/filters.VIDEO \& filters.ChatType.PRIVATE)/g' submission_bot.py
            sed -i 's/filters\.AUDIO)/filters.AUDIO \& filters.ChatType.PRIVATE)/g' submission_bot.py
            sed -i 's/filters\.VOICE)/filters.VOICE \& filters.ChatType.PRIVATE)/g' submission_bot.py
            
            log_success "投稿机器人私聊限制配置完成"
        fi
    else
        log_warning "submission_bot.py文件不存在"
    fi
}

# 更新版本信息
update_version() {
    log_header "更新版本信息"
    
    # 从.version文件读取版本，如果不存在则使用默认版本
    if [[ -f ".version" ]]; then
        CURRENT_VERSION=$(cat .version)
        log_info "当前版本: $CURRENT_VERSION"
    else
        echo "v2.3.0" > .version
        log_success "创建版本文件: v2.3.0"
    fi
}

# 验证系统
verify_system() {
    log_header "验证系统"
    
    # 检查关键文件
    REQUIRED_FILES=(
        "submission_bot.py"
        "publish_bot.py" 
        "control_bot.py"
        "database.py"
        "config_manager.py"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "✓ $file"
        else
            log_error "✗ $file 缺失"
            MISSING_FILES=true
        fi
    done
    
    if [[ "$MISSING_FILES" == "true" ]]; then
        log_error "关键文件缺失，系统可能无法正常运行"
        return 1
    fi
    
    # 检查配置文件
    if [[ -f "config.local.ini" || -f "config.ini" ]]; then
        log_success "✓ 配置文件存在"
    else
        log_error "✗ 配置文件不存在"
        return 1
    fi
    
    # 检查数据库
    if [[ -f "telegram_bot.db" ]]; then
        log_success "✓ 数据库文件存在"
    else
        log_warning "数据库文件不存在，首次运行时会自动创建"
    fi
    
    log_success "系统验证通过"
}

# 启动机器人
start_bots() {
    log_header "启动机器人"
    
    # 创建PID目录
    mkdir -p pids
    
    # 启动投稿机器人
    if [[ -f "submission_bot.py" ]]; then
        nohup python3 submission_bot.py > submission_bot.log 2>&1 &
        echo $! > pids/submission_bot.pid
        log_success "启动投稿机器人 (PID: $!)"
        sleep 2
    fi
    
    # 启动发布机器人
    if [[ -f "publish_bot.py" ]]; then
        nohup python3 publish_bot.py > publish_bot.log 2>&1 &
        echo $! > pids/publish_bot.pid
        log_success "启动发布机器人 (PID: $!)"
        sleep 2
    fi
    
    # 启动控制机器人
    if [[ -f "control_bot.py" ]]; then
        nohup python3 control_bot.py > control_bot.log 2>&1 &
        echo $! > pids/control_bot.pid
        log_success "启动控制机器人 (PID: $!)"
        sleep 2
    fi
    
    # 等待启动完成
    sleep 5
    
    # 检查进程状态
    log_info "检查机器人状态..."
    
    RUNNING_COUNT=0
    for bot in submission_bot publish_bot control_bot; do
        if [[ -f "pids/${bot}.pid" ]]; then
            PID=$(cat "pids/${bot}.pid")
            if kill -0 "$PID" 2>/dev/null; then
                log_success "✓ ${bot} 运行正常 (PID: $PID)"
                ((RUNNING_COUNT++))
            else
                log_error "✗ ${bot} 启动失败"
                rm -f "pids/${bot}.pid"
            fi
        fi
    done
    
    log_success "成功启动 $RUNNING_COUNT 个机器人"
}

# 显示更新结果
show_result() {
    log_header "更新完成"
    
    # 显示版本信息
    if [[ -f ".version" ]]; then
        VERSION=$(cat .version)
        log_success "当前版本: $VERSION"
    fi
    
    # 显示备份信息
    if [[ -f ".last_backup" ]]; then
        BACKUP_DIR=$(cat .last_backup)
        log_success "备份位置: $BACKUP_DIR"
    fi
    
    # 显示运行状态
    log_info "系统状态:"
    RUNNING_BOTS=0
    
    for bot in submission_bot publish_bot control_bot; do
        if [[ -f "pids/${bot}.pid" ]]; then
            PID=$(cat "pids/${bot}.pid")
            if kill -0 "$PID" 2>/dev/null; then
                echo "  ✅ ${bot}: 运行中 (PID: $PID)"
                ((RUNNING_BOTS++))
            else
                echo "  ❌ ${bot}: 未运行"
            fi
        else
            echo "  ❌ ${bot}: 未运行"
        fi
    done
    
    echo
    if [[ $RUNNING_BOTS -eq 3 ]]; then
        log_success "🎉 系统更新完成！所有机器人运行正常"
    else
        log_warning "⚠️  系统更新完成，但部分机器人未运行"
        echo "请检查配置文件和日志，然后手动启动机器人"
    fi
    
    echo
    echo "📋 有用的命令:"
    echo "  查看日志: tail -f *.log"
    echo "  重启系统: ./one_click_update.sh"
    echo "  检查状态: ps aux | grep python"
    echo "  手动启动: python3 submission_bot.py &"
}

# 主函数
main() {
    echo "🚀 电报机器人投稿系统 - 一键更新脚本 v2.3.0"
    echo "========================================"
    echo "更新时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "工作目录: $(pwd)"
    echo
    
    # 确认更新
    read -p "确认更新系统？这将停止所有机器人并更新代码 [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "更新已取消"
        exit 0
    fi
    
    # 执行更新流程
    check_environment
    backup_system
    stop_bots
    update_code
    update_dependencies
    update_version
    fix_database
    fix_markdown
    fix_submission_bot_privacy
    verify_system
    start_bots
    show_result
}

# 错误处理
trap 'log_error "更新过程中发生错误，退出码: $?"' ERR

# 运行主函数
main "$@"