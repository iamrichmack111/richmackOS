# RichmackOS

RichmackOS is a lightweight, terminal-first personal computing assistant for Linux.

It keeps deterministic system work local and delegates expensive AI work to the Ollama service running on:

http://richmack.local:11434

The Debian server handles indexing, search, project discovery, memory, RAG retrieval, duplicate detection, documentation, skills, and system inspection.

The Richmack workstation handles:

- LLM inference
- embeddings
- semantic reasoning
- AI-generated summaries and documentation

## Architecture

Debian Server
|
+-- RichmackOS
|   |
|   +-- File index
|   +-- SQLite metadata
|   +-- Project catalog
|   +-- Memory
|   +-- Skills
|   +-- Plugins
|   +-- Duplicate detection
|   +-- RAG retrieval
|   +-- Documentation tools
|
+------ LAN ------> richmack.local:11434
                    |
                    +-- Ollama
                    +-- Granite
                    +-- Nomic embeddings
                    +-- Other configured models

## Main Command

richmack

Display help:

richmack help

## System Status

richmack status

Shortcut:

richmacksys

Shows:

- hostname
- uptime
- RAM usage
- disk usage
- indexed file count
- indexed project count
- memory count
- AI server state
- model count
- RAG availability

## Diagnostics

richmack doctor

Checks:

- python3
- git
- curl
- richmackai
- richmackrag
- connectivity to richmack.local

## Scan Files

Scan your home directory:

richmack scan ~

Shortcut:

richmackindex ~

Scan a specific folder:

richmack scan ~/Projects

The index is stored in:

~/.richmackos/richmackos.db

The scanner records:

- path
- filename
- extension
- size
- modification time
- category
- project information

Common categories include:

- document
- text
- spreadsheet
- data
- config
- python
- shell
- javascript
- typescript
- web
- archive
- audio
- video
- image
- disk-image
- other

## Search

Search indexed paths and filenames:

richmack search kubernetes

Shortcut:

richmacksearch kubernetes

Example:

richmack search docker

## Large Files

richmack large

Shows the largest indexed files.

## Duplicate Detection

richmack duplicates

Duplicate detection works in two stages:

1. Find files with matching sizes.
2. Confirm exact duplicates using SHA-256.

RichmackOS does not automatically delete duplicate files.

## Git Repository Catalog

richmack repos

Shortcut:

richmackgit

RichmackOS detects Git repositories and records:

- repository name
- path
- detected stack
- branch
- clean or dirty state
- origin remote
- last commit date

Supported project markers include:

- Python
- Node.js
- Rust
- Go
- Ruby
- PHP
- Java
- Docker

## Memory

Remember something:

richmack remember "The Debian server stores my RAG database."

List memories:

richmack memories

Recall by text:

richmack recall Debian

Forget by ID:

richmack forget 3

Shortcut:

richmackmem remember "example memory"

Memory is stored locally in:

~/.richmackos/richmackos.db

## Skills

Skills are saved shell procedures.

Add a skill:

richmack skill add diskfree "df -h"

List skills:

richmack skill list

Show a skill:

richmack skill show diskfree

Run a skill:

richmack skill run diskfree

RichmackOS asks for confirmation before running a stored shell skill.

Skill files are stored in:

~/.richmackos/skills

## Plugins

List plugins:

richmack plugins

Shortcut:

richmackplugins

Plugin directory:

~/.richmackos/plugins

Current plugin placeholders include:

- Linux
- Git
- RAG

## RichmackAI

Ask a one-shot AI question:

richmack ai "Explain systemd."

Direct command:

richmackai "Explain systemd."

Interactive chat:

richmack chat

or:

richmackai --chat

Choose a model:

richmackai -m gemma2:2b --chat

Save a one-shot answer:

richmackai -o ~/answer.txt "Explain Linux permissions."

Save an interactive chat transcript:

richmackai --chat -o ~/richmack-chat.txt

RichmackAI prints responses in bold cyan.

## Richmack RAG

Richmack RAG provides retrieval-augmented generation using documents stored on the Debian server.

The Debian server performs:

- document storage
- text chunking
- SQLite storage
- vector storage
- similarity search

The Richmack workstation performs:

- embeddings
- LLM generation

### Index a file

richmackrag index ~/computer-specs.txt

### Index a directory

richmackrag index ~/Documents

### Show RAG statistics

richmackrag stats

### Search retrieved chunks

