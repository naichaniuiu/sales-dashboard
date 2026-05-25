@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ======================================
echo   中西部大区销售看板 - 一键更新
echo ======================================
echo.

cd /d "%~dp0"

REM 检查是否已有保存的Token
if exist ".github_token" (
    set /p GH_TOKEN=<.github_token
    echo [Token] 使用已保存的Token
    goto :run_update
)

echo 首次使用，请输入GitHub Personal Access Token:
echo （在 GitHub → Settings → Developer settings → Tokens 中创建）
set /p GH_TOKEN=
if "!GH_TOKEN!"=="" (
    echo [错误] Token不能为空！
    pause
    exit /b 1
)
echo !GH_TOKEN!>.github_token
echo [Token] 已保存

:run_update
git remote set-url origin https://naichaniuiu:!GH_TOKEN!@github.com/naichaniuiu/sales-dashboard.git >nul 2>&1

echo.
set PYTHON=C:\Users\wm881\.workbuddy\binaries\python\versions\3.13.12\python.exe

echo [1/6] 从Excel提取数据并计算...
%PYTHON% generate_dashboard.py
if %errorlevel% neq 0 goto error

echo.
echo [2/6] 生成看板页面...
%PYTHON% generate_html.py
if %errorlevel% neq 0 goto error

echo.
echo [3/6] 回款周期下钻数据...
%PYTHON% gen_cycle_drill.py
if %errorlevel% neq 0 goto error
%PYTHON% update_cycle_drill.py
if %errorlevel% neq 0 goto error

echo.
echo [4/6] 欠款/业绩下钻数据...
%PYTHON% gen_drill_data.py
if %errorlevel% neq 0 goto error
%PYTHON% update_drill.py
if %errorlevel% neq 0 goto error

echo.
echo [5/6] 提交到GitHub...
git add -A
git commit -m "数据更新 %date%"
git push origin master
if %errorlevel% neq 0 goto error

echo.
echo ======================================
echo   ✓ 更新完成！
echo ======================================
echo.
echo 看板地址：https://naichaniuiu.github.io/sales-dashboard/
echo 2-3分钟后刷新即可看到最新数据
echo.
pause
exit /b 0

:error
echo.
echo ======================================
echo   ✗ 更新失败！请检查上方错误信息
echo ======================================
echo.
pause
exit /b 1
