@set FILE=".\error\%DATE%.log"

@if not exist "error" mkdir "error"

@echo ################################ >> %FILE%
@echo.##   %DATE% %TIME%   ## >> %FILE%
@echo.################################ >> %FILE%
@echo. >> %FILE%

python ".\start.py" 2>> %FILE%
@echo. >> %FILE%
@echo. >> %FILE%

@pause