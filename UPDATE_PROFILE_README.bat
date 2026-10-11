@echo off
cd /d "%~dp0"
echo ================================================
echo   ANIK2059 - Restore links and update projects
echo ================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py find_old_live_links.py --apply
  if errorlevel 1 goto :failed
  py update_readme.py
  if errorlevel 1 goto :failed
) else (
  python find_old_live_links.py --apply
  if errorlevel 1 goto :failed
  python update_readme.py
  if errorlevel 1 goto :failed
)
echo.
echo Review README.md and projects.json before pushing to GitHub.
echo See MANAGE_FEATURED_PROJECTS.md for the full instructions.
pause
exit /b 0
:failed
echo.
echo Something failed. Read the message above and see MANAGE_FEATURED_PROJECTS.md.
pause
exit /b 1
