@echo off
setlocal enabledelayedexpansion

:: Ensure conda is initialized
call "%USERPROFILE%\anaconda3\Scripts\conda.exe" init

:: Initialize conda for batch script
call "%USERPROFILE%\anaconda3\Scripts\activate.bat"

:: Set environment name and Python version
set ENV_NAME=trolltweets
set PYTHON_VERSION=3.12.3

:: Check if environment exists and remove it if it does
conda env list | find "%ENV_NAME%" > nul
if not errorlevel 1 (
    echo Environment %ENV_NAME% exists. Removing...
    call conda env remove --name %ENV_NAME% -y
)

:: Create initial environment.yml with core dependencies
(
echo name: %ENV_NAME%
echo channels:
echo   - conda-forge
echo   - defaults
echo dependencies:
echo   - python=%PYTHON_VERSION%
echo   - pandas
echo   - pip
echo   - pip:
echo     - stdlib_list
) > environment.yml

:: Create and activate conda environment from yml
echo Creating conda environment with Python %PYTHON_VERSION%...
call conda env create -f environment.yml
call conda activate %ENV_NAME%

:: Create the Python import scanner script
(
echo import sys
echo import pkg_resources
echo from stdlib_list import stdlib_list
echo.
echo stdlib = stdlib_list("3.12"^)
echo.
echo imports = set(^)
echo for line in sys.stdin:
echo     line = line.strip(^)
echo     if not line:  # Skip empty lines
echo         continue
echo     try:
echo         if line.startswith('import'^):
echo             parts = line.split(^)
echo             if len(parts^) ^>= 2:
echo                 package = parts[1].split('.'^)[0]
echo                 imports.add(package^)
echo         elif line.startswith('from'^):
echo             parts = line.split(^)
echo             if len(parts^) ^>= 2:
echo                 package = parts[1].split('.'^)[0]
echo                 imports.add(package^)
echo     except IndexError:
echo         continue  # Skip malformed lines
echo.
echo imports = {pkg for pkg in imports if pkg not in stdlib}
echo imports = {pkg for pkg in imports if pkg not in ['sys', 'pkg_resources', 'stdlib_list']}
echo.
echo with open('environment.yml', 'a', encoding='utf-8'^) as f:
echo     for pkg in sorted(imports^):
echo         f.write(f"    - {pkg}\n"^)
) > scan_imports.py

:: Scan all Python files for imports
echo Scanning Python files for imports...
for /r %%i in (*.py) do (
    echo Processing: %%i
    type "%%i" | findstr /i /r "^import .* ^from .* import" | python scan_imports.py
)

:: Clean up temporary files
del scan_imports.py

:: Export final environment
conda env export > environment.yml

echo Setup complete! Environment created and packages installed.
echo To activate the environment, use: conda activate %ENV_NAME%
echo To recreate this environment elsewhere, use: conda env create -f environment.yml

endlocal 