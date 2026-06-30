@echo off
:: 设置字符编码为UTF-8，防止乱码
chcp 65009 >nul

:: 1. 将 "D:\MiyX\CodeProject\八字" 替换为你项目的实际绝对路径
cd /d "D:\MiyX\CodeProject\八字"

echo 正在拉取项目最新代码...
echo ================================================

:: 2. 执行 git pull
git pull

echo ================================================
echo 更新完成！
pause
