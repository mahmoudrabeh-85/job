# Job Hunt — Smart Job Search & CV Analysis Platform

A local-first job search intelligence platform: aggregates jobs from free no-key sources, scores them against your CV, generates SWOT / gap analysis reports, and provides an interactive web dashboard.

> This is the **public showcase version**. All personal data (name, phone, email, social links) has been replaced with placeholders (`[Your Name]`, `[Phone]`, `[Email]`).

## Features

- **Job Aggregation** — collects jobs from free APIs with no API key required (RemoteOK, WeWorkRemotely, Remotive, Jobicy)
- **Smart Scoring** — scores each job (0–100) against your CV skills (procurement, supply chain, sales, pharma, ERP…)
- **Intelligent Web UI** — interactive dashboard with filters, search, sorting, and per-job analysis modal with a ready HR message (AR/EN)
- **SWOT Analysis** — generates a personal SWOT report based on candidate profile + job market data
- **Auto-Apply Toolkit** — ready-to-copy application messages + auto-apply helper (use at your own risk)
- **Data exported** — CSV / JSON export from the UI settings panel

## Project Structure

```
├── app/                    # Web server (Python stdlib only — no dependencies)
│   ├── job_app.py          # Main server (port 8767)
│   ├── index.html          # UI entry
│   ├── main.py / database.py / config.py
│   └── routers/
│       ├── jobs.py         # /api/v1/jobs
│       ├── analysis.py     # /api/analyze (CV vs job)
│       └── vet.py          # job vetting / filters
├── frontend/               # Standalone HTML+JS UI (static version)
│   ├── index.html / app.js / style.css
│   └── landing.html
├── tools/                  # CLI tools
│   ├── job_aggregator.py   # Collect jobs from free sources → SQLite
│   ├── job_analyzer.py     # CV vs job gap analysis → HTML report
│   ├── job_swot.py         # SWOT report generator
│   ├── smart_scorer.py     # Scoring engine shared by tools
│   ├── custom_sources.py   # Extra source adapters
│   ├── auto_apply.py       # Auto-apply helper (experimental)
│   └── generate_html_report.py
└── docs/
    └── JOB-SEARCH-RESEARCH-REPORT.md
```

## Quick Start

1. **Collect jobs** (requires Python 3.10+):

   ```
   python tools/job_aggregator.py
   ```

2. **Start the web dashboard**:

   ```
   python app/job_app.py
   # → http://127.0.0.1:8767/
   ```

3. **Generate analysis / SWOT reports**:

   ```
   python tools/job_analyzer.py --analyze-all
   python tools/job_swot.py
   ```

## Configuration

- Copy your CV text files to `cv/candidate_EN.txt` and `cv/candidate_AR.txt` (the server reads them for scoring).
- Optional API keys are read from a local `.env` file (see `app/config.py`). The platform works fully without keys.
- Jobs are stored in `data/jobs.db` (auto-created, excluded from git).

## Sources (no API key needed)

| Source | Limit | Notes |
|--------|-------|-------|
| RemoteOK | ~99 | Public API; needs UTF-8 fix (mojibake) |
| WeWorkRemotely | ~88 | RSS feed |
| Remotive | 16 (free tier) | Paid tier unlocks more |
| Jobicy | up to 200 | Public API with salaries |

## Disclaimer

This is a personal productivity tool. Respect each job source's terms of service. Auto-apply features are experimental — review every message before sending.