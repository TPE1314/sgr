import configparser
import os
from typing import List

class ConfigManager:
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")
        
        self.config.read(self.config_file, encoding='utf-8')
    
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
        """检查用户是否为管理员"""
        return user_id in self.get_admin_users()