richmackrag search "What CPU does this computer have?"

### Ask indexed documents

richmackrag ask "How much RAM does this computer have and what CPU does it use?"

Or through RichmackOS:

richmack rag "How much RAM does this computer have and what CPU does it use?"

Example:

Query embedding    ██████████████████████████████ 100%
Searching          ██████████████████████████████ 100%
Preparing context  ██████████████████████████████ 100%
Generating answer  ██████████████████████████████ 100%

╭─ RICHMACK AI ─────────────────────────────
The computer has 2.8 GiB of RAM and uses an
AMD Athlon Processor LE-1640. [1][2]
╰────────────────────────────────────────────

Evidence match: 66% (MEDIUM)

References
[1] /home/wisdom/computer-specs.txt
[2] /home/wisdom/computer-specs.txt

Evidence Match measures retrieval relevance.

It is not a guarantee of factual accuracy.

## RAG Architecture

Documents on Debian
        |
        v
Text extraction
        |
        v
Chunking
        |
        v
richmack.local
Nomic embeddings
        |
        v
Vectors returned
        |
        v
SQLite database on Debian
        |
        v
User question
        |
        v
Question embedding on Richmack
        |
        v
Similarity search on Debian
        |
        v
Relevant chunks
        |
        v
Granite on Richmack
        |
        v
Answer + references

## Documentation Generator

Generate a README for a project:

richmack readme .

Shortcut:

richmackdoc .

Generated README files are stored under:

~/Readme/PROJECT_NAME/README.md

RichmackOS can inspect common project files including:

- README.md
- pyproject.toml
- requirements.txt
- package.json
- Dockerfile
- docker-compose.yml
- compose.yaml

## Application Files

Main application:

~/.richmackos/richmackos.py

Main database:

~/.richmackos/richmackos.db

Plugins:

~/.richmackos/plugins

Skills:

~/.richmackos/skills

RichmackAI:

/usr/local/bin/richmackai

Richmack RAG:

/usr/local/bin/richmackrag

RichmackOS:

/usr/local/bin/richmack

RAG application:

~/.richmack-rag/rag.py

RAG database:

~/.richmack-rag/rag.db

README:

~/Readme/RichmackOS/README.md

Man page:

man richmack

## Shortcut Commands

richmacksys

richmackindex

richmacksearch

richmackgit

richmackmem

richmackdoc

richmackskill

richmackplugins

## Requirements

Debian-side requirements:

- Bash
- Python 3
- SQLite
- Git
- curl
- LAN access to richmack.local

No local LLM is required on the Debian server.

## Default AI Models

Generation:

huihui_ai/granite4.1-abliterated:3b

Embeddings:

nomic-embed-text

The models run on the Richmack Ollama server.

## Security Philosophy

RichmackOS prefers deterministic Linux tools whenever possible.

It does not automatically delete or move files during scanning.

Stored shell skills require confirmation before execution.

AI is used when language understanding, classification, semantic retrieval, summarization, or reasoning adds value.

## Current Version

RichmackOS v0.1

Current capabilities:

- system dashboard
- diagnostics
- filesystem indexing
- filename/path search
- large-file discovery
- SHA-256 duplicate detection
- Git repository catalog
- local memory
- reusable skills
- plugin directory
- RichmackAI integration
- remote Ollama inference
- RAG
- evidence references
- evidence-match scoring
- documentation generation

## Planned Features

Future versions may add:

- richmack organize
- organization plans before file moves
- file watching
- automatic incremental indexing
- PDF metadata extraction
- media metadata extraction
- stale Git repository detection
- README quality analysis
- project tagging
- scheduled backups
- enhanced plugin execution
- system health history
- automatic RAG indexing
- richer command history intelligence

## Goal

RichmackOS turns a lightweight Linux server into a terminal-first personal computing assistant.

The Debian machine performs the lightweight storage, indexing, retrieval, and operating-system work.

The Richmack workstation supplies the expensive AI compute.

This keeps the system fast, local-first, modular, and usable even on older hardware.

## Organization Logging and Undo

Every successful organization run is logged under:

    ~/.richmackos/organize-logs/

List move logs:

    richmack organize --logs

Each successful move is stored as a JSONL record containing:

- timestamp
- original source path
- destination path
- file extension

Undo the most recent successful organization run:

    richmack organize --undo-last

Before restoring files, RichmackOS displays the complete reverse-move plan.

