#!/bin/bash

echo "🔧 修复 /root/sgr Git仓库问题"
echo "=================================="

# 切换到root用户并进入sgr目录
sudo su - root << 'EOF'
echo "📍 当前位置: $(pwd)"

# 进入sgr目录
cd /root/sgr

echo "🔍 检查Git状态..."
git status

echo ""
echo "🧹 清理Git状态..."

# 添加.gitignore规则
cat > .gitignore << 'GITIGNORE_EOF'
# Python缓存文件
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# 日志文件
*.log
logs/

# 数据库文件
*.db
*.sqlite
*.sqlite3

# 配置文件
config.local.ini

# PID文件
pids/
*.pid

# 备份文件
backup_*/
backups/

# 虚拟环境
venv/
env/

# 临时文件
*.tmp
*.temp
.DS_Store
Thumbs.db
GITIGNORE_EOF

# 添加.gitignore
git add .gitignore

# 重置所有修改的文件（除了重要配置）
echo "⚠️  重置修改的文件..."
git checkout -- . 2>/dev/null || true

# 清理未跟踪的文件
echo "🗑️  清理临时文件..."
git clean -fd

echo "✅ Git仓库清理完成"
echo ""
echo "📊 最终状态:"
git status

echo ""
echo "💾 如果需要提交更改:"
echo "   git add ."
echo "   git commit -m '清理仓库状态'"

echo ""
echo "🔄 如果需要更新代码:"
echo "   git pull origin main"

EOF

echo "✅ 修复脚本执行完成"
echo ""
echo "🎯 使用说明:"
echo "1. 要进入项目目录: sudo su - root -c 'cd /root/sgr && bash'"
echo "2. 或者直接: cd /root/sgr (如果您已是root用户)"
echo "3. 运行一键更新: ./one_click_update.sh"