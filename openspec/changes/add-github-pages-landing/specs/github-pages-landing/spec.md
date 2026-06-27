## ADDED Requirements

### Requirement: Static landing page content

The project SHALL provide a static marketing landing page at `docs/index.html` that describes the Career Market Fit Scanner and directs users to the live application.

#### Scenario: Hero and primary CTA

- **WHEN** a visitor opens the GitHub Pages landing page
- **THEN** the page displays the product name, a short value proposition, and a prominent link or button to the live Railway app at `https://job-listing-comparer-production.up.railway.app/`

#### Scenario: Feature summary visible

- **WHEN** the landing page renders
- **THEN** it summarizes core capabilities (resume upload, job source comparison, career tracks, skill gaps, downloadable reports) without requiring the visitor to read the full README

#### Scenario: Data sources and attribution

- **WHEN** the landing page describes job data sources
- **THEN** it mentions Remotive, Arbeitnow, and optional Adzuna, and includes Remotive attribution consistent with API terms

#### Scenario: Limitations noted

- **WHEN** the landing page describes the product
- **THEN** it briefly notes MVP limitations relevant to users (e.g. keyword matching, no accounts, resume sent to configured LLM when Groq is enabled)

### Requirement: Landing page styling

The landing page SHALL use dedicated static CSS under `docs/` that is visually consistent with the web app (system fonts, light background, card sections, blue primary button).

#### Scenario: Mobile-friendly layout

- **WHEN** the landing page is viewed on a narrow viewport
- **THEN** content remains readable without horizontal scrolling and the CTA remains easy to tap

#### Scenario: No app server dependencies

- **WHEN** the landing page is served from GitHub Pages
- **THEN** all assets load using paths valid under the Pages URL prefix (relative CSS, no FastAPI `/static` routes)

### Requirement: GitHub Pages publish path

The repository SHALL document enabling GitHub Pages from the `/docs` folder on the default branch.

#### Scenario: Pages source documented

- **WHEN** a maintainer reads the README GitHub Pages section
- **THEN** instructions explain selecting branch `main`, folder `/docs`, and the expected URL pattern `https://<owner>.github.io/job-listing-comparer/`

#### Scenario: Landing page entry point

- **WHEN** GitHub Pages is enabled
- **THEN** `docs/index.html` is served as the site home page
