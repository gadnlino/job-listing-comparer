## 1. Model and Configuration

- [x] 1.1 Add `LinkStatus` type and `link_status` / `link_status_code` fields to `JobMatch` and `TopJobSummary`
- [x] 1.2 Add config vars: `LINK_VALIDATION_ENABLED`, `LINK_VALIDATION_MAX_JOBS`, `LINK_VALIDATION_TIMEOUT_SECONDS`, `LINK_VALIDATION_MIN_BODY_BYTES` in `config.py` and `.env.example`

## 2. Link Validator

- [x] 2.1 Implement `src/analysis/link_validator.py` with `validate_job_links(matches) -> list[JobMatch]`
- [x] 2.2 GET-only requests with `stream=True`, partial body read (16 KB max), redirect following, timeout, and concurrency cap
- [x] 2.3 Classify 403/429 as `unknown`; 404/410/5xx/timeout/empty URL as `inaccessible`; 2xx with body > min bytes as `accessible`
- [x] 2.4 Per-URL error isolation; empty URL → inaccessible
- [x] 2.5 Add `link_validation_summary(matches) -> dict[str, dict]` for per-source accessible/inaccessible/unknown/excluded counts
- [x] 2.6 Add `filter_displayable_matches(matches) -> list[JobMatch]` returning accessible + unknown only

## 3. Pipeline Integration

- [x] 3.1 Call link validation in `src/app.py` after `match_jobs()`, before `generate_reports()`
- [x] 3.2 Pass full match set to market stats / LLM; pass filtered set to reports and UI
- [x] 3.3 Add warnings when >20% of a source's validated links are inaccessible (excluded)
- [x] 3.4 Respect `LINK_VALIDATION_ENABLED=false` to skip checks (all statuses `unknown`, no filtering)

## 4. Reports

- [x] 4.1 CSV export uses filtered matches only; include `link_status` and `link_status_code` columns
- [x] 4.2 Top jobs table in `build_report_markdown()` uses filtered matches; add link status column for unknown entries
- [x] 4.3 Add excluded (inaccessible) link count per source in Markdown report summary note

## 5. Web UI

- [x] 5.1 Update `results.html` — show filtered matches only; clickable "View" when accessible; neutral link when unknown
- [x] 5.2 Show link validation exclusion warnings in results warnings section

## 6. Tests and Documentation

- [x] 6.1 Add `tests/test_link_validator.py` — accessible (200 + body), 404, timeout, redirect, empty URL, 403-as-unknown, 429-as-unknown, small-body-as-inaccessible, disabled
- [x] 6.2 Add tests for `filter_displayable_matches()` — inaccessible excluded, unknown kept
- [x] 6.3 Update `tests/test_report_csv.py`, `tests/test_web_app.py`, `tests/test_integration_pipeline.py`
- [x] 6.4 Update README with GET-only validation, exclusion behavior, and config
- [x] 6.5 Run full pytest suite and fix failures

## 7. Manual Verification

- [ ] 7.1 Run analysis with all sources; confirm inaccessible Adzuna/expired links are excluded from UI and CSV; market stats still reflect full set
