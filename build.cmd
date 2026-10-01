@echo off
setlocal
cd /d "%~dp0"

set BLENDER="C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
set EXT_ID=RayCarve
set OLD_EXT_ID=RayFacet
set REPO=user_default

rem --- A running Blender keeps the old code in memory: warn before installing ---
tasklist /fi "imagename eq blender.exe" 2>nul | find /i "blender.exe" >nul
if not errorlevel 1 (
    echo.
    echo WARNING: Blender is running. Close it now for a clean refresh,
    echo          or press a key to continue and restart Blender afterwards.
    pause
)

rem --- Read version from manifest ---
for /f "tokens=2 delims==" %%v in ('findstr /b "version" blender_manifest.toml') do set VERSION=%%v
set VERSION=%VERSION:"=%
set VERSION=%VERSION: =%
set OUTFILE=dist\%EXT_ID%-%VERSION%.zip
echo Building %EXT_ID% %VERSION%

rem --- Clean local caches and old build of the same version ---
for /d /r %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"
if not exist dist mkdir dist
if exist "%OUTFILE%" del /q "%OUTFILE%"

rem --- Build ---
%BLENDER% --factory-startup --command extension build --output-filepath "%OUTFILE%"
if errorlevel 1 goto :fail

rem --- Publish zip + manuals to the website folder (GitHub Pages) ---
if not exist website goto :skipsite
if not exist website\downloads mkdir website\downloads
copy /y "%OUTFILE%" website\downloads\ >nul
if not exist website\manual\%VERSION% mkdir website\manual\%VERSION%
copy /y MANUAL.md website\manual\%VERSION%\en.md >nul
if exist MANUAL.de.md copy /y MANUAL.de.md website\manual\%VERSION%\de.md >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f='website\versions.json'; $v='%VERSION%'; $j=Get-Content -Raw -Encoding UTF8 $f | ConvertFrom-Json; $j.versions=@(@($j.versions) + $v | Select-Object -Unique | Sort-Object { [version]$_ } -Descending); $j.latest=$j.versions[0]; [IO.File]::WriteAllText((Resolve-Path $f), ($j | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding $false))"
if errorlevel 1 echo WARNING: could not update website\versions.json
echo Website updated: downloads, manual %VERSION%, versions.json
:skipsite

rem --- Remove old install completely (removes stale files and old __pycache__) ---
%BLENDER% --factory-startup --command extension remove %REPO%.%EXT_ID% >nul 2>&1
set EXT_DIR=%APPDATA%\Blender Foundation\Blender\5.1\extensions\%REPO%\%EXT_ID%
if exist "%EXT_DIR%" rd /s /q "%EXT_DIR%"

rem --- Remove the old RayFacet install: both would register the same classes ---
%BLENDER% --factory-startup --command extension remove %REPO%.%OLD_EXT_ID% >nul 2>&1
set OLD_EXT_DIR=%APPDATA%\Blender Foundation\Blender\5.1\extensions\%REPO%\%OLD_EXT_ID%
if exist "%OLD_EXT_DIR%" rd /s /q "%OLD_EXT_DIR%"

rem --- Install and enable ---
%BLENDER% --factory-startup --command extension install-file -r %REPO% -e "%OUTFILE%"
if errorlevel 1 goto :fail

echo.
echo Installed %EXT_ID% %VERSION%. Start Blender (or restart it) to use the new version.
pause
exit /b 0

:fail
echo.
echo BUILD/INSTALL FAILED - see messages above.
pause
exit /b 1
