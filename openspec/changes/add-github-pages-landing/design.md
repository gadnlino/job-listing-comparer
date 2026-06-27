## Context

The FastAPI app runs on Railway at `https://job-listing-comparer-production.up.railway.app/`. The GitHub repository README already describes features and includes the live demo link, but there is no dedicated public marketing page. GitHub Pages can host static files from the repo at no extra cost with minimal setup.

## Goals / Non-Goals

**Goals:**

- Publish a single-page static landing site that explains the product and links to the live app
- Use GitHub Pages with the `/docs` folder on the default branch (no separate build pipeline required)
- Match existing visual tone (system fonts, blue CTA, card layout) derived from `src/web/static/styles.css`
- Document enablement steps in the README

**Non-Goals:**

- Hosting the FastAPI app on GitHub Pages (not possible — Pages is static only)
- Blog, docs site, or multi-page marketing site
- GitHub Actions deploy workflow (optional future enhancement; manual Settings is enough for v1)
- Custom domain or SEO optimization beyond basic meta tags
- Embedding the analyze form on the landing page (CTA redirects to Railway)

## Decisions

### 1. `docs/` folder + GitHub Pages “Deploy from branch”

**Choice:** Put `index.html` and `styles.css` in `/docs`, enable Pages source = `main` branch, `/docs` folder.

**Alternatives considered:**

| Option | Pros | Cons |
|--------|------|------|
| **`/docs` on main** | Zero CI; edit in same PR as code | URL is `owner.github.io/repo-name/` |
| **`gh-pages` branch** | Classic pattern | Extra branch to maintain |
| **GitHub Actions + artifact** | Flexible | Overkill for one HTML page |

**Rationale:** Easiest path for a solo maintainer; changes ship with normal commits.

### 2. Plain static HTML (no Jekyll)

**Choice:** Single `index.html` with linked CSS — no `_config.yml`, no Liquid.

**Rationale:** Avoid Jekyll gem/build quirks; page is one screen of content.

### 3. CTA targets Railway production URL

**Choice:** Primary button href = `https://job-listing-comparer-production.up.railway.app/` (absolute URL).

**Rationale:** App lives off GitHub; relative links would 404 on Pages.

### 4. Content sourced from README

**Choice:** Reuse “What it does”, data sources table, MVP limitations, and Remotive attribution from README — not duplicate long dev setup instructions.

**Rationale:** Landing page is for end users, not contributors.

## Risks / Trade-offs

- **[Risk] Two URLs to maintain (Pages + Railway)** → Keep production URL in one constant at top of `index.html` and README; document both in cloud-deployment spec.
- **[Risk] GitHub Pages path prefix breaks asset links** → Use relative `styles.css`; avoid root-absolute `/static/...` paths.
- **[Risk] Repo name / owner change breaks Pages URL** → README documents pattern `https://<owner>.github.io/job-listing-comparer/`.
- **[Trade-off] No automated deploy verification** → Manual smoke: open Pages URL after Settings change.

## Migration Plan

1. Merge `docs/` landing files to `main`
2. GitHub → Settings → Pages → Source: **Deploy from a branch** → Branch: `main`, Folder: **`/docs`**
3. Wait for Pages build (~1–2 min); verify URL loads and CTA opens Railway app
4. Add published Pages URL to README (optional second link alongside Railway)

Rollback: disable Pages in Settings or revert `docs/` commit — no impact on Railway app.

## Open Questions

- None blocking v1. Optional follow-up: custom domain, Open Graph image, or GitHub Action to lint `docs/index.html`.
