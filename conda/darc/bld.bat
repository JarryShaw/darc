@ECHO OFF

REM "%PYTHON%" -m pip install conda\wheels\* --target DARC/_extern -vv
FOR /F "Tokens=*" %A IN ('DIR /B conda\wheels\') DO @(
    "%PYTHON%" -m pip install conda\wheels\%A --target DARC\_extern -vv
)

"%PYTHON%" -m pip install . -vv

IF ERRORLEVEL 1 EXIT 1
