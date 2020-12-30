@echo off
REM --------------------------------------------------------
REM Print interface MAC address in CSV format
REM 
REM MAARK1/MAARK2 use this information to validate a host is reaching Splunk Cloud
REM --------------------------------------------------------
getmac.exe /FO:CSV /V