#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多媒体处理模块
Media Processing Module

提供全面的多媒体文件处理功能，包括：
- 图片压缩和格式转换
- 音频格式转换和压缩
- 视频处理和预览生成
- 文档文字提取(OCR)
- 自动标签识别
- 元数据提取和分析

作者: AI Assistant
创建时间: 2024-12-19
"""

import os
import io
import logging
import tempfile
import hashlib
import mimetypes
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

# 尝试导入可选依赖
try:
    from PIL import Image, ImageFilter, ImageEnhance, ExifTags
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import mutagen
    from mutagen.id3 import ID3, TIT2, TPE1, TALB
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MediaInfo:
    """媒体文件信息数据类"""
    file_path: str
    file_size: int
    mime_type: str
    media_type: str  # image, audio, video, document
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    metadata: Optional[Dict] = None
    extracted_text: Optional[str] = None
    tags: Optional[List[str]] = None
    thumbnail_path: Optional[str] = None

class ImageProcessor:
    """
    图片处理器
    Image Processor
    
    提供图片压缩、格式转换、OCR等功能
    """
    
    def __init__(self):
        """初始化图片处理器"""
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow未安装，图片处理功能受限")
        
        # 支持的图片格式
        self.supported_formats = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'
        }
        
        # 压缩配置
        self.compression_configs = {
            'high': {'quality': 95, 'max_size': (2048, 2048)},
            'medium': {'quality': 85, 'max_size': (1200, 1200)},
            'low': {'quality': 75, 'max_size': (800, 800)},
            'thumbnail': {'quality': 80, 'max_size': (300, 300)}
        }
        
        logger.info("图片处理器初始化完成")
    
    def analyze_image(self, file_path: str) -> MediaInfo:
        """
        分析图片文件
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            MediaInfo: 图片信息
        """
        try:
            if not PIL_AVAILABLE:
                raise RuntimeError("PIL/Pillow未安装")
            
            # 基础文件信息
            file_size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # 打开图片
            if not PIL_AVAILABLE:
                raise RuntimeError("PIL/Pillow未安装")
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
                
                # 提取EXIF信息
                metadata = self._extract_exif(img)
                
                # 创建媒体信息
                media_info = MediaInfo(
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type or 'image/unknown',
                    media_type='image',
                    width=width,
                    height=height,
                    format=format_name,
                    metadata=metadata
                )
                
                # OCR文字提取（如果可用）
                if TESSERACT_AVAILABLE:
                    try:
                        extracted_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                        if extracted_text.strip():
                            media_info.extracted_text = extracted_text.strip()
                    except Exception as e:
                        logger.debug(f"OCR提取失败: {e}")
                
                # 生成标签
                media_info.tags = self._generate_image_tags(media_info)
                
                logger.debug(f"图片分析完成: {file_path} ({width}x{height})")
                return media_info
                
        except Exception as e:
            logger.error(f"图片分析失败: {file_path}: {e}")
            raise
    
    def _extract_exif(self, img) -> Dict:
        """
        提取EXIF信息
        
        Args:
            img: PIL图片对象
            
        Returns:
            Dict: EXIF信息字典
        """
        metadata = {}
        
        try:
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    
                    # 处理特殊值类型
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except UnicodeDecodeError:
                            value = str(value)
                    elif hasattr(value, '__iter__') and not isinstance(value, str):
                        value = str(value)
                    
                    metadata[str(tag)] = value
        except Exception as e:
            logger.debug(f"EXIF提取失败: {e}")
        
        return metadata
    
    def _generate_image_tags(self, media_info: MediaInfo) -> List[str]:
        """
        生成图片标签
        
        Args:
            media_info: 媒体信息
            
        Returns:
            List[str]: 标签列表
        """
        tags = []
        
        # 基于尺寸的标签
        if media_info.width and media_info.height:
            pixel_count = media_info.width * media_info.height
            if pixel_count > 8000000:  # > 8MP
                tags.append('高分辨率')
            elif pixel_count > 2000000:  # > 2MP
                tags.append('中分辨率')
            else:
                tags.append('低分辨率')
            
            # 宽高比
            aspect_ratio = media_info.width / media_info.height
            if aspect_ratio > 1.5:
                tags.append('横向')
            elif aspect_ratio < 0.7:
                tags.append('纵向')
            else:
                tags.append('方形')
        
        # 基于格式的标签
        if media_info.format:
            tags.append(f'格式:{media_info.format}')
        
        # 基于文件大小的标签
        size_mb = media_info.file_size / (1024 * 1024)
        if size_mb > 10:
            tags.append('大文件')
        elif size_mb > 1:
            tags.append('中等文件')
        else:
            tags.append('小文件')
        
        # 基于OCR文本的标签
        if media_info.extracted_text:
            if len(media_info.extracted_text) > 100:
                tags.append('含文字')
            else:
                tags.append('少量文字')
        
        return tags
    
    def compress_image(self, 
                      input_path: str, 
                      output_path: str, 
                      quality: str = 'medium') -> Dict[str, Any]:
        """
        压缩图片
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            quality: 压缩质量 (high, medium, low, thumbnail)
            
        Returns:
            Dict: 压缩结果信息
        """
        try:
            if not PIL_AVAILABLE:
                raise RuntimeError("PIL/Pillow未安装")
            
            config = self.compression_configs.get(quality, self.compression_configs['medium'])
            
            # 获取原始文件信息
            original_size = os.path.getsize(input_path)
            
            with Image.open(input_path) as img:
                # 转换为RGB（如果需要）
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整尺寸
                max_width, max_height = config['max_size']
                if img.size[0] > max_width or img.size[1] > max_height:
                    # 使用兼容的缩略图方法
                    try:
                        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    except AttributeError:
                        # 兼容旧版本PIL
                        img.thumbnail((max_width, max_height), Image.LANCZOS)
                
                # 保存压缩后的图片
                save_kwargs = {
                    'quality': config['quality'],
                    'optimize': True,
                    'progressive': True
                }
                
                # 根据输出格式调整参数
                output_format = Path(output_path).suffix.lower()
                if output_format in ['.jpg', '.jpeg']:
                    img.save(output_path, 'JPEG', **save_kwargs)
                elif output_format == '.png':
                    # PNG特殊处理
                    img.save(output_path, 'PNG', optimize=True)
                elif output_format == '.webp':
                    img.save(output_path, 'WebP', **save_kwargs)
                else:
                    # 默认保存为JPEG
                    output_path = str(Path(output_path).with_suffix('.jpg'))
                    img.save(output_path, 'JPEG', **save_kwargs)
                
                # 获取压缩后文件信息
                compressed_size = os.path.getsize(output_path)
                compression_ratio = (1 - compressed_size / original_size) * 100
                
                result = {
                    'success': True,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': f"{compression_ratio:.1f}%",
                    'output_path': output_path,
                    'final_size': img.size
                }
                
                logger.info(f"图片压缩完成: {input_path} -> {output_path} "
                          f"({original_size} -> {compressed_size} bytes, {compression_ratio:.1f}%)")
                
                return result
                
        except Exception as e:
            logger.error(f"图片压缩失败: {input_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_thumbnail(self, input_path: str, output_path: str, size: Tuple[int, int] = (300, 300)) -> bool:
        """
        创建缩略图
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            size: 缩略图尺寸
            
        Returns:
            bool: 是否成功
        """
        try:
            if not PIL_AVAILABLE:
                return False
            
            with Image.open(input_path) as img:
                # 创建缩略图
                try:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                except AttributeError:
                    # 兼容旧版本PIL
                    img.thumbnail(size, Image.LANCZOS)
                
                # 转换为RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存缩略图
                img.save(output_path, 'JPEG', quality=80, optimize=True)
                
                logger.debug(f"缩略图创建完成: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"缩略图创建失败: {input_path}: {e}")
            return False

class AudioProcessor:
    """
    音频处理器
    Audio Processor
    
    提供音频格式转换、元数据提取等功能
    """
    
    def __init__(self):
        """初始化音频处理器"""
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen未安装，音频处理功能受限")
        
        # 支持的音频格式
        self.supported_formats = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'
        }
        
        logger.info("音频处理器初始化完成")
    
    def analyze_audio(self, file_path: str) -> MediaInfo:
        """
        分析音频文件
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            MediaInfo: 音频信息
        """
        try:
            # 基础文件信息
            file_size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # 创建基础媒体信息
            media_info = MediaInfo(
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type or 'audio/unknown',
                media_type='audio'
            )
            
            # 提取音频元数据
            if MUTAGEN_AVAILABLE:
                try:
                    audio_file = mutagen.File(file_path)
                    if audio_file:
                        # 基础信息
                        media_info.duration = getattr(audio_file.info, 'length', None)
                        media_info.format = audio_file.mime[0] if audio_file.mime else None
                        
                        # 元数据
                        metadata = {}
                        for key, value in audio_file.items():
                            if isinstance(value, list) and len(value) == 1:
                                value = value[0]
                            metadata[str(key)] = str(value)
                        
                        media_info.metadata = metadata
                        
                        # 生成标签
                        media_info.tags = self._generate_audio_tags(media_info)
                        
                except Exception as e:
                    logger.debug(f"音频元数据提取失败: {e}")
            
            logger.debug(f"音频分析完成: {file_path}")
            return media_info
            
        except Exception as e:
            logger.error(f"音频分析失败: {file_path}: {e}")
            raise
    
    def _generate_audio_tags(self, media_info: MediaInfo) -> List[str]:
        """
        生成音频标签
        
        Args:
            media_info: 媒体信息
            
        Returns:
            List[str]: 标签列表
        """
        tags = []
        
        # 基于时长的标签
        if media_info.duration:
            duration_min = media_info.duration / 60
            if duration_min > 60:
                tags.append('长音频')
            elif duration_min > 5:
                tags.append('中等音频')
            else:
                tags.append('短音频')
        
        # 基于文件大小的标签
        size_mb = media_info.file_size / (1024 * 1024)
        if size_mb > 50:
            tags.append('高质量')
        elif size_mb > 10:
            tags.append('标准质量')
        else:
            tags.append('压缩音频')
        
        # 基于元数据的标签
        if media_info.metadata:
            if any(key.lower() in ['title', 'tit2'] for key in media_info.metadata.keys()):
                tags.append('有标题')
            if any(key.lower() in ['artist', 'tpe1'] for key in media_info.metadata.keys()):
                tags.append('有艺术家')
            if any(key.lower() in ['album', 'talb'] for key in media_info.metadata.keys()):
                tags.append('有专辑')
        
        return tags

class VideoProcessor:
    """
    视频处理器
    Video Processor
    
    提供视频分析、预览生成等功能
    """
    
    def __init__(self):
        """初始化视频处理器"""
        if not MOVIEPY_AVAILABLE:
            logger.warning("MoviePy未安装，视频处理功能受限")
        
        # 支持的视频格式
        self.supported_formats = {
            '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'
        }
        
        logger.info("视频处理器初始化完成")
    
    def analyze_video(self, file_path: str) -> MediaInfo:
        """
        分析视频文件
        
        Args:
            file_path: 视频文件路径
            
        Returns:
            MediaInfo: 视频信息
        """
        try:
            # 基础文件信息
            file_size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # 创建基础媒体信息
            media_info = MediaInfo(
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type or 'video/unknown',
                media_type='video'
            )
            
            # 提取视频信息
            if MOVIEPY_AVAILABLE:
                try:
                    with mp.VideoFileClip(file_path) as video:
                        media_info.width = video.w
                        media_info.height = video.h
                        media_info.duration = video.duration
                        media_info.format = Path(file_path).suffix[1:].upper()
                        
                        # 元数据
                        metadata = {
                            'fps': video.fps,
                            'audio': hasattr(video, 'audio') and video.audio is not None
                        }
                        media_info.metadata = metadata
                        
                        # 生成标签
                        media_info.tags = self._generate_video_tags(media_info)
                        
                except Exception as e:
                    logger.debug(f"视频信息提取失败: {e}")
            
            logger.debug(f"视频分析完成: {file_path}")
            return media_info
            
        except Exception as e:
            logger.error(f"视频分析失败: {file_path}: {e}")
            raise
    
    def _generate_video_tags(self, media_info: MediaInfo) -> List[str]:
        """
        生成视频标签
        
        Args:
            media_info: 媒体信息
            
        Returns:
            List[str]: 标签列表
        """
        tags = []
        
        # 基于分辨率的标签
        if media_info.width and media_info.height:
            if media_info.width >= 3840:  # 4K
                tags.append('4K超清')
            elif media_info.width >= 1920:  # 1080p
                tags.append('1080p高清')
            elif media_info.width >= 1280:  # 720p
                tags.append('720p高清')
            else:
                tags.append('标清')
        
        # 基于时长的标签
        if media_info.duration:
            duration_min = media_info.duration / 60
            if duration_min > 60:
                tags.append('长视频')
            elif duration_min > 5:
                tags.append('中等视频')
            else:
                tags.append('短视频')
        
        # 基于文件大小的标签
        size_mb = media_info.file_size / (1024 * 1024)
        if size_mb > 1000:
            tags.append('大文件')
        elif size_mb > 100:
            tags.append('中等文件')
        else:
            tags.append('小文件')
        
        # 基于元数据的标签
        if media_info.metadata:
            if media_info.metadata.get('audio'):
                tags.append('有音频')
            else:
                tags.append('无音频')
        
        return tags
    
    def create_video_thumbnail(self, input_path: str, output_path: str, time: float = 1.0) -> bool:
        """
        创建视频缩略图
        
        Args:
            input_path: 输入视频路径
            output_path: 输出图片路径
            time: 截取时间点（秒）
            
        Returns:
            bool: 是否成功
        """
        try:
            if not MOVIEPY_AVAILABLE:
                return False
            
            with mp.VideoFileClip(input_path) as video:
                # 选择合适的时间点
                if time > video.duration:
                    time = video.duration / 2
                
                # 提取帧
                frame = video.get_frame(time)
                
                # 转换为PIL图片并保存
                if PIL_AVAILABLE:
                    img = Image.fromarray(frame)
                    try:
                        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    except AttributeError:
                        # 兼容旧版本PIL
                        img.thumbnail((300, 300), Image.LANCZOS)
                    img.save(output_path, 'JPEG', quality=80)
                else:
                    # 使用moviepy直接保存
                    video.save_frame(output_path, t=time)
                
                logger.debug(f"视频缩略图创建完成: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"视频缩略图创建失败: {input_path}: {e}")
            return False

class MediaProcessor:
    """
    多媒体处理器主类
    Media Processor Main Class
    
    整合所有多媒体处理功能
    """
    
    def __init__(self, temp_dir: str = None):
        """
        初始化多媒体处理器
        
        Args:
            temp_dir: 临时文件目录
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # 初始化各个处理器
        self.image_processor = ImageProcessor()
        self.audio_processor = AudioProcessor()
        self.video_processor = VideoProcessor()
        
        # 媒体类型映射
        self.type_mapping = {
            **{ext: 'image' for ext in self.image_processor.supported_formats},
            **{ext: 'audio' for ext in self.audio_processor.supported_formats},
            **{ext: 'video' for ext in self.video_processor.supported_formats}
        }
        
        logger.info("多媒体处理器初始化完成")
    
    def get_media_type(self, file_path: str) -> str:
        """
        获取媒体文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 媒体类型 (image, audio, video, document, unknown)
        """
        file_ext = Path(file_path).suffix.lower()
        return self.type_mapping.get(file_ext, 'unknown')
    
    def analyze_media(self, file_path: str) -> MediaInfo:
        """
        分析媒体文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            MediaInfo: 媒体信息
        """
        media_type = self.get_media_type(file_path)
        
        try:
            if media_type == 'image':
                return self.image_processor.analyze_image(file_path)
            elif media_type == 'audio':
                return self.audio_processor.analyze_audio(file_path)
            elif media_type == 'video':
                return self.video_processor.analyze_video(file_path)
            else:
                # 未知类型，返回基础信息
                file_size = os.path.getsize(file_path)
                mime_type, _ = mimetypes.guess_type(file_path)
                
                return MediaInfo(
                    file_path=file_path,
                    file_size=file_size,
                    mime_type=mime_type or 'application/octet-stream',
                    media_type=media_type,
                    tags=['未知格式']
                )
                
        except Exception as e:
            logger.error(f"媒体文件分析失败: {file_path}: {e}")
            raise
    
    def process_media(self, 
                     file_path: str, 
                     operations: List[str] = None,
                     output_dir: str = None) -> Dict[str, Any]:
        """
        处理媒体文件
        
        Args:
            file_path: 输入文件路径
            operations: 处理操作列表 ['compress', 'thumbnail', 'extract_text']
            output_dir: 输出目录
            
        Returns:
            Dict: 处理结果
        """
        operations = operations or []
        output_dir = output_dir or self.temp_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 分析媒体文件
        media_info = self.analyze_media(file_path)
        
        results = {
            'media_info': media_info,
            'operations': {}
        }
        
        file_stem = Path(file_path).stem
        
        try:
            # 压缩处理
            if 'compress' in operations and media_info.media_type == 'image':
                output_path = os.path.join(output_dir, f"{file_stem}_compressed.jpg")
                compress_result = self.image_processor.compress_image(file_path, output_path)
                results['operations']['compress'] = compress_result
            
            # 缩略图生成
            if 'thumbnail' in operations:
                thumbnail_path = os.path.join(output_dir, f"{file_stem}_thumb.jpg")
                
                if media_info.media_type == 'image':
                    success = self.image_processor.create_thumbnail(file_path, thumbnail_path)
                elif media_info.media_type == 'video':
                    success = self.video_processor.create_video_thumbnail(file_path, thumbnail_path)
                else:
                    success = False
                
                results['operations']['thumbnail'] = {
                    'success': success,
                    'path': thumbnail_path if success else None
                }
                
                if success:
                    media_info.thumbnail_path = thumbnail_path
            
            # 文字提取
            if 'extract_text' in operations and media_info.media_type == 'image':
                if media_info.extracted_text:
                    results['operations']['extract_text'] = {
                        'success': True,
                        'text': media_info.extracted_text
                    }
                else:
                    results['operations']['extract_text'] = {
                        'success': False,
                        'error': 'OCR不可用或未提取到文字'
                    }
            
            logger.info(f"媒体处理完成: {file_path}")
            
        except Exception as e:
            logger.error(f"媒体处理失败: {file_path}: {e}")
            results['error'] = str(e)
        
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'supported_formats': {
                'image': list(self.image_processor.supported_formats),
                'audio': list(self.audio_processor.supported_formats),
                'video': list(self.video_processor.supported_formats)
            },
            'available_features': {
                'image_processing': PIL_AVAILABLE,
                'video_processing': MOVIEPY_AVAILABLE,
                'audio_processing': MUTAGEN_AVAILABLE,
                'ocr': TESSERACT_AVAILABLE
            }
        }

# 全局媒体处理器实例
_media_processor: Optional[MediaProcessor] = None

def get_media_processor() -> MediaProcessor:
    """
    获取全局媒体处理器实例
    
    Returns:
        MediaProcessor: 媒体处理器实例
    """
    global _media_processor
    if _media_processor is None:
        _media_processor = MediaProcessor()
    return _media_processor

def initialize_media_processor(temp_dir: str = None) -> MediaProcessor:
    """
    初始化全局媒体处理器
    
    Args:
        temp_dir: 临时文件目录
        
    Returns:
        MediaProcessor: 媒体处理器实例
    """
    global _media_processor
    _media_processor = MediaProcessor(temp_dir)
    return _media_processor