ZYNTRASEC UNIVERSAL HTML ENGINE — AUTO + MANUAL
1. Extract ZIP.
2. Run RUN_ZYNTRASEC_UNIVERSAL_HTML_ENGINE_AUTO_MANUAL.bat.
3. Select SOURCE HTML FILE (.html/.htm) and OUTPUT FOLDER.
AUTO: BUILD INDEX + OPEN VIEWER runs indexing, shows count, then opens the indexed viewer.
MANUAL: Open Original HTML, Build/Rebuild Index, Open Indexed Viewer buttons are separate.
Do not select .sqlite in SOURCE HTML FILE.
Requires Python 3. Uses built-in sqlite3; no separate SQLite download or third-party package.
Original HTML is not modified.
Limitations: indexing supports standard HTML tables and chooses the largest top-level table. JavaScript/div-based report layouts may need specialized extraction. Verify indexed row count against source report.
