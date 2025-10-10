@echo off
SET "WATCH_DIR=C:\Users\poga\Desktop\wiffzack_additions\server"
SET "TARGET_FILE=.restart"

echo Watchdog active
:monitor
IF EXIST "%WATCH_DIR%\%TARGET_FILE%" (
    echo Target file found! Killing Python processes...
    taskkill /IM python.exe /F
    DEL "%WATCH_DIR%\%TARGET_FILE%"
    echo Python processes killed and target file deleted.
	echo Restarting server process
	start C:\Users\poga\Desktop\start_server.cmd
    GOTO :monitor
)
timeout /t 5 >nul
GOTO :monitor