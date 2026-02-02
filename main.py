# -*- coding: utf-8 -*-
"""
闲聊花花 - 马里奥惊奇风格桌宠程序
"""
import sys
import os
import json

# 设置高DPI支持
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"

# 检查是否需要管理员权限（在导入Qt前检查，以便重启）
def check_admin_on_startup():
    """启动时检查权限配置"""
    # 首先检查当前是否已经是管理员
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            print("[Startup] 当前已是管理员权限")
            return  # 已经是管理员，无需申请
    except:
        pass
    
    # 不是管理员，检查配置是否需要管理员
    try:
        config = {}
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        
        cpu_enabled = config.get("enable_cpu_temp", True)
        cpu_mode = config.get("cpu_temp_mode", "admin")
        
        if cpu_enabled and cpu_mode == "admin":
            print("[Startup] 配置需要管理员权限(WMI模式)，正在申请...")
            print("[Startup] 将显示UAC提示，请点击'是'同意")
            
            from uac_helper import restart_as_admin
            if restart_as_admin(wait=False):
                print("[Startup] 已启动管理员权限程序，本程序退出")
                sys.exit(0)
            else:
                print("[Startup] 申请权限失败，将继续以普通权限运行")
                print("[Startup] CPU温度检测可能无法正常工作")
    except Exception as e:
        print(f"[Startup] 权限检查失败: {e}")

# 在导入Qt前执行权限检查
check_admin_on_startup()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from flower import FlowerWidget


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 设置应用属性
    app.setApplicationName("TalkingFlower")
    app.setApplicationDisplayName("闲聊花花")
    
    # 检查当前权限状态并输出
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if is_admin:
            print("[Startup] 当前以管理员权限运行")
        else:
            print("[Startup] 当前以普通权限运行")
    except:
        pass
    
    # 创建花体窗体
    flower = FlowerWidget()
    flower.show()
    
    print("=" * 50)
    print("[TalkingFlower] 已启动！")
    print("=" * 50)
    print("功能说明:")
    print("  - 单击：触发互动对话")
    print("  - 双击/三连击：彩蛋台词")
    print("  - 拖拽：移动位置")
    print("  - 右键：打开菜单")
    print("=" * 50)
    
    # 运行应用
    exit_code = app.exec()
    print(f"[TalkingFlower] 已退出，代码: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
