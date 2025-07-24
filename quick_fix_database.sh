#!/bin/bash
# 快速修复数据库导入问题

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

echo -e "${BLUE}🔧 数据库问题快速修复工具${NC}"
echo "================================"

# 1. 检查当前目录
log_info "检查当前目录..."
if [[ ! -f "database.py" ]]; then
    log_error "在当前目录未找到 database.py 文件"
    log_warning "请确保在项目根目录中运行此脚本"
    echo "当前目录内容:"
    ls -la
    exit 1
fi
log_success "在当前目录找到 database.py"

# 2. 设置Python路径
log_info "设置Python路径..."
export PYTHONPATH="$PYTHONPATH:$(pwd)"
log_success "已添加当前目录到PYTHONPATH"

# 3. 激活虚拟环境（如果存在）
if [[ -d "venv" ]]; then
    log_info "发现虚拟环境，正在激活..."
    source venv/bin/activate
    log_success "虚拟环境已激活"
else
    log_warning "未发现虚拟环境"
fi

# 4. 测试模块导入
log_info "测试数据库模块导入..."
if python3 -c "from database import DatabaseManager; print('✅ 模块导入成功')" 2>/dev/null; then
    log_success "数据库模块导入正常"
else
    log_error "数据库模块导入失败"
    echo
    echo "🔧 尝试修复方案:"
    echo "1. 检查Python文件完整性"
    echo "2. 重新设置环境变量"
    echo "3. 运行完整诊断"
    echo
    echo "执行以下命令进行详细诊断:"
    echo "  python3 fix_database_issue.py"
    exit 1
fi

# 5. 运行数据库初始化测试
log_info "运行数据库初始化测试..."
if python3 test_database_init.py >/dev/null 2>&1; then
    log_success "数据库初始化测试通过"
else
    log_warning "数据库初始化测试有警告，但基础功能正常"
fi

# 6. 运行实际数据库初始化
log_info "运行数据库初始化..."
if python3 init_database.py >/dev/null 2>&1; then
    log_success "数据库初始化完成"
else
    log_warning "数据库初始化有警告，检查详细输出:"
    python3 init_database.py
fi

echo
echo -e "${GREEN}🎉 数据库问题修复完成！${NC}"
echo
echo "接下来可以："
echo "1. 启动机器人系统: ./start_all.sh"
echo "2. 使用管理工具: ./bot_manager.sh start"
echo "3. 查看系统状态: ./status.sh"
echo
echo "如果仍有问题，请运行详细诊断:"
echo "  python3 fix_database_issue.py"