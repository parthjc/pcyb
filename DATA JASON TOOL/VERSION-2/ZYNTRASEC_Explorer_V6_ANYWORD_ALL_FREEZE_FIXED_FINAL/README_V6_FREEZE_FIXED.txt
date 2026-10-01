ZYNTRASEC Explorer V6 FREEZE FIXED

Base:
- Original V6 ANYWORD/ALL version.

Requested V6 features retained unchanged:
- Match: Any word / number
- Max results: 0 = ALL

ONLY additional change:
- GUI freeze / Not Responding mitigation.
- Database/USB session initialization moved off the Tk main thread.
- Worker UI callbacks routed through a thread-safe queue.
- Browse no longer creates folders on the database drive from the UI thread.
- Lightweight minimize/restore repaint handling.

Build:
    build_exe_V6_FREEZE_FIXED.bat

Final:
    dist\ZYNTRASEC_Explorer_PRO.exe

No other requested search behavior was intentionally changed.
