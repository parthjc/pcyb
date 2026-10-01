ZYNTRASEC FINAL - ONE STABLE RELEASE + GUIDED SETUP
================================================

INSTALL FLOW
- Run BUILD_AND_INSTALL_FINAL.bat as Administrator.
- The installer creates a backup before changing the existing installation.
- The service is registered in DEMAND mode during setup so the lock screen cannot start before owner registration. After setup it runs the real Python watchdog service, which launches/restarts the per-user event monitor and performs periodic integrity checks.
- FIRST_RUN_SETUP.bat then guides the user through all required steps.

GUIDED STEPS
1. Component check.
2. Secure first-run mode: old ZYNTRASEC processes/tasks are stopped.
3. Owner Face + Master Password registration:
   - create emergency master password
   - Windows Camera opens automatically
   - LOOK LEFT / LOOK RIGHT / LOOK CENTER guided live captures
   - five live samples are registered
4. Security settings and SHA-256 integrity baseline are created.
5. Protected Windows startup is enabled:
   - ZYNTRASECWatchdog AUTO_START service
   - Boot Service Recovery task
   - Logon Service Recovery task
   - User Event Monitor logon task
6. Final verification and reboot-test instructions.

PRIMARY STARTUP
- Windows Service: ZYNTRASECWatchdog (AUTO_START) — real Python/pywin32 watchdog
- Service recovery: restart on failure

BACKUP STARTUP
- ZYNTRASEC Logon Service Recovery (ONLOGON) can verify the service path without racing service startup
- User Event Monitor runs once per interactive logon
- No Task Manager Startup Apps dependency

DUPLICATE PROTECTION
- Event Monitor uses a named Windows mutex.
- Installer removes legacy ZYNTRASEC scheduled tasks and Run entries.
- Only one User Event Monitor task is registered.

SECURITY / FACE
- V32 stable backup is preserved in BACKUP_V32.
- Live-video/passive-liveness authentication remains in the supplied baseline.

BACKUP / RECOVERY
- Existing ProgramData installation is backed up before replacement.
- Security data is preserved.
- UNINSTALL_ZYNTRASEC_FINAL.bat performs cleanup while preserving backup folders.

IMPORTANT
This is application-level protection. A Windows administrator can ultimately disable or remove software. For stronger platform security, use BitLocker, Secure Boot, and a standard daily user account.


FIXED PACKAGE NOTE
The guided setup uses PowerShell Scheduled Task LogonType=Interactive for the per-user ZYNTRASEC Event Monitor. This is the valid enum on the target Windows PowerShell ScheduledTasks cmdlets.


CLEAN INSTALL BEHAVIOR
START_HERE.bat and BUILD_AND_INSTALL_FINAL.bat first remove the existing installed ZYNTRASEC service, scheduled tasks, startup entries, processes, and C:\ProgramData\ZYNTRASEC, then perform a fresh install. The V32 backup bundled inside this ZIP is preserved.


FINAL SERVICE STABILITY FIX:
- ZYNTRASECWatchdog is the actual pywin32 watchdog service. It stays in Session 0, checks integrity, detects the active console session, and launches the user-session monitor with CreateProcessAsUser.
- AUTO_START is the primary boot mechanism.
- The previous ONSTART sc-start recovery task is intentionally not created because it can race SCM and produce START_PENDING/restart behavior.
- The interactive Event Monitor remains per-user and protected by a Global named mutex.
