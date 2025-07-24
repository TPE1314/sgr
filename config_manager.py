import configparser
import os
from typing import List

class ConfigManager:
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件，优先使用本地配置"""
        # 优先使用本地配置文件（包含真实Token）
        local_config = "config.local.ini"
        if os.path.exists(local_config):
            self.config.read(local_config, encoding='utf-8')
            print(f"✅ 已加载本地配置文件: {local_config}")
        elif os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
            print(f"✅ 已加载配置文件: {self.config_file}")
        else:
            raise FileNotFoundError(f"配置文件 {self.config_file} 和 {local_config} 都不存在")
    
    def get_submission_bot_token(self) -> str:
        """获取投稿机器人token"""
        return self.config.get('telegram', 'submission_bot_token')
    
    def get_publish_bot_token(self) -> str:
        """获取发布机器人token"""
        return self.config.get('telegram', 'publish_bot_token')
    
    def get_admin_bot_token(self) -> str:
        """获取管理机器人token"""
        return self.config.get('telegram', 'admin_bot_token')
    
    def get_channel_id(self) -> str:
        """获取频道ID"""
        return self.config.get('telegram', 'channel_id')
    
    def get_admin_group_id(self) -> str:
        """获取管理员群组ID"""
        return self.config.get('telegram', 'admin_group_id')
    
    def get_review_group_id(self) -> str:
        """获取审核群组ID"""
        return self.config.get('telegram', 'review_group_id')
    
    def get_admin_users(self) -> List[int]:
        """获取管理员用户ID列表"""
        admin_users_str = self.config.get('telegram', 'admin_users')
        return [int(user_id.strip()) for user_id in admin_users_str.split(',') if user_id.strip()]
    
    def get_db_file(self) -> str:
        """获取数据库文件路径"""
        return self.config.get('database', 'db_file')
    
    def require_approval(self) -> bool:
        """是否需要管理员审核"""
        return self.config.getboolean('settings', 'require_approval')
    
    def get_auto_publish_delay(self) -> int:
        """获取自动发布延迟时间"""
        return self.config.getint('settings', 'auto_publish_delay')
    
    def is_admin(self, user_id: int) -> bool:
        """检查用户是否为管理员（包括动态管理员）"""
        # 检查配置文件中的管理员
        if user_id in self.get_admin_users():
            return True
        
        # 检查动态管理员
        try:
            from database import DatabaseManager
            db = DatabaseManager(self.get_db_file())
            return db.is_dynamic_admin(user_id)
        except:
            return False
    
    def is_super_admin(self, user_id: int) -> bool:
        """检查用户是否为超级管理员（配置文件中的管理员）"""
        return user_id in self.get_admin_users()
    
    def get_admin_level(self, user_id: int) -> str:
        """获取管理员级别"""
        if self.is_super_admin(user_id):
            return "super"
        elif self.is_admin(user_id):
            try:
                from database import DatabaseManager
                db = DatabaseManager(self.get_db_file())
                return db.get_admin_permissions(user_id) or "basic"
            except:
                return "basic"
        return "none"