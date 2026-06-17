@echo off
cd /d "%~dp0"
title 百度文章备份工具

echo ============================================
echo   百度文章批量备份工具 - 一键启动版
echo   工作目录: %cd%
echo ============================================
echo.
echo  [1] 启动抓取 - Chrome版
echo  [2] 启动抓取 - Edge版_Profile2
echo  [3] CSV 转 Markdown
echo  [4] CSV 转 TXT
echo  [5] 打开输出目录
echo  [0] 退出
echo.

set /p choice=请选择操作 (0-5): 

if "%choice%"=="1" goto crawl
if "%choice%"=="2" goto crawl_edge
if "%choice%"=="3" goto md
if "%choice%"=="4" goto txt
if "%choice%"=="5" goto open
if "%choice%"=="0" goto end
echo 无效选择
pause
goto end

:crawl
echo.
echo 启动Chrome抓取...
echo 浏览器打开后请登录百度，进入文章列表后按回车
pause
"C:\Users\zhang\.workbuddy\binaries\python\envs\baidu-backup\Scripts\python.exe" BaiduExporter.py
goto ask

:crawl_edge
echo.
echo ========================================
echo   启动Edge版抓取
echo ========================================
echo.
echo 重要提示:
echo 1. 请关闭所有 Edge 浏览器窗口
echo 2. 脚本将使用 Profile 2 的登录状态
echo 3. Edge 浏览器会自动打开
echo.
pause
echo 正在启动 Edge 浏览器...
"C:\Users\zhang\.workbuddy\binaries\python\envs\baidu-backup\Scripts\python.exe" BaiduExporter_Edge.py
if errorlevel 1 (
    echo.
    echo ========================================
    echo   脚本异常退出！请截图上方错误信息
    echo ========================================
    pause
)
goto ask

:md
echo.
echo CSV转Markdown...
"C:\Users\zhang\.workbuddy\binaries\python\envs\baidu-backup\Scripts\python.exe" csv_to_md.py
echo 文件已生成到 md_output 目录
pause
goto end

:txt
echo.
echo CSV转TXT...
"C:\Users\zhang\.workbuddy\binaries\python\envs\baidu-backup\Scripts\python.exe" csv_to_txt.py
echo 文件已生成到 txt_output 目录
pause
goto end

:open
start "" "md_output"
start "" "txt_output"
echo 已打开输出目录
pause
goto end

:ask
set /p a=转换为Markdown？(y/n): 
if /i "%a%"=="y" goto md
set /p b=转换为TXT？(y/n): 
if /i "%b%"=="y" goto txt

:end
echo 完成！
pause
