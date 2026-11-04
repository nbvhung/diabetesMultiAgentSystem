@echo off
setlocal
cd /d "%~dp0"
python scripts\local_neo4j.py start
if errorlevel 1 (
    echo.
    echo Neo4j could not start. Review the error above.
    pause
    exit /b 1
)
echo.
echo Neo4j Browser: http://127.0.0.1:7474/browser/
echo Username: neo4j
echo Password: read NEO4J_PASSWORD in your project .env file.
echo You can close this window after Neo4j has started.
pause
