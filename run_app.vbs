Set WshShell = CreateObject("WScript.Shell")
' Run the app asynchronously (False) and hide the window completely (0)
WshShell.Run "cmd /c ""cd /d """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & """ & call venv311\Scripts\activate & start """" pythonw app.py""", 0, False
