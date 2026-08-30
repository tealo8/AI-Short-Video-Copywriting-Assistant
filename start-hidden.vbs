' ============================================================
' AI Content Studio - one-click launcher (HIDDEN background mode)
' Double-click this file: NO console window appears; services run
' in background; all output is written to backend\logs\launcher.log.
' Browser opens automatically. (Recommended: use the .lnk shortcut;
' this VBS is a fallback where VBS scripting is allowed.)
' Stop services: kill python / node processes in Task Manager.
' ============================================================
Option Explicit

Dim Wsh, fso, baseDir, logDir, logPath, cmdLine

Set Wsh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
logDir = baseDir & "\backend\logs"
If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)
logPath = logDir & "\launcher.log"

' Silent flag propagates to the child cmd (start.bat skips pause prompts)
Wsh.Environment("PROCESS")("ACP_SILENT") = "1"

' cmd /c ""bat-path" > "log" 2>&1"   (window style 0 = hidden, no wait)
cmdLine = "cmd /c """ & baseDir & "\start.bat"" > """ & logPath & """ 2>&1"
Wsh.Run cmdLine, 0, False
