@echo off
title CineVault OS v2.0 Launcher
cls
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0start-dev.ps1" %*
