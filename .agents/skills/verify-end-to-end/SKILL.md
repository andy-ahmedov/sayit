---
name: verify-end-to-end
description: Use this skill when validating that the repository works end-to-end after implementing or refactoring features.
---

Verification checklist:
1. run tests;
2. run compile check;
3. check CLI help output;
4. confirm README still matches actual behavior;
5. identify missing gaps between docs and code.

Default commands:
```bash
bash tools/verify.sh
```

If you cannot run a true end-to-end audio generation test, at least verify:
- command construction;
- file planning;
- error paths;
- deterministic outputs.