The user must type:

    UNDO

before files are restored.

Undo is refused if:

- a moved file is missing from its current destination
- the original source path already exists

After a successful undo, the move log is renamed with the extension:

    .undone

This preserves a recovery history while preventing the same log from being
automatically undone twice.

## Organization Logging and Undo

Every successful organization run is logged under:

    ~/.richmackos/organize-logs/

List move logs:

    richmack organize --logs

Each successful move is stored as a JSONL record containing:

- timestamp
- original source path
- destination path
- file extension

Undo the most recent successful organization run:

    richmack organize --undo-last

Before restoring files, RichmackOS displays the complete reverse-move plan.

The user must type:

    UNDO

before files are restored.

Undo is refused if:

- a moved file is missing from its current destination
- the original source path already exists

After a successful undo, the move log is renamed with the extension:

    .undone

This preserves a recovery history while preventing the same log from being
automatically undone twice.

## Recursive Organization

RichmackOS can inspect subdirectories recursively:

    richmack organize ~ --recursive

Recursive mode skips sensitive and high-churn directories including:

    .git
    .cache
    .config
    .local
    .ssh
    .gnupg
    .richmackos
    .richmack-rag
    node_modules
    __pycache__
    .venv
    venv

It also skips RichmackOS destination directories so already-organized
files are not continually reprocessed.

Recursive mode is still a dry run unless --apply is specified.

Example:

    richmack organize ~/Downloads --recursive

Apply:

    richmack organize ~/Downloads --recursive --apply

## AI Fallback Classification

RichmackOS uses deterministic file-extension rules first.

If a file cannot be classified, AI-assisted classification can be enabled:

    richmack organize ~/Downloads --ai

Only the real filename, extension, and file size are sent to RichmackAI.

File contents are not sent.

AI is only used for items that deterministic rules cannot classify.

Combine recursive mode and AI:

    richmack organize ~ --recursive --ai

Apply after reviewing:

    richmack organize ~ --recursive --ai --apply

The safety model remains:

    inspect
    → propose
    → approve
    → move
    → log
    → undo

## Incremental Filesystem Watcher

RichmackOS includes a lightweight filesystem watcher based on Linux inotify.

The watcher notices changes as they happen and updates the RichmackOS SQLite
file index one file at a time.

This avoids repeatedly rescanning the entire home directory.

### Start

    richmack watch start

### Stop

    richmack watch stop

### Restart

    richmack watch restart

### Status

    richmack watch status

### Recent Watcher Log

    richmack watch log

### Follow Events Live

    richmack watch follow

Press Ctrl+C to stop following the journal. The watcher itself continues
running.

### Events

The watcher processes:

- newly created files
- completed writes
- files moved into watched directories
- files moved away
- deleted files

The watcher updates:

    ~/.richmackos/richmackos.db

### Classification

Incremental classification uses:

    extension
        ↓
    MIME type
        ↓
    other

AI is not called automatically by the background watcher.

This keeps the watcher lightweight and predictable.

AI-assisted organization remains available through:

    richmack organize PATH --ai

### Excluded Directories

The watcher ignores high-churn, sensitive, or application-internal directories
including:

    .git
    .cache
    .config
    .local
    .ssh
    .gnupg
    .richmackos
    .richmack-rag
    node_modules
    __pycache__
    .venv
    venv

### Service

The watcher runs as a systemd user service:

    richmack-watch.service

User lingering is enabled so the service can continue running when the user
is not actively connected through SSH.

### Design

The watcher does not move or delete user files.

It only updates RichmackOS metadata.

Actual file organization remains a separate explicit workflow:

    inspect
      ↓
    propose
      ↓
    APPLY
      ↓
    log
      ↓
    undo

## Automatic RAG Indexing

The RichmackOS filesystem watcher can automatically update the RAG knowledge
base when supported documents are created or modified.

Supported automatic RAG file types currently include:

    .txt
    .md
    .markdown
    .rst
    .csv
    .json
    .yaml
    .yml
    .html

Workflow:

    file created or modified
        ↓
    inotify watcher
        ↓
    RichmackOS SQLite index updated
        ↓
    richmackrag index FILE
        ↓
    text chunked on Debian
        ↓
    embeddings generated on richmack.local
        ↓
    vectors stored in Debian RAG database

AI inference and embeddings still run on the Richmack workstation.

The Debian server only performs lightweight filesystem, SQLite, chunking, and
retrieval work.

