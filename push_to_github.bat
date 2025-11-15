@echo off
REM Batch file to push code to GitHub
REM This will run the PowerShell script

echo =========================================
echo Push to GitHub - Uncertainty-Aware SLAM
echo =========================================
echo.

REM Change to the workspace directory
cd /d "%~dp0"

REM Run PowerShell script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0push_to_github.ps1"

pause

