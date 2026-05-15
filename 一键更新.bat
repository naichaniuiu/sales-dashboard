@echo off
chcp 65001 >nul
echo ======================================
echo   中西部大区销售看板 - 一键更新
echo ======================================
echo.

cd /d "%~dp0"

REM 配置GitHub认证（使用Token）
set GH_TOKEN=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
git config credential.helper store
git config credential.helper "store --file .git/credentials"
git remote set-url origin https://naichaniunu:%GH_TOKEN%@github.com/naichaniuiu/sales-dashboard.git

echo [1/5] 提取最新数据...
python extract_all_data.py
if %errorlevel% neq 0 goto error

echo.
echo [2/5] 生成销售员明细数据...
python generate_sales_detail.py
if %errorlevel% neq 0 goto error

echo.
echo [3/5] 更新看板HTML...
python generate_dashboard.py
if %errorlevel% neq 0 goto error

echo.
echo [4/5] 提交到GitHub...
git add -A
git commit -m "数据更新 %date%"
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
echo [错误] 更新失败，请检查错误信息
pause
exit /b 1
