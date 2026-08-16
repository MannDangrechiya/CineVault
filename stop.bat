@echo off
title CineVault OS v2.0 Shutdown
cls
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\stop-dev.ps1" %*
