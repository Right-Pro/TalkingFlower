"""
音频管理器 - 管理所有音频资源和播放
"""
import json
import os
import random
from pathlib import Path
from typing import Optional, Dict, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioEntry:
    """音频条目"""
    def __init__(self, data: dict):
        self.id = data.get("id", "")
        self.filename = data.get("filename", "")
        self.text = data.get("text", "")
        self.weight = data.get("weight", 10)
        self.animation = data.get("animation", "Talking")
        self.duration_ms = data.get("duration_ms", 2000)
        self.trigger = data.get("trigger", "")
        self.play_once_per_day = data.get("play_once_per_day", False)
        self.cooldown_minutes = data.get("cooldown_minutes", 0)
        self.hour = data.get("hour", -1)
        self.minute = data.get("minute", -1)
        self.is_error = data.get("is_error", False)
        self.correction_text = data.get("correction_text", "")
        self.correction_filename = data.get("correction_filename", "")


class AudioCategory:
    """音频分类"""
    def __init__(self, name: str, audio_dir: str, json_path: str):
        self.name = name
        self.audio_dir = audio_dir
        self.json_path = json_path
        self.description = ""
        self.entries: List[AudioEntry] = []
        self.error_rate = 0
        self.correction_delay_ms = 1500
        self._last_played: Dict[str, float] = {}  # 记录上次播放时间
        self._played_today: set = set()  # 今天已播放的一次性条目
        self._recent_played: list = []  # 最近播放的条目ID列表
        self._recent_limit: int = 5  # 最近播放记录上限
        self._no_repeat_duration: int = 300  # 防重复时间（秒，默认5分钟）

    def load(self):
        """加载JSON配置"""
        if not os.path.exists(self.json_path):
            return
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.description = data.get("description", "")
        self.error_rate = data.get("error_rate", 0)
        self.correction_delay_ms = data.get("correction_delay_ms", 1500)
        
        self.entries = []
        for entry_data in data.get("entries", []):
            self.entries.append(AudioEntry(entry_data))

    def get_random_entry(self) -> Optional[AudioEntry]:
        """根据权重随机获取条目"""
        if not self.entries:
            return None
        
        # 过滤掉在冷却中的条目
        import time
        now = time.time()
        available_entries = []
        weights = []
        
        for entry in self.entries:
            # 检查是否是一次性且已播放
            if entry.play_once_per_day and entry.id in self._played_today:
                continue
            
            # 检查冷却时间
            if entry.id in self._last_played:
                elapsed = (now - self._last_played[entry.id]) / 60  # 转换为分钟
                if entry.cooldown_minutes > 0 and elapsed < entry.cooldown_minutes:
                    continue
            
            # 检查是否在最近播放列表中（防重复）
            if entry.id in self._recent_played:
                continue
            
            available_entries.append(entry)
            weights.append(entry.weight)
        
        # 如果所有条目都被过滤了，放宽条件（只排除最近一个）
        if not available_entries and self.entries:
            for entry in self.entries:
                if entry.play_once_per_day and entry.id in self._played_today:
                    continue
                if entry.id in self._recent_played and len(self._recent_played) > 0:
                    if entry.id == self._recent_played[-1]:
                        continue
                available_entries.append(entry)
                weights.append(entry.weight)
        
        if not available_entries:
            return None
        
        # 加权随机选择
        total = sum(weights)
        r = random.uniform(0, total)
        upto = 0
        for entry, weight in zip(available_entries, weights):
            upto += weight
            if r <= upto:
                return entry
        
        return available_entries[-1]

    def get_entry_by_id(self, entry_id: str) -> Optional[AudioEntry]:
        """根据ID获取条目"""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_random_entry_by_trigger(self, trigger: str) -> Optional[AudioEntry]:
        """根据trigger随机获取条目"""
        import time
        now = time.time()
        
        # 筛选符合条件的条目
        available_entries = []
        weights = []
        
        for entry in self.entries:
            # 检查trigger是否匹配
            if trigger not in entry.trigger:
                continue
            
            # 检查是否是一次性且已播放
            if entry.play_once_per_day and entry.id in self._played_today:
                continue
            
            # 检查冷却时间
            if entry.id in self._last_played:
                elapsed = (now - self._last_played[entry.id]) / 60
                if entry.cooldown_minutes > 0 and elapsed < entry.cooldown_minutes:
                    continue
            
            # 检查是否在最近播放列表中（防重复）
            if entry.id in self._recent_played:
                continue
            
            available_entries.append(entry)
            weights.append(entry.weight)
        
        # 如果所有条目都被过滤了，放宽条件（只排除最近一个）
        if not available_entries:
            for entry in self.entries:
                if trigger not in entry.trigger:
                    continue
                if entry.play_once_per_day and entry.id in self._played_today:
                    continue
                if entry.id in self._recent_played and len(self._recent_played) > 0:
                    if entry.id == self._recent_played[-1]:
                        continue
                available_entries.append(entry)
                weights.append(entry.weight)
        
        if not available_entries:
            return None
        
        # 加权随机选择
        total = sum(weights)
        r = random.uniform(0, total)
        upto = 0
        for entry, weight in zip(available_entries, weights):
            upto += weight
            if r <= upto:
                return entry
        
        return available_entries[-1]

    def get_entries_by_trigger(self, trigger: str) -> List[AudioEntry]:
        """根据trigger获取所有匹配的条目"""
        result = []
        for entry in self.entries:
            if trigger in entry.trigger:
                result.append(entry)
        return result

    def get_time_entry(self, hour: int, minute: int) -> Optional[AudioEntry]:
        """获取整点报时条目"""
        # 先找正常版本
        normal_entries = [e for e in self.entries 
                         if e.hour == hour and e.minute == minute and not e.is_error]
        
        if not normal_entries:
            return None
        
        return random.choice(normal_entries)

    def get_time_entry_with_error(self, hour: int, minute: int) -> tuple:
        """获取整点报时条目，可能包含错误彩蛋
        
        Returns:
            (正确条目, 错误条目列表 or None)
            如果触发错误，返回 (None, [error_01, error_02])
            如果没有触发错误，返回 (正确条目, None)
        """
        # 先找正常版本
        normal_entries = [e for e in self.entries 
                         if e.hour == hour and e.minute == minute and not e.is_error]
        
        if not normal_entries:
            return None, None
        
        # 检查是否触发错误彩蛋
        if random.random() < self.error_rate:
            # 找对应的错误版本 (error_01 和 error_02)
            error_01_list = [e for e in self.entries 
                           if e.hour == hour and e.minute == minute 
                           and e.is_error and "error_01" in e.id]
            error_02_list = [e for e in self.entries 
                           if e.hour == hour and e.minute == minute 
                           and e.is_error and "error_02" in e.id]
            
            if error_01_list and error_02_list:
                return None, [error_01_list[0], error_02_list[0]]
        
        return random.choice(normal_entries), None

    def mark_played(self, entry_id: str):
        """标记条目已播放"""
        import time
        self._last_played[entry_id] = time.time()
        entry = self.get_entry_by_id(entry_id)
        if entry and entry.play_once_per_day:
            self._played_today.add(entry_id)
        
        # 更新最近播放列表（防重复）
        if entry_id in self._recent_played:
            self._recent_played.remove(entry_id)
        self._recent_played.append(entry_id)
        # 限制列表长度
        if len(self._recent_played) > self._recent_limit:
            self._recent_played.pop(0)

    def reset_daily(self):
        """重置每日记录"""
        self._played_today.clear()
        self._recent_played.clear()


