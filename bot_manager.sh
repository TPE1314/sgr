#!/bin/bash
# 电报机器人系统管理脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 脚本版本
VERSION="1.0.0"

# 显示帮助信息
show_help() {
    echo -e "${CYAN}📚 电报机器人系统管理工具 v${VERSION}${NC}"
    echo "================================"
    echo
    echo -e "${YELLOW}用法:${NC}"
    echo "  $0 [命令] [选项]"
    echo
    echo -e "${YELLOW}命令:${NC}"
    echo "  start       启动所有机器人"
    echo "  stop        停止所有机器人"
    echo "  restart     重启所有机器人"
    echo "  status      显示系统状态"
    echo "  logs        查看日志"
    echo "  monitor     实时监控"
    echo "  install     重新运行安装脚本"
    echo "  update      更新系统"
    echo "  backup      备份配置"
    echo "  restore     恢复配置"
    echo "  help        显示此帮助信息"
    echo
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 start              # 启动所有机器人"
    echo "  $0 logs -f            # 实时查看日志"
    echo "  $0 monitor            # 实时监控状态"
    echo "  $0 backup             # 备份当前配置"
    echo
    echo -e "${CYAN}📞 获取帮助: https://github.com/TPE1314/sgr${NC}"
}

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

# 检查必需文件
check_requirements() {
    local missing_files=()
    
    # 检查脚本文件
    for script in start_all.sh stop_all.sh status.sh; do
        if [[ ! -f "$script" ]]; then
            missing_files+=("$script")
        fi
    done
    
    # 检查配置文件
    if [[ ! -f "config.ini" ]]; then
        missing_files+=("config.ini")
    fi
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "缺少必需文件: ${missing_files[*]}"
        echo "请运行: $0 install"
        return 1
    fi
    
    return 0
}

# 启动系统
cmd_start() {
    log_info "🚀 启动机器人系统..."
    
    if [[ ! -x "start_all.sh" ]]; then
        chmod +x start_all.sh
    fi
    
    if ./start_all.sh; then
        log_success "系统启动完成"
        echo
        echo -e "${CYAN}💡 使用建议：${NC}"
        echo "• 查看状态: $0 status"
        echo "• 实时监控: $0 monitor"
        echo "• 查看日志: $0 logs"
    else
        log_error "系统启动失败"
        return 1
    fi
}

# 停止系统
cmd_stop() {
    log_info "🛑 停止机器人系统..."
    
    if [[ ! -x "stop_all.sh" ]]; then
        chmod +x stop_all.sh
    fi
    
    if ./stop_all.sh; then
        log_success "系统停止完成"
    else
        log_error "系统停止失败"
        return 1
    fi
}

# 重启系统
cmd_restart() {
    log_info "🔄 重启机器人系统..."
    
    cmd_stop
    sleep 3
    cmd_start
}

# 显示状态
cmd_status() {
    if [[ ! -x "status.sh" ]]; then
        chmod +x status.sh
    fi
    
    ./status.sh
}

