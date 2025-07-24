#!/bin/bash
# 交互式配置脚本

echo "⚙️ 电报机器人系统配置向导"
echo "=========================="
echo ""

# 检查配置文件是否存在
if [ -f "config.ini" ]; then
    echo "⚠️ 配置文件已存在！"
    read -p "是否要重新配置? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "配置已取消"
        exit 0
    fi
    cp config.ini config.ini.backup
    echo "✅ 已备份现有配置为 config.ini.backup"
fi

echo "📝 请准备以下信息："
echo "1. 三个机器人的Token"
echo "2. 发布频道ID"
echo "3. 审核群组ID"
echo "4. 管理员用户ID"
echo ""

read -p "准备好了吗? 按Enter继续..."

# 获取机器人Token
echo ""
echo "🤖 配置机器人Token"
echo "=================="
read -p "投稿机器人Token: " submission_token
read -p "发布机器人Token: " publish_token
read -p "控制机器人Token: " admin_token

# 获取频道和群组ID
echo ""
echo "📢 配置频道和群组"
echo "================"
read -p "发布频道ID (格式: -1001234567890): " channel_id
read -p "审核群组ID (格式: -1001234567890): " review_group_id
read -p "管理员群组ID (可选，格式: -1001234567890): " admin_group_id

# 如果管理员群组ID为空，使用审核群组ID
if [ -z "$admin_group_id" ]; then
    admin_group_id=$review_group_id
fi

# 获取管理员用户ID
echo ""
echo "👨‍💼 配置管理员"
echo "=============="
read -p "管理员用户ID (多个用逗号分隔): " admin_users

# 验证输入
echo ""
echo "🔍 验证配置信息"
echo "=============="

validate_token() {
    local token=$1
    local name=$2
    if [[ ! $token =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        echo "❌ $name Token格式不正确"
        return 1
    fi
    return 0
}

validate_id() {
    local id=$1
    local name=$2
    if [[ ! $id =~ ^-?[0-9]+$ ]]; then
        echo "❌ $name ID格式不正确"
        return 1
    fi
    return 0
}

# 验证Token
validate_token "$submission_token" "投稿机器人" || exit 1
validate_token "$publish_token" "发布机器人" || exit 1
validate_token "$admin_token" "控制机器人" || exit 1

# 验证ID
validate_id "$channel_id" "频道" || exit 1
validate_id "$review_group_id" "审核群组" || exit 1
validate_id "$admin_group_id" "管理员群组" || exit 1

echo "✅ 配置信息验证通过"

# 创建配置文件
echo ""
echo "💾 生成配置文件"
echo "=============="

cat > config.ini << EOF
[telegram]
# 机器人tokens
submission_bot_token = $submission_token
publish_bot_token = $publish_token
admin_bot_token = $admin_token

# 频道和群组ID
channel_id = $channel_id
admin_group_id = $admin_group_id
review_group_id = $review_group_id

# 管理员用户ID列表 (用逗号分隔)
admin_users = $admin_users

[database]
db_file = telegram_bot.db

[settings]
# 是否需要管理员审核
require_approval = true
# 自动发布延迟时间(秒)
auto_publish_delay = 0
EOF

# 设置文件权限
chmod 600 config.ini

echo "✅ 配置文件已生成"

# 测试配置
echo ""
echo "🧪 测试配置"
echo "=========="

echo "正在测试Python模块..."
python3 -c "
try:
    from config_manager import ConfigManager
    config = ConfigManager()
    print('✅ 配置文件格式正确')
    print(f'✅ 投稿机器人Token: {config.get_submission_bot_token()[:10]}...')
    print(f'✅ 发布机器人Token: {config.get_publish_bot_token()[:10]}...')
    print(f'✅ 控制机器人Token: {config.get_admin_bot_token()[:10]}...')
    print(f'✅ 频道ID: {config.get_channel_id()}')
    print(f'✅ 审核群组ID: {config.get_review_group_id()}')
    print(f'✅ 管理员数量: {len(config.get_admin_users())}')
except Exception as e:
    print(f'❌ 配置测试失败: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 配置完成！"
    echo "============"
    echo ""
    echo "📋 下一步操作："
    echo "1. 启动系统: ./start_all.sh"
    echo "2. 查看状态: ./status.sh"
    echo "3. 查看日志: tail -f *.log"
    echo ""
    echo "⚠️ 重要提醒："
    echo "• 确保机器人已添加到对应的频道和群组"
    echo "• 确保机器人在群组中有管理员权限"
    echo "• 配置文件包含敏感信息，请妥善保管"
    echo ""
    
    read -p "是否现在启动系统? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 启动系统..."
        ./start_all.sh
    fi
else
    echo "❌ 配置测试失败，请检查配置信息"
    exit 1
fi