class AudioManager(QObject):
    """音频管理器"""
    # 信号
    audio_started = pyqtSignal(str, str, int)  # category, text, duration_ms
    audio_finished = pyqtSignal()  # 音频播放完成
    
    def __init__(self, assets_dir: str = "Assets"):
        super().__init__()
        self.assets_dir = Path(assets_dir)
        self.audio_dir = self.assets_dir / "Audio"
        self.library_dir = self.assets_dir / "Library"
        
        self.categories: Dict[str, AudioCategory] = {}
        self.volume = 0.8
        self.mute = False
        
        # 播放器
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)
        
        # 文件监视器（热重载）
        self._watcher = QFileSystemWatcher()
        self._watcher.fileChanged.connect(self._on_file_changed)
        
        # 当前播放信息
        self._current_category: Optional[str] = None
        self._current_entry: Optional[AudioEntry] = None
        self._is_correction_playing = False
        
    def initialize(self):
        """初始化音频管理器"""
        # 加载所有分类（音频文件统一在Index目录）
        self._load_category("Idle", "Index")
        self._load_category("DoubleClick", "Index")
        self._load_category("System", "Index")
        self._load_category("TimeAnnounce", "TimeAnnounce")
        
        self.set_volume(self.volume)
        self.set_mute(self.mute)
    
    def _load_category(self, name: str, folder: str):
        """加载单个分类"""
        audio_dir = self.audio_dir / folder
        json_path = self.library_dir / f"{name.lower()}.json"
        
        category = AudioCategory(name, str(audio_dir), str(json_path))
        category.load()
        self.categories[name] = category
        
        # 监视JSON文件变更
        if json_path.exists():
            self._watcher.addPath(str(json_path))
    
    def _on_file_changed(self, path: str):
        """文件变更回调（热重载）"""
        path = Path(path)
        category_name = path.stem.capitalize()
        
        # 特殊处理
        if category_name == "Doubleclick":
            category_name = "DoubleClick"
        elif category_name == "Timeannounce":
            category_name = "TimeAnnounce"
        
        if category_name in self.categories:
            print(f"[AudioManager] 检测到配置变更: {category_name}")
            self.categories[category_name].load()
    
    def set_volume(self, volume: float):
        """设置音量"""
        self.volume = max(0.0, min(1.0, volume))
        self._audio_output.setVolume(self.volume)
    
    def set_mute(self, mute: bool):
        """设置静音"""
        self.mute = mute
        self._audio_output.setMuted(mute)
    
    def play_random(self, category: str) -> bool:
        """随机播放分类中的音频"""
        print(f"\n[AudioManager] ========== 随机播放 ==========")
        print(f"[AudioManager] 目标分类: {category}")
        
        if category not in self.categories:
            print(f"[AudioManager] ✗ 错误: 分类 '{category}' 不存在")
            print(f"[AudioManager] 可用分类: {list(self.categories.keys())}")
            print(f"[AudioManager] ==============================")
            return False
        
        cat = self.categories[category]
        available = len([e for e in cat.entries if e.id not in cat._recent_played])
        total = len(cat.entries)
        
        print(f"[AudioManager] 分类状态: {available}/{total} 可用 (排除最近{len(cat._recent_played)}条)")
        
        entry = cat.get_random_entry()
        
        if entry is None:
            print(f"[AudioManager] ✗ 错误: 没有可用的音频条目")
            print(f"[AudioManager] ==============================")
            return False
        
        print(f"[AudioManager] 选中条目: {entry.id}")
        print(f"[AudioManager] ==============================")
        
        return self._play_entry(category, entry)
    
    def play_specific(self, category: str, entry_id: str) -> bool:
        """播放指定条目"""
        if category not in self.categories:
            return False
        
        cat = self.categories[category]
        entry = cat.get_entry_by_id(entry_id)
        
        if entry is None:
            return False
        
        return self._play_entry(category, entry)

    def play_by_trigger(self, category: str, trigger: str) -> bool:
        """根据trigger随机播放分类中的音频"""
        print(f"\n[AudioManager] ========== 按Trigger播放 ==========")
        print(f"[AudioManager] 分类: {category}")
        print(f"[AudioManager] Trigger: {trigger}")
        
        if category not in self.categories:
            print(f"[AudioManager] ✗ 错误: 分类 '{category}' 不存在")
            print(f"[AudioManager] =================================")
            return False
        
        cat = self.categories[category]
        
        # 统计匹配的条目
        matching = [e for e in cat.entries if trigger in e.trigger]
        print(f"[AudioManager] 匹配条目数: {len(matching)}")
        
        entry = cat.get_random_entry_by_trigger(trigger)
        
        if entry is None:
            print(f"[AudioManager] ✗ 错误: 没有匹配的可用条目")
            print(f"[AudioManager] =================================")
            return False
        
        print(f"[AudioManager] 选中条目: {entry.id}")
        print(f"[AudioManager] =================================")
        
        return self._play_entry(category, entry)
    
    def play_time(self, hour: int, minute: int) -> bool:
        """播放整点报时"""
        if "TimeAnnounce" not in self.categories:
            return False
        
        cat = self.categories["TimeAnnounce"]
        correct_entry, error_entries = cat.get_time_entry_with_error(hour, minute)
        
        if correct_entry is None and error_entries is None:
            return False
        
        # 如果触发错误彩蛋，播放错误序列
        if error_entries:
            return self._play_time_error_sequence(error_entries)
        
        # 正常播放
        return self._play_entry("TimeAnnounce", correct_entry)
    
    def _play_time_error_sequence(self, error_entries: list) -> bool:
        """播放整点报时错误序列（error_01 + error_02）"""
        if len(error_entries) < 2:
            return False
        
        self._time_error_sequence = error_entries
        self._time_error_index = 0
        
        # 合并文本
        combined_text = "".join([e.text for e in error_entries])
        total_duration = sum([e.duration_ms for e in error_entries]) + self.categories["TimeAnnounce"].correction_delay_ms
        
        # 发射信号显示合并文本
        self.audio_started.emit("TimeAnnounce", combined_text, total_duration)
        
        # 播放第一条（错误）
        return self._play_time_error_next()
    
    def _play_time_error_next(self) -> bool:
        """播放下一条时间错误音频"""
        if self._time_error_index >= len(self._time_error_sequence):
            # 序列播放完成
            self.audio_finished.emit()
            return True
        
        entry = self._time_error_sequence[self._time_error_index]
        self._time_error_index += 1
        
        cat = self.categories["TimeAnnounce"]
        audio_path = Path(cat.audio_dir) / entry.filename
        
        if not audio_path.exists():
            print(f"[AudioManager] 音频文件不存在: {audio_path}")
            # 跳过这条，播放下一条
            return self._play_time_error_next()
        
        # 停止当前播放
        self.stop()
        
        self._current_category = "TimeAnnounce"
        self._current_entry = entry
        self._is_time_error_playing = True
        
        # 设置音频源
        from PyQt6.QtCore import QUrl
        self._player.setSource(QUrl.fromLocalFile(str(audio_path)))
        
        # 标记已播放
        cat.mark_played(entry.id)
        
        # 播放
        self._player.play()
        
        return True
    
    def _play_entry(self, category: str, entry: AudioEntry) -> bool:
        """播放指定条目"""
        print(f"\n[AudioManager] ---------- 播放音频 ----------")
        print(f"[AudioManager] 分类: {category}")
        print(f"[AudioManager] 条目ID: {entry.id}")
        print(f"[AudioManager] 文本: {entry.text}")
        print(f"[AudioManager] 文件名: {entry.filename}")
        print(f"[AudioManager] 时长: {entry.duration_ms}ms")
        
        cat = self.categories[category]
        audio_path = Path(cat.audio_dir) / entry.filename
        
        print(f"[AudioManager] 完整路径: {audio_path}")
        
        if not audio_path.exists():
            print(f"[AudioManager] ✗ 错误: 音频文件不存在!")
            print(f"[AudioManager] ------------------------------")
            return False
        
        print(f"[AudioManager] ✓ 文件存在")
        
        # 停止当前播放
        self.stop()
        
        self._current_category = category
        self._current_entry = entry
        self._is_correction_playing = False
        
        # 设置音频源
        from PyQt6.QtCore import QUrl
        self._player.setSource(QUrl.fromLocalFile(str(audio_path)))
        
        # 标记已播放
        cat.mark_played(entry.id)
        
        # 播放
        self._player.play()
        
        print(f"[AudioManager] ✓ 开始播放")
        print(f"[AudioManager] ------------------------------")
        
        # 发射信号
        self.audio_started.emit(category, entry.text, entry.duration_ms)
        
        return True
    
    def _on_media_status_changed(self, status):
        """媒体状态变更回调"""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 检查是否正在播放时间错误序列
            if hasattr(self, '_is_time_error_playing') and self._is_time_error_playing:
                self._is_time_error_playing = False
                # 延迟后播放下一条
                if hasattr(self, '_time_error_sequence') and self._time_error_index < len(self._time_error_sequence):
                    from PyQt6.QtCore import QTimer
                    delay = self.categories["TimeAnnounce"].correction_delay_ms
                    QTimer.singleShot(delay, self._play_time_error_next)
                    return
                else:
                    self._finish_playback()
                    return
            
            # 检查是否需要播放纠正音频（彩蛋）
            if (self._current_entry and self._current_entry.is_error 
                and self._current_entry.correction_filename
                and not self._is_correction_playing):
                self._play_correction()
            else:
                self._finish_playback()
    
    def _play_correction(self):
        """播放纠正音频（彩蛋）"""
        if not self._current_entry:
            return
        
        entry = self._current_entry
        cat = self.categories.get(self._current_category)
        if not cat:
            return
        
        # 延迟后播放纠正
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(cat.correction_delay_ms, self._do_play_correction)
    
    def _do_play_correction(self):
        """实际播放纠正音频"""
        if not self._current_entry:
            return
        
        entry = self._current_entry
        cat = self.categories.get(self._current_category)
        if not cat:
            return
        
        correction_path = Path(cat.audio_dir) / entry.correction_filename
        
        if correction_path.exists():
            self._is_correction_playing = True
            self._player.setSource(str(correction_path))
            self._player.play()
            
            # 发射纠正信号
            self.audio_started.emit(
                self._current_category, 
                entry.correction_text, 
                2000  # 默认纠正音频时长
            )
        else:
            self._finish_playback()
    
    def _finish_playback(self):
        """完成播放"""
        self._current_category = None
        self._current_entry = None
        self._is_correction_playing = False
        self.audio_finished.emit()
    
    def stop(self):
        """停止播放"""
        self._player.stop()
    
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
    
    def reset_daily(self):
        """重置每日记录"""
        for cat in self.categories.values():
            cat.reset_daily()
