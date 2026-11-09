# SP12 Phase 1 code-path regression checks — 2026-11-09

The following isolated regression suites passed in the current session:

| Area | Result | Raw log |
| --- | --- | --- |
| Boot synchronization and recovery paths | 16 passed | `output/phase1/phase1-boot-sync-unit-20261109.log` (SHA-256 `01a1d82782791ba27cec8bde6bfd6be1569f8ad8b535c49a128ddc4df4d84a47`) |
| Fallback kernel selection | 4 passed | `output/phase1/phase1-fallback-selection-unit-20261109.log` (SHA-256 `2a6f3ffb7a9826b94e1b6f8ee5ac782247c7188cb6ef2feea78eeb9c187f4c13`) |
| Fallback installer | 6 passed | `output/phase1/phase1-fallback-installer-unit-20261109.log` (SHA-256 `9a56630e4022dda11486d829f3a7c291e27a49532bad0678947306bc7b5f2fb4`) |
| Boot-sync installer | 3 passed | `output/phase1/phase1-boot-sync-installer-unit-20261109.log` (SHA-256 `78e7c57839a2966f3380719fde15097f006d6570dc2e1e010135c10a4f830d92`) |

These suites use temporary fixtures and mocked host tools. They check recovery
and rollback logic, fallback selection, and installer behavior without
touching the SP12 root filesystem or ESP. They do not verify the live recovery
snapshot, a real package install/removal, a firmware boot, or recovery on
physical hardware. Those Phase 1 gates remain open.
