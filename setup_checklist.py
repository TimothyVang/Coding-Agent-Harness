#!/usr/bin/env python3
"""
Setup Checklist for Rust-DFIR Toolkit
======================================

This script initializes the project checklist based on app_spec.txt.
It creates 50 discrete tasks covering all phases of development.
"""

from pathlib import Path
from checklist_manager import ChecklistManager

# Initialize the manager
project_dir = Path.cwd()
manager = ChecklistManager(project_dir)

# Define all tasks based on app_spec.txt
# Organized by phase with clear dependencies

tasks = [
    # ===========================================
    # PHASE 0: PROOF OF CONCEPTS (Weeks 1-2)
    # ===========================================
    {
        "title": "Set up Cargo workspace structure",
        "description": "Create workspace Cargo.toml at project root, crates/ directory with core, cli, tui, web-gui subdirectories. Initialize each crate and configure workspace dependencies. Set up .gitignore for Rust. Create examples/, tests/integration/, tests/fixtures/ directories."
    },
    {
        "title": "Add Phase 0 dependencies to Cargo.toml",
        "description": "Add windows-sys (0.59) with Win32_Foundation, Win32_Storage_FileSystem, Win32_System_IO, Win32_Storage_Vss, Win32_System_Com features. Add crossbeam-channel (0.5) and rayon (1.7)."
    },
    {
        "title": "POC: Raw Disk Access (poc_raw_disk.rs)",
        "description": "Create examples/poc_raw_disk.rs. Implement to_wide() for UTF-16 conversion, open_physical_drive() with CreateFileW + NO_BUFFERING, AlignedBuffer struct with manual memory alignment, read_sectors() with ReadFile + OVERLAPPED. Read 1MB from PhysicalDrive0 and display hex dump. Requires admin privileges."
    },
    {
        "title": "POC: Ring Buffer Threading (poc_ring_buffer.rs)",
        "description": "Create examples/poc_ring_buffer.rs. Implement bounded channel with 16 slots capacity, producer/consumer threads, backpressure demonstration, performance measurement. Verify no deadlocks, clean shutdown, all data received in order."
    },
    {
        "title": "POC: Volume Shadow Copy (poc_vss.rs)",
        "description": "Create examples/poc_vss.rs. Implement COM initialization, IVssBackupComponents creation, VSS_BT_FULL backup, add volume to snapshot set, PrepareForBackup/DoSnapshotSet, query snapshot properties, read locked file (SAM), cleanup. Requires admin privileges."
    },

    # ===========================================
    # PHASE 1: MVP - BASIC IMAGER (Weeks 3-6)
    # ===========================================
    {
        "title": "Add Phase 1 dependencies",
        "description": "Add thiserror (1.0), sha2 (0.10), md-5 (0.10), sha1 (0.10), serde with derive (1.0), serde_json (1.0), chrono (0.4), clap with derive (4.4), indicatif (0.17). Add criterion (0.5) as dev-dependency."
    },
    {
        "title": "Implement error.rs - Error types",
        "description": "Create crates/core/src/error.rs. Define ForensicError enum with variants: DiskAccessError, AlignmentError, HashMismatchError, VssError, IoError. Implement Display/Error traits using thiserror. Add Result<T> type alias. Write unit tests."
    },
    {
        "title": "Implement disk/sector_align.rs - Aligned buffers",
        "description": "Create crates/core/src/disk/mod.rs and sector_align.rs. Port AlignedBuffer from POC with Debug impl, as_ptr()/as_mut_ptr() methods, Send+Sync traits. Add alignment validation, unit tests for 512/4096 byte alignment, docstrings with safety invariants."
    },
    {
        "title": "Implement pipeline/ring_buffer.rs - Thread-safe buffer",
        "description": "Create crates/core/src/pipeline/mod.rs and ring_buffer.rs. Port POC ring buffer with generic T: Send, configurable capacity (64MB / chunk_size default), Sender/Receiver handles. Add unit tests for send/recv, backpressure behavior."
    },
    {
        "title": "Implement disk/reader.rs - Physical disk reader",
        "description": "Create crates/core/src/disk/reader.rs. Port POC functions to DiskReader struct with handle, sector_size, total_size fields. Implement open(drive_number), read_at(buffer, offset). Implement Drop for handle cleanup. Add comprehensive error handling and integration tests."
    },
    {
        "title": "Implement disk/writer.rs - Image file writer",
        "description": "Create crates/core/src/disk/writer.rs. Create ImageWriter struct. Implement create(path), write(buffer). Implement Drop for flush/close. Add validation for write success. Write unit tests with temporary files."
    },
    {
        "title": "Implement integrity/hasher.rs - Multi-algorithm hasher",
        "description": "Create crates/core/src/integrity/mod.rs and hasher.rs. Create MultiHasher struct with MD5, SHA1, SHA256 hashers. Implement new(), update(data), finalize() returning HashResult with hex strings. Write unit tests with NIST test vectors."
    },
    {
        "title": "Implement pipeline/worker.rs - Pipeline workers",
        "description": "Create crates/core/src/pipeline/worker.rs. Implement reader_worker (disk read loop), hasher_worker (hash update loop), writer_worker (image write loop). Add error propagation, integration test coordinating all 3 workers."
    },
    {
        "title": "Implement pipeline/coordinator.rs - Acquisition coordinator",
        "description": "Create crates/core/src/pipeline/coordinator.rs. Create AcquisitionCoordinator struct with source_drive, output_path, ring_buffer_capacity, chunk_size. Implement run() returning ChainOfCustody. Spawn 3 threads, join/collect results, handle panics, add progress tracking, performance metrics."
    },
    {
        "title": "Implement forensics/custody.rs - Chain of custody",
        "description": "Create crates/core/src/forensics/mod.rs and custody.rs. Define ChainOfCustody struct with examiner, case_number, source_device, output_path, timestamps, sizes, hashes, errors. Implement Serialize/Deserialize, to_json(), save_to_file(). Write serialization tests."
    },
    {
        "title": "Implement cli/cli.rs - CLI argument parsing",
        "description": "Create crates/cli/src/cli.rs. Define Args struct with source (drive number), output (path), examiner (name), case_number (optional), chunk_size (optional, default 1MB). Add help text, examples, unit tests for argument parsing."
    },
    {
        "title": "Implement cli/main.rs - Main entry point",
        "description": "Edit crates/cli/src/main.rs. Parse CLI arguments, create AcquisitionCoordinator, run coordinator, save chain of custody JSON, display summary. Add error handling, exit codes, progress indicators with indicatif crate."
    },
    {
        "title": "Create integration tests for disk imaging",
        "description": "Create tests/integration/disk_imaging.rs. Set up 100MB test disk image in fixtures. Test full workflow: image disk, verify hash, verify size, verify chain of custody. Add #[ignore] attribute, document setup in README."
    },
    {
        "title": "Create performance benchmarks (>200 MB/s target)",
        "description": "Create benches/throughput.rs. Add [[bench]] to Cargo.toml. Implement benchmarks for disk read, hash computation, image write, end-to-end pipeline throughput. Verify targets: read >200MB/s, hash >500MB/s, write >300MB/s, pipeline >200MB/s."
    },
    {
        "title": "Create hash validation tests vs FTK Imager (PHASE GATE)",
        "description": "Create tests/integration/hash_validation.rs. Document manual FTK setup. Implement test: read both JSON files, compare MD5/SHA1/SHA256. Assert EXACT match. This is a CRITICAL PHASE GATE - cannot proceed to Phase 2 without 100% hash match."
    },

    # ===========================================
    # PHASE 2: TARGETED TRIAGE (Weeks 7-10)
    # ===========================================
    {
        "title": "Add Phase 2 triage dependencies",
        "description": "Add mft (0.5) for MFT parsing, evtx (0.8) for event logs, nt-hive2 (0.1) for registry, serde_yaml (0.9) for YAML configs."
    },
    {
        "title": "Implement triage/mft_resolver.rs - MFT parser",
        "description": "Create crates/core/src/triage/mod.rs and mft_resolver.rs. Parse $MFT to resolve file paths. Target: Parse 1TB drive's MFT in <30 seconds. Add integration tests with sample MFT."
    },
    {
        "title": "Implement triage/vss.rs - VSS integration",
        "description": "Create crates/core/src/triage/vss.rs. Port POC VSS code to production module. Create/delete VSS snapshots, access locked files via snapshot path. Target: Extract Registry via VSS in <2 minutes."
    },
    {
        "title": "Implement parsers/registry.rs - Registry parser",
        "description": "Create crates/core/src/parsers/mod.rs and registry.rs. Parse Registry hives (SAM, SYSTEM, SOFTWARE, etc.). Extract common artifacts: user accounts, installed software, recent files. Use nt-hive2 crate."
    },
    {
        "title": "Implement parsers/evtx.rs - Event log parser",
        "description": "Create crates/core/src/parsers/evtx.rs. Parse Windows Event Logs (.evtx files). Extract security events, logons, process creation. Use evtx crate. Output structured JSON."
    },
    {
        "title": "Implement triage/config.rs - YAML config system",
        "description": "Create crates/core/src/triage/config.rs. Parse KAPE-compatible YAML configs. Define TriageConfig struct with targets (file patterns, registry keys, artifacts). Load/validate configs from configs/targets/ directory."
    },
    {
        "title": "Create triage target configs (windows-registry.yaml, event-logs.yaml)",
        "description": "Create configs/targets/windows-registry.yaml and event-logs.yaml. Define collection targets for common Windows artifacts. Include SAM, SYSTEM, Security.evtx, Application.evtx, browser history paths."
    },
    {
        "title": "Create triage integration tests (<5 min target)",
        "description": "Create tests/integration/triage_workflow.rs. Test full triage workflow on test system. Target: Collect top 20 artifacts in <5 minutes. Verify all artifacts collected, hashes computed, chain of custody updated."
    },

    # ===========================================
    # TERMINAL AND WEB GUI (Phase 2-3)
    # ===========================================
    {
        "title": "Add TUI dependencies and setup crate",
        "description": "Add ratatui (0.25), crossterm (0.27) to crates/tui. Create basic crate structure with main.rs, app.rs, ui.rs, events.rs."
    },
    {
        "title": "Implement TUI dashboard layout",
        "description": "Create TUI with real-time progress bars, live throughput metrics, ASCII art dashboard, scrollable audit log viewer, keyboard controls (q to quit, arrows to navigate)."
    },
    {
        "title": "Wire TUI to core library",
        "description": "Connect TUI to core library functions. Display acquisition progress in real-time. Add progress callbacks to AcquisitionCoordinator."
    },
    {
        "title": "Research and decide Web GUI framework (Tauri vs Axum+HTMX)",
        "description": "Prototype both Tauri and Axum+HTMX options. Evaluate binary size, XP compatibility, complexity. Document decision with rationale."
    },
    {
        "title": "Implement Web GUI (chosen framework)",
        "description": "Implement Web GUI with point-and-click device selector, real-time progress display, HTML forensic reports, settings management."
    },

    # ===========================================
    # PHASE 3: NETWORK STREAMING (Weeks 11-13)
    # ===========================================
    {
        "title": "Add Phase 3 network dependencies",
        "description": "Add tonic (0.10), prost (0.12), tokio with rt-multi-thread/net features (1.34), zstd (0.13), tokio-rustls (0.25)."
    },
    {
        "title": "Create gRPC protocol definition (proto/forensics.proto)",
        "description": "Create proto/forensics.proto. Define ForensicStream service with methods: StartAcquisition, StreamChunk, GetProgress, GetHashes. Define message types for chunks, metadata, status."
    },
    {
        "title": "Implement network/compressor.rs - Zstd compression",
        "description": "Create crates/core/src/network/mod.rs and compressor.rs. Implement streaming Zstd compression. Target: Reduce bandwidth by 50%+ for typical disk data."
    },
    {
        "title": "Implement network/server.rs - gRPC server",
        "description": "Create crates/core/src/network/server.rs. Implement ForensicServer serving gRPC endpoints. Stream disk chunks over network. Add authentication, rate limiting."
    },
    {
        "title": "Implement network/client.rs - gRPC client",
        "description": "Create crates/core/src/network/client.rs. Implement ForensicClient connecting to server. Receive and reassemble chunks. Handle disconnection/resume."
    },
    {
        "title": "Add TLS certificate support",
        "description": "Implement TLS 1.3 with certificate validation using tokio-rustls. Generate test certificates. Document certificate setup for production."
    },
    {
        "title": "Create network streaming integration tests (>500 Mbps target)",
        "description": "Create tests/integration/network_streaming.rs. Test full network streaming workflow. Verify >500 Mbps over gigabit LAN, encrypted transport, resume after disconnect."
    },

    # ===========================================
    # PHASE 4: AI-ASSISTED ANALYSIS (Weeks 14-16)
    # ===========================================
    {
        "title": "Add Phase 4 AI dependencies",
        "description": "Add reqwest with json feature (0.11), regex (1.10)."
    },
    {
        "title": "Implement ai/sanitizer.rs - PII redaction",
        "description": "Create crates/core/src/ai/mod.rs and sanitizer.rs. Implement PII sanitization: redact emails, IPs, usernames, paths containing usernames. All PII MUST be redacted before external API calls."
    },
    {
        "title": "Implement ai/prompts.rs - LLM system prompts",
        "description": "Create crates/core/src/ai/prompts.rs. Define system prompts for PowerShell deobfuscation, event log analysis, suspicious pattern detection. Include forensic context."
    },
    {
        "title": "Implement ai/analyzer.rs - LLM integration",
        "description": "Create crates/core/src/ai/analyzer.rs. Implement HTTP client for LLM API (OpenAI, Anthropic, or local). Send sanitized artifacts, parse responses. Target: <10 seconds per artifact."
    },
    {
        "title": "Create AI analysis integration tests",
        "description": "Test PowerShell Base64 deobfuscation, suspicious event log pattern detection. Verify all PII redacted before API calls, analysis completes <10 seconds."
    },

    # ===========================================
    # PHASE 5: LEGACY WINDOWS SUPPORT (Weeks 17-18)
    # ===========================================
    {
        "title": "Configure .cargo/config.toml for i686-pc-windows-msvc",
        "description": "Create .cargo/config.toml. Set default target to i686-pc-windows-msvc for 32-bit Windows compatibility. Configure static linking, optimize for size."
    },
    {
        "title": "Implement compat/win_api.rs - Runtime API detection",
        "description": "Create crates/core/src/compat/mod.rs and win_api.rs. Implement runtime detection for APIs unavailable on XP. Provide fallback implementations using windows-sys thunking."
    },
    {
        "title": "Adjust concurrency for Windows XP (no tokio runtime)",
        "description": "Modify async code to work without tokio on XP. Use std::thread for concurrency. Ensure graceful degradation of network/async features."
    },
    {
        "title": "Test on Windows XP SP3, 7, 10, 11 VMs",
        "description": "Set up test VMs for each Windows version. Run full test suite on each. Verify core features work on all, document any degraded features on XP/7."
    },
    {
        "title": "Verify single binary <15MB",
        "description": "Build release binary with all optimizations. Verify size <15MB. If larger, apply size optimizations: LTO, strip symbols, remove unused code, opt-level=z."
    },

    # ===========================================
    # PHASE 6: PRODUCTION HARDENING (Weeks 19-20)
    # ===========================================
    {
        "title": "Implement forensics/integrity.rs - Write-blocking verification",
        "description": "Create crates/core/src/forensics/integrity.rs. Implement write-blocking verification test that confirms no writes to source. Run before every acquisition."
    },
    {
        "title": "Enhance chain of custody with digital signatures",
        "description": "Add optional digital signature to ChainOfCustody. Implement Ed25519 signing of custody JSON. Document key management for forensic use."
    },
    {
        "title": "Implement forensics/logging.rs - Comprehensive audit logging",
        "description": "Create crates/core/src/forensics/logging.rs. Implement structured JSON audit logging for all sensitive operations. Include timestamps, actions, results, errors."
    },
    {
        "title": "Write README.md with project overview and setup",
        "description": "Create comprehensive README.md with project overview, installation instructions, quick start guide, architecture diagram, contribution guidelines."
    },
    {
        "title": "Write USER_GUIDE.md with detailed usage instructions",
        "description": "Create USER_GUIDE.md with detailed CLI usage, TUI/GUI guides, common workflows, troubleshooting, FAQ."
    },
    {
        "title": "Write FORENSIC_METHODOLOGY.md documenting forensic approach",
        "description": "Create FORENSIC_METHODOLOGY.md documenting forensic soundness approach, chain of custody procedures, validation methodology, legal considerations."
    },
    {
        "title": "Create full end-to-end test suite",
        "description": "Create comprehensive test suite covering all modules. Achieve >80% code coverage. Ensure all clippy warnings fixed, all tests pass."
    },
    {
        "title": "Final FTK Imager validation (CRITICAL PHASE GATE)",
        "description": "Run final hash comparison with FTK Imager on multiple test drives. MD5, SHA1, SHA256 MUST match 100%. Document validation results. This is the FINAL GATE before v1.0."
    },
    {
        "title": "Code review and security audit",
        "description": "Conduct thorough code review. Run cargo audit for dependency vulnerabilities. Review all unsafe blocks. Document security considerations."
    },
    {
        "title": "Create Release v1.0.0",
        "description": "Tag v1.0.0 release. Build release binaries for all target platforms. Create GitHub release with changelog. Publish documentation."
    },
]

# Initialize the checklist
manager.initialize(project_name="Rust-DFIR Toolkit", tasks=tasks)

# Export to markdown
manager.export_to_markdown()

print(f"Checklist initialized with {len(tasks)} tasks")
print("CHECKLIST.md created")
print("\nPhase breakdown:")
print("  - Phase 0 (POCs):           5 tasks")
print("  - Phase 1 (MVP Imager):     15 tasks")
print("  - Phase 2 (Triage):         8 tasks")
print("  - Phase 2-3 (GUI):          5 tasks")
print("  - Phase 3 (Network):        7 tasks")
print("  - Phase 4 (AI):             5 tasks")
print("  - Phase 5 (Legacy):         5 tasks")
print("  - Phase 6 (Production):     10 tasks")
print(f"\nTotal: {len(tasks)} tasks")
