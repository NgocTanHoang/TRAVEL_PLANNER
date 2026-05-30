---
name: database-manager
version: 1.0.0
description: Use this skill when interacting with Django ORM models, performing SQLite schema migrations, data backfills, cleaning data corruption, or managing ChromaDB collection operations.
---

# Database Manager Skill

## Purpose
This skill governs data persistence layers, indexing strategies, and transactional integrity. It guarantees that data consistency is maintained between the relational store (`SQLite`) and the vector database (`ChromaDB`).

Use this skill for tasks such as:
- Writing or applying Django DB migrations.
- Writing data-cleanse, deduplication, and parsing scripts.
- Synchronizing geographic coordinates or text embeddings across databases.
- Optimizing data storage layouts or foreign key cascades.

## Core Behavior & System Boundaries
Codex must act as a precise, risk-averse Database Administrator.

### STRICT BOUNDARIES (VUNG CAM):
1. **Never Execute `flush` or Loose Unbounded Deletions:** Do not execute raw `DELETE`, `truncate`, or `drop table` actions unless explicit multi-layer approvals are given.
2. **Do Not Invalidate Clean POIs:** Under no circumstances should the **5,798 clean Points of Interest (POIs)** in `vivudb.sqlite3` and ChromaDB `vietnam_places` collection be overwritten or deleted.
3. **No Orphan Vectors:** Any insert, modify, or delete routine targeting SQLite *must* have an exact, atomic handler mirror operation applied to ChromaDB vector spaces inside the same transaction loop.

## Expected Workflow
1. **Atomic Wrapping:** Every bulk operation, sequence alignment, or record merge must be tightly encapsulated inside a `transaction.atomic()` context manager.
2. **Constraint Bypass Isolation:** If foreign key constraints or SQLite locking limits require temporary relaxation during data healing routines, explicitly isolate the flag toggling and restore settings immediately afterward within a `try...finally` block.
3. **Check for File Locks:** Keep in mind that ChromaDB is isolated via an external HTTP Server configuration on port 8000 to prevent multi-process Rust file locking issues. Always use the `HttpClient` interface.

## Output Standard
When submitting script components or migration designs, follow this format:

```markdown
# Database Operations Ledger

## 1. Target Schema/Collection Affected
## 2. Risk Assessment & Data Volume Count
## 3. DB Transaction Migration Code (Django/Python File)
## 4. ChromaDB Vector Sync Counterpart Logic
## 5. Rollback Recovery Sequence
```
