"""
动画播放器 - 管理动画帧的加载和播放
支持 PNG 序列或静态 PNG 图片
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap


class AnimationSequence:
    """动画序列 - 支持多帧或静态图片"""
    def __init__(self, name: str, folder_path: str):
        self.name = name
        self.folder_path = Path(folder_path)
        self.frames: List[QPixmap] = []
        self.loaded = False
        self.is_static = False  # 是否为静态图片
    
    def load(self, scale: float = 1.0, size: int = 150):
        """加载所有帧 - 支持 PNG 序列或静态图片"""
        if not self.folder_path.exists():
            return False
        
        self.frames = []
        
        # 1. 首先尝试加载 PNG 序列
        png_files = sorted([f for f in self.folder_path.iterdir() 
                          if f.suffix.lower() == '.png'])
        
        if len(png_files) > 1:
            # 多帧动画
            for png_file in png_files:
                pixmap = QPixmap(str(png_file))
                if not pixmap.isNull():
                    if scale != 1.0:
                        new_size = int(pixmap.width() * scale)
                        pixmap = pixmap.scaledToWidth(
                            new_size, 
                            Qt.TransformationMode.SmoothTransformation
                        )
                    self.frames.append(pixmap)
            self.is_static = False
        elif len(png_files) == 1:
            # 单张静态图片
            pixmap = QPixmap(str(png_files[0]))
            if not pixmap.isNull():
                # 缩放到指定大小
                target_size = int(size * scale)
                pixmap = pixmap.scaled(
                    target_size, target_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.frames = [pixmap]
                self.is_static = True
        
        self.loaded = len(self.frames) > 0
        if self.loaded:
            frame_info = "静态图片" if self.is_static else f"{len(self.frames)} 帧"
            print(f"[AnimationPlayer] 加载: {self.name} ({frame_info})")
        return self.loaded
    
    def get_frame(self, index: int) -> Optional[QPixmap]:
        """获取指定帧 - 静态图片始终返回第0帧"""
        if not self.frames:
            return None
        if self.is_static:
            return self.frames[0]
        return self.frames[index % len(self.frames)]


class AnimationPlayer(QObject):
    """动画播放器"""
    # 信号
    frame_changed = pyqtSignal(QPixmap)  # 帧变更
    animation_finished = pyqtSignal(str)  # 动画完成，返回下一个状态
    
    def __init__(self, visual_dir: str = "Assets/Visual", fps: int = 12, size: int = 150):
        super().__init__()
        self.visual_dir = Path(visual_dir)
        self.fps = fps
        self.frame_interval = int(1000 / fps)  # 毫秒
        self.size = size
        self.scale = 1.0
        
        self.sequences: Dict[str, AnimationSequence] = {}
        
        # 播放状态
        self._current_sequence: Optional[AnimationSequence] = None
        self._current_index = 0
        self._is_looping = True
        self._next_state = "Idle"
        self._is_playing = False
        
        # 定时器
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_frame_timeout)
    
    def initialize(self, scale: float = 1.0):
        """初始化，预加载所有动画（Idle 除外，由 reload_idle_form 加载）"""
        self.scale = scale
        
        # 加载除 Idle 外的动画序列
        animations = ["Talking", "Drag", "Sleep", "React", "Transition"]
        
        for anim_name in animations:
            folder_path = self.visual_dir / anim_name
            if folder_path.exists():
                seq = AnimationSequence(anim_name, str(folder_path))
                if seq.load(scale, self.size):
                    self.sequences[anim_name] = seq
    
    def reload_idle_form(self, form_number: int):
        """重新加载 Idle 形态（切换 flower1.png / flower2.png）"""
        idle_path = self.visual_dir / "Idle"
        if not idle_path.exists():
            return
        
        # 获取所有 PNG 文件
        png_files = sorted([f for f in idle_path.iterdir() if f.suffix.lower() == '.png'])
        
        if len(png_files) < form_number:
            print(f"[AnimationPlayer] 形态 {form_number} 不存在，只有 {len(png_files)} 张图片")
            return
        
        # 选择对应图片 (form_number 从 1 开始)
        selected_file = png_files[form_number - 1]
        
        # 创建新的 Idle 序列，只包含选中的图片
        new_seq = AnimationSequence("Idle", str(idle_path))
        
        # 手动加载指定图片
        pixmap = QPixmap(str(selected_file))
        if not pixmap.isNull():
            target_size = int(self.size * self.scale)
            pixmap = pixmap.scaled(
                target_size, target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            new_seq.frames = [pixmap]
            new_seq.loaded = True
            new_seq.is_static = True
            self.sequences["Idle"] = new_seq
            
            # 如果当前正在播放 Idle，立即切换
            if self._current_sequence and self._current_sequence.name == "Idle":
                self._current_sequence = new_seq
                self.frame_changed.emit(new_seq.get_frame(0))
            
            print(f"[AnimationPlayer] 切换到形态 {form_number}: {selected_file.name}")
    
    def play(self, animation_name: str, loop: bool = True, next_state: str = "Idle"):
        """
        播放动画
        
        Args:
            animation_name: 动画名称
            loop: 是否循环
            next_state: 单次播放完成后的下一个状态
        """
        # 检查是否存在该动画，不存在则回退到Talking，再不存在则回退到Idle
        if animation_name not in self.sequences:
            if animation_name != "Talking" and "Talking" in self.sequences:
                animation_name = "Talking"
            elif "Idle" in self.sequences:
                animation_name = "Idle"
            else:
                return  # 没有任何可用动画
        
        self._current_sequence = self.sequences[animation_name]
        self._current_index = 0
        self._is_looping = loop
        self._next_state = next_state
        self._is_playing = True
        
        # 发送第一帧
        frame = self._current_sequence.get_frame(0)
        if frame:
            self.frame_changed.emit(frame)
        
        # 如果是静态图片，不需要启动定时器
        if self._current_sequence.is_static and loop:
            return
        
        # 启动定时器
        self._timer.start(self.frame_interval)
    
    def play_once(self, animation_name: str, next_state: str = "Idle"):
        """播放一次动画"""
        self.play(animation_name, loop=False, next_state=next_state)
    
    def stop(self):
        """停止播放"""
        self._timer.stop()
        self._is_playing = False
    
    def _on_frame_timeout(self):
        """帧超时回调"""
        if not self._current_sequence:
            return
        
        # 静态图片不需要更新
        if self._current_sequence.is_static:
            return
        
        self._current_index += 1
        
        # 检查是否到最后一帧
        if self._current_index >= len(self._current_sequence.frames):
            if self._is_looping:
                # 循环播放
                self._current_index = 0
            else:
                # 单次播放完成
                self.stop()
                self.animation_finished.emit(self._next_state)
                return
        
        # 发送当前帧
        frame = self._current_sequence.get_frame(self._current_index)
        if frame:
            self.frame_changed.emit(frame)
    
    def get_current_frame(self) -> Optional[QPixmap]:
        """获取当前帧"""
        if not self._current_sequence:
            return None
        return self._current_sequence.get_frame(self._current_index)
    
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self._is_playing
    
    def set_fps(self, fps: int):
        """设置帧率"""
        self.fps = fps
        self.frame_interval = int(1000 / fps)
        if self._timer.isActive():
            self._timer.setInterval(self.frame_interval)
    
    def get_available_animations(self) -> List[str]:
        """获取所有可用动画名称"""
        return list(self.sequences.keys())
