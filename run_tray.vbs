Set WshShell = CreateObject("WScript.Shell")
cmd = Chr(34) & "D:\Developer\App\EXFIN_OPS\backend\venv\Scripts\python.exe" & Chr(34) & " " & Chr(34) & "D:\Developer\App\EXFIN_OPS\backend\tray_app.py" & Chr(34)
WshShell.Run cmd, 0
Set WshShell = Nothing
