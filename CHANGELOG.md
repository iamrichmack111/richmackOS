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

## v0.6.0 latest-video consistency fix
- Use transcript `UPLOAD_DATE` instead of filesystem mtime when `youtube knowledge build --limit N` chooses newest videos.
- Make `youtube summarize` prefer the structured knowledge index so it summarizes the same canonical video set/order as the knowledge engine.
- Make YouTube evidence chat use upload-date ordering when limiting channel transcripts.
- Add regression tests for stale/incorrect filesystem mtimes versus actual YouTube upload dates.
- Include the root `richmack` launcher in the release archive.

- Added YouTube summarize --pager support (auto/bat/less) with TTY-safe behavior.
