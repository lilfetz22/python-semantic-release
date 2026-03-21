# Plan: Fix false `.git/` warning in monorepo setup (Issue #1418)

**Issue**: https://github.com/python-semantic-release/python-semantic-release/issues/1418
**Status**: In Progress
**Date**: 2026-03-21

## Summary

Fix the `verify_git_repo_dir` validator in `RawConfig` that emits a false "Found .git/ in higher parent directory" warning when `repo_dir` uses relative paths like `..`. The root cause is `.absolute()` not resolving `..` components — switching to `.resolve()` on both sides of the comparison fixes the path mismatch. The warning message will be improved for clarity. Tests cover unit validation and an e2e smoke test.

## Root Cause

In `src/semantic_release/cli/config.py`, the `verify_git_repo_dir` validator (lines 382–404) uses `.absolute()` which does NOT resolve `..` components:

```python
# Line 393: found_path uses .absolute()
found_path = Path(git_repo.working_tree_dir or git_repo.working_dir).expanduser().absolute()

# Line 399: dir_path uses .absolute() — does NOT resolve ".."
if dir_path.absolute() != found_path:
    logging.warning("Found .git/ in higher parent directory...")
```

`Path("..").absolute()` → `/path/to/package/..` (unexpanded)
`found_path.absolute()` → `/path/to/repo` (expanded by GitPython)

These don't match even though they point to the same directory.

## Phases

### Phase 1: Fix the validator ⬜
- [ ] File: `src/semantic_release/cli/config.py` lines 382–404
- [ ] Change `found_path` construction: `.absolute()` → `.resolve()` (line 393)
- [ ] Change comparison: `dir_path.absolute()` → `dir_path.resolve()` (line 399)
- [ ] Improve warning message to include both paths for debuggability
- [ ] Keep `return found_path.resolve()` on line 404 as-is

### Phase 2: Unit tests ⬜
- [ ] File: `tests/unit/semantic_release/cli/test_config.py`
- [ ] Test: valid `repo_dir = "."` — no warning, resolves correctly
- [ ] Test: relative parent `..` in monorepo layout — no false warning
- [ ] Test: legitimate mismatch — warning IS emitted with improved message
- [ ] Test: no git repo — `InvalidGitRepositoryError` raised
- [ ] Use `tmp_path`, `monkeypatch.chdir()`, `caplog`
- [ ] Follow `@pytest.mark.unit` and `Given/When/Then` docstring patterns

### Phase 3: E2E smoke test ⬜
- [ ] Simulate exact reproduction: git repo with `package-a/pyproject.toml` containing `repo_dir = ".."`
- [ ] Run `semantic-release version --print` from the subdirectory
- [ ] Assert exit code 0, no false warning in stderr
- [ ] Mark with `@pytest.mark.e2e`

### Phase 4: Validation ⬜
- [ ] Activate `.venv` virtual environment
- [ ] `ruff format .` + `ruff check --unsafe-fixes .`
- [ ] `mypy .`
- [ ] `pytest -m unit -k test_config` (targeted unit tests)
- [ ] `pytest -m e2e` (targeted e2e tests)
- [ ] Full `pytest -m unit`

## Relevant Files

| File | Purpose |
|------|---------|
| `src/semantic_release/cli/config.py` (L382-404) | `verify_git_repo_dir` validator — FIX HERE |
| `tests/unit/semantic_release/cli/test_config.py` | Add unit tests |
| `tests/e2e/cmd_version/test_version_print.py` | Reference for e2e `--print` patterns |
| `tests/e2e/conftest.py` | `run_cli` shared fixture for CLI invocation |

## Decisions

- **Both sides use `.resolve()`**: Normalizes symlinks and `..` components for correct comparison
- **Warning kept but improved**: Includes both paths when there IS a real mismatch
- **Scope limited**: Only validator fix + tests; no doc changes or logging infra changes
- **Virtual env**: `.venv` must be activated before running any tests or linting

## Verification Checklist

- [ ] `pytest -m unit -k "verify_git_repo_dir or repo_dir"` — new unit tests pass
- [ ] `pytest -m e2e -k "monorepo"` — e2e smoke test passes
- [ ] `ruff check --unsafe-fixes .` — no lint errors
- [ ] `mypy .` — no type errors