# 查看日志
cmd_logs() {
    local follow_mode="$1"
    
    # 创建日志目录（如果不存在）
    mkdir -p logs
    
    if [[ "$follow_mode" == "-f" || "$follow_mode" == "--follow" ]]; then
        log_info "📝 实时查看日志 (按 Ctrl+C 退出)..."
        echo
        if command -v multitail >/dev/null 2>&1; then
            # 使用 multitail（如果可用）
            multitail logs/submission_bot.log logs/publish_bot.log logs/control_bot.log
        else
            # 使用 tail
            tail -f logs/*.log 2>/dev/null || {
                log_warning "没有找到日志文件"
                echo "机器人可能尚未启动，请先运行: $0 start"
            }
        fi
    else
        log_info "📝 查看最近的日志..."
        echo
        for bot in submission_bot publish_bot control_bot; do
            log_file="logs/${bot}.log"
            if [[ -f "$log_file" ]]; then
                echo -e "${CYAN}=== $bot 最近日志 ===${NC}"
                tail -n 10 "$log_file"
                echo
            else
                echo -e "${YELLOW}⚠️ $log_file 不存在${NC}"
            fi
        done
    fi
}

# 实时监控
cmd_monitor() {
    log_info "📊 启动实时监控 (按 Ctrl+C 退出)..."
    echo
    
    if command -v watch >/dev/null 2>&1; then
        watch -n 3 -c "./status.sh"
    else
        # 备用监控方式
        while true; do
            clear
            echo -e "${CYAN}📊 机器人系统实时监控 - $(date)${NC}"
            echo "========================================"
            cmd_status
            echo
            echo -e "${YELLOW}刷新间隔: 5秒 | 按 Ctrl+C 退出${NC}"
            sleep 5
        done
    fi
}

# 安装系统
cmd_install() {
    log_info "🔧 运行安装脚本..."
    
    if [[ -f "quick_setup.sh" ]]; then
        if [[ ! -x "quick_setup.sh" ]]; then
            chmod +x quick_setup.sh
        fi
        ./quick_setup.sh
    else
        log_error "找不到 quick_setup.sh 安装脚本"
        echo "请从 https://github.com/TPE1314/sgr 下载完整项目"
        return 1
    fi
}

# 更新系统
cmd_update() {
    log_info "🔄 更新系统..."
    
    # 检查是否在git仓库中
    if [[ -d ".git" ]]; then
        log_info "从 Git 仓库更新..."
        git pull origin main || {
            log_error "Git 更新失败"
            return 1
        }
        
        # 更新Python依赖
        if [[ -f "requirements.txt" ]]; then
            log_info "更新Python依赖..."
            pip3 install -r requirements.txt --upgrade
        fi
        
        log_success "系统更新完成"
        echo "建议重启系统: $0 restart"
    else
        log_warning "不在Git仓库中，无法自动更新"
        echo "请手动下载最新版本: https://github.com/TPE1314/sgr"
    fi
}

# 备份配置
cmd_backup() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "💾 备份配置到 $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # 备份配置文件
    if [[ -f "config.ini" ]]; then
        cp config.ini "$backup_dir/"
        log_success "配置文件已备份"
    fi
    
    # 备份数据库
    if [[ -f "telegram_bot.db" ]]; then
        cp telegram_bot.db "$backup_dir/"
        log_success "数据库已备份"
    fi
    
    # 备份日志（最近的）
    if [[ -d "logs" ]]; then
        mkdir -p "$backup_dir/logs"
        cp logs/*.log "$backup_dir/logs/" 2>/dev/null || true
        log_success "日志文件已备份"
    fi
    
    # 创建备份信息文件
    cat > "$backup_dir/backup_info.txt" << EOF
备份时间: $(date)
系统版本: $VERSION
备份内容: 
- config.ini
- telegram_bot.db
- logs/*.log
EOF
    
    log_success "备份完成: $backup_dir"
}

# 恢复配置
cmd_restore() {
    log_info "🔄 配置恢复..."
    
    if [[ ! -d "backups" ]]; then
        log_error "没有找到备份目录"
        return 1
    fi
    
    # 列出可用备份
    echo -e "${CYAN}可用的备份:${NC}"
    local backups=(backups/*)
    if [[ ${#backups[@]} -eq 0 ]]; then
        log_error "没有找到任何备份"
        return 1
    fi
    
    local i=1
    for backup in "${backups[@]}"; do
        if [[ -d "$backup" ]]; then
            echo "$i) $(basename "$backup")"
            ((i++))
        fi
    done
    
    echo
    read -p "选择要恢复的备份 (1-$((i-1))): " choice
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && [[ "$choice" -ge 1 ]] && [[ "$choice" -lt "$i" ]]; then
        local selected_backup="${backups[$((choice-1))]}"
        
        log_info "恢复备份: $(basename "$selected_backup")"
        
        # 停止系统
        cmd_stop
        
        # 恢复文件
        if [[ -f "$selected_backup/config.ini" ]]; then
            cp "$selected_backup/config.ini" .
            log_success "配置文件已恢复"
        fi
        
        if [[ -f "$selected_backup/telegram_bot.db" ]]; then
            cp "$selected_backup/telegram_bot.db" .
            log_success "数据库已恢复"
        fi
        
        log_success "配置恢复完成"
        echo "建议重启系统: $0 restart"
    else
        log_error "无效选择"
        return 1
    fi
}

# 主函数
main() {
    local command="$1"
    local option="$2"
    
    # 如果没有参数，显示状态
    if [[ -z "$command" ]]; then
        echo -e "${CYAN}📊 电报机器人系统管理工具${NC}"
        echo
        if check_requirements; then
            cmd_status
            echo
            echo -e "${YELLOW}💡 使用 '$0 help' 查看所有命令${NC}"
        fi
        return
    fi
    
    case "$command" in
        start)
            check_requirements && cmd_start
            ;;
        stop)
            check_requirements && cmd_stop
            ;;
        restart)
            check_requirements && cmd_restart
            ;;
        status)
            check_requirements && cmd_status
            ;;
        logs)
            check_requirements && cmd_logs "$option"
            ;;
        monitor)
            check_requirements && cmd_monitor
            ;;
        install)
            cmd_install
            ;;
        update)
            cmd_update
            ;;
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            echo "使用 '$0 help' 查看可用命令"
            return 1
            ;;
    esac
}

# 运行主函数
main "$@"