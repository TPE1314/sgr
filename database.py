import sqlite3
import datetime
import json
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 创建投稿表
        cursor.execute('''
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
        ''')
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_banned BOOLEAN DEFAULT FALSE,
                submission_count INTEGER DEFAULT 0,
                last_submission TIMESTAMP
            )
        ''')
        
        # 创建管理员操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_submission(self, user_id: int, username: str, content_type: str, 
                      content: str = None, media_file_id: str = None, 
                      caption: str = None) -> int:
        """添加新投稿"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO submissions (user_id, username, content_type, content, media_file_id, caption)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, content_type, content, media_file_id, caption))
        
        submission_id = cursor.lastrowid
        
        # 更新用户统计
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, submission_count, last_submission)
            VALUES (?, ?, 
                COALESCE((SELECT submission_count FROM users WHERE user_id = ?), 0) + 1,
                CURRENT_TIMESTAMP)
        ''', (user_id, username, user_id))
        
        conn.commit()
        conn.close()
        return submission_id
    
    def get_pending_submissions(self) -> List[Dict]:
        """获取待审核的投稿"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM submissions 
            WHERE status = 'pending' 
            ORDER BY submit_time ASC
        ''')
        
        submissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return submissions
    
    def approve_submission(self, submission_id: int, reviewer_id: int) -> bool:
        """批准投稿"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE submissions 
            SET status = 'approved', reviewer_id = ?, review_time = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'pending'
        ''', (reviewer_id, submission_id))
        
        success = cursor.rowcount > 0
        
        if success:
            # 记录管理员操作
            cursor.execute('''
                INSERT INTO admin_logs (admin_id, action, target_id)
                VALUES (?, 'approve', ?)
            ''', (reviewer_id, submission_id))
        
        conn.commit()
        conn.close()
        return success
    
    def reject_submission(self, submission_id: int, reviewer_id: int, reason: str = None) -> bool:
        """拒绝投稿"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE submissions 
            SET status = 'rejected', reviewer_id = ?, review_time = CURRENT_TIMESTAMP, reject_reason = ?
            WHERE id = ? AND status = 'pending'
        ''', (reviewer_id, reason, submission_id))
        
        success = cursor.rowcount > 0
        
        if success:
            # 记录管理员操作
            cursor.execute('''
                INSERT INTO admin_logs (admin_id, action, target_id, details)
                VALUES (?, 'reject', ?, ?)
            ''', (reviewer_id, submission_id, reason))
        
        conn.commit()
        conn.close()
        return success
    
    def mark_published(self, submission_id: int) -> bool:
        """标记为已发布"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE submissions 
            SET status = 'published', publish_time = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'approved'
        ''', (submission_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_submission_by_id(self, submission_id: int) -> Optional[Dict]:
        """根据ID获取投稿"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def get_approved_submissions(self) -> List[Dict]:
        """获取已批准但未发布的投稿"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM submissions 
            WHERE status = 'approved' 
            ORDER BY review_time ASC
        ''')
        
        submissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return submissions
    
    def get_user_stats(self, user_id: int) -> Dict:
        """获取用户统计信息"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'published' THEN 1 END) as published,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
            FROM submissions 
            WHERE user_id = ?
        ''', (user_id,))
        
        stats = dict(cursor.fetchone())
        conn.close()
        return stats
    
    def ban_user(self, user_id: int, admin_id: int) -> bool:
        """封禁用户"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET is_banned = TRUE WHERE user_id = ?
        ''', (user_id,))
        
        # 记录管理员操作
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_id)
            VALUES (?, 'ban_user', ?)
        ''', (admin_id, user_id))
        
        conn.commit()
        conn.close()
        return True
    
    def unban_user(self, user_id: int, admin_id: int) -> bool:
        """解封用户"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET is_banned = FALSE WHERE user_id = ?
        ''', (user_id,))
        
        # 记录管理员操作
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_id)
            VALUES (?, 'unban_user', ?)
        ''', (admin_id, user_id))
        
        conn.commit()
        conn.close()
        return True
    
    def is_user_banned(self, user_id: int) -> bool:
        """检查用户是否被封禁"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result and result[0] if result else False