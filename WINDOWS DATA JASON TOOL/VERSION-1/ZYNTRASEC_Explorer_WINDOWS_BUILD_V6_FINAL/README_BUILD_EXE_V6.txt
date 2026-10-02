ZYNTRASEC Explorer PRO - Windows EXE Build V6

V6 fixes the Windows "Not Responding" issue seen during a large scan.

Main fix:
- Worker thread NEVER calls Tkinter directly.
- UI updates use a thread-safe queue handled by the main Tk thread.
- Progress updates are coalesced so the GUI is not flooded.
- Removed nested update()/update_idletasks() restore logic that could stall
  Windows repaint/event handling.

Retained:
- Fast large-JSON search
- Pause / Resume / Stop
- Auto-save
- checkpoint + Resume
- USB disconnect recovery
- <database drive>\data output
- local recovery mirror
- Recovery button
- Minimize/Maximize restore protection
- Export and Preview

Build:
    build_exe_V6.bat

Final:
    dist\ZYNTRASEC_Explorer_PRO.exe

The final EXE does not require Python on the target Windows PC.

Use only with datasets you are authorized to process.
