# -*- coding: utf-8 -*-
"""
花体核心类 - 主窗体和交互逻辑
简化版：只保留对话框，无动画
"""
import sys
import json
import os
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter, QFontMetrics
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QApplication, QMenu,
    QInputDialog, QMessageBox
)

from audio_manager import AudioManager
from event_watcher import EventWatcher


class WeatherPopupWidget(QWidget):
    """美观的天气提示弹窗"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # 标题栏
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        self.city_label = QLabel("天气预报")
        self.city_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.city_label.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(self.city_label)
        
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Microsoft YaHei", 10))
        self.time_label.setStyleSheet("color: #7f8c8d;")
        title_layout.addWidget(self.time_label)
        
        layout.addLayout(title_layout)
        
        # 分隔线
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background: linear-gradient(to right, #3498db, #2ecc71); border-radius: 1px;")
        layout.addWidget(line)
        
        # 天气信息网格
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # 天气状况和温度（大字体）
        weather_layout = QHBoxLayout()
        self.weather_icon_label = QLabel("☀")
        self.weather_icon_label.setFont(QFont("Segoe UI Emoji", 32))
        weather_layout.addWidget(self.weather_icon_label)
        
        self.weather_desc_label = QLabel("--")
        self.weather_desc_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        self.weather_desc_label.setStyleSheet("color: #2c3e50;")
        weather_layout.addWidget(self.weather_desc_label)
        weather_layout.addStretch()
        info_layout.addLayout(weather_layout)
        
        # 温度
        self.temp_label = QLabel("--°C")
        self.temp_label.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
        self.temp_label.setStyleSheet("color: #e74c3c;")
        info_layout.addWidget(self.temp_label)
        
        # 详细信息网格
        details_layout = QHBoxLayout()
        details_layout.setSpacing(15)
        
        # 体感温度
        feels_layout = QVBoxLayout()
        feels_layout.setSpacing(2)
        feels_title = QLabel("体感")
        feels_title.setFont(QFont("Microsoft YaHei", 9))
        feels_title.setStyleSheet("color: #7f8c8d;")
        feels_layout.addWidget(feels_title)
        self.feels_label = QLabel("--°C")
        self.feels_label.setFont(QFont("Microsoft YaHei", 11))
        self.feels_label.setStyleSheet("color: #34495e;")
        feels_layout.addWidget(self.feels_label)
        details_layout.addLayout(feels_layout)
        
        # 湿度
        humidity_layout = QVBoxLayout()
        humidity_layout.setSpacing(2)
        humidity_title = QLabel("湿度")
        humidity_title.setFont(QFont("Microsoft YaHei", 9))
        humidity_title.setStyleSheet("color: #7f8c8d;")
        humidity_layout.addWidget(humidity_title)
        self.humidity_label = QLabel("--%")
        self.humidity_label.setFont(QFont("Microsoft YaHei", 11))
        self.humidity_label.setStyleSheet("color: #34495e;")
        humidity_layout.addWidget(self.humidity_label)
        details_layout.addLayout(humidity_layout)
        
        # 空气质量
        aqi_layout = QVBoxLayout()
        aqi_layout.setSpacing(2)
        aqi_title = QLabel("AQI")
        aqi_title.setFont(QFont("Microsoft YaHei", 9))
        aqi_title.setStyleSheet("color: #7f8c8d;")
        aqi_layout.addWidget(aqi_title)
        self.aqi_label = QLabel("--")
        self.aqi_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.aqi_label.setStyleSheet("color: #27ae60;")
        aqi_layout.addWidget(self.aqi_label)
        details_layout.addLayout(aqi_layout)
        
        info_layout.addLayout(details_layout)
        layout.addLayout(info_layout)
        
        # 底部提示
        self.tip_label = QLabel("每半小时自动更新")
        self.tip_label.setFont(QFont("Microsoft YaHei", 9))
        self.tip_label.setStyleSheet("color: #95a5a6; font-style: italic;")
        self.tip_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.tip_label)
        
        self.setFixedWidth(280)
        self.hide()
        
        # 自动关闭定时器
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
    
    def update_weather(self, data: dict):
        """更新天气数据显示"""
        from datetime import datetime
        
        city = data.get('city', '未知')
        weather = data.get('weather', '--')
        temp = data.get('temperature', '--')
        feels = data.get('apparent_temperature', '--')
        humidity = data.get('humidity', '--')
        aqi = data.get('aqi', '--')
        skycon = data.get('skycon', '')
        
        self.city_label.setText(f"📍 {city}")
        self.time_label.setText(datetime.now().strftime("%Y年%m月%d日 %H:%M"))
        
        # 天气图标
        icon_map = {
            'CLEAR': '☀', 'CLEAR_DAY': '☀', 'CLEAR_NIGHT': '🌙',
            'PARTLY_CLOUDY': '⛅', 'PARTLY_CLOUDY_DAY': '⛅', 'PARTLY_CLOUDY_NIGHT': '☁',
            'CLOUDY': '☁', 'OVERCAST': '☁',
            'RAIN': '🌧', 'LIGHT_RAIN': '🌦', 'MODERATE_RAIN': '🌧', 'HEAVY_RAIN': '⛈',
            'SNOW': '❄', 'LIGHT_SNOW': '🌨', 'MODERATE_SNOW': '❄', 'HEAVY_SNOW': '❄',
            'FOG': '🌫', 'HAZE': '🌫', 'DUST': '😷', 'SAND': '😷',
            'WIND': '💨',
        }
        icon = '☀'
        for key in icon_map:
            if key in skycon:
                icon = icon_map[key]
                break
        self.weather_icon_label.setText(icon)
        
        self.weather_desc_label.setText(weather)
        self.temp_label.setText(f"{temp}°C")
        self.feels_label.setText(f"{feels}°C")
        self.humidity_label.setText(f"{humidity}%")
        self.aqi_label.setText(str(aqi))
        
        # AQI颜色
        try:
            aqi_val = int(aqi)
            if aqi_val <= 50:
                self.aqi_label.setStyleSheet("color: #27ae60;")  # 绿
            elif aqi_val <= 100:
                self.aqi_label.setStyleSheet("color: #f1c40f;")  # 黄
            elif aqi_val <= 150:
                self.aqi_label.setStyleSheet("color: #e67e22;")  # 橙
            else:
                self.aqi_label.setStyleSheet("color: #e74c3c;")  # 红
        except:
            self.aqi_label.setStyleSheet("color: #7f8c8d;")
    
    def show_popup(self, x: int, y: int, duration_ms: int = 10000):
        """显示天气弹窗"""
        self.move(x, y)
        self.show()
        self.raise_()
        self._hide_timer.stop()
        self._hide_timer.start(duration_ms)
    
    def paintEvent(self, event):
        """绘制圆角背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 渐变背景
        from PyQt6.QtGui import QLinearGradient, QBrush
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, 245))
        gradient.setColorAt(1, QColor(245, 248, 250, 245))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QColor(200, 210, 220, 200))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 15, 15)
        
        # 阴影效果
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 20))
        painter.drawRoundedRect(self.rect().adjusted(5, 5, 0, 0), 15, 15)
        
        super().paintEvent(event)


