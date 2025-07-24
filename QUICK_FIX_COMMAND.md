# 🚨 快速修复命令

## 如果您遇到 `ModuleNotFoundError: No module named 'database'` 错误

**请直接复制粘贴以下命令运行：**

```bash
# 一行命令紧急修复
python3 -c "
import os
import sys

# 创建database.py文件
database_content = '''import sqlite3
import datetime
import json
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = None
        self.init_database()
    
    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file)
        return self.conn
    
    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute(\\\"\\\"\\\"
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                content_type TEXT NOT NULL,
                content TEXT,
                media_file_id TEXT,
                caption TEXT,
                status TEXT DEFAULT 'pending',
                submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                review_time TIMESTAMP,
                publish_time TIMESTAMP,
                reviewer_id INTEGER,
                reject_reason TEXT
            )
        \\\"\\\"\\\")
        
        cursor.execute(\\\"\\\"\\\"
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_banned BOOLEAN DEFAULT FALSE,
                submission_count INTEGER DEFAULT 0,
                last_submission_time TIMESTAMP,
                registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        \\\"\\\"\\\")
        
        cursor.execute(\\\"\\\"\\\"
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                permission_level INTEGER DEFAULT 1,
                added_by INTEGER,
                added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        \\\"\\\"\\\")
        
        cursor.execute(\\\"\\\"\\\"
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        \\\"\\\"\\\")
        
        cursor.execute(\\\"\\\"\\\"
            CREATE TABLE IF NOT EXISTS advertisements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                ad_type TEXT DEFAULT 'text',
                position TEXT DEFAULT 'bottom',
                status TEXT DEFAULT 'active',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                click_count INTEGER DEFAULT 0
            )
        \\\"\\\"\\\")
        
        conn.commit()
        conn.close()
    
    def add_submission(self, user_id: int, username: str, content_type: str, 
                      content: str = None, media_file_id: str = None, caption: str = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\"\\\"\\\"
            INSERT INTO submissions (user_id, username, content_type, content, media_file_id, caption)
            VALUES (?, ?, ?, ?, ?, ?)
        \\\"\\\"\\\", (user_id, username, content_type, content, media_file_id, caption))
        
        submission_id = cursor.lastrowid
        conn.commit()
        return submission_id
    
    def get_pending_submissions(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\"\\\"\\\"
            SELECT * FROM submissions WHERE status = 'pending' ORDER BY submit_time ASC
        \\\"\\\"\\\")
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_submission_status(self, submission_id: int, status: str, reviewer_id: int = None, reject_reason: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status == 'approved':
            cursor.execute(\\\"\\\"\\\"
                UPDATE submissions SET status = ?, reviewer_id = ?, review_time = CURRENT_TIMESTAMP
                WHERE id = ?
            \\\"\\\"\\\", (status, reviewer_id, submission_id))
        elif status == 'rejected':
            cursor.execute(\\\"\\\"\\\"
                UPDATE submissions SET status = ?, reviewer_id = ?, reject_reason = ?, review_time = CURRENT_TIMESTAMP
                WHERE id = ?
            \\\"\\\"\\\", (status, reviewer_id, reject_reason, submission_id))
        else:
            cursor.execute(\\\"\\\"\\\"
                UPDATE submissions SET status = ? WHERE id = ?
            \\\"\\\"\\\", (status, submission_id))
        
        conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\"\\\"\\\"
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        \\\"\\\"\\\", (user_id, username, first_name, last_name))
        
        conn.commit()
    
    def get_config(self, key: str, default=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return default
    
    def set_config(self, key: str, value: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\"\\\"\\\"
            INSERT OR REPLACE INTO config (key, value, updated_time)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        \\\"\\\"\\\", (key, value))
        
        conn.commit()
'''

# 写入database.py文件
with open('database.py', 'w', encoding='utf-8') as f:
    f.write(database_content)

print('✅ database.py 文件已创建')

# 设置Python路径
sys.path.insert(0, os.getcwd())
os.environ['PYTHONPATH'] = os.getcwd()

# 测试导入
try:
    from database import DatabaseManager
    db = DatabaseManager('telegram_bot.db')
    print('✅ 数据库导入和初始化成功')
    print('🎉 问题已修复！现在可以重新运行安装脚本')
except Exception as e:
    print(f'❌ 测试失败: {e}')
"
```

## 或者使用简化版本：

```bash
# 下载并运行紧急修复脚本
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/emergency_db_fix_v2_3_0.py | python3
```

## 修复完成后：

```bash
# 重新运行一键安装脚本
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/quick_setup.sh | bash

# 或者如果已下载，直接运行
./quick_setup.sh
```

## 验证修复：

```bash
# 检查database.py文件是否存在
ls -la database.py

# 测试数据库导入
python3 -c "from database import DatabaseManager; print('✅ 导入成功')"
```

---

**复制上面的命令直接运行即可修复问题！** 🚀