@echo off
REM --------------------------------------------------------
REM Print the audit policy in CSV format
REM 
REM This will enable Splunk to validate required auditing
REM is enabled
REM --------------------------------------------------------
auditpol.exe /get /category:* /r