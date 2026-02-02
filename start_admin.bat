@echo off
chcp 65001 >nul
echo ========================================
echo 正在以管理员权限启动 闲聊花花...
echo ========================================

:: 检查是否已经是管理员
net session >nul 2>&1
if %errorLevel% == 0 (
    echo 已是管理员权限，直接启动...
    python main.py
    pause
) else (
    echo 需要管理员权限，正在申请...
    :: 使用 PowerShell 启动管理员权限
    powershell -Command "Start-Process python -ArgumentList 'main.py' -Verb RunAs -WorkingDirectory '%~dp0'"
    echo.
    echo 请查看新弹出的窗口...
)
