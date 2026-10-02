ZYNTRASEC WINDOWS CONTROL CENTER
FINAL PARTITION SAFETY BUILD

What is fixed:
- INT64/uint64-safe disk size calculations.
- Real unallocated-space calculation from partition extents.
- Equal Split uses the existing data volume plus genuinely usable unallocated space.
- Equal Split is blocked when the existing data volume is not the last partition, avoiding unsafe assumptions about free space trapped before Recovery/other partitions.
- EFI/System/Recovery partitions are not selected for automatic resize.
- Live disk state is re-read immediately before resize/create.
- Storage cache is refreshed after resize.
- Final disk state is verified after automatic partition creation.
- Launcher automatically requests Administrator permission.
- Launcher checks that Python is available.

Important:
- Partition changes are real disk changes. Back up important data first.
- The tool does NOT delete or format existing partitions in Equal Split.
- If Windows cannot shrink the source volume, the operation stops without creating new partitions.
- Equal Split supports one existing data volume plus unallocated space, with the data volume as the last partition on the disk.

Start:
START_ZYNTRASEC.bat

Verification:
Run VERIFY_PARTITION_FIX.ps1 as Administrator.


PARTITION EQUAL-SPLIT SAFETY UPDATE
The equal-split planner uses only the contiguous unallocated extent immediately after the selected data volume. A Recovery/MSR/EFI partition after the data volume is allowed and remains untouched. Free space elsewhere on the disk is not counted.

FINAL6 CHANGE: background partition detection no longer uses the global operation lock. Disk refresh runs independently and cannot block other ZYNTRASEC tasks.

FINAL20 SECURITY CENTER UPDATE:
- Memory Integrity detection now uses both the HVCI registry state and Windows Device Guard status.
- Security status checks run in the background so the UI stays responsive.
- Output now separates SCAN STATUS from install/change actions.
- Project-only Defender exclusion controls require Administrator and do not disable Defender globally.


EXE BUILD:
Run BUILD_EXE.bat. It builds a windowed (no console window) EXE in dist\ZYNTRASEC_WINDOWS_CONTROL_CENTER\.
