# 🔐 安全配置指南

## ⚠️ 重要安全提醒

**绝对不要将真实的Bot Token提交到公共仓库！**

## 📋 配置文件说明

### 🔒 `config.local.ini` (本地配置)
- **用途**: 存储真实的Token和敏感配置
- **位置**: 项目根目录
- **特点**: 已添加到 `.gitignore`，不会被提交到仓库
- **示例**:
```ini
[telegram]
submission_bot_token = 你的真实Token
publish_bot_token = 你的真实Token
admin_bot_token = 你的真实Token
```

### 📝 `config.ini` (模板配置)
- **用途**: 作为配置模板和示例
- **位置**: 项目根目录  
- **特点**: 使用占位符，可以安全地提交到仓库
- **示例**:
```ini
[telegram]
submission_bot_token = YOUR_SUBMISSION_BOT_TOKEN
publish_bot_token = YOUR_PUBLISH_BOT_TOKEN
admin_bot_token = YOUR_ADMIN_BOT_TOKEN
```

## 🔄 配置加载优先级

系统会按以下顺序加载配置：
1. **优先**: `config.local.ini` (如果存在)
2. **备用**: `config.ini` (如果本地配置不存在)

## 🛡️ 安全最佳实践

### ✅ 应该做的
- 将真实Token写入 `config.local.ini`
- 确保 `config.local.ini` 在 `.gitignore` 中
- 定期更换Bot Token
- 只在必要时分享Token

### ❌ 不应该做的
- 将真实Token写入 `config.ini`
- 将 `config.local.ini` 提交到仓库
- 在公共场所泄露Token
- 使用弱密码保护服务器

## 📂 文件结构
```
项目根目录/
├── config.ini          # 模板配置 (可提交)
├── config.local.ini     # 真实配置 (不提交)
├── .gitignore          # 包含 config.local.ini
└── 其他文件...
```

## 🔧 如何配置

1. **复制模板**:
```bash
cp config.ini config.local.ini
```

2. **编辑本地配置**:
```bash
nano config.local.ini
```

3. **填入真实Token并保存**

4. **验证**: 系统会自动优先使用 `config.local.ini`

## 🚨 紧急情况

如果Token泄露：
1. 立即到 [@BotFather](https://t.me/botfather) 重新生成Token
2. 更新 `config.local.ini` 中的Token
3. 重启相关机器人
4. 检查是否有未授权使用

---
**记住**: 保护Token就是保护您的机器人安全！