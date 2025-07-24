#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
国际化和时区管理模块
Internationalization and Timezone Manager

提供全面的国际化功能，包括：
- 多语言界面支持
- 动态语言切换
- 时区处理和转换
- 本地化格式处理
- 语言包管理
- 用户偏好设置

作者: AI Assistant
创建时间: 2024-12-19
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
from dataclasses import dataclass, asdict
import locale

# 尝试导入时区库
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False

try:
    from babel import Locale, dates, numbers
    from babel.support import Format
    BABEL_AVAILABLE = True
except ImportError:
    BABEL_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class UserLocaleSettings:
    """用户本地化设置数据类"""
    user_id: int
    language: str = 'zh-CN'  # 默认中文
    timezone: str = 'Asia/Shanghai'  # 默认北京时间
    date_format: str = '%Y-%m-%d'
    time_format: str = '%H:%M:%S'
    datetime_format: str = '%Y-%m-%d %H:%M:%S'
    number_format: str = 'decimal'
    currency: str = 'CNY'
    first_day_of_week: int = 1  # 1=Monday, 0=Sunday

class LanguageManager:
    """
    语言管理器
    Language Manager
    
    管理多语言文本和动态语言切换
    """
    
    def __init__(self, languages_dir: str = "languages"):
        """
        初始化语言管理器
        
        Args:
            languages_dir: 语言包目录
        """
        self.languages_dir = languages_dir
        self.languages: Dict[str, Dict[str, str]] = {}
        self.default_language = 'zh-CN'
        self.supported_languages = {
            'zh-CN': '简体中文',
            'zh-TW': '繁體中文', 
            'en-US': 'English',
            'ja-JP': '日本語',
            'ko-KR': '한국어',
            'ru-RU': 'Русский',
            'fr-FR': 'Français',
            'de-DE': 'Deutsch',
            'es-ES': 'Español',
            'pt-BR': 'Português',
            'it-IT': 'Italiano',
            'ar-SA': 'العربية'
        }
        
        # 确保语言包目录存在
        os.makedirs(languages_dir, exist_ok=True)
        
        # 加载语言包
        self._load_languages()
        
        # 初始化默认语言包（如果不存在）
        self._initialize_default_languages()
        
        logger.info(f"语言管理器初始化完成: 支持 {len(self.languages)} 种语言")
    
    def _load_languages(self):
        """加载所有语言包"""
        try:
            for lang_file in Path(self.languages_dir).glob("*.json"):
                lang_code = lang_file.stem
                
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        language_data = json.load(f)
                        self.languages[lang_code] = language_data
                        logger.debug(f"加载语言包: {lang_code}")
                        
                except Exception as e:
                    logger.error(f"加载语言包失败: {lang_file}: {e}")
                    
        except Exception as e:
            logger.error(f"扫描语言包目录失败: {e}")
    
    def _initialize_default_languages(self):
        """初始化默认语言包"""
        # 中文语言包
        zh_cn_texts = {
            # 通用文本
            "common.yes": "是",
            "common.no": "否",
            "common.ok": "确定",
            "common.cancel": "取消",
            "common.save": "保存",
            "common.delete": "删除",
            "common.edit": "编辑",
            "common.view": "查看",
            "common.back": "返回",
            "common.next": "下一步",
            "common.previous": "上一步",
            "common.loading": "加载中...",
            "common.success": "成功",
            "common.error": "错误",
            "common.warning": "警告",
            "common.info": "信息",
            
            # 时间相关
            "time.now": "现在",
            "time.today": "今天",
            "time.yesterday": "昨天",
            "time.tomorrow": "明天",
            "time.this_week": "本周",
            "time.last_week": "上周",
            "time.next_week": "下周",
            "time.this_month": "本月",
            "time.last_month": "上月",
            "time.next_month": "下月",
            "time.this_year": "今年",
            "time.last_year": "去年",
            "time.next_year": "明年",
            
            # 星期
            "weekday.monday": "星期一",
            "weekday.tuesday": "星期二", 
            "weekday.wednesday": "星期三",
            "weekday.thursday": "星期四",
            "weekday.friday": "星期五",
            "weekday.saturday": "星期六",
            "weekday.sunday": "星期日",
            
            # 月份
            "month.january": "一月",
            "month.february": "二月",
            "month.march": "三月",
            "month.april": "四月",
            "month.may": "五月",
            "month.june": "六月",
            "month.july": "七月",
            "month.august": "八月",
            "month.september": "九月",
            "month.october": "十月",
            "month.november": "十一月",
            "month.december": "十二月",
            
            # 机器人相关
            "bot.welcome": "欢迎使用电报机器人系统",
            "bot.help": "帮助",
            "bot.settings": "设置",
            "bot.status": "状态",
            "bot.admin_panel": "管理面板",
            "bot.permission_denied": "您没有权限执行此操作",
            "bot.invalid_command": "无效的命令",
            "bot.processing": "正在处理...",
            
            # 投稿系统
            "submission.title": "投稿系统",
            "submission.submit": "提交投稿",
            "submission.submitted": "投稿已提交",
            "submission.approved": "投稿已通过",
            "submission.rejected": "投稿被拒绝",
            "submission.pending": "等待审核",
            "submission.review": "审核",
            "submission.approve": "通过",
            "submission.reject": "拒绝",
            
            # 用户管理
            "user.profile": "用户资料",
            "user.settings": "用户设置",
            "user.language": "语言",
            "user.timezone": "时区",
            "user.banned": "已封禁",
            "user.active": "活跃",
            "user.admin": "管理员",
            "user.moderator": "版主",
            "user.normal": "普通用户",
            
            # 文件处理
            "file.upload": "上传文件",
            "file.download": "下载文件",
            "file.processing": "处理文件中...",
            "file.processed": "文件处理完成",
            "file.failed": "文件处理失败",
            "file.too_large": "文件过大",
            "file.invalid_format": "无效的文件格式",
            
            # 系统管理
            "system.update": "系统更新",
            "system.restart": "重启系统",
            "system.backup": "备份",
            "system.restore": "恢复",
            "system.maintenance": "维护中",
            "system.online": "在线",
            "system.offline": "离线",
            
            # 通知消息
            "notification.new_submission": "新投稿: {title}",
            "notification.submission_approved": "您的投稿已通过审核",
            "notification.submission_rejected": "您的投稿被拒绝: {reason}",
            "notification.system_update": "系统更新完成",
            "notification.maintenance": "系统将在 {time} 进行维护",
            
            # 错误消息
            "error.network": "网络连接错误",
            "error.database": "数据库错误",
            "error.permission": "权限不足",
            "error.not_found": "未找到",
            "error.invalid_input": "输入无效",
            "error.system": "系统错误",
            "error.timeout": "操作超时",
            
            # 设置页面
            "settings.title": "设置",
            "settings.language_changed": "语言已更改为中文",
            "settings.timezone_changed": "时区已更改为 {timezone}",
            "settings.saved": "设置已保存",
            "settings.reset": "重置设置",
        }
        
        # 英文语言包
        en_us_texts = {
            # 通用文本
            "common.yes": "Yes",
            "common.no": "No", 
            "common.ok": "OK",
            "common.cancel": "Cancel",
            "common.save": "Save",
            "common.delete": "Delete",
            "common.edit": "Edit",
            "common.view": "View",
            "common.back": "Back",
            "common.next": "Next",
            "common.previous": "Previous",
            "common.loading": "Loading...",
            "common.success": "Success",
            "common.error": "Error",
            "common.warning": "Warning",
            "common.info": "Information",
            
            # 时间相关
            "time.now": "Now",
            "time.today": "Today",
            "time.yesterday": "Yesterday",
            "time.tomorrow": "Tomorrow",
            "time.this_week": "This Week",
            "time.last_week": "Last Week",
            "time.next_week": "Next Week",
            "time.this_month": "This Month",
            "time.last_month": "Last Month",
            "time.next_month": "Next Month",
            "time.this_year": "This Year",
            "time.last_year": "Last Year",
            "time.next_year": "Next Year",
            
            # 星期
            "weekday.monday": "Monday",
            "weekday.tuesday": "Tuesday",
            "weekday.wednesday": "Wednesday", 
            "weekday.thursday": "Thursday",
            "weekday.friday": "Friday",
            "weekday.saturday": "Saturday",
            "weekday.sunday": "Sunday",
            
            # 月份
            "month.january": "January",
            "month.february": "February",
            "month.march": "March",
            "month.april": "April",
            "month.may": "May",
            "month.june": "June",
            "month.july": "July",
            "month.august": "August",
            "month.september": "September",
            "month.october": "October",
            "month.november": "November",
            "month.december": "December",
            
            # 机器人相关
            "bot.welcome": "Welcome to Telegram Bot System",
            "bot.help": "Help",
            "bot.settings": "Settings",
            "bot.status": "Status",
            "bot.admin_panel": "Admin Panel",
            "bot.permission_denied": "Permission denied",
            "bot.invalid_command": "Invalid command",
            "bot.processing": "Processing...",
            
            # 投稿系统
            "submission.title": "Submission System",
            "submission.submit": "Submit",
            "submission.submitted": "Submitted",
            "submission.approved": "Approved",
            "submission.rejected": "Rejected",
            "submission.pending": "Pending",
            "submission.review": "Review",
            "submission.approve": "Approve",
            "submission.reject": "Reject",
            
            # 用户管理
            "user.profile": "User Profile",
            "user.settings": "User Settings",
            "user.language": "Language",
            "user.timezone": "Timezone",
            "user.banned": "Banned",
            "user.active": "Active",
            "user.admin": "Administrator",
            "user.moderator": "Moderator",
            "user.normal": "Normal User",
            
            # 文件处理
            "file.upload": "Upload File",
            "file.download": "Download File",
            "file.processing": "Processing file...",
            "file.processed": "File processed",
            "file.failed": "File processing failed",
            "file.too_large": "File too large",
            "file.invalid_format": "Invalid file format",
            
            # 系统管理
            "system.update": "System Update",
            "system.restart": "Restart System",
            "system.backup": "Backup",
            "system.restore": "Restore",
            "system.maintenance": "Under Maintenance",
            "system.online": "Online",
            "system.offline": "Offline",
            
            # 通知消息
            "notification.new_submission": "New submission: {title}",
            "notification.submission_approved": "Your submission has been approved",
            "notification.submission_rejected": "Your submission was rejected: {reason}",
            "notification.system_update": "System update completed",
            "notification.maintenance": "System maintenance at {time}",
            
            # 错误消息
            "error.network": "Network connection error",
            "error.database": "Database error", 
            "error.permission": "Insufficient permissions",
            "error.not_found": "Not found",
            "error.invalid_input": "Invalid input",
            "error.system": "System error",
            "error.timeout": "Operation timeout",
            
            # 设置页面
            "settings.title": "Settings",
            "settings.language_changed": "Language changed to English",
            "settings.timezone_changed": "Timezone changed to {timezone}",
            "settings.saved": "Settings saved",
            "settings.reset": "Reset Settings",
        }
        
        # 保存语言包
        self._save_language_pack('zh-CN', zh_cn_texts)
        self._save_language_pack('en-US', en_us_texts)
    
    def _save_language_pack(self, language: str, texts: Dict[str, str]):
        """
        保存语言包到文件
        
        Args:
            language: 语言代码
            texts: 文本字典
        """
        try:
            file_path = Path(self.languages_dir) / f"{language}.json"
            
            # 如果文件已存在且有内容，则不覆盖
            if file_path.exists() and file_path.stat().st_size > 100:
                return
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(texts, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的语言包
            self.languages[language] = texts
            
            logger.info(f"保存语言包: {language}")
            
        except Exception as e:
            logger.error(f"保存语言包失败: {language}: {e}")
    
    def get_text(self, key: str, language: str = None, **kwargs) -> str:
        """
        获取本地化文本
        
        Args:
            key: 文本键
            language: 语言代码，默认使用系统默认语言
            **kwargs: 格式化参数
            
        Returns:
            str: 本地化文本
        """
        language = language or self.default_language
        
        # 获取语言包
        lang_pack = self.languages.get(language)
        if not lang_pack:
            # 如果指定语言不存在，使用默认语言
            lang_pack = self.languages.get(self.default_language, {})
        
        # 获取文本
        text = lang_pack.get(key, key)  # 如果找不到，返回键本身
        
        # 格式化文本
        try:
            if kwargs:
                text = text.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"文本格式化失败: {key}: {e}")
        
        return text
    
    def add_text(self, language: str, key: str, text: str):
        """
        添加或更新文本
        
        Args:
            language: 语言代码
            key: 文本键
            text: 文本内容
        """
        if language not in self.languages:
            self.languages[language] = {}
        
        self.languages[language][key] = text
        
        # 保存到文件
        try:
            file_path = Path(self.languages_dir) / f"{language}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.languages[language], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存文本失败: {language}.{key}: {e}")
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        获取支持的语言列表
        
        Returns:
            Dict[str, str]: 语言代码到语言名称的映射
        """
        return self.supported_languages.copy()
    
    def is_language_supported(self, language: str) -> bool:
        """
        检查语言是否被支持
        
        Args:
            language: 语言代码
            
        Returns:
            bool: 是否支持
        """
        return language in self.languages
    
    def reload_languages(self):
        """重新加载所有语言包"""
        self.languages.clear()
        self._load_languages()
        logger.info("语言包已重新加载")

class TimezoneManager:
    """
    时区管理器
    Timezone Manager
    
    管理时区转换和本地化时间显示
    """
    
    def __init__(self):
        """初始化时区管理器"""
        self.default_timezone = 'Asia/Shanghai'
        
        # 常用时区列表
        self.common_timezones = {
            'Asia/Shanghai': '北京时间 (UTC+8)',
            'Asia/Tokyo': '东京时间 (UTC+9)',
            'Asia/Seoul': '首尔时间 (UTC+9)',
            'Asia/Taipei': '台北时间 (UTC+8)',
            'Asia/Hong_Kong': '香港时间 (UTC+8)',
            'Asia/Singapore': '新加坡时间 (UTC+8)',
            'Asia/Bangkok': '曼谷时间 (UTC+7)',
            'Asia/Dubai': '迪拜时间 (UTC+4)',
            'Europe/London': '伦敦时间 (UTC+0/+1)',
            'Europe/Paris': '巴黎时间 (UTC+1/+2)',
            'Europe/Berlin': '柏林时间 (UTC+1/+2)',
            'Europe/Moscow': '莫斯科时间 (UTC+3)',
            'America/New_York': '纽约时间 (UTC-5/-4)',
            'America/Los_Angeles': '洛杉矶时间 (UTC-8/-7)',
            'America/Chicago': '芝加哥时间 (UTC-6/-5)',
            'America/Denver': '丹佛时间 (UTC-7/-6)',
            'America/Toronto': '多伦多时间 (UTC-5/-4)',
            'America/Sao_Paulo': '圣保罗时间 (UTC-3/-2)',
            'Australia/Sydney': '悉尼时间 (UTC+10/+11)',
            'Australia/Melbourne': '墨尔本时间 (UTC+10/+11)',
            'Pacific/Auckland': '奥克兰时间 (UTC+12/+13)',
            'UTC': '协调世界时 (UTC+0)'
        }
        
        logger.info("时区管理器初始化完成")
    
    def get_timezone_info(self, timezone_name: str) -> Dict[str, Any]:
        """
        获取时区信息
        
        Args:
            timezone_name: 时区名称
            
        Returns:
            Dict: 时区信息
        """
        try:
            if PYTZ_AVAILABLE:
                tz = pytz.timezone(timezone_name)
                now = datetime.now(tz)
                
                return {
                    'name': timezone_name,
                    'display_name': self.common_timezones.get(timezone_name, timezone_name),
                    'offset': now.strftime('%z'),
                    'offset_hours': now.utcoffset().total_seconds() / 3600,
                    'is_dst': now.dst() != timedelta(0),
                    'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z')
                }
            else:
                # 简单的时区处理
                return {
                    'name': timezone_name,
                    'display_name': self.common_timezones.get(timezone_name, timezone_name),
                    'offset': '+0000',
                    'offset_hours': 0,
                    'is_dst': False,
                    'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"获取时区信息失败: {timezone_name}: {e}")
            return self.get_timezone_info(self.default_timezone)
    
    def convert_time(self, 
                    dt: datetime, 
                    from_tz: str = None, 
                    to_tz: str = None) -> datetime:
        """
        转换时间到指定时区
        
        Args:
            dt: 时间对象
            from_tz: 源时区
            to_tz: 目标时区
            
        Returns:
            datetime: 转换后的时间
        """
        try:
            if not PYTZ_AVAILABLE:
                # 简单处理，直接返回原时间
                return dt
            
            # 设置默认时区
            from_tz = from_tz or self.default_timezone
            to_tz = to_tz or self.default_timezone
            
            # 如果时间没有时区信息，添加源时区
            if dt.tzinfo is None:
                source_tz = pytz.timezone(from_tz)
                dt = source_tz.localize(dt)
            
            # 转换到目标时区
            target_tz = pytz.timezone(to_tz)
            converted_dt = dt.astimezone(target_tz)
            
            return converted_dt
            
        except Exception as e:
            logger.error(f"时区转换失败: {e}")
            return dt
    
    def format_time(self, 
                   dt: datetime, 
                   timezone_name: str = None,
                   format_string: str = None,
                   language: str = 'zh-CN') -> str:
        """
        格式化时间显示
        
        Args:
            dt: 时间对象
            timezone_name: 时区名称
            format_string: 格式字符串
            language: 语言代码
            
        Returns:
            str: 格式化后的时间字符串
        """
        try:
            # 转换时区
            if timezone_name:
                dt = self.convert_time(dt, to_tz=timezone_name)
            
            # 默认格式
            if not format_string:
                format_string = '%Y-%m-%d %H:%M:%S'
            
            # 使用Babel进行本地化格式化（如果可用）
            if BABEL_AVAILABLE:
                try:
                    locale_obj = Locale.parse(language.replace('-', '_'))
                    
                    if '%Y-%m-%d %H:%M:%S' in format_string:
                        # 使用Babel的日期时间格式化
                        return dates.format_datetime(dt, locale=locale_obj)
                    elif '%Y-%m-%d' in format_string:
                        # 只格式化日期
                        return dates.format_date(dt, locale=locale_obj)
                    elif '%H:%M:%S' in format_string:
                        # 只格式化时间
                        return dates.format_time(dt, locale=locale_obj)
                        
                except Exception as e:
                    logger.debug(f"Babel格式化失败: {e}")
            
            # 使用标准格式化
            return dt.strftime(format_string)
            
        except Exception as e:
            logger.error(f"时间格式化失败: {e}")
            return str(dt)
    
    def get_relative_time(self, 
                         dt: datetime, 
                         language: str = 'zh-CN') -> str:
        """
        获取相对时间描述
        
        Args:
            dt: 时间对象
            language: 语言代码
            
        Returns:
            str: 相对时间描述
        """
        try:
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            diff = now - dt
            
            # 根据语言选择文本
            if language.startswith('zh'):
                if diff.days > 365:
                    return f"{diff.days // 365}年前"
                elif diff.days > 30:
                    return f"{diff.days // 30}个月前"
                elif diff.days > 0:
                    return f"{diff.days}天前"
                elif diff.seconds > 3600:
                    return f"{diff.seconds // 3600}小时前"
                elif diff.seconds > 60:
                    return f"{diff.seconds // 60}分钟前"
                else:
                    return "刚刚"
            else:
                if diff.days > 365:
                    years = diff.days // 365
                    return f"{years} year{'s' if years > 1 else ''} ago"
                elif diff.days > 30:
                    months = diff.days // 30
                    return f"{months} month{'s' if months > 1 else ''} ago"
                elif diff.days > 0:
                    return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
                elif diff.seconds > 3600:
                    hours = diff.seconds // 3600
                    return f"{hours} hour{'s' if hours > 1 else ''} ago"
                elif diff.seconds > 60:
                    minutes = diff.seconds // 60
                    return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                else:
                    return "just now"
                    
        except Exception as e:
            logger.error(f"相对时间计算失败: {e}")
            return str(dt)
    
    def get_common_timezones(self) -> Dict[str, str]:
        """
        获取常用时区列表
        
        Returns:
            Dict[str, str]: 时区代码到显示名称的映射
        """
        return self.common_timezones.copy()

class LocaleManager:
    """
    本地化管理器
    Locale Manager
    
    整合语言和时区管理，提供完整的本地化功能
    """
    
    def __init__(self, languages_dir: str = "languages"):
        """
        初始化本地化管理器
        
        Args:
            languages_dir: 语言包目录
        """
        self.language_manager = LanguageManager(languages_dir)
        self.timezone_manager = TimezoneManager()
        self.user_settings: Dict[int, UserLocaleSettings] = {}
        
        logger.info("本地化管理器初始化完成")
    
    def set_user_locale(self, user_id: int, settings: UserLocaleSettings):
        """
        设置用户本地化偏好
        
        Args:
            user_id: 用户ID
            settings: 本地化设置
        """
        self.user_settings[user_id] = settings
        logger.debug(f"设置用户本地化: {user_id} -> {settings.language}/{settings.timezone}")
    
    def get_user_locale(self, user_id: int) -> UserLocaleSettings:
        """
        获取用户本地化设置
        
        Args:
            user_id: 用户ID
            
        Returns:
            UserLocaleSettings: 用户本地化设置
        """
        return self.user_settings.get(user_id, UserLocaleSettings(user_id=user_id))
    
    def get_user_text(self, user_id: int, key: str, **kwargs) -> str:
        """
        获取用户的本地化文本
        
        Args:
            user_id: 用户ID
            key: 文本键
            **kwargs: 格式化参数
            
        Returns:
            str: 本地化文本
        """
        settings = self.get_user_locale(user_id)
        return self.language_manager.get_text(key, settings.language, **kwargs)
    
    def format_user_time(self, 
                        user_id: int, 
                        dt: datetime, 
                        format_type: str = 'datetime') -> str:
        """
        格式化用户时间
        
        Args:
            user_id: 用户ID
            dt: 时间对象
            format_type: 格式类型 (datetime, date, time, relative)
            
        Returns:
            str: 格式化后的时间
        """
        settings = self.get_user_locale(user_id)
        
        if format_type == 'relative':
            return self.timezone_manager.get_relative_time(dt, settings.language)
        
        # 选择格式字符串
        format_map = {
            'datetime': settings.datetime_format,
            'date': settings.date_format,
            'time': settings.time_format
        }
        format_string = format_map.get(format_type, settings.datetime_format)
        
        return self.timezone_manager.format_time(
            dt, settings.timezone, format_string, settings.language
        )
    
    def change_user_language(self, user_id: int, language: str) -> bool:
        """
        更改用户语言
        
        Args:
            user_id: 用户ID
            language: 新语言代码
            
        Returns:
            bool: 是否成功
        """
        if not self.language_manager.is_language_supported(language):
            return False
        
        settings = self.get_user_locale(user_id)
        settings.language = language
        self.set_user_locale(user_id, settings)
        
        return True
    
    def change_user_timezone(self, user_id: int, timezone_name: str) -> bool:
        """
        更改用户时区
        
        Args:
            user_id: 用户ID
            timezone_name: 新时区名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 验证时区
            self.timezone_manager.get_timezone_info(timezone_name)
            
            settings = self.get_user_locale(user_id)
            settings.timezone = timezone_name
            self.set_user_locale(user_id, settings)
            
            return True
            
        except Exception as e:
            logger.error(f"更改用户时区失败: {e}")
            return False
    
    def get_locale_stats(self) -> Dict[str, Any]:
        """
        获取本地化统计信息
        
        Returns:
            Dict: 统计信息
        """
        language_stats = {}
        timezone_stats = {}
        
        for settings in self.user_settings.values():
            # 语言统计
            lang = settings.language
            language_stats[lang] = language_stats.get(lang, 0) + 1
            
            # 时区统计
            tz = settings.timezone
            timezone_stats[tz] = timezone_stats.get(tz, 0) + 1
        
        return {
            'total_users': len(self.user_settings),
            'languages': {
                'supported': list(self.language_manager.get_supported_languages().keys()),
                'loaded': list(self.language_manager.languages.keys()),
                'usage': language_stats
            },
            'timezones': {
                'common': list(self.timezone_manager.get_common_timezones().keys()),
                'usage': timezone_stats
            },
            'features': {
                'pytz_available': PYTZ_AVAILABLE,
                'babel_available': BABEL_AVAILABLE
            }
        }

# 全局本地化管理器实例
_locale_manager: Optional[LocaleManager] = None

def get_locale_manager() -> LocaleManager:
    """
    获取全局本地化管理器实例
    
    Returns:
        LocaleManager: 本地化管理器实例
    """
    global _locale_manager
    if _locale_manager is None:
        _locale_manager = LocaleManager()
    return _locale_manager

def initialize_locale_manager(languages_dir: str = "languages") -> LocaleManager:
    """
    初始化全局本地化管理器
    
    Args:
        languages_dir: 语言包目录
        
    Returns:
        LocaleManager: 本地化管理器实例
    """
    global _locale_manager
    _locale_manager = LocaleManager(languages_dir)
    return _locale_manager

def _(user_id: int, key: str, **kwargs) -> str:
    """
    快捷本地化文本获取函数
    
    Args:
        user_id: 用户ID
        key: 文本键
        **kwargs: 格式化参数
        
    Returns:
        str: 本地化文本
    """
    return get_locale_manager().get_user_text(user_id, key, **kwargs)