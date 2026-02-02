# 闲聊花花 (Talking Flower)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

一个灵感来自《超级马里奥兄弟：惊奇》中"闲聊花花"的桌面宠物程序。

## 功能特性

- 语音互动：点击花朵会随机播放语音
- 天气播报：支持彩云天气和 wttr.in 双API
- CPU监测：温度监测（需管理员）或使用率监测
- 定时提醒：早上、中午、夕阳、夜晚等时段提醒
- 彩蛋台词：双击或三击触发特殊语音
- 天气弹窗：每半小时显示美观的天气提示

## 安装

### 环境要求
- Python 3.10 或更高版本
- Windows 系统（部分功能需要管理员权限）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 准备音频文件

1. 在 `Assets/Audio/Index/` 目录下放置音频文件（.wav 格式）
2. 参考 `Assets/Library/` 下的 JSON 文件配置语音触发条件

### 配置文件

1. 复制 `config.example.json` 为 `config.json`
2. 按需修改配置：
   - `weather_city`: 设置城市名称
   - `caiyun_api_key`: 彩云天气 API Key（可选）
   - `cpu_monitor_mode`: `usage`（推荐）或 `temp`

## 使用

### 普通启动

```bash
python main.py
```

### 管理员启动（完整功能）

双击 `start_admin.bat` 或以管理员身份运行：

```powershell
# PowerShell 管理员
python main.py
```

### 交互操作

| 操作 | 功能 |
|------|------|
| 单击 | 触发随机语音互动 |
| 双击/三击 | 触发彩蛋台词 |
| 拖拽 | 移动花朵位置 |
| 右键 | 打开设置菜单 |

## 配置说明

### 天气 API 选择

- **wttr.in**（默认）：免费，无需配置，但可能不稳定
- **彩云天气**：需要申请 API Key，数据更准确
  - 申请地址：https://www.caiyunapp.com/

### CPU 监测模式

- **使用率监测**（推荐）：无需管理员权限，准确反映 CPU 负载
- **温度监测**：需要管理员权限，Windows 上可能读取不到正确温度

### 定时提醒

在 `config.json` 中设置：
- `time_morning`: 早上提醒时间
- `time_noon`: 中午提醒时间
- `time_sunset`: 夕阳提醒时间
- `time_night`: 夜晚提醒时间
- `time_bedtime`: 就寝时间（自动静音）
- `time_wake`: 起床时间（自动取消静音）

## 项目结构

```
TalkingFlower/
├── main.py                 # 主程序入口
├── flower.py              # 主窗体UI
├── event_watcher.py       # 事件监视器（天气、CPU、定时）
├── audio_manager.py       # 音频管理
├── animation_player.py    # 动画播放器
├── uac_helper.py         # UAC权限助手
├── requirements.txt      # 依赖列表
├── config.json           # 用户配置文件（不上传Git）
├── config.example.json   # 配置示例
├── Assets/
│   ├── Audio/Index/      # 音频文件
│   ├── Library/          # JSON配置文件
│   └── Visual/           # 图片资源
└── README.md
```

## 注意事项

1. **音频文件**：需要将 `.wav` 文件放在 `Assets/Audio/Index/` 目录
2. **管理员权限**：温度监测和开机自启需要管理员权限
3. **API Key**：彩云天气需要自行申请免费 API Key

## License

MIT License
