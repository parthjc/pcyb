ZYNTRASEC V36 // FINAL ALL-IN-ONE
============================

START
-----
1. Extract the package.
2. Run BUILD_AND_INSTALL_FINAL.bat as Administrator.
3. Complete Owner Face + Master Password registration.
4. Verify the service reaches RUNNING.
5. Reboot Windows once for a complete startup test.

ONE CONTROL CENTER
------------------
After installation run:
  C:\ProgramData\ZYNTRASEC\System\ZYNTRASEC_ALL_IN_ONE.exe

It provides:
- Owner Face Setup
- Security Console
- Advanced Control Center
- Health Check
- Diagnostics
- Integrity Check
- Encrypted Backup
- Backup Restore
- Service Repair
- Final Diagnostic Test
- Start/Restart/Stop Watchdog
- Audit log access

RECOVERY
--------
ZYNTRASEC_BACKUP.exe creates encrypted .zyntrasec backups using AES-GCM and Scrypt.
V36 backups use a V36 magic header. Legacy V34 backup files remain restorable.

INTEGRITY
---------
The watchdog checks the installed integrity baseline periodically. Integrity read or
calculation errors are treated as a failed check rather than silently passing.

SERVICE
-------
ZYNTRASECWatchdog is a real pywin32 service. The frozen executable explicitly starts the
Windows service dispatcher when launched by SCM, avoiding the previous 1053 startup
failure mode.

TESTING
-------
ZYNTRASEC_FINAL_TEST.exe writes:
  C:\ProgramData\ZYNTRASEC\System\final_test_report.json

Run ZYNTRASEC_FINAL_TEST.bat from the installed folder for a quick diagnostic pass.

LIMITATION
----------
This package cannot be runtime-tested against your Windows SCM, webcam, sleep/wake,
or Secure Boot environment from a non-Windows build environment. Test those flows on
the target Windows PC after installation.

V36.3 HOTFIX: DuplicateTokenEx pywin32 311+ argument compatibility fix.

V36.3 FIX: explicit win32security.SECURITY_ATTRIBUTES objects are passed to CreateProcessAsUser for pywin32 311+ compatibility; this addresses "The object is not a PySECURITY_ATTRIBUTES object" during monitor launch.
