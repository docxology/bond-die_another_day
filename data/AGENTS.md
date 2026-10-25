# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed here.

## Rules

1. Commit human-authored or externally sourced inputs only — never generated CSV/JSON/PNG/artifacts.
2. Record every added file in [`README.md`](README.md) with its role.
3. Keep inputs deterministic: no wall-clock timestamps or machine-specific paths.

Quick orientation: [`README.md`](README.md).
