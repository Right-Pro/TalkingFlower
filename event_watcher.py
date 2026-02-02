# -*- coding: utf-8 -*-
"""事件监视器 - 检测天气、CPU监测和固定时间触发语音"""
import random
import time
import psutil
import urllib.parse
import urllib.request
import json
import ssl
from datetime import datetime
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

WEATHER_MAP = {'sunny': '晴', 'clear': '晴', 'cloudy': '多云', 'rain': '雨'}
CITY_COORDS = {'沈阳': [123.43, 41.81], '北京': [116.41, 39.90]}
CAIYUN_SKYCON_MAP = {'CLEAR_DAY': '晴', 'CLEAR_NIGHT': '晴', 'CLOUDY': '阴'}

class EventWatcher(QObject):
    idle_trigger = pyqtSignal()
    weather_good = pyqtSignal()
    cpu_temp_high = pyqtSignal()
    cpu_temp_low = pyqtSignal()
    cpu_usage_high = pyqtSignal()
    cpu_usage_low = pyqtSignal()
    time_morning = pyqtSignal()
    time_noon = pyqtSignal()
    time_sunset = pyqtSignal()
    time_night = pyqtSignal()
    time_bedtime = pyqtSignal()
    time_wake = pyqtSignal()
    time_announce = pyqtSignal(int, int)
    astronomy_updated = pyqtSignal(str, str)
    weather_data_ready = pyqtSignal(str, dict)
    weather_popup = pyqtSignal()
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self._weather_cooldown = 0
        self._cpu_temp_high_cooldown = 0
        self._cpu_temp_low_cooldown = 0
        self._last_weather_check = None
        self._last_cpu_check = 0
        self._last_temp_status = None
        self._first_temp_check = True
        self.is_bedtime = False
        self._cpu_monitor_mode = config.get("cpu_monitor_mode", "temp")
        self._cpu_usage_high_cooldown = 0
        self._cpu_usage_low_cooldown = 0
        self._last_usage_status = None
        self._last_morning_triggered = -1
        self._last_noon_triggered = -1
        self._last_sunset_triggered = -1
        self._last_night_triggered = -1
        self._last_bedtime_triggered = -1
        self._last_wake_triggered = -1
        self._last_hour_announced = -1
        self._idle_timer = QTimer()
        self._idle_timer.timeout.connect(self._on_idle_timer)
        self._reset_idle_timer()
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._on_system_check)
        self._check_timer.start(30000)
        if self.config.get("cpu_monitor_enabled", True):
            print("\n[CPU] CPU监测已启用...")
            self._check_cpu()
    
    def _reset_idle_timer(self):
        interval = random.randint(900, 1800)
        self._idle_timer.stop()
        self._idle_timer.start(interval * 1000)
    
    def _on_idle_timer(self):
        if not self.is_bedtime:
            self.idle_trigger.emit()
        self._reset_idle_timer()
    
    def _on_system_check(self):
        current_time = time.time()
        now = datetime.now()
        if current_time - self._weather_cooldown > 3600:
            self._check_weather()
        if current_time - self._last_cpu_check > 10:
            self._check_cpu()
            self._last_cpu_check = current_time
        self._check_fixed_time(now)
    
    def _check_cpu(self):
        if not self.config.get("cpu_monitor_enabled", True):
            return
        if self._cpu_monitor_mode == "usage":
            self._check_cpu_usage()
        else:
            self._check_cpu_temp()
    
    def _check_cpu_temp(self):
        """检查CPU温度 - 详细记录所有传感器"""
        if self._first_temp_check:
            print("\n[CPU] ========== 开始温度监测 ==========")
            print("[CPU] 正在搜索所有可用温度传感器...")
            self._first_temp_check = False
        
        max_temp = None
        all_temps = []
        
        # 方法1: psutil - 详细记录每个传感器
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    print(f"[CPU] psutil 找到 {len(temps)} 个传感器组:")
                    for name, entries in temps.items():
                        for entry in entries:
                            label = entry.label if entry.label else "未命名"
                            temp = entry.current
                            print(f"[CPU]   - {name}/{label}: {temp}°C")
                            if temp and -50 < temp < 150:  # 合理范围
                                all_temps.append((f"{name}/{label}", temp))
                                if max_temp is None or temp > max_temp:
                                    max_temp = temp
        except Exception as e:
            print(f"[CPU] psutil 错误: {e}")
        
        # 方法2: Windows WMI (备选)
        if max_temp is None:
            print("[CPU] psutil 未找到有效温度，尝试 WMI...")
            wmi_temp = self._get_windows_cpu_temp()
            if wmi_temp:
                all_temps.append(("WMI ThermalZone", wmi_temp))
                max_temp = wmi_temp
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if max_temp is not None and all_temps:
            print(f"[CPU] 所有传感器: {', '.join([f'{n}={t:.1f}' for n,t in all_temps])}")
            
            if max_temp > 80:
                current_status, status_label = "high", "高温"
            elif max_temp < 40:
                current_status, status_label = "low", "低温"
            else:
                current_status, status_label = "normal", "正常"
            
            if self._last_temp_status is not None and self._last_temp_status != current_status:
                status_names = {'high': '高温', 'low': '低温', 'normal': '正常'}
                old_label = status_names.get(self._last_temp_status, self._last_temp_status)
                print(f"[CPU] [{timestamp}] 状态: {old_label} -> {status_label} (最高: {max_temp:.1f}°C)")
            else:
                print(f"[CPU] [{timestamp}] 最高温度: {max_temp:.1f}°C [{status_label}]")
            
            current_time = time.time()
            if max_temp > 80:
                if current_time - self._cpu_temp_high_cooldown > 300:
                    self.cpu_temp_high.emit()
                    self._cpu_temp_high_cooldown = current_time
                self._last_temp_status = current_status
            elif max_temp < 40:
                if current_time - self._cpu_temp_low_cooldown > 600:
                    self.cpu_temp_low.emit()
                    self._cpu_temp_low_cooldown = current_time
                self._last_temp_status = current_status
            else:
                self._last_temp_status = current_status
        else:
            print(f"[CPU] [{timestamp}] 无法读取温度")
            print("[CPU] 建议: 安装OpenHardwareMonitor驱动或使用使用率监测")
    
    def _check_cpu_usage(self):
        if self._first_temp_check:
            print("\n[CPU] ========== 开始使用率监测 ==========")
            print("[CPU] 使用率监测已启用 (无需管理员权限)")
            self._first_temp_check = False
        try:
            usage = psutil.cpu_percent(interval=1)
            timestamp = datetime.now().strftime("%H:%M:%S")
            if usage > 80:
                current_status, status_label = "high", "高负载"
            elif usage < 20:
                current_status, status_label = "low", "低负载"
            else:
                current_status, status_label = "normal", "正常"
            if self._last_usage_status is not None and self._last_usage_status != current_status:
                status_names = {'high': '高负载', 'low': '低负载', 'normal': '正常'}
                old_label = status_names.get(self._last_usage_status, self._last_usage_status)
                print(f"[CPU] [{timestamp}] 负载变化: {old_label} -> {status_label} ({usage:.1f}%)")
            else:
                print(f"[CPU] [{timestamp}] 使用率: {usage:.1f}% [{status_label}]")
            current_time = time.time()
            if usage > 80:
                if current_time - self._cpu_usage_high_cooldown > 300:
                    self.cpu_usage_high.emit()
                    self._cpu_usage_high_cooldown = current_time
                self._last_usage_status = current_status
            elif usage < 20:
                if current_time - self._cpu_usage_low_cooldown > 600:
                    self.cpu_usage_low.emit()
                    self._cpu_usage_low_cooldown = current_time
                self._last_usage_status = current_status
            else:
                self._last_usage_status = current_status
        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[CPU] [{timestamp}] 无法读取使用率: {e}")
    
    def _get_windows_cpu_temp(self):
        """获取Windows CPU温度 - 使用WMI"""
        import subprocess
        
        temps = []
        
        # 使用 PowerShell 获取温度
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 'Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature | ForEach-Object { $_.CurrentTemperature }'],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.isdigit():
                    temp_k = int(line)
                    temp_c = (temp_k / 10) - 273.15
                    if -50 < temp_c < 150:
                        temps.append(temp_c)
                        print(f"[CPU] WMI ThermalZone: {temp_c:.1f}°C")
        except Exception as e:
            print(f"[CPU] WMI 读取失败: {e}")
        
        return max(temps) if temps else None
    
    def _check_weather(self):
        print("\n[Weather] ========== 天气检查 ==========")
        city = self.config.get("weather_city", "")
        weather_api = self.config.get("weather_api", "wttr.in")
        print(f"[Weather] 配置城市: {city if city else '(未设置)'}")
        print(f"[Weather] API来源: {weather_api}")
        if not city:
            print("[Weather] 未设置城市，跳过天气检查")
            self._weather_cooldown = time.time()
            return
        weather_data = None
        if weather_api == "caiyun":
            api_key = self.config.get("caiyun_api_key", "").strip()
            if not api_key:
                print("[Weather] 错误: 未配置彩云天气API Key")
                self.weather_data_ready.emit("[错误] 请先在程序根目录的config.json中填写您的API！", {})
                self._weather_cooldown = time.time()
                return
            weather_data = self._fetch_caiyun_weather(city, api_key)
        else:
            weather_data = self._fetch_wttr_weather(city)
        if weather_data:
            try:
                if weather_api == "caiyun":
                    self._parse_caiyun_data(city, weather_data)
                else:
                    self._parse_wttr_data(city, weather_data)
            except Exception as e:
                print(f"[Weather] 解析数据失败: {e}")
                self._last_weather_check = "unknown"
        else:
            print("[Weather] 获取天气失败")
            if not self._last_weather_check:
                self._last_weather_check = "good"
        self._weather_cooldown = time.time()
        print("[Weather] ========== 完成 ==========\n")
    
    def _parse_caiyun_data(self, city, data):
        result = data.get('result', {})
        realtime = result.get('realtime', {})
        temperature = realtime.get('temperature', '?')
        apparent_temp = realtime.get('apparent_temperature', '?')
        humidity = realtime.get('humidity', 0)
        skycon = realtime.get('skycon', '')
        wind_speed = realtime.get('wind', {}).get('speed', '?')
        air_quality = realtime.get('air_quality', {})
        aqi_chn = air_quality.get('aqi', {}).get('chn', '?')
        pm25 = air_quality.get('pm25', '?')
        weather_zh = CAIYUN_SKYCON_MAP.get(skycon, skycon)
        if skycon in ['CLEAR_DAY', 'CLEAR_NIGHT']:
            status = 'sunny'
        elif 'RAIN' in skycon:
            status = 'rainy'
        else:
            status = 'good'
        self._last_weather_check = status
        humidity_percent = int(humidity * 100) if humidity else '?'
        print(f"[Weather] 来源: 彩云天气")
        print(f"[Weather] 城市: {city}")
        print(f"[Weather] 天气: {weather_zh}")
        print(f"[Weather] 温度: {temperature}°C (体感 {apparent_temp}°C)")
        print(f"[Weather] 湿度: {humidity_percent}%")
        weather_info = {
            'city': city, 'weather': weather_zh, 'temperature': temperature,
            'apparent_temperature': apparent_temp, 'humidity': humidity_percent,
            'wind_speed': wind_speed, 'aqi': aqi_chn, 'pm25': pm25, 'source': '彩云天气'
        }
        if status in ['sunny', 'good']:
            self.weather_good.emit()
        info_text = f"[{datetime.now().strftime('%H:%M')}] 天气: {weather_zh}, {temperature}°C"
        self.weather_data_ready.emit(info_text, weather_info)
    
    def _parse_wttr_data(self, city, data):
        current = data.get('current_condition', [{}])[0]
        temp = current.get('temp_C', '?')
        feels = current.get('FeelsLikeC', '?')
        humidity = current.get('humidity', '?')
        desc = current.get('weatherDesc', [{}])[0].get('value', '')
        weather_zh = WEATHER_MAP.get(desc.lower(), desc)
        status = 'good'
        print(f"[Weather] 来源: wttr.in")
        print(f"[Weather] 城市: {city}")
        print(f"[Weather] 天气: {weather_zh}")
        print(f"[Weather] 温度: {temp}°C")
        weather_info = {
            'city': city, 'weather': weather_zh, 'temperature': temp,
            'apparent_temperature': feels, 'humidity': humidity,
            'aqi': '-', 'pm25': '-', 'source': 'wttr.in'
        }
        if status in ['sunny', 'good']:
            self.weather_good.emit()
        info_text = f"[{datetime.now().strftime('%H:%M')}] 天气: {weather_zh}, {temp}°C"
        self.weather_data_ready.emit(info_text, weather_info)
    
    def _fetch_caiyun_weather(self, city, api_key):
        try:
            coords = CITY_COORDS.get(city)
            if not coords:
                return None
            lng, lat = coords
            url = f"https://api.caiyunapp.com/v2.6/{api_key}/{lng},{lat}/realtime"
            print(f"[Weather] 请求: 彩云天气 API")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10, context=SSL_CONTEXT) as r:
                data = json.loads(r.read().decode('utf-8'))
            if data.get('status') != 'ok':
                return None
            return data
        except Exception as e:
            print(f"[Weather] API错误: {e}")
            return None
    
    def _fetch_wttr_weather(self, city):
        try:
            url = f'http://wttr.in/{urllib.parse.quote(city)}?format=j1'
            print(f"[Weather] 请求: wttr.in")
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            print(f"[Weather] wttr.in错误: {e}")
            return None
    
    def _check_fixed_time(self, now):
        current_hour = now.hour
        current_minute = now.minute
        times = {
            'morning': self.config.get("time_morning", "08:00"),
            'noon': self.config.get("time_noon", "12:00"),
            'sunset': self.config.get("time_sunset", "18:00"),
            'night': self.config.get("time_night", "22:00"),
            'bedtime': self.config.get("time_bedtime", "23:00"),
            'wake': self.config.get("time_wake", "07:00")
        }
        if current_minute == 0 and not self.is_bedtime:
            if self._last_hour_announced != current_hour:
                self._last_hour_announced = current_hour
                self.time_announce.emit(current_hour, current_minute)
        for period, time_str in times.items():
            if self._check_time_match(current_hour, current_minute, time_str):
                attr = f"_last_{period}_triggered"
                signal = getattr(self, f"time_{period}").emit
                if getattr(self, attr) != now.day:
                    setattr(self, attr, now.day)
                    if period == 'bedtime':
                        self.is_bedtime = True
                    elif period == 'wake':
                        self.is_bedtime = False
                    signal()
    
    def _check_time_match(self, hour, minute, time_str):
        try:
            h, m = map(int, time_str.split(":"))
            return hour == h and minute == m
        except:
            return False
    
    def force_idle(self):
        self.idle_trigger.emit()
        self._reset_idle_timer()
    
    def force_check_weather(self, city=""):
        if city:
            self.config["weather_city"] = city
        self._weather_cooldown = 0
        self._check_weather()
