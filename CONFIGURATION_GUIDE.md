# 🔧 投稿系统配置指南

## 📋 问题诊断结果

您的投稿系统问题已确诊：

### ❌ 当前问题
1. **配置不完整** - 只配置了投稿机器人Token
2. **机器人未运行** - 发布机器人和控制机器人无法启动
3. **Token冲突** - 投稿机器人出现409冲突错误

### ✅ 解决方案
需要完成剩余的配置才能正常使用系统。

---

## 🤖 第一步：创建机器人Token

您需要从 [@BotFather](https://t.me/BotFather) 创建3个机器人：

### 1. 投稿机器人 (已有)
```
✅ 已配置: 7983511863:AAGTLwLrGF9ZsCu8imXUuq-qnD_OeHCIXM8
```

### 2. 发布机器人 (需要创建)
```
1. 发送 /newbot 给 @BotFather
2. 设置机器人名称，如：MyPublishBot
3. 设置用户名，如：my_publish_bot
4. 保存返回的Token
```

### 3. 控制机器人 (需要创建)
```
1. 发送 /newbot 给 @BotFather
2. 设置机器人名称，如：MyControlBot
3. 设置用户名，如：my_control_bot
4. 保存返回的Token
```

---

## 📢 第二步：创建频道和群组

### 1. 创建发布频道
```
1. 创建一个新频道 (用于发布审核通过的投稿)
2. 将发布机器人添加为管理员
3. 转发频道中的任意消息给 @userinfobot 获取频道ID
4. 频道ID格式：-1001234567890
```

### 2. 创建审核群组
```
1. 创建一个新群组 (管理员审核投稿的地方)
2. 将发布机器人添加到群组
3. 转发群组中的任意消息给 @userinfobot 获取群组ID
4. 群组ID格式：-1001234567890
```

### 3. 创建管理群组 (可选)
```
1. 创建一个新群组 (接收系统通知)
2. 将控制机器人添加到群组
3. 获取群组ID
```

---

## ⚙️ 第三步：更新配置文件

编辑 `config.local.ini` 文件：

```ini
[telegram]
# 机器人tokens
submission_bot_token = 7983511863:AAGTLwLrGF9ZsCu8imXUuq-qnD_OeHCIXM8
publish_bot_token = YOUR_PUBLISH_BOT_TOKEN_HERE
admin_bot_token = YOUR_CONTROL_BOT_TOKEN_HERE

# 频道和群组ID
channel_id = YOUR_CHANNEL_ID_HERE
admin_group_id = YOUR_ADMIN_GROUP_ID_HERE
review_group_id = YOUR_REVIEW_GROUP_ID_HERE

# 管理员用户ID列表 (用逗号分隔)
admin_users = 123456789,987654321

[database]
db_file = telegram_bot.db

[settings]
# 是否需要管理员审核
require_approval = true
```

### 📝 配置示例
```ini
[telegram]
submission_bot_token = 7983511863:AAGTLwLrGF9ZsCu8imXUuq-qnD_OeHCIXM8
publish_bot_token = 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ123456789
admin_bot_token = 9876543210:ZYXwvuTSRqponMLKjihGFEdcBA987654321

channel_id = -1001234567890
admin_group_id = -1009876543210
review_group_id = -1005555666677

admin_users = 123456789,987654321
```

---

## 🎯 第四步：获取用户ID

### 如何获取您的用户ID
1. 发送任意消息给 [@userinfobot](https://t.me/userinfobot)
2. 机器人会返回您的用户ID
3. 将您的用户ID添加到 `admin_users` 中

---

## 🚀 第五步：启动系统

配置完成后，运行修复脚本：

```bash
python3 fix_submission_system.py
```

或者手动启动：

```bash
# 终止旧进程
pkill -f "python.*bot.py"

# 启动三个机器人
nohup python3 submission_bot.py &
nohup python3 publish_bot.py &
nohup python3 control_bot.py &
```

---

## 📱 第六步：测试系统

### 1. 测试投稿机器人
```
1. 向投稿机器人发送 /start
2. 发送测试消息
3. 查看是否收到确认
```

### 2. 测试审核流程
```
1. 检查审核群组是否收到投稿
2. 点击审核按钮进行审核
3. 查看频道是否发布内容
```

### 3. 测试控制机器人
```
1. 向控制机器人发送 /start
2. 使用 /status 查看系统状态
3. 测试各种管理功能
```

---

## ❓ 常见问题

### Q1: 如何知道配置是否正确？
运行 `python3 fix_submission_system.py` 会检查所有配置。

### Q2: 机器人无法添加到群组怎么办？
确保机器人用户名正确，搜索 @your_bot_username 添加。

### Q3: 获取不到群组ID怎么办？
1. 确保机器人已在群组中
2. 在群组中发送任意消息
3. 转发该消息给 @userinfobot

### Q4: 仍然显示待审核怎么办？
确保：
1. 发布机器人Token正确配置
2. 发布机器人正在运行
3. 审核群组ID正确配置
4. 发布机器人已添加到审核群组

---

## 🔧 快速修复命令

如果您已经有了所有Token和ID，可以直接编辑配置文件：

```bash
# 编辑配置文件
nano config.local.ini

# 运行修复脚本
python3 fix_submission_system.py
```

---

## 📞 获取帮助

如果按照以上步骤仍有问题：

1. 检查日志文件：`tail -f *.log`
2. 确认网络连接正常
3. 验证所有Token都是有效的
4. 确保机器人有足够的权限

配置完成后，您的投稿系统就能正常工作了！

---

*最后更新：2025-01-25*  
*版本：v2.3.0*