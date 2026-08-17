@echo off
title CineVault OS v2.0 Shutdown
cls
call "%~dp0infra\scripts\stop.bat" %*