PDF files are not automatically sent to RAG yet because PDF text extraction
has not been added to the current RAG pipeline.

Watcher logs show successful RAG updates using:

    RAG /path/to/file

View recent events:

    richmack watch log

Follow live:

    richmack watch follow

## Knowledge Inbox

RichmackOS provides a simple document-ingestion workflow using:

    ~/Knowledge-Inbox

Files copied into this directory are detected automatically by the
RichmackOS filesystem watcher.

Supported text-based documents are automatically added to the RAG index.

Current automatically indexed extensions include:

    .txt
    .md
    .markdown
    .rst
    .csv
    .json
    .yaml
    .yml
    .html

### Workflow

    Mac / Laptop / Other Computer
                |
                | scp / rsync
                v
    ~/Knowledge-Inbox on Debian
                |
                v
    RichmackOS inotify watcher
                |
                +----> filesystem SQLite index
                |
                v
    richmackrag index FILE
                |
                v
    text chunking on Debian
                |
                v
    embedding request
                |
                v
    richmack.local:11434
                |
                +----> nomic-embed-text
                |
                v
    vectors returned to Debian
                |
                v
    ~/.richmack-rag/rag.db
                |
                v
    richmack rag "QUESTION"
                |
                v
    Granite on richmack.local
                |
                v
    answer + references + evidence match

### Send a Document from a Mac

Example:

    scp ~/Desktop/aws-notes.txt \
        wisdom@192.168.1.78:~/Knowledge-Inbox/

The watcher notices the file automatically.

Check the watcher:

    richmack watch log

Check RAG statistics:

    richmackrag stats

Ask the document collection:

    richmack rag "What do my AWS notes say about IAM?"

