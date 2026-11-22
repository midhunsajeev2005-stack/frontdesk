@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $env:FRONTDESK_LOCAL='1'; $env:FRONTDESK_DB_PASSWORD=[System.Net.NetworkCredential]::new('',(Read-Host 'Enter the frontdesk_app database password' -AsSecureString)).Password; $py='.\.venv\Scripts\python.exe'; if (!(Test-Path $py)) { $py=Read-Host 'Enter full path to your project .venv\Scripts\python.exe' }; & $py manage.py migrate; if ($LASTEXITCODE) { exit 1 }; & $py manage.py demo; if ($LASTEXITCODE) { exit 1 }; Write-Host 'Save the demo logins printed above. Open http://127.0.0.1:8000 in Chrome.'; & $py manage.py runserver 127.0.0.1:8000 --noreload"
pause
