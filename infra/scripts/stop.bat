@echo off
title CineVault OS v2.0 Shutdown
cls
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0stop-dev.ps1" %*
