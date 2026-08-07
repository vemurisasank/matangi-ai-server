@echo off

call venv\Scripts\activate

pip freeze > requirements_generated.txt

pause