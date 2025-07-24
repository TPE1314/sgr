#!/bin/bash
# 启动所有电报机器人的脚本

set -e  # 遇到错误时停止执行

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查配置文件是否存在
if [ ! -f "config.ini" ]; then
    log_error "配置文件 config.ini 不存在，请先配置"
    exit 1
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    log_info "激活虚拟环境..."
    source venv/bin/activate
fi

# 检查Python依赖
log_info "检查Python依赖..."
python3 -c "
import sys
import importlib

required_modules = ['telegram', 'sqlite3', 'psutil', 'configparser']
missing_modules = []

for module in required_modules:
    try:
        importlib.import_module(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print(f'缺少模块: {missing_modules}')
    sys.exit(1)
else:
    print('所有依赖检查通过')
" 2>/dev/null

if [ $? -ne 0 ]; then
    log_error "Python依赖检查失败，请运行: pip3 install -r requirements.txt"
    exit 1
fi

# 创建必要的目录
mkdir -p logs pids
log_info "创建日志和PID目录"

# 检查端口是否被占用
check_bot_running() {
    local bot_name=$1
    local pid_file="pids/${bot_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # 进程运行中
        else
            rm -f "$pid_file"  # 清理无效的PID文件
            return 1  # 进程不存在
        fi
    fi
    return 1  # PID文件不存在
}

# 启动单个机器人的函数
start_bot() {
    local bot_name=$1
    local bot_script=$2
    local display_name=$3
    local emoji=$4
    
    log_info "${emoji} 启动${display_name}..."
    
    # 检查是否已经运行
    if check_bot_running "$bot_name"; then
        log_warning "${display_name}已在运行中"
        return 0
    fi
    
    # 检查脚本文件是否存在
    if [ ! -f "$bot_script" ]; then
        log_error "${display_name}脚本文件 $bot_script 不存在"
        return 1
    fi
    
    # 启动机器人
    nohup python3 "$bot_script" > "logs/${bot_name}.log" 2>&1 &
    local pid=$!
    
    # 保存PID
    echo $pid > "pids/${bot_name}.pid"
    
    # 等待启动并检查
    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        log_success "${display_name}启动成功 (PID: $pid)"
        return 0
    else
        log_error "${display_name}启动失败"
        rm -f "pids/${bot_name}.pid"
        return 1
    fi
}

log_info "🚀 开始启动所有机器人..."

# 启动标志
declare -a failed_bots=()
declare -a success_bots=()

# 启动投稿机器人
if start_bot "submission_bot" "submission_bot.py" "投稿机器人" "📝"; then
    success_bots+=("投稿机器人")
else
    failed_bots+=("投稿机器人")
fi

# 启动发布机器人
if start_bot "publish_bot" "publish_bot.py" "发布机器人" "📢"; then
    success_bots+=("发布机器人")
else
    failed_bots+=("发布机器人")
fi

# 启动控制机器人
if start_bot "control_bot" "control_bot.py" "控制机器人" "🎛️"; then
    success_bots+=("控制机器人")
else
    failed_bots+=("控制机器人")
fi

echo
echo "📊 启动结果："
echo "================================"

if [ ${#success_bots[@]} -gt 0 ]; then
    log_success "成功启动: ${success_bots[*]}"
fi

if [ ${#failed_bots[@]} -gt 0 ]; then
    log_error "启动失败: ${failed_bots[*]}"
    echo
    echo -e "${YELLOW}💡 故障排除建议：${NC}"
    echo "1. 检查日志: tail -f logs/*.log"
    echo "2. 检查配置: cat config.ini"
    echo "3. 手动测试: python3 submission_bot.py"
    echo "4. 查看状态: ./status.sh"
fi

echo
if [ ${#success_bots[@]} -eq 3 ]; then
    log_success "✅ 所有机器人启动完成！"
    
    # 显示运行状态
    echo
    echo -e "${BLUE}📋 运行状态：${NC}"
    for bot in submission_bot publish_bot control_bot; do
        if check_bot_running "$bot"; then
            pid=$(cat "pids/${bot}.pid")
            echo -e "${GREEN}✅${NC} $bot: 运行中 (PID: $pid)"
        else
            echo -e "${RED}❌${NC} $bot: 未运行"
        fi
    done
    
    echo
    echo -e "${YELLOW}💡 管理命令：${NC}"
    echo "• 查看状态: ./status.sh"
    echo "• 停止所有: ./stop_all.sh"
    echo "• 重启系统: ./stop_all.sh && ./start_all.sh"
    echo "• 查看日志: tail -f logs/*.log"
    echo "• 实时监控: watch -n 2 './status.sh'"
    
    echo
    log_success "🎯 系统已在后台运行，可以开始使用！"
    
    exit 0
else
    log_error "部分机器人启动失败，请检查配置和日志"
    exit 1
fi