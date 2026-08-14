# RichmackOS Changelog

## v0.7.0 — Engineering Quality and Architecture

### Engineering Metrics

RichmackOS v0.7.0 introduces a native engineering metrics subsystem for measuring repository quality, maintainability, testing, automation, complexity, technical debt, throughput, and the custom Richmack Weissman engineering-efficiency score.

New commands:

```bash
richmack metrics
richmack metrics hotspots
richmack metrics --json
```

The metrics subsystem reports source size, test coverage, Git activity, Python complexity, technical debt, maintainability, the Engineering Index, and the Richmack Weissman score.

### Quality Framework

Added a repository-wide quality gate:

```bash
make quality
```

The quality gate validates Python syntax, shell syntax, unit and regression tests, ResourceWarnings, metrics JSON, and engineering metrics generation.

### YouTube Knowledge Architecture

Refactored major YouTube Knowledge Engine components while preserving behavior through characterization and regression tests.

Major refactors include:

- keyword extraction
- research Markdown rendering
- channel index generation
- topic validation
- transcript candidate filtering
- active YouTube chat routing
- chat command handling
- chat rendering
- channel-wide execution
- single-video execution

### Active YouTube Chat

Removed the obsolete legacy `youtube_chat.py` implementation.

`youtube_chat_v2.py` is now the authoritative YouTube chat engine.

The active `chat()` function was reduced from approximately:

- cyclomatic complexity 30
- 516 lines

to approximately:

- cyclomatic complexity 13
- 185 lines

Routing and execution are now separated into independently testable components including:

- `classify_chat_route()`
- `select_chat_evidence()`
- `run_channel_question()`
- `run_video_question()`

### Engineering Quality Results

At the v0.7 release audit:

- 30 source files
- approximately 12.9K source lines
- 12 test files
- approximately 3.1K test lines
- approximately 24% test/source ratio
- 92 passing tests
- zero Python syntax errors
- average complexity approximately 3.86
- maximum complexity 13
- Engineering Index approximately 8.2/10
- Richmack Weissman approximately 8.4/10

The Richmack Weissman score is a custom RichmackOS engineering-efficiency metric and is not the fictional Weissman Score compression metric from *Silicon Valley*.

All notable RichmackOS changes are documented here.
