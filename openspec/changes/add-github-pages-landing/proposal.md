## Why

The app is deployed on Railway at a production URL, but the GitHub repo has no public landing page. Visitors who find the repository (or a future `*.github.io` URL) cannot quickly understand what the product does or click through to try it. A static GitHub Pages site is low effort — no backend, no extra hosting cost — and fits a solo project that already has README copy and visual styling to reuse.

## What Changes

- Add a static marketing landing page (HTML + CSS) under `docs/` served by GitHub Pages
- Primary call-to-action links to the live Railway app: `https://job-listing-comparer-production.up.railway.app/`
- Reuse existing app branding, feature bullets, and attribution notes from the README
- Document one-time GitHub repo Settings → Pages enablement (source: `/docs` on default branch)
- Optional: link the GitHub Pages URL from the README once published

No changes to the FastAPI app, Railway deploy, or analysis pipeline.

## Capabilities

### New Capabilities

- `github-pages-landing`: Static public landing page hosted on GitHub Pages with hero, feature summary, privacy/limitations note, and CTA to the live app

### Modified Capabilities

- `cloud-deployment`: Document GitHub Pages as the public repo-facing entry point alongside Railway production URL

## Impact

- **New files:** `docs/index.html`, `docs/styles.css` (or shared/minimal CSS)
- **Docs:** README section for enabling GitHub Pages and the published URL pattern
- **Ops:** Manual GitHub Settings step (not automatable from repo alone without Actions workflow)
- **No runtime impact** on the Railway app or local development
