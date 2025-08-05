@echo off
echo Creating dashboard-reborn branch...
git checkout -b dashboard-reborn
git add .
git commit -m "Dashboard reborn: Clean project with optimized metrics system"
git push -u origin dashboard-reborn
echo Done!
pause 