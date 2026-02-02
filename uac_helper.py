# -*- coding: utf-8 -*-
"""
UAC 权限助手 - 处理Windows管理员权限申请
"""
import sys
import os
import ctypes
import subprocess
import tempfile


def is_admin():
    """检查当前是否有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin(executable=None, args=None, wait=True):
    """
    以管理员权限重新运行程序
    
    Args:
        executable: 要运行的程序路径，默认为当前Python解释器
        args: 参数列表
        wait: 是否等待程序结束
    
    Returns:
        是否成功启动
    """
    if executable is None:
        executable = sys.executable
    
    if args is None:
        args = sys.argv
    
    # 构建命令行
    if isinstance(args, list):
        cmd_line = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in args)
    else:
        cmd_line = args
    
    try:
        # 使用 ShellExecute 以管理员权限运行
        if wait:
            # 使用 subprocess 等待完成
            proc = subprocess.Popen(
                cmd_line,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return proc
        else:
            # 使用 ShellExecute 显示UAC提示
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                executable,
                cmd_line,
                None,
                1  # SW_SHOWNORMAL
            )
            return True
    except Exception as e:
        print(f"[UAC] 申请权限失败: {e}")
        return False


def restart_as_admin(wait=False):
    """
    以管理员权限重新启动当前程序
    
    Args:
        wait: 是否等待新程序启动完成
    
    Returns:
        是否成功重启
    """
    if is_admin():
        print("[UAC] 已经是管理员权限，无需重启")
        return True
    
    print("[UAC] 正在申请管理员权限...")
    
    # 获取当前脚本路径（绝对路径）
    script_path = os.path.abspath(sys.argv[0])
    
    # 获取当前工作目录
    work_dir = os.getcwd()
    
    # 构建参数
    if script_path.endswith('.py'):
        # Python脚本: python.exe script.py [args...]
        executable = sys.executable
        # 参数是脚本路径 + 原始参数
        args = f'"{script_path}"'
        if len(sys.argv) > 1:
            args += ' ' + ' '.join(f'"{arg}"' for arg in sys.argv[1:])
    else:
        # 可执行文件
        executable = script_path
        args = ' '.join(f'"{arg}"' for arg in sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    print(f"[UAC] 启动: {executable}")
    print(f"[UAC] 参数: {args}")
    print(f"[UAC] 工作目录: {work_dir}")
    
    try:
        # 使用 ShellExecute 以管理员权限运行
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,           # hwnd
            "runas",        # lpOperation
            executable,     # lpFile
            args,           # lpParameters
            work_dir,       # lpDirectory (工作目录)
            1               # nShowCmd (SW_SHOWNORMAL)
        )
        
        # 检查返回值
        if ret > 32:  # 成功
            print("[UAC] 已启动管理员权限程序，本程序即将退出...")
            return True
        else:
            print(f"[UAC] ShellExecute 失败，返回值: {ret}")
            return False
            
    except Exception as e:
        print(f"[UAC] 重启失败: {e}")
        return False


def create_elevated_script(script_content, wait=True):
    """
    创建一个临时VBS脚本来申请管理员权限
    用于一些特殊情况
    """
    try:
        # 创建临时VBS脚本
        fd, vbs_path = tempfile.mkstemp(suffix='.vbs')
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        
        # 运行VBS脚本
        if wait:
            subprocess.run(['cscript', '//nologo', vbs_path], check=True)
        else:
            subprocess.Popen(['cscript', '//nologo', vbs_path])
        
        # 清理临时文件
        os.unlink(vbs_path)
        return True
        
    except Exception as e:
        print(f"[UAC] 创建提权脚本失败: {e}")
        return False


def check_and_request_admin(config=None):
    """
    检查配置并根据需要申请管理员权限
    
    Args:
        config: 配置字典，包含 cpu_temp_enabled 和 cpu_temp_mode
    
    Returns:
        是否继续运行（False表示已重启，原程序应退出）
    """
    if config is None:
        config = {}
    
    # 检查是否已配置为需要管理员
    cpu_enabled = config.get("enable_cpu_temp", True)
    cpu_mode = config.get("cpu_temp_mode", "admin")
    
    if not cpu_enabled:
        print("[UAC] CPU温度检测已禁用，无需管理员权限")
        return True
    
    if cpu_mode != "admin":
        print("[UAC] CPU温度模式为LHM，无需管理员权限")
        return True
    
    # 检查当前权限
    if is_admin():
        print("[UAC] 已获得管理员权限")
        return True
    
    # 需要申请管理员权限
    print("[UAC] 配置需要管理员权限(WMI模式)，正在申请...")
    
    if restart_as_admin(wait=False):
        # 重启成功，当前程序应退出
        return False
    else:
        print("[UAC] 申请权限失败，将继续以普通权限运行")
        print("[UAC] 提示: CPU温度检测可能无法正常工作")
        return True


if __name__ == "__main__":
    # 测试
    print(f"当前管理员状态: {is_admin()}")
    
    if not is_admin():
        print("尝试申请管理员权限...")
        restart_as_admin()
    else:
        print("已获得管理员权限")
        input("按回车键继续...")
