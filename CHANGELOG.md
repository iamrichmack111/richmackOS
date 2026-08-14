# RichmackOS Changelog

## v0.6.0 — Integration and hardening release

- Unified user-facing and build version numbers at 0.6.0.
- Added `richmack version` and expanded main help for YouTube, watcher and organizer subsystems.
- Hardened malformed CLI argument handling and skill-name validation.
- Prevented home scans from indexing `~/.richmackos` and other sensitive/runtime directories.
- Removed stale indexed file records after rescans.
- Made the user watcher service portable with `%h` instead of a hard-coded username.
- Routed `richmack youtube research` and `resources` to the research engine.
- Added `install.sh` for user-local installation.
- Added the missing ARM64 qcow2 base-image creation script.
- Added smoke tests and a `make test` target.
