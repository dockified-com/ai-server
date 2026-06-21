# ADR: ai-server as a Separate Repository

**Date:** 2026-06-21  
**Status:** Accepted

## Decision

The `ai_server/` (Python FastAPI) moves to its own repository, separate from `ai-tutor-native`.

## Context

`ai_server/` currently lives inside this repo as `ai_server/`. It was built as an extraction of all LLM inference logic from the original backend.

## Considered

**Keep in monorepo** — rejected. Different language (Python vs TypeScript) means every developer needs both runtimes. Different deployment cadence — the AI server can be updated (new model, new provider) without touching frontend or backend. No shared types between the Python service and the TypeScript codebase — the contract is HTTP + JSON, not code-level types.

**Move to separate repo** (chosen) — clean runtime separation, independent deploys, team members who own the AI server don't need Node.js. The HTTP boundary + shared secret is the only coupling point.

## Consequences

- `ai_server/` will be extracted to a new repo (exact name TBD)
- This repo's `backend/` calls `ai-server` via HTTP with `AI_SERVICE_SECRET`
- The `ai-server` repo should have its own `README.md`, `docs/`, local setup guide, and deployment instructions
- The session token JWT contract between NestJS and ai-server is the only interface — document it in both repos
