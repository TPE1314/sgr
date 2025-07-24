#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
广告管理模块
Advertisement Manager Module

提供全面的广告管理功能，包括：
- 广告内容管理（增删改查）
- 广告展示策略配置
- 广告统计和分析
- 广告轮播和随机展示
- 广告有效期管理
- 广告位置控制

作者: AI Assistant
创建时间: 2024-12-19
"""

import logging
import json
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3

logger = logging.getLogger(__name__)

class AdPosition(Enum):
    """广告位置枚举"""
    BEFORE_CONTENT = "before_content"    # 内容前
    AFTER_CONTENT = "after_content"      # 内容后
    MIDDLE_CONTENT = "middle_content"    # 内容中间（长内容）

class AdType(Enum):
    """广告类型枚举"""
    TEXT = "text"                        # 纯文本广告
    LINK = "link"                        # 链接广告
    IMAGE = "image"                      # 图片广告
    VIDEO = "video"                      # 视频广告
    BUTTON = "button"                    # 按钮广告

class AdStatus(Enum):
    """广告状态枚举"""
    ACTIVE = "active"                    # 激活
    PAUSED = "paused"                    # 暂停
    EXPIRED = "expired"                  # 过期
    DRAFT = "draft"                      # 草稿

@dataclass
class Advertisement:
    """广告数据类"""
    id: int                              # 广告ID
    name: str                            # 广告名称
    type: AdType                         # 广告类型
    position: AdPosition                 # 显示位置
    content: str                         # 广告内容
    url: Optional[str] = None            # 链接地址
    button_text: Optional[str] = None    # 按钮文字
    media_path: Optional[str] = None     # 媒体文件路径
    priority: int = 1                    # 优先级 (1-10, 数字越大优先级越高)
    weight: int = 1                      # 权重 (影响随机选择概率)
    status: AdStatus = AdStatus.DRAFT    # 状态
    start_date: Optional[datetime] = None # 开始时间
    end_date: Optional[datetime] = None   # 结束时间
    max_displays: Optional[int] = None   # 最大展示次数
    display_count: int = 0               # 已展示次数
    click_count: int = 0                 # 点击次数
    created_by: int = 0                  # 创建者ID
    created_at: Optional[datetime] = None # 创建时间
    updated_at: Optional[datetime] = None # 更新时间
    tags: Optional[List[str]] = None     # 标签
    target_content_types: Optional[List[str]] = None  # 目标内容类型

@dataclass
class AdDisplayConfig:
    """广告展示配置"""
    enabled: bool = True                 # 是否启用广告
    max_ads_per_post: int = 3           # 每篇文章最大广告数
    min_ads_per_post: int = 0           # 每篇文章最小广告数
    position_weights: Dict[AdPosition, float] = None  # 位置权重
    show_ad_label: bool = True          # 是否显示"广告"标签
    ad_separator: str = "\n\n━━━━━━━━━━\n\n"  # 广告分隔符
    random_selection: bool = True        # 是否随机选择广告

class AdvertisementManager:
    """
    广告管理器
    Advertisement Manager
    
    管理所有广告相关功能
    """
    
    def __init__(self, db_file: str):
        """
        初始化广告管理器
        
        Args:
            db_file: 数据库文件路径
        """
        self.db_file = db_file
        self.config = AdDisplayConfig()
        
        # 初始化数据库表
        self._init_database()
        
        logger.info("广告管理器初始化完成")
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 广告表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS advertisements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        position TEXT NOT NULL,
                        content TEXT NOT NULL,
                        url TEXT,
                        button_text TEXT,
                        media_path TEXT,
                        priority INTEGER DEFAULT 1,
                        weight INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'draft',
                        start_date TIMESTAMP,
                        end_date TIMESTAMP,
                        max_displays INTEGER,
                        display_count INTEGER DEFAULT 0,
                        click_count INTEGER DEFAULT 0,
                        created_by INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tags TEXT,
                        target_content_types TEXT
                    )
                ''')
                
                # 广告展示记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ad_display_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ad_id INTEGER,
                        submission_id INTEGER,
                        channel_message_id INTEGER,
                        position TEXT,
                        displayed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_clicked BOOLEAN DEFAULT FALSE,
                        clicked_at TIMESTAMP,
                        FOREIGN KEY (ad_id) REFERENCES advertisements (id)
                    )
                ''')
                
                # 广告配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ad_config (
                        id INTEGER PRIMARY KEY,
                        config_data TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("广告数据库表初始化完成")
                
        except Exception as e:
            logger.error(f"初始化广告数据库失败: {e}")
            raise
    
    def create_advertisement(self, ad: Advertisement) -> int:
        """
        创建广告
        
        Args:
            ad: 广告对象
            
        Returns:
            int: 新创建的广告ID
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 设置创建时间
                ad.created_at = datetime.now()
                ad.updated_at = datetime.now()
                
                cursor.execute('''
                    INSERT INTO advertisements (
                        name, type, position, content, url, button_text, media_path,
                        priority, weight, status, start_date, end_date, max_displays,
                        display_count, click_count, created_by, created_at, updated_at,
                        tags, target_content_types
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ad.name, ad.type.value, ad.position.value, ad.content,
                    ad.url, ad.button_text, ad.media_path, ad.priority, ad.weight,
                    ad.status.value, ad.start_date, ad.end_date, ad.max_displays,
                    ad.display_count, ad.click_count, ad.created_by,
                    ad.created_at, ad.updated_at,
                    json.dumps(ad.tags) if ad.tags else None,
                    json.dumps(ad.target_content_types) if ad.target_content_types else None
                ))
                
                ad_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"创建广告成功: {ad.name} (ID: {ad_id})")
                return ad_id
                
        except Exception as e:
            logger.error(f"创建广告失败: {e}")
            raise
    
    def update_advertisement(self, ad_id: int, updates: Dict[str, Any]) -> bool:
        """
        更新广告
        
        Args:
            ad_id: 广告ID
            updates: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        try:
            if not updates:
                return False
            
            # 添加更新时间
            updates['updated_at'] = datetime.now()
            
            # 构建SQL
            set_clause = ', '.join(f"{key} = ?" for key in updates.keys())
            values = list(updates.values())
            values.append(ad_id)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute(f'''
                    UPDATE advertisements 
                    SET {set_clause}
                    WHERE id = ?
                ''', values)
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"更新广告成功: ID {ad_id}")
                    return True
                else:
                    logger.warning(f"广告不存在: ID {ad_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"更新广告失败: {e}")
            return False
    
    def delete_advertisement(self, ad_id: int) -> bool:
        """
        删除广告
        
        Args:
            ad_id: 广告ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM advertisements WHERE id = ?', (ad_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"删除广告成功: ID {ad_id}")
                    return True
                else:
                    logger.warning(f"广告不存在: ID {ad_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"删除广告失败: {e}")
            return False
    
    def get_advertisement(self, ad_id: int) -> Optional[Advertisement]:
        """
        获取单个广告
        
        Args:
            ad_id: 广告ID
            
        Returns:
            Advertisement: 广告对象
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM advertisements WHERE id = ?', (ad_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_advertisement(row, cursor.description)
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"获取广告失败: {e}")
            return None
    
    def get_advertisements(self, 
                          status: Optional[AdStatus] = None,
                          position: Optional[AdPosition] = None,
                          ad_type: Optional[AdType] = None,
                          active_only: bool = False) -> List[Advertisement]:
        """
        获取广告列表
        
        Args:
            status: 状态过滤
            position: 位置过滤
            ad_type: 类型过滤
            active_only: 是否只返回有效广告
            
        Returns:
            List[Advertisement]: 广告列表
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                conditions = []
                params = []
                
                if status:
                    conditions.append('status = ?')
                    params.append(status.value)
                
                if position:
                    conditions.append('position = ?')
                    params.append(position.value)
                
                if ad_type:
                    conditions.append('type = ?')
                    params.append(ad_type.value)
                
                if active_only:
                    now = datetime.now()
                    conditions.extend([
                        'status = ?',
                        '(start_date IS NULL OR start_date <= ?)',
                        '(end_date IS NULL OR end_date >= ?)',
                        '(max_displays IS NULL OR display_count < max_displays)'
                    ])
                    params.extend(['active', now, now])
                
                # 构建完整查询
                where_clause = ' AND '.join(conditions) if conditions else '1=1'
                query = f'SELECT * FROM advertisements WHERE {where_clause} ORDER BY priority DESC, weight DESC'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_advertisement(row, cursor.description) for row in rows]
                
        except Exception as e:
            logger.error(f"获取广告列表失败: {e}")
            return []
    
    def select_ads_for_content(self, 
                              content_type: str = None,
                              target_positions: List[AdPosition] = None) -> Dict[AdPosition, List[Advertisement]]:
        """
        为内容选择合适的广告
        
        Args:
            content_type: 内容类型
            target_positions: 目标位置列表
            
        Returns:
            Dict[AdPosition, List[Advertisement]]: 按位置分组的广告
        """
        if not self.config.enabled:
            return {}
        
        target_positions = target_positions or list(AdPosition)
        result = {}
        
        try:
            for position in target_positions:
                # 获取该位置的有效广告
                ads = self.get_advertisements(position=position, active_only=True)
                
                # 按内容类型过滤
                if content_type:
                    ads = [ad for ad in ads if self._matches_content_type(ad, content_type)]
                
                if not ads:
                    continue
                
                # 选择广告
                selected_ads = self._select_ads_by_strategy(ads, position)
                
                if selected_ads:
                    result[position] = selected_ads
            
            # 确保不超过最大广告数
            result = self._limit_total_ads(result)
            
            logger.debug(f"为内容选择广告: {len(sum(result.values(), []))} 个")
            return result
            
        except Exception as e:
            logger.error(f"选择广告失败: {e}")
            return {}
    
    def _matches_content_type(self, ad: Advertisement, content_type: str) -> bool:
        """
        检查广告是否匹配内容类型
        
        Args:
            ad: 广告对象
            content_type: 内容类型
            
        Returns:
            bool: 是否匹配
        """
        if not ad.target_content_types:
            return True  # 没有指定目标类型，匹配所有内容
        
        return content_type in ad.target_content_types
    
    def _select_ads_by_strategy(self, ads: List[Advertisement], position: AdPosition) -> List[Advertisement]:
        """
        根据策略选择广告
        
        Args:
            ads: 候选广告列表
            position: 广告位置
            
        Returns:
            List[Advertisement]: 选中的广告
        """
        if not ads:
            return []
        
        # 获取该位置的最大广告数
        max_ads = min(self.config.max_ads_per_post, len(ads))
        if max_ads <= 0:
            return []
        
        if self.config.random_selection:
            # 加权随机选择
            return self._weighted_random_selection(ads, max_ads)
        else:
            # 按优先级选择
            return sorted(ads, key=lambda x: (x.priority, x.weight), reverse=True)[:max_ads]
    
    def _weighted_random_selection(self, ads: List[Advertisement], count: int) -> List[Advertisement]:
        """
        加权随机选择广告
        
        Args:
            ads: 广告列表
            count: 选择数量
            
        Returns:
            List[Advertisement]: 选中的广告
        """
        if count >= len(ads):
            return ads
        
        # 计算权重
        weights = []
        for ad in ads:
            # 权重 = 基础权重 * 优先级 / (展示次数 + 1)
            weight = ad.weight * ad.priority / (ad.display_count + 1)
            weights.append(weight)
        
        # 随机选择
        selected = []
        remaining_ads = ads.copy()
        remaining_weights = weights.copy()
        
        for _ in range(count):
            if not remaining_ads:
                break
            
            # 加权随机选择
            total_weight = sum(remaining_weights)
            if total_weight <= 0:
                # 如果权重都为0，随机选择
                index = random.randint(0, len(remaining_ads) - 1)
            else:
                rand_value = random.uniform(0, total_weight)
                cumulative_weight = 0
                index = 0
                
                for i, weight in enumerate(remaining_weights):
                    cumulative_weight += weight
                    if rand_value <= cumulative_weight:
                        index = i
                        break
            
            # 添加选中的广告
            selected.append(remaining_ads[index])
            remaining_ads.pop(index)
            remaining_weights.pop(index)
        
        return selected
    
    def _limit_total_ads(self, ads_by_position: Dict[AdPosition, List[Advertisement]]) -> Dict[AdPosition, List[Advertisement]]:
        """
        限制总广告数量
        
        Args:
            ads_by_position: 按位置分组的广告
            
        Returns:
            Dict[AdPosition, List[Advertisement]]: 限制后的广告
        """
        total_ads = sum(len(ads) for ads in ads_by_position.values())
        max_total = self.config.max_ads_per_post
        
        if total_ads <= max_total:
            return ads_by_position
        
        # 需要减少广告数量
        result = {}
        remaining_quota = max_total
        
        # 按位置优先级分配
        position_priority = [AdPosition.BEFORE_CONTENT, AdPosition.AFTER_CONTENT, AdPosition.MIDDLE_CONTENT]
        
        for position in position_priority:
            if position in ads_by_position and remaining_quota > 0:
                ads = ads_by_position[position]
                allocated = min(len(ads), remaining_quota)
                result[position] = ads[:allocated]
                remaining_quota -= allocated
        
        return result
    
    def format_ads_for_display(self, 
                              ads_by_position: Dict[AdPosition, List[Advertisement]],
                              content: str = "") -> Dict[str, str]:
        """
        格式化广告用于显示
        
        Args:
            ads_by_position: 按位置分组的广告
            content: 原始内容
            
        Returns:
            Dict[str, str]: 格式化后的内容 {'before': '', 'after': '', 'middle': ''}
        """
        result = {'before': '', 'after': '', 'middle': ''}
        
        try:
            for position, ads in ads_by_position.items():
                if not ads:
                    continue
                
                formatted_ads = []
                for ad in ads:
                    formatted_ad = self._format_single_ad(ad)
                    if formatted_ad:
                        formatted_ads.append(formatted_ad)
                
                if formatted_ads:
                    position_key = {
                        AdPosition.BEFORE_CONTENT: 'before',
                        AdPosition.AFTER_CONTENT: 'after',
                        AdPosition.MIDDLE_CONTENT: 'middle'
                    }[position]
                    
                    result[position_key] = self.config.ad_separator.join(formatted_ads)
            
            return result
            
        except Exception as e:
            logger.error(f"格式化广告失败: {e}")
            return result
    
    def _format_single_ad(self, ad: Advertisement) -> str:
        """
        格式化单个广告
        
        Args:
            ad: 广告对象
            
        Returns:
            str: 格式化后的广告文本
        """
        try:
            # 广告标签
            ad_label = "📢 广告" if self.config.show_ad_label else ""
            
            if ad.type == AdType.TEXT:
                return f"{ad_label}\n{ad.content}" if ad_label else ad.content
            
            elif ad.type == AdType.LINK:
                if ad.url:
                    return f"{ad_label}\n[{ad.content}]({ad.url})" if ad_label else f"[{ad.content}]({ad.url})"
                else:
                    return f"{ad_label}\n{ad.content}" if ad_label else ad.content
            
            elif ad.type == AdType.BUTTON:
                # 按钮广告需要特殊处理，这里先返回文本格式
                button_text = ad.button_text or "点击查看"
                if ad.url:
                    return f"{ad_label}\n{ad.content}\n👆 [{button_text}]({ad.url})" if ad_label else f"{ad.content}\n👆 [{button_text}]({ad.url})"
                else:
                    return f"{ad_label}\n{ad.content}" if ad_label else ad.content
            
            elif ad.type in [AdType.IMAGE, AdType.VIDEO]:
                # 媒体广告需要在发送时特殊处理
                return f"{ad_label}\n{ad.content}" if ad_label else ad.content
            
            else:
                return ad.content
                
        except Exception as e:
            logger.error(f"格式化广告失败: {ad.id}: {e}")
            return ad.content
    
    def record_ad_display(self, ad_id: int, submission_id: int = None, 
                         channel_message_id: int = None, position: AdPosition = None) -> bool:
        """
        记录广告展示
        
        Args:
            ad_id: 广告ID
            submission_id: 投稿ID
            channel_message_id: 频道消息ID
            position: 广告位置
            
        Returns:
            bool: 是否记录成功
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 记录展示日志
                cursor.execute('''
                    INSERT INTO ad_display_logs (ad_id, submission_id, channel_message_id, position)
                    VALUES (?, ?, ?, ?)
                ''', (ad_id, submission_id, channel_message_id, position.value if position else None))
                
                # 更新广告展示计数
                cursor.execute('''
                    UPDATE advertisements 
                    SET display_count = display_count + 1 
                    WHERE id = ?
                ''', (ad_id,))
                
                conn.commit()
                logger.debug(f"记录广告展示: ID {ad_id}")
                return True
                
        except Exception as e:
            logger.error(f"记录广告展示失败: {e}")
            return False
    
    def record_ad_click(self, ad_id: int, display_log_id: int = None) -> bool:
        """
        记录广告点击
        
        Args:
            ad_id: 广告ID
            display_log_id: 展示日志ID
            
        Returns:
            bool: 是否记录成功
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 更新展示日志
                if display_log_id:
                    cursor.execute('''
                        UPDATE ad_display_logs 
                        SET user_clicked = TRUE, clicked_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (display_log_id,))
                
                # 更新广告点击计数
                cursor.execute('''
                    UPDATE advertisements 
                    SET click_count = click_count + 1 
                    WHERE id = ?
                ''', (ad_id,))
                
                conn.commit()
                logger.debug(f"记录广告点击: ID {ad_id}")
                return True
                
        except Exception as e:
            logger.error(f"记录广告点击失败: {e}")
            return False
    
    def get_ad_statistics(self, ad_id: int = None) -> Dict[str, Any]:
        """
        获取广告统计信息
        
        Args:
            ad_id: 广告ID，None表示获取所有广告统计
            
        Returns:
            Dict: 统计信息
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                if ad_id:
                    # 单个广告统计
                    cursor.execute('''
                        SELECT 
                            a.id, a.name, a.display_count, a.click_count,
                            COUNT(l.id) as total_displays,
                            COUNT(CASE WHEN l.user_clicked THEN 1 END) as total_clicks
                        FROM advertisements a
                        LEFT JOIN ad_display_logs l ON a.id = l.ad_id
                        WHERE a.id = ?
                        GROUP BY a.id
                    ''', (ad_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'ad_id': row[0],
                            'name': row[1],
                            'display_count': row[2],
                            'click_count': row[3],
                            'actual_displays': row[4],
                            'actual_clicks': row[5],
                            'ctr': (row[5] / row[4] * 100) if row[4] > 0 else 0
                        }
                    else:
                        return {}
                else:
                    # 全部广告统计
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_ads,
                            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_ads,
                            SUM(display_count) as total_displays,
                            SUM(click_count) as total_clicks
                        FROM advertisements
                    ''')
                    
                    row = cursor.fetchone()
                    total_displays = row[2] or 0
                    total_clicks = row[3] or 0
                    
                    return {
                        'total_ads': row[0],
                        'active_ads': row[1],
                        'total_displays': total_displays,
                        'total_clicks': total_clicks,
                        'overall_ctr': (total_clicks / total_displays * 100) if total_displays > 0 else 0
                    }
                    
        except Exception as e:
            logger.error(f"获取广告统计失败: {e}")
            return {}
    
    def update_config(self, config: AdDisplayConfig) -> bool:
        """
        更新广告配置
        
        Args:
            config: 新的配置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            self.config = config
            
            # 保存到数据库
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                config_data = json.dumps(asdict(config), default=str)
                cursor.execute('''
                    INSERT OR REPLACE INTO ad_config (id, config_data, updated_at)
                    VALUES (1, ?, CURRENT_TIMESTAMP)
                ''', (config_data,))
                
                conn.commit()
                
            logger.info("广告配置更新成功")
            return True
            
        except Exception as e:
            logger.error(f"更新广告配置失败: {e}")
            return False
    
    def load_config(self) -> bool:
        """
        从数据库加载配置
        
        Returns:
            bool: 是否加载成功
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT config_data FROM ad_config WHERE id = 1')
                row = cursor.fetchone()
                
                if row:
                    config_data = json.loads(row[0])
                    # 将位置权重字符串键转换回枚举
                    if 'position_weights' in config_data and config_data['position_weights']:
                        position_weights = {}
                        for pos_str, weight in config_data['position_weights'].items():
                            try:
                                pos_enum = AdPosition(pos_str)
                                position_weights[pos_enum] = weight
                            except ValueError:
                                continue
                        config_data['position_weights'] = position_weights
                    
                    self.config = AdDisplayConfig(**config_data)
                    logger.info("广告配置加载成功")
                    return True
                else:
                    logger.info("使用默认广告配置")
                    return True
                    
        except Exception as e:
            logger.error(f"加载广告配置失败: {e}")
            return False
    
    def _row_to_advertisement(self, row: tuple, description: List) -> Advertisement:
        """
        将数据库行转换为Advertisement对象
        
        Args:
            row: 数据库行
            description: 列描述
            
        Returns:
            Advertisement: 广告对象
        """
        # 创建字段名到值的映射
        data = dict(zip([col[0] for col in description], row))
        
        # 转换枚举字段
        data['type'] = AdType(data['type'])
        data['position'] = AdPosition(data['position'])
        data['status'] = AdStatus(data['status'])
        
        # 转换JSON字段
        if data['tags']:
            data['tags'] = json.loads(data['tags'])
        
        if data['target_content_types']:
            data['target_content_types'] = json.loads(data['target_content_types'])
        
        # 转换时间字段
        for field in ['start_date', 'end_date', 'created_at', 'updated_at']:
            if data[field]:
                data[field] = datetime.fromisoformat(data[field])
        
        return Advertisement(**data)

# 全局广告管理器实例
_ad_manager: Optional[AdvertisementManager] = None

def get_ad_manager() -> AdvertisementManager:
    """
    获取全局广告管理器实例
    
    Returns:
        AdvertisementManager: 广告管理器实例
    """
    global _ad_manager
    if _ad_manager is None:
        raise RuntimeError("广告管理器未初始化，请先调用 initialize_ad_manager()")
    return _ad_manager

def initialize_ad_manager(db_file: str) -> AdvertisementManager:
    """
    初始化全局广告管理器
    
    Args:
        db_file: 数据库文件路径
        
    Returns:
        AdvertisementManager: 广告管理器实例
    """
    global _ad_manager
    _ad_manager = AdvertisementManager(db_file)
    _ad_manager.load_config()
    return _ad_manager