---
name: implement-pdf-extraction
description: Use this skill when implementing or refactoring PDF reading, page selection, reading order, table handling, or page-region extraction logic.
---

Repository-specific extraction rules:
- primary source is a clean born-digital PDF;
- extract directly from PDF, not via PDF->Word conversion;
- do not introduce OCR in the happy path;
- start simple and make extraction behavior explicit.

Implementation order:
1. inspect page count;
2. validate user page selection;
3. extract page text in stable order;
4. add table strategy hooks;
5. add tests.

If layout is tricky, prefer a configurable fallback path using blocks / words rather than hidden heuristics.
