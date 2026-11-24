@echo off
setlocal
title RAG 文档问答 - 本地服务
cd /d "%~dp0"

set "PORT=7860"
set "URL=http://127.0.0.1:%PORT%"

rem 已经开着就直接开浏览器，不重复起进程
netstat -ano | findstr /R /C:":%PORT% " | findstr /I "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [信息] 服务已经在运行，直接打开浏览器。
    start "" "%URL%"
    timeout /t 2 >nul
    exit /b 0
)

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 找不到 .venv 虚拟环境。请在项目目录执行：
    echo        python -m venv --system-site-packages .venv
    echo        .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [错误] 缺少 .env 文件。
    echo        请把 .env.example 复制成 .env，填上 DEEPSEEK_API_KEY=sk-你的key
    echo.
    pause
    exit /b 1
)

findstr /R /C:"^DEEPSEEK_API_KEY=.." ".env" >nul 2>&1
if errorlevel 1 (
    echo [错误] .env 里的 DEEPSEEK_API_KEY 是空的，先填 key 再启动。
    echo.
    pause
    exit /b 1
)

set "PYTHONUTF8=1"
".venv\Scripts\python.exe" "demo\app.py"
set "CODE=%ERRORLEVEL%"

echo.
if "%CODE%"=="0" (
    echo [服务已停止]
) else (
    echo [服务异常退出，退出码 %CODE%，把上面的报错发给我]
)
pause
