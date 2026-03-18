@echo off

echo Deadlock Intel Toolkit

echo Creating rollback snapshot...
powershell -ExecutionPolicy Bypass -File scripts\create_rollback_snapshot.ps1
if errorlevel 1 (
	echo Snapshot creation failed. Aborting to protect rollback safety.
	pause
	exit /b 1
)

python -m venv venv
call venv\Scripts\activate

pip install -r requirements.txt

python src/main.py all

pause