### Send Multiple Documents

    scp ~/Documents/*.txt \
        wisdom@192.168.1.78:~/Knowledge-Inbox/

### Send a Directory

    scp -r ~/Documents/DevOps \
        wisdom@192.168.1.78:~/Knowledge-Inbox/

### Rsync Documents

For repeated synchronization, rsync is more efficient:

    rsync -av \
        ~/Documents/DevOps/ \
        wisdom@192.168.1.78:~/Knowledge-Inbox/DevOps/

Only changed files need to be transferred on later runs.

### Automatic Indexing

No manual RAG command is required for supported files.

The workflow is:

    copy file
        ↓
    watcher detects file
        ↓
    local filesystem index updated
        ↓
    RAG index updated
        ↓
    embeddings generated remotely
        ↓
    document becomes searchable

### Verify a Document Was Indexed

Search the normal filesystem index:

    richmack search aws-notes

View watcher activity:

    richmack watch log

View RAG statistics:

    richmackrag stats

Test retrieval:

    richmackrag search "IAM permissions"

Ask naturally:

    richmack rag "What do my documents say about IAM permissions?"

### Files Already on the Server

Existing documents can still be indexed manually:

    richmackrag index ~/Documents

or:

    richmackrag index ~/Knowledge-Inbox

### PDF Documents

PDF automatic ingestion is not enabled yet.

The current RAG engine reads text-based files directly.

PDF support will require text extraction, typically using:

    pdftotext

Once PDF extraction is added, PDF files placed into Knowledge-Inbox can
follow the same automatic workflow.

## Recommended Daily Workflow

1. Send documents to:

       ~/Knowledge-Inbox

2. Let the watcher detect and index them automatically.

3. Verify activity when needed:

       richmack watch log

4. Search filenames:

       richmack search QUERY

5. Search document meaning:

       richmackrag search "QUESTION"

6. Ask the knowledge base:

       richmack rag "QUESTION"

7. Use regular AI without documents:

       richmack ai "QUESTION"

8. Start an interactive AI conversation:

       richmack chat

This separates normal AI chat from document-grounded RAG queries.

## RichmackOS Data Flow

    Files
      |
      +----> Organizer
      |       extension
      |       MIME
      |       optional AI
      |
      +----> Filesystem Index
      |       SQLite
      |
      +----> RAG
              chunks
              embeddings
              semantic retrieval
                    |
                    v
              richmack.local
                    |
                    v
                 Ollama

## YouTube Knowledge Ingestion

RichmackOS can ingest recent YouTube subtitles from a curated channel list.

Configured channels include:

- Danny Jones
- Tim Ferriss
- Poetik Flakko
- VladTV
- Fireship
- ESOTERICA
- Chill Dude Explains

List channels:

    richmack youtube channels

Sync the newest 10 videos from every configured channel:

    richmack youtube sync

Sync five videos per channel:

    richmack youtube sync --limit 5

Sync one channel:

    richmack youtube sync --channel fireship

Available channel keys include:

    danny-jones
    tim-ferriss
    poetik-flakko
    vladtv
    fireship
    esoterica
    chill-dude-explains

View state:

    richmack youtube status

Search saved transcript text:

    richmack youtube search kubernetes

### Workflow

    YouTube channels
          |
          v
    yt-dlp metadata/subtitles
          |
          v
    VTT subtitle file
          |
          v
    RichmackOS transcript cleaner
          |
          v
    plain UTF-8 .txt transcript
          |
          v
    ~/Knowledge-Inbox/YouTube/CHANNEL/
          |
          v
    RichmackOS watcher
          |
          v
    richmackrag index
          |
          v
    embeddings on richmack.local
          |
          v
    RAG database on Debian
          |
          v
    richmack rag "QUESTION"

Clean transcript files contain metadata including:

- title
- channel
- video ID
- YouTube URL
- upload date
- duration
- description
- transcript text

The state database prevents already-ingested videos from being repeatedly
downloaded.

The default first sync is limited to the newest ten videos from each channel.
Future syncs skip successfully indexed video IDs.

Example RAG queries:

    richmack rag "What has Fireship discussed recently about JavaScript?"

    richmack rag "What themes come up in recent Danny Jones interviews?"

    richmack rag "Compare recent discussions from Tim Ferriss and Danny Jones."

    richmack rag "What does ESOTERICA say about Gnosticism?"

YouTube transcripts are stored under:

    ~/Knowledge-Inbox/YouTube

Ingestion state is stored at:

    ~/.richmackos/youtube-state.json

## RAG Namespaces

RichmackOS supports scoped RAG queries.

Normal unscoped RAG remains available:

    richmack rag "QUESTION"

Scoped queries use:

    richmack rag --scope SCOPE "QUESTION"

Available scopes:

    all
    youtube
    docs
    projects
    system

Examples:

    richmack rag --scope youtube \
        "What have my YouTube transcripts said about robotics?"

    richmack rag --scope docs \
        "What do my personal documents say about IAM?"

    richmack rag --scope projects \
        "How does RichmackOS perform file organization?"

    richmack rag --scope system \
        "What CPU does this Debian server use?"

The purpose of scopes is to prevent unrelated documents from outranking the
documents relevant to the question.

### Scope Layout

youtube:

    ~/Knowledge-Inbox/YouTube/

docs:

    ~/Knowledge-Inbox/
    ~/Documents/

The YouTube subtree is excluded from the docs scope.

projects:

    ~/Projects/
    ~/RichmackOS/

system:

    ~/Readme/
    ~/computer-specs.txt

## YouTube Time and Video Filters

YouTube RAG queries can be restricted by channel and time.

Latest transcript:

    richmack youtube ask fireship --latest \
        "What did this video discuss?"

Recent videos:

    richmack youtube ask danny-jones --days 30 \
        "What subjects came up most often?"

Since a date:

    richmack youtube ask tim-ferriss --since 2026-08-01 \
        "What themes were discussed?"

One specific video:

    richmack youtube ask fireship --video VIDEO_ID \
        "Summarize this video."

Filters can be combined where sensible.

For example:

    richmack youtube ask esoterica \
        --days 90 \
        "What religious traditions were discussed?"

The YouTube query engine searches only transcript chunks belonging to the
selected channel and selected video/date range.

This prevents unrelated RichmackOS documentation or personal documents from
being included in YouTube answers.

### Updated Knowledge Architecture

    RAG Database
        |
        +-- youtube namespace
        |
        +-- docs namespace
        |
        +-- projects namespace
        |
        +-- system namespace
        |
        +-- all

Queries can therefore select the most appropriate knowledge domain before
semantic retrieval occurs.

## YouTube Research Mode

RichmackOS includes a multi-pass research extraction engine.

Unlike the normal summarizer, Research Mode does not depend on the LLM
to format the final report.

The model performs several focused extraction passes and RichmackOS
renders the final Markdown and JSON deterministically.

### Research One Channel

    richmack youtube research chill-dude-explains --limit 3

### Research Fireship

    richmack youtube research fireship --limit 5

### Research Every Channel

    richmack youtube research --all --limit 3

### Research Recent Videos

    richmack youtube research danny-jones --days 30 --limit 10

### Select Model

    richmack youtube research chill-dude-explains \
        --limit 3 \
        --model gemma3:4b

### Pipeline

    transcripts
        |
        v
    Pass 1 - detailed synthesis
        |
        v
    Pass 2 - structured extraction
        |
        v
    Pass 3 - research roadmap
        |
        v
    deterministic renderer
        |
        +----> Markdown
        |
        +----> JSON

### Extracted Knowledge

Research Mode extracts:

- detailed summary
- channel overview
- key themes
- keywords
- tags
- resources
- URLs
- people
- organizations
- books
- websites
- tools
- medical terminology
- legal terminology
- psychology terminology
- technologies
- research queries
- notable claims
- questions raised
- topics requiring verification
- concept relationships
- practical takeaways
- source-video metadata

### Research Files

Results are stored under:

    ~/Knowledge/Research/youtube/CHANNEL/

Each run creates:

    YYYY-MM-DD_HHMMSS.md
    YYYY-MM-DD_HHMMSS.json

The newest research result is also copied to:

    latest.md
    latest.json

The Markdown file is intended for human reading.

The JSON file provides a structured knowledge layer for future
RichmackOS search, comparison, cross-channel analysis, and AI tools.

## Research Output Embedding

RichmackOS YouTube Research Mode stores results under:

    ~/Knowledge/Research/youtube/CHANNEL/

Each research run creates:

    YYYY-MM-DD_HHMMSS.md
    YYYY-MM-DD_HHMMSS.json
    latest.md
    latest.json

Because the RichmackOS watcher recursively monitors the user's home directory,
and both `.md` and `.json` are supported RAG extensions, these research
artifacts are automatically submitted to:

    richmackrag index FILE

This means both raw transcripts and derived research briefs become part of
the local knowledge base.

The resulting flow is:

    YouTube transcript
        |
        v
    Knowledge-Inbox
        |
        v
    automatic embedding
        |
        v
    Research Mode
        |
        +----> Markdown brief
        |
        +----> JSON knowledge object
                    |
                    v
              automatic embedding
                    |
                    v
              RichmackRAG

This creates two searchable knowledge layers:

1. raw source transcripts
2. structured derived research

Example queries:

    richmack rag --scope youtube \
      "What has Chill Dude Explains said about crowd crush?"

    richmack rag \
      "What resources were extracted from Chill Dude Explains?"

    richmack rag \
      "What topics should I research further from my YouTube research briefs?"

The raw transcript remains the primary source record.

Research briefs are model-generated derived artifacts and should be treated
as summaries and extracted knowledge rather than original source text.

## Multi-Pass YouTube Research

Research Mode now splits knowledge extraction into focused passes:

    deterministic URL extraction
    summary
    keywords
    entities
    resources
    research roadmap
    merge
    final Markdown / JSON

This is designed to improve reliability with smaller local models such as
Gemma 3 4B.

Run:

    richmack youtube research chill-dude-explains --limit 3

Artifacts:

    ~/Knowledge/Research/youtube/CHANNEL/runs/TIMESTAMP/summary.json
    ~/Knowledge/Research/youtube/CHANNEL/runs/TIMESTAMP/keywords.json
    ~/Knowledge/Research/youtube/CHANNEL/runs/TIMESTAMP/entities.json
    ~/Knowledge/Research/youtube/CHANNEL/runs/TIMESTAMP/resources.json
    ~/Knowledge/Research/youtube/CHANNEL/runs/TIMESTAMP/research.json
    ~/Knowledge/Research/youtube/CHANNEL/runs/TIMESTAMP/final.json
    ~/Knowledge/Research/youtube/CHANNEL/runs/TIMESTAMP/final.md

Convenience copies:

    ~/Knowledge/Research/youtube/CHANNEL/latest.json
    ~/Knowledge/Research/youtube/CHANNEL/latest.md

### Resource-Only Analysis

    richmack youtube resources chill-dude-explains --limit 3

This extracts:

- URLs
- named resources
- tools
- apps
- courses
- training programs
- procedures
- frameworks
- useful search terms

Explicit URLs are extracted deterministically before model analysis.

## YouTube Knowledge System

RichmackOS can ingest, summarize, search, and chat with a configurable set of
YouTube channels.

The YouTube pipeline uses:

    yt-dlp
        ↓
    subtitles / auto-subtitles
        ↓
    VTT cleanup
        ↓
    plain-text transcripts
        ↓
    ~/Knowledge-Inbox/YouTube/
        ↓
    RichmackOS watcher
        ↓
    RichmackRAG
        ↓
    embeddings on richmack.local
        ↓
    semantic search and AI queries

The default YouTube summarizer model is:

    gemma3:4b

This model runs through Ollama on:

    http://richmack.local:11434

### Configured Channels

Channels are stored in:

    ~/.richmackos/youtube-channels.json

List configured channels:

    richmack youtube channels

Add a channel from the command line:

    richmack youtube add-channel \
      channel-key \
      "Display Name" \
      "https://www.youtube.com/@channel/videos"

Example:

    richmack youtube add-channel \
      renaissance-periodization \
      "Renaissance Periodization" \
      "https://www.youtube.com/@RenaissancePeriodization/videos"

Remove a channel:

    richmack youtube remove-channel channel-key

### Synchronizing Videos

Sync recent videos from every configured channel:

    richmack youtube sync --limit 3

Sync one channel:

    richmack youtube sync \
      --channel fireship \
      --limit 3

RichmackOS stores cleaned transcripts beneath:

    ~/Knowledge-Inbox/YouTube/

Already-ingested video IDs are tracked so future syncs can skip duplicates.

### Automatic RAG Indexing

Clean transcript `.txt` files are automatically noticed by the RichmackOS
filesystem watcher.

The workflow is:

    new transcript
        ↓
    filesystem watcher
        ↓
    local filesystem index
        ↓
    richmackrag index
        ↓
    remote embedding request
        ↓
    richmack.local
        ↓
    vectors returned to Debian
        ↓
    ~/.richmack-rag/rag.db

This makes new transcript material searchable without manually running a RAG
index command.

### YouTube Search

Search saved transcript text:

    richmack youtube search robotics

### Scoped YouTube RAG

Ask a question about one channel:

    richmack youtube ask fireship \
      "What programming topics are discussed?"

Restrict the question to the latest transcript:

    richmack youtube ask fireship \
      --latest \
      "What did this video discuss?"

The YouTube ask command is scoped so unrelated RichmackOS documentation and
other documents are not included in retrieval.

### Detailed Channel Summaries

Summarize the latest three transcripts from one channel:

    richmack youtube summarize \
      chill-dude-explains \
      --limit 3

Summarize all configured channels:

    richmack youtube summarize \
      --all \
      --limit 3

The summarizer displays progress while reading transcripts, preparing context,
and generating the response.

### Combined Cross-Channel Summary

Generate individual summaries for every configured channel and then create a
single combined briefing:

    richmack youtube summarize \
      --all \
      --limit 3 \
      --combined

The combined briefing can identify:

- recurring themes
- relationships among channels
- major differences
- keywords
- tags
- people and organizations
- resources mentioned
- things to look up
- notable claims
- practical takeaways

### Interactive YouTube Chat

Open an interactive chat grounded in one channel:

    richmack youtube chat chill-dude-explains

Open a chat across all configured channels:

    richmack youtube chat --all

The chat uses Gemma 3 4B by default and maintains conversational history during
the session.

Available interactive commands:

    /clear
    /quit

The chat shows a progress bar while generating each answer.

Source material is treated as untrusted data. Instructions appearing inside
transcripts are not intended to override RichmackOS system behavior.

### Recommended YouTube Workflow

    1. Add channels

       richmack youtube add-channel KEY "NAME" URL

    2. Sync recent uploads

       richmack youtube sync --limit 3

    3. Summarize one channel

       richmack youtube summarize CHANNEL --limit 3

    4. Summarize all channels

       richmack youtube summarize --all --limit 3

    5. Produce a combined briefing

       richmack youtube summarize --all --limit 3 --combined

    6. Ask RAG questions

       richmack youtube ask CHANNEL "QUESTION"

    7. Open an interactive chat

       richmack youtube chat CHANNEL

       or:

       richmack youtube chat --all

This preserves a simple architecture:

    deterministic ingestion
        ↓
    local transcript storage
        ↓
    automatic embeddings
        ↓
    scoped RAG
        ↓
    summaries
        ↓
    interactive chat

The experimental multi-pass research pipeline is not part of the active
YouTube workflow.
