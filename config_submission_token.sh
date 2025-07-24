#!/bin/bash

echo "🔧 配置投稿机器人Token"
echo "=" * 30

# 创建或更新config.local.ini
cat > config.local.ini << 'EOF'
[telegram]
# 在这里填入你的机器人tokens
submission_bot_token = 7983511863:AAGTLwLrGF9ZsCu8imXUuq-qnD_OeHCIXM8
publish_bot_token = YOUR_PUBLISH_BOT_TOKEN
admin_bot_token = YOUR_ADMIN_BOT_TOKEN

# 频道和群组ID
channel_id = YOUR_CHANNEL_ID
admin_group_id = YOUR_ADMIN_GROUP_ID
review_group_id = YOUR_REVIEW_GROUP_ID

# 管理员用户ID列表 (用逗号分隔)
admin_users = 123456789,987654321

[database]
db_file = telegram_bot.db

[settings]
# 是否需要管理员审核
require_approval = true
EOF

echo "✅ 已创建 config.local.ini 并配置投稿机器人Token"
echo "📝 文件内容："
echo "投稿机器人Token: 7983511863:AAGTLwLrGF...（已配置）"
echo ""
echo "⚠️  注意：其他机器人Token仍需要您手动配置"