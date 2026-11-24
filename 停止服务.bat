@echo off
setlocal
title 停止 RAG 文档问答
set "PORT=7860"
set "FOUND="

for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":%PORT% " ^| findstr /I "LISTENING"') do set "FOUND=%%p"

if not defined FOUND (
    echo [信息] %PORT% 端口上没有正在运行的服务。
    timeout /t 2 >nul
    exit /b 0
)

echo 正在结束 PID %FOUND% ...
taskkill /PID %FOUND% /F >nul 2>&1
if errorlevel 1 (
    echo [失败] 结束进程失败，可能需要管理员权限。
) else (
    echo [完成] 服务已停止，%PORT% 端口已释放。
)
timeout /t 2 >nul
