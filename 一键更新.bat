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

echo 首次使用，请输入您的GitHub Personal Access Token（以ghp_开头）:
set /p GH_TOKEN=
if "!GH_TOKEN!"=="" (
    echo [错误] Token不能为空！
    pause
    exit /b 1
)
echo !GH_TOKEN!>.github_token
echo [Token] 已保存，下次运行无需再输入

:run_update
git remote set-url origin https://naichaniuiu:!GH_TOKEN!@github.com/naichaniuiu/sales-dashboard.git

echo.
set PYTHON=C:\Users\wm881\.workbuddy\binaries\python\versions\3.13.12\python.exe

echo [1/6] 提取最新数据...
%PYTHON% extract_all_data.py
if %errorlevel% neq 0 goto error

echo.
echo [2/6] 生成销售员明细数据...
%PYTHON% generate_sales_detail.py
if %errorlevel% neq 0 goto error

echo.
echo [3/6] 更新JSON数据...
%PYTHON% update_final_json.py
if %errorlevel% neq 0 goto error

echo.
echo [4/6] 生成看板HTML...
%PYTHON% generate_html.py
if %errorlevel% neq 0 goto error

echo.
echo [5/6] 生成回款周期下钻数据...
%PYTHON% gen_cycle_drill.py
if %errorlevel% neq 0 goto error

echo.
echo [6/6] 注入回款周期下钻到HTML...
%PYTHON% update_cycle_drill.py
if %errorlevel% neq 0 goto error

echo.
echo [推送] 提交到GitHub...
git add -A
git commit -m "数据更新 %date% %time:~0,5%"
git push origin master
if %errorlevel% neq 0 goto error

echo.
echo ======================================
echo   更新完成！
echo ======================================
echo.
echo 看板地址：https://naichaniuiu.github.io/sales-dashboard/
echo 部署需要2-3分钟，请稍后刷新页面
echo.
pause
exit /b 0

:error
echo.
echo [错误] 更新失败，请检查上方错误信息
echo.
pause
exit /b 1