class BubbleWidget(QWidget):
    """对话气泡"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 15)
        
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Microsoft YaHei", 12))
        self.label.setStyleSheet("""
            QLabel {
                color: #333333;
                background: transparent;
            }
        """)
        layout.addWidget(self.label)
        
        self.setFixedWidth(250)
        self.hide()
        
        self._type_timer = QTimer()
        self._type_timer.timeout.connect(self._on_type_tick)
        self._full_text = ""
        self._current_index = 0
        
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)
        
        # 当前形态，用于绘制三角形位置
        self._form = 1
    
    def show_text(self, text: str, duration_ms: int = 5000):
        """显示文本（带打字机效果）"""
        self._full_text = text
        self._current_index = 0
        self.label.setText("")
        
        fm = QFontMetrics(self.label.font())
        rect = fm.boundingRect(0, 0, 220, 1000, Qt.TextFlag.TextWordWrap, text)
        self.setFixedHeight(rect.height() + 30)
        
        self.show()
        self._type_timer.start(50)
        
        self._hide_timer.stop()
        self._hide_timer.start(duration_ms + len(text) * 50)
    
    def _on_type_tick(self):
        """打字机效果定时器"""
        if self._current_index < len(self._full_text):
            self._current_index += 1
            self.label.setText(self._full_text[:self._current_index])
        else:
            self._type_timer.stop()
    
    def paintEvent(self, event):
        """绘制气泡背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.setPen(QColor(200, 200, 200, 200))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)
        
        import PyQt6.QtCore as QtCore
        
        if self._form == 2:
            # 形态2：三角形在左边，指向左下方的花朵
            triangle = [
                QtCore.QPoint(-1, self.height() // 2 - 10),
                QtCore.QPoint(-1, self.height() // 2 + 10),
                QtCore.QPoint(-10, self.height() // 2)
            ]
        else:
            # 形态1：三角形在下边，指向下方的花朵
            triangle = [
                QtCore.QPoint(self.width() // 2 - 10, self.height() - 1),
                QtCore.QPoint(self.width() // 2 + 10, self.height() - 1),
                QtCore.QPoint(self.width() // 2, self.height() + 10)
            ]
        painter.drawPolygon(triangle)
        
        super().paintEvent(event)
    
    def position_above(self, x: int, y: int, flower_width: int, flower_height: int = 150, form: int = 1):
        """定位气泡位置
        form=1: 在花朵上方
        form=2: 在花朵右方
        """
        self._form = form
        if form == 2:
            # 形态2：在花朵右方
            self.move(
                x + flower_width + 10,
                y + flower_height // 2 - self.height() // 2
            )
        else:
            # 形态1：在花朵上方（默认）
            self.move(
                x + flower_width // 2 - self.width() // 2,
                y - self.height() - 10
            )


class FlowerWidget(QWidget):
    """花体主窗体"""
    
    def __init__(self):
        super().__init__()
        
        self.config = self._load_config()
        self.scale = self.config.get("scale", 1.0)
        
        # 窗口设置
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 拖拽状态
        self._drag_start_pos = None
        self._is_dragging = False
        
        # 点击计数（用于双击/三击检测）
        self._click_count = 0
        self._click_timer = QTimer()
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_click_timeout)
        
        # 静音序列播放状态
        self._mute_sequence_playing = False
        self._mute_sequence_entries = []
        self._mute_sequence_index = 0
        self._mute_sequence_texts = []
        
        self._init_components()
        self._init_ui()
        
        pos = self.config.get("position", {"x": 1200, "y": 800})
        self.move(pos["x"], pos["y"])
        
        self._init_context_menu()
    
    def _load_config(self) -> dict:
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def _save_config(self):
        self.config["position"] = {"x": self.x(), "y": self.y()}
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _init_components(self):
        """初始化组件"""
        # 音频管理器
        self.audio_manager = AudioManager()
        self.audio_manager.initialize()
        self.audio_manager.set_volume(self.config.get("volume", 0.8))
        self.audio_manager.audio_started.connect(self._on_audio_started)
        self.audio_manager.audio_finished.connect(self._on_audio_finished)
        
        # 事件监视器
        self.event_watcher = EventWatcher(self.config)
        self.event_watcher.idle_trigger.connect(self._on_idle_trigger)
        self.event_watcher.weather_good.connect(self._on_weather_good)
        self.event_watcher.cpu_temp_high.connect(self._on_cpu_temp_high)
        self.event_watcher.cpu_temp_low.connect(self._on_cpu_temp_low)
        self.event_watcher.cpu_usage_high.connect(self._on_cpu_usage_high)
        self.event_watcher.cpu_usage_low.connect(self._on_cpu_usage_low)
        self.event_watcher.time_morning.connect(self._on_time_morning)
        self.event_watcher.time_noon.connect(self._on_time_noon)
        self.event_watcher.time_sunset.connect(self._on_time_sunset)
        self.event_watcher.time_night.connect(self._on_time_night)
        self.event_watcher.time_announce.connect(self._on_time_announce)
        self.event_watcher.time_bedtime.connect(self._on_time_bedtime)
        self.event_watcher.time_wake.connect(self._on_time_wake)
        self.event_watcher.astronomy_updated.connect(self._on_astronomy_updated)
        self.event_watcher.weather_data_ready.connect(self._on_weather_data_ready)
        self.event_watcher.weather_popup.connect(self._on_weather_popup)
        
        # 天气弹窗
        self.weather_popup = WeatherPopupWidget()
        self._last_weather_data = None
        
        # 半小时天气弹窗定时器
        self._weather_popup_timer = QTimer()
        self._weather_popup_timer.timeout.connect(self._auto_show_weather_popup)
        self._weather_popup_timer.start(30 * 60 * 1000)  # 30分钟 = 1800000毫秒
        
        # 启用天气弹窗标志
        self._weather_popup_enabled = True
        
        # 弹窗关闭后刷新定时器
        self._popup_refresh_timer = QTimer()
        self._popup_refresh_timer.setSingleShot(True)
        self._popup_refresh_timer.timeout.connect(self._refresh_weather_after_popup)
    
    def _on_weather_data_ready(self, info_text: str, data: dict = None):
        """天气数据准备好时的回调 - 输出到终端并保存数据"""
        print(f"\n[WeatherInfo] {info_text}\n")
        if data:
            self._last_weather_data = data
    
    def _on_weather_popup(self):
        """收到天气弹窗信号"""
        self._show_weather_popup()
    
    def _auto_show_weather_popup(self):
        """自动显示天气弹窗（每30分钟）- 显示前先刷新天气"""
        if not self._weather_popup_enabled:
            return
        
        print("[WeatherPopup] 自动显示时间到，先刷新天气数据...")
        # 连接一次性信号，在天气刷新完成后显示弹窗
        self.event_watcher.weather_data_ready.connect(self._on_weather_ready_for_popup)
        self.event_watcher.force_check_weather()
    
    def _on_weather_ready_for_popup(self, info_text: str, data: dict = None):
        """天气数据准备好后显示弹窗（自动模式）"""
        # 断开信号，避免重复连接
        try:
            self.event_watcher.weather_data_ready.disconnect(self._on_weather_ready_for_popup)
        except:
            pass
        
        if data and self._weather_popup_enabled:
            self._show_weather_popup_internal(data)
    
    def _show_weather_popup(self):
        """手动显示天气弹窗（右键菜单）- 使用当前缓存数据，显示结束后刷新"""
        if not self._last_weather_data:
            # 如果没有缓存数据，先刷新再显示
            print("[WeatherPopup] 无缓存数据，先刷新天气...")
            self.event_watcher.weather_data_ready.connect(self._on_weather_ready_for_popup)
            self.event_watcher.force_check_weather()
            return
        
        # 使用当前缓存数据显示弹窗
        self._show_weather_popup_internal(self._last_weather_data)
        
        # 设置定时器，在弹窗关闭后（15秒后）刷新天气
        print("[WeatherPopup] 手动显示已启动，将在弹窗关闭后自动刷新天气...")
        self._popup_refresh_timer.start(16000)  # 16秒后刷新（弹窗15秒关闭）
    
    def _show_weather_popup_internal(self, data: dict):
        """内部方法：实际显示天气弹窗"""
        # 更新弹窗数据
        self.weather_popup.update_weather(data)
        
        # 计算弹窗位置（花朵上方偏右）
        popup_x = self.x() + self.width() // 2 - 140
        popup_y = self.y() - self.weather_popup.height() - 20
        
        # 确保不超出屏幕顶部
        screen = QApplication.primaryScreen().geometry()
        if popup_y < 50:
            popup_y = self.y() + self.height() + 20
        
        self.weather_popup.show_popup(popup_x, popup_y, 15000)
        print("[WeatherPopup] 显示天气提示弹窗")
    
    def _refresh_weather_after_popup(self):
        """弹窗关闭后刷新天气数据"""
        print("[WeatherPopup] 弹窗已关闭，自动刷新天气数据...")
        self.event_watcher.force_check_weather()
    
    def _toggle_weather_popup(self, enabled: bool):
        """切换天气弹窗开关"""
        self._weather_popup_enabled = enabled
        if enabled:
            print("[WeatherPopup] 天气提示弹窗已启用（每30分钟显示一次）")
        else:
            print("[WeatherPopup] 天气提示弹窗已关闭")
    
    def _init_ui(self):
        """初始化UI"""
        base_size = int(150 * self.scale)
        self.setFixedSize(base_size, base_size)
        
        # 花朵图片
        self.flower_label = QLabel(self)
        self.flower_label.setFixedSize(base_size, base_size)
        self.flower_label.setScaledContents(True)
        
        # 加载图片
        self._load_flower_image()
        
        # 气泡
        self.bubble = BubbleWidget()
        
        # 启动欢迎语
        QTimer.singleShot(500, self._play_startup)
    
    def _load_flower_image(self):
        """加载花朵图片"""
        form = self.config.get("flower_form", 1)
        idle_path = Path("Assets/Visual/Idle")
        
        if idle_path.exists():
            png_files = sorted([f for f in idle_path.iterdir() if f.suffix.lower() == '.png'])
            if len(png_files) >= form:
                pixmap = QPixmap(str(png_files[form - 1]))
                if not pixmap.isNull():
                    target_size = int(150 * self.scale)
                    pixmap = pixmap.scaled(
                        target_size, target_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.flower_label.setPixmap(pixmap)
    
    def _init_context_menu(self):
        """初始化右键菜单"""
        self.context_menu = QMenu(self)
        
        # 静音/取消静音
        self.mute_action = self.context_menu.addAction("静音")
        self.mute_action.setCheckable(True)
        self.mute_action.setChecked(self.config.get("mute", False))
        self.mute_action.triggered.connect(self._toggle_mute)
        
        # CPU监测菜单
        self.cpu_monitor_menu = self.context_menu.addMenu("CPU监测")
        
        # CPU监测总开关
        self.cpu_monitor_action = self.cpu_monitor_menu.addAction("启用CPU监测")
        self.cpu_monitor_action.setCheckable(True)
        self.cpu_monitor_action.setChecked(self.config.get("cpu_monitor_enabled", True))
        self.cpu_monitor_action.triggered.connect(self._toggle_cpu_monitor)
        
        self.cpu_monitor_menu.addSeparator()
        
        # 监测模式选择
        self.cpu_monitor_temp = self.cpu_monitor_menu.addAction("温度监测(需管理员)")
        self.cpu_monitor_temp.setCheckable(True)
        self.cpu_monitor_temp.triggered.connect(lambda: self._set_cpu_monitor_mode("temp"))
        
        self.cpu_monitor_usage = self.cpu_monitor_menu.addAction("使用率监测")
        self.cpu_monitor_usage.setCheckable(True)
        self.cpu_monitor_usage.triggered.connect(lambda: self._set_cpu_monitor_mode("usage"))
        
        # 设置当前选中的模式
        current_monitor_mode = self.config.get("cpu_monitor_mode", "temp")
        self.cpu_monitor_temp.setChecked(current_monitor_mode == "temp")
        self.cpu_monitor_usage.setChecked(current_monitor_mode == "usage")
        
        self.context_menu.addSeparator()
        
        # 形态切换
        self.form_menu = self.context_menu.addMenu("切换形态")
        self.form_action_1 = self.form_menu.addAction("形态 1")
        self.form_action_1.setCheckable(True)
        self.form_action_1.triggered.connect(lambda: self._switch_form(1))
        
        self.form_action_2 = self.form_menu.addAction("形态 2")
        self.form_action_2.setCheckable(True)
        self.form_action_2.triggered.connect(lambda: self._switch_form(2))
        
        current_form = self.config.get("flower_form", 1)
        self.form_action_1.setChecked(current_form == 1)
        self.form_action_2.setChecked(current_form == 2)
        
        self.context_menu.addSeparator()
        
        # 天气设置
        self.weather_popup_action = self.context_menu.addAction("天气提示")
        self.weather_popup_action.setCheckable(True)
        self.weather_popup_action.setChecked(True)
        self.weather_popup_action.triggered.connect(self._toggle_weather_popup)
        
        # 天气API选择
        self.weather_api_menu = self.context_menu.addMenu("天气API")
        self.weather_api_wttr = self.weather_api_menu.addAction("wttr.in (免费，可能不稳定)")
        self.weather_api_wttr.setCheckable(True)
        self.weather_api_wttr.triggered.connect(lambda: self._set_weather_api("wttr.in"))
        
        self.weather_api_caiyun = self.weather_api_menu.addAction("彩云天气 (需配置API)")
        self.weather_api_caiyun.setCheckable(True)
        self.weather_api_caiyun.triggered.connect(lambda: self._set_weather_api("caiyun"))
        
        # 设置当前选中的API
        current_weather_api = self.config.get("weather_api", "wttr.in")
        self.weather_api_wttr.setChecked(current_weather_api == "wttr.in")
        self.weather_api_caiyun.setChecked(current_weather_api == "caiyun")
        
        self.context_menu.addAction("显示天气弹窗").triggered.connect(self._show_weather_popup)
        self.context_menu.addAction("设置天气城市").triggered.connect(self._set_weather_city)
        self.context_menu.addAction("刷新天气").triggered.connect(self._refresh_weather)
        
        self.context_menu.addSeparator()
        
        # 时间设置
        self.time_menu = self.context_menu.addMenu("设置固定时间")
        self.time_menu.addAction("设置早上时间...").triggered.connect(lambda: self._set_time("morning", "早上"))
        self.time_menu.addAction("设置中午时间...").triggered.connect(lambda: self._set_time("noon", "中午"))
        self.time_menu.addAction("设置夕阳时间...").triggered.connect(lambda: self._set_time("sunset", "夕阳"))
        self.time_menu.addAction("设置入寝时间...").triggered.connect(lambda: self._set_time("night", "入寝"))
        self.time_menu.addSeparator()
        self.time_menu.addAction("设置就寝时间（静音）...").triggered.connect(lambda: self._set_time("bedtime", "就寝"))
        self.time_menu.addAction("设置起床时间（取消静音）...").triggered.connect(lambda: self._set_time("wake", "起床"))
        
        self.context_menu.addSeparator()
        
        # 强制说话
        self.context_menu.addAction("说点什么").triggered.connect(
            self.event_watcher.force_idle
        )
        
        self.context_menu.addSeparator()
        
        # 退出
        self.context_menu.addAction("退出").triggered.connect(self._quit)
    
    def _switch_form(self, form_number: int):
        """切换花朵形态"""
        if self.config.get("flower_form", 1) == form_number:
            return
        
        self.config["flower_form"] = form_number
        self._save_config()
        
        self.form_action_1.setChecked(form_number == 1)
        self.form_action_2.setChecked(form_number == 2)
        
        # 重新加载图片
        self._load_flower_image()
    
    def _set_weather_city(self):
        """设置天气城市"""
        current_city = self.config.get("weather_city", "")
        text, ok = QInputDialog.getText(
            self, "设置天气城市", 
            "请输入城市名称（如：北京、上海）：",
            text=current_city
        )
        if ok and text:
            self.config["weather_city"] = text
            self._save_config()
            self.bubble.show_text(f"已设置天气城市：{text}", 3000)
            self._update_bubble_position()
    
    def _refresh_weather(self):
        """刷新天气"""
        city = self.config.get("weather_city", "")
        self.event_watcher.force_check_weather(city)
        self.bubble.show_text("正在刷新天气...", 2000)
        self._update_bubble_position()
    
    def _set_time(self, time_type: str, time_name: str):
        """设置固定时间"""
        current_time = self.config.get(f"time_{time_type}", "")
        if not current_time:
            defaults = {"morning": "08:00", "noon": "12:00", "sunset": "18:00", "night": "22:00", "bedtime": "23:00", "wake": "07:00"}
            current_time = defaults.get(time_type, "08:00")
        
        text, ok = QInputDialog.getText(
            self, f"设置{time_name}时间",
            f"请输入{time_name}时间（格式：HH:MM）：",
            text=current_time
        )
        if ok and text:
            # 验证时间格式
            try:
                hour, minute = map(int, text.split(":"))
                if 0 <= hour < 24 and 0 <= minute < 60:
                    self.config[f"time_{time_type}"] = f"{hour:02d}:{minute:02d}"
                    self._save_config()
                    self.bubble.show_text(f"已设置{time_name}时间为：{self.config[f'time_{time_type}']}", 3000)
                    self._update_bubble_position()
                else:
                    QMessageBox.warning(self, "格式错误", "请输入有效的时间！")
            except:
                QMessageBox.warning(self, "格式错误", "时间格式错误，请使用 HH:MM 格式！")
    
    def _play_startup(self):
        """播放启动欢迎语"""
        self.audio_manager.play_by_trigger("System", "on_start")
    
    def _on_audio_started(self, category: str, text: str, duration_ms: int):
        """音频开始播放回调"""
        self.bubble.show_text(text, duration_ms)
        self._update_bubble_position()
    
    def _on_audio_finished(self):
        """音频播放完成回调"""
        # 如果正在播放静音序列，继续播放下一条
        if self._mute_sequence_playing:
            self._play_next_in_mute_sequence()
    
    def _on_idle_trigger(self):
        """随机闲聊触发"""
        print("[FlowerWidget] 处理: 随机闲聊触发 → 播放Idle语音")
        self.audio_manager.play_random("Idle")
    
    def _on_weather_good(self):
        """天气好触发"""
        print("[FlowerWidget] 处理: 天气好触发 → 播放天气语音")
        self.audio_manager.play_by_trigger("System", "weather_sunny")
    
    def _on_cpu_temp_high(self):
        """CPU温度高触发"""
        print("[FlowerWidget] 处理: CPU高温触发 → 播放温度警告语音")
        self.audio_manager.play_by_trigger("System", "cpu_temp>65")
    
    def _on_cpu_temp_low(self):
        """CPU温度低触发"""
        print("[FlowerWidget] 处理: CPU低温触发 → 播放温度提示语音")
        self.audio_manager.play_by_trigger("System", "cpu_temp<35")
    
    def _on_cpu_usage_high(self):
        """CPU使用率高触发"""
        print("[FlowerWidget] 处理: CPU高负载触发 → 播放高负载提示语音")
        # 使用通用的系统警告语音
        self.audio_manager.play_by_trigger("System", "cpu_temp>65")
    
    def _on_cpu_usage_low(self):
        """CPU使用率低触发"""
        print("[FlowerWidget] 处理: CPU低负载触发 → 播放低负载提示语音")
        # 使用通用的系统提示语音
        self.audio_manager.play_by_trigger("System", "cpu_temp<35")
    
    def _on_time_morning(self):
        """早上触发"""
        print("[FlowerWidget] 处理: 早上时段触发 → 播放早上语音")
        self.audio_manager.play_by_trigger("System", "time_morning")
    
    def _on_time_noon(self):
        """中午触发"""
        print("[FlowerWidget] 处理: 中午时段触发 → 播放中午语音")
        self.audio_manager.play_by_trigger("System", "time_noon")
    
    def _on_time_sunset(self):
        """夕阳触发"""
        print("[FlowerWidget] 处理: 夕阳时段触发 → 播放夕阳语音")
        self.audio_manager.play_by_trigger("System", "time_sunset")
    
    def _on_time_night(self):
        """入寝触发"""
        print("[FlowerWidget] 处理: 入寝时段触发 → 播放入寝语音")
        self.audio_manager.play_by_trigger("System", "time_night")
    
    def _on_time_announce(self, hour: int, minute: int):
        """整点报时触发"""
        print(f"[FlowerWidget] 处理: 整点报时 ({hour:02d}:{minute:02d}) → 播放时间语音")
        self.audio_manager.play_time(hour, minute)
    
    def _on_time_bedtime(self):
        """就寝时段开始 - 静音"""
        print("\n" + "!"*50)
        print("[FlowerWidget] !!!!!!!!!! 状态变更: 进入就寝时段 !!!!!!!!!!")
        print("[FlowerWidget] 操作: 开启静音 + 屏蔽整点报时")
        self.config["mute"] = True
        self.audio_manager.set_mute(True)
        self.mute_action.setChecked(True)
        self._save_config()
        print("[FlowerWidget] !"*50 + "\n")
    
    def _on_time_wake(self):
        """起床时段开始 - 取消静音"""
        print("\n" + "!"*50)
        print("[FlowerWidget] !!!!!!!!!! 状态变更: 进入起床时段 !!!!!!!!!!")
        print("[FlowerWidget] 操作: 取消静音 + 恢复整点报时")
        self.config["mute"] = False
        self.audio_manager.set_mute(False)
        self.mute_action.setChecked(False)
        self._save_config()
        print("[FlowerWidget] !"*50 + "\n")
    
    def _on_astronomy_updated(self, sunset_time: str, moonrise_time: str):
        """天文数据更新 - 自动匹配夕阳和入寝时间"""
        print(f"\n[FlowerWidget] ========== 收到天文数据更新 ==========")
        print(f"[FlowerWidget] 日落时间: {sunset_time} → 夕阳时段")
        print(f"[FlowerWidget] 月出时间: {moonrise_time} → 入寝时段")
        
        # 更新配置
        old_sunset = self.config.get("time_sunset", "")
        old_night = self.config.get("time_night", "")
        
        self.config["time_sunset"] = sunset_time
        self.config["time_night"] = moonrise_time
        
        self._save_config()
        
        print(f"[FlowerWidget] 配置已更新:")
        print(f"[FlowerWidget]   夕阳: {old_sunset} → {sunset_time}")
        print(f"[FlowerWidget]   入寝: {old_night} → {moonrise_time}")
        print(f"[FlowerWidget] ======================================\n")
        
        # 显示气泡提示
        self.bubble.show_text(f"已根据天文数据更新时段\n夕阳: {sunset_time}\n入寝: {moonrise_time}", 5000)
        self._update_bubble_position()
    
    def _update_bubble_position(self):
        """更新气泡位置"""
        current_form = self.config.get("flower_form", 1)
        base_size = int(150 * self.scale)
        self.bubble.position_above(self.x(), self.y(), self.width(), base_size, current_form)
    
    def moveEvent(self, event):
        """移动事件"""
        super().moveEvent(event)
        self._update_bubble_position()
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self._is_dragging = False
            
            self._click_count += 1
            if self._click_count == 1:
                self._click_timer.start(300)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_menu.exec(event.globalPosition().toPoint())
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽"""
        if self._drag_start_pos is not None:
            if not self._is_dragging:
                delta = (event.pos() - self._drag_start_pos).manhattanLength()
                if delta > 5:
                    self._is_dragging = True
            
            if self._is_dragging:
                new_pos = event.globalPosition().toPoint() - self._drag_start_pos
                self.move(new_pos)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_dragging:
                self._is_dragging = False
                self._drag_start_pos = None
                self._save_config()
            else:
                self._drag_start_pos = None
    
    def _on_click_timeout(self):
        """点击超时（连击检测结束）"""
        if self._click_count == 1:
            self._on_single_click()
        elif self._click_count == 2:
            self._on_double_click()
        elif self._click_count >= 3:
            self._on_triple_click()
        
        self._click_count = 0
    
    def _on_single_click(self):
        """单击处理 - 和随机触发一样"""
        self.audio_manager.play_random("Idle")
    
    def _on_double_click(self):
        """双击处理"""
        self.audio_manager.play_random("DoubleClick")
    
    def _on_triple_click(self):
        """三连击彩蛋"""
        if "DoubleClick" in self.audio_manager.categories:
            cat = self.audio_manager.categories["DoubleClick"]
            for entry in cat.entries:
                if "triple" in entry.id:
                    self.audio_manager.play_specific("DoubleClick", entry.id)
                    return
        self.audio_manager.play_random("DoubleClick")
    
    def _toggle_mute(self):
        """切换静音状态"""
        mute = not self.config.get("mute", False)
        
        # 播放静音/取消静音语音
        if mute:
            # 静音时播放两条语音序列
            self._start_mute_sequence()
        else:
            # 取消静音时直接播放
            self.config["mute"] = False
            self.audio_manager.set_mute(False)
            self.mute_action.setChecked(False)
            self._save_config()
            self.audio_manager.play_by_trigger("System", "mute_off")
    
    def _toggle_cpu_monitor(self):
        """切换CPU监测开关"""
        enable = not self.config.get("cpu_monitor_enabled", False)
        self.config["cpu_monitor_enabled"] = enable
        self.cpu_monitor_action.setChecked(enable)
        self._save_config()
        
        mode = self.config.get("cpu_monitor_mode", "temp")
        if enable:
            if mode == "temp":
                self.bubble.show_text("已开启CPU监测\n模式: 温度 (需管理员权限)", 3000)
            else:
                self.bubble.show_text("已开启CPU监测\n模式: 使用率 (无需管理员)", 3000)
        else:
            self.bubble.show_text("已关闭CPU监测", 3000)
        self._update_bubble_position()
    
    def _set_cpu_monitor_mode(self, mode: str):
        """设置CPU监测模式"""
        current_mode = self.config.get("cpu_monitor_mode", "temp")
        if current_mode == mode:
            return
        
        self.config["cpu_monitor_mode"] = mode
        self._save_config()
        
        if mode == "temp":
            self.cpu_monitor_temp.setChecked(True)
            self.cpu_monitor_usage.setChecked(False)
            self.bubble.show_text("已切换为温度监测\n(需要管理员权限)", 3000)
            print("[Config] 已切换为CPU温度监测模式")
        else:
            self.cpu_monitor_temp.setChecked(False)
            self.cpu_monitor_usage.setChecked(True)
            self.bubble.show_text("已切换为使用率监测\n(无需管理员权限)", 3000)
            print("[Config] 已切换为CPU使用率监测模式")
        
        # 重置检测器的首次检测标志
        if hasattr(self, 'event_watcher') and self.event_watcher:
            self.event_watcher._cpu_monitor_mode = mode
            self.event_watcher._first_temp_check = True
        
        self._update_bubble_position()
    
    def _set_weather_api(self, api: str):
        """设置天气API"""
        current_api = self.config.get("weather_api", "wttr.in")
        if current_api == api:
            return
        
        if api == "caiyun":
            # 检查是否配置了API Key
            api_key = self.config.get("caiyun_api_key", "").strip()
            if not api_key:
                # 未配置API Key，弹出提示
                QMessageBox.warning(
                    self,
                    "未配置API Key",
                    "请先在程序根目录的config.json中填写您的API！\n\n"
                    "1. 打开 config.json\n"
                    "2. 在 'caiyun_api_key' 中填写您的API Key\n"
                    "3. 保存文件后重新选择\n\n"
                    "API获取地址: https://www.caiyunapp.com/",
                    QMessageBox.StandardButton.Ok
                )
                # 恢复原来的选择
                self.weather_api_wttr.setChecked(True)
                self.weather_api_caiyun.setChecked(False)
                return
            
            # 已配置API Key，切换到彩云天气
            self.config["weather_api"] = "caiyun"
            self.weather_api_caiyun.setChecked(True)
            self.weather_api_wttr.setChecked(False)
            self._save_config()
            self.bubble.show_text("已切换到彩云天气\n数据更准确", 3000)
            print("[Config] 已切换到彩云天气API")
            
        else:
            # 切换到wttr.in
            self.config["weather_api"] = "wttr.in"
            self.weather_api_wttr.setChecked(True)
            self.weather_api_caiyun.setChecked(False)
            self._save_config()
            self.bubble.show_text("已切换到 wttr.in\n无需配置API", 3000)
            print("[Config] 已切换到 wttr.in API")
        
        self._update_bubble_position()
    
    def _set_cpu_temp_mode(self, mode: str):
        """设置CPU温度检测模式"""
        # 如果已经是当前模式，不做任何操作
        current_mode = self.config.get("cpu_temp_mode", "admin")
        if current_mode == mode:
            return
        
        if mode == "lhm":
            # 切换到LHM模式（无需管理员）
            self.config["cpu_temp_mode"] = "lhm"
            self.cpu_temp_mode_lhm.setChecked(True)
            self.cpu_temp_mode_admin.setChecked(False)
            self._save_config()
            self.event_watcher.set_cpu_temp_mode(mode)
            self.bubble.show_text("已切换到 LibreHardwareMonitor 模式\n(无需管理员权限)", 3000)
            print("[Config] 已切换到 LibreHardwareMonitor 模式")
            
        else:
            # 切换到WMI模式（需要管理员）- 弹出确认对话框
            reply = QMessageBox.question(
                self,
                "需要管理员权限",
                "切换到 WMI 模式需要管理员权限才能读取CPU温度。\n\n"
                "点击【是】将申请管理员权限并重启程序\n"
                "点击【否】取消切换",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 用户同意，保存配置并申请权限
                self.config["cpu_temp_mode"] = "admin"
                self._save_config()
                
                print("[Config] 用户同意切换WMI模式，准备申请管理员权限...")
                self.bubble.show_text("正在申请管理员权限...", 2000)
                
                # 延迟导入并申请权限
                QTimer.singleShot(1000, self._restart_as_admin)
            else:
                # 用户取消，恢复原来的选择
                self.cpu_temp_mode_lhm.setChecked(True)
                self.cpu_temp_mode_admin.setChecked(False)
                print("[Config] 用户取消切换WMI模式")
        
        self._update_bubble_position()
    
    def _restart_as_admin(self):
        """以管理员权限重启程序"""
        try:
            from uac_helper import restart_as_admin
            if restart_as_admin(wait=False):
                print("[UAC] 已启动管理员权限程序，本程序即将退出...")
                self.bubble.show_text("已启动管理员权限程序\n本程序即将退出", 2000)
                QTimer.singleShot(2000, QApplication.instance().quit)
            else:
                print("[UAC] 申请权限失败")
                self.bubble.show_text("申请权限失败\n请手动以管理员身份运行", 3000)
        except Exception as e:
            print(f"[UAC] 重启失败: {e}")
            self.bubble.show_text(f"申请权限失败: {e}", 3000)
    
    def _start_mute_sequence(self):
        """开始静音序列播放（Mute-1 + Mute-2）"""
        if "System" not in self.audio_manager.categories:
            # 没有System分类，直接静音
            self._apply_mute()
            return
        
        cat = self.audio_manager.categories["System"]
        # 获取所有 mute_on 的条目
        entries = cat.get_entries_by_trigger("mute_on")
        
        if len(entries) < 2:
            # 不足两条，直接播放一条或直接静音
            if entries:
                self._mute_sequence_entries = entries
                self._mute_sequence_index = 0
                self._mute_sequence_texts = []
                self._mute_sequence_playing = True
                self._play_next_in_mute_sequence()
            else:
                self._apply_mute()
            return
        
        # 按ID排序，确保 Mute-1 在 Mute-2 之前
        # 这样合并文本就是"诶？我很吵吗？"
        entries_sorted = sorted(entries, key=lambda e: e.id)
        selected = entries_sorted[:2]  # 取前两条（Mute-1 和 Mute-2）
        
        self._mute_sequence_entries = selected
        self._mute_sequence_index = 0
        self._mute_sequence_texts = [e.text for e in selected]
        self._mute_sequence_playing = True
        
        # 先显示合并文本
        combined_text = "".join(self._mute_sequence_texts)
        self.bubble.show_text(combined_text, 5000)
        self._update_bubble_position()
        
        # 然后开始播放第一条
        self._play_next_in_mute_sequence()
    
    def _play_next_in_mute_sequence(self):
        """播放静音序列中的下一条"""
        if self._mute_sequence_index >= len(self._mute_sequence_entries):
            # 序列播放完成，执行静音
            self._finish_mute_sequence()
            return
        
        entry = self._mute_sequence_entries[self._mute_sequence_index]
        self._mute_sequence_index += 1
        
        # 播放这一条（不通过audio_manager的signal，直接播放）
        cat = self.audio_manager.categories["System"]
        audio_path = Path(cat.audio_dir) / entry.filename
        
        if audio_path.exists():
            from PyQt6.QtCore import QUrl
            self.audio_manager._player.setSource(QUrl.fromLocalFile(str(audio_path)))
            self.audio_manager._current_entry = entry
            self.audio_manager._current_category = "System"
            self.audio_manager._player.play()
        else:
            # 文件不存在，跳过
            self._play_next_in_mute_sequence()
    
    def _finish_mute_sequence(self):
        """静音序列播放完成"""
        self._mute_sequence_playing = False
        self._mute_sequence_entries = []
        self._mute_sequence_texts = []
        self._mute_sequence_index = 0
        
        # 执行真正的静音
        self._apply_mute()
    
    def _apply_mute(self):
        """应用静音设置"""
        self.config["mute"] = True
        self.audio_manager.set_mute(True)
        self.mute_action.setChecked(True)
        self._save_config()
    
    def _quit(self):
        """退出程序"""
        # 播放退出语音（在静音状态下也播放）
        was_mute = self.audio_manager.mute
        self.audio_manager.set_mute(False)
        self.audio_manager.play_by_trigger("System", "on_exit")
        
        # 等待语音播放开始
        import time
        time.sleep(0.1)
        
        # 等待语音播放完成
        while self.audio_manager.is_playing():
            time.sleep(0.1)
        
        self._save_config()
        QApplication.quit()
    
    def closeEvent(self, event):
        """关闭事件"""
        self._save_config()
        event.accept()
