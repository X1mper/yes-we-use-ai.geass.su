# Yes, we use AI.

[![Yes, we use AI.](https://yes-we-use-ai.geass.su/badge.svg)](https://yes-we-use-ai.geass.su/en/)

**English** · [Russian](README_ru.md)

**We use AI. We test our work. We take responsibility. You're free to do things differently.**

An open letter about choosing our tools, taking responsibility for what we make, and treating each other with respect.

Read the letter: **[English](https://yes-we-use-ai.geass.su/en/)** · **[Russian](https://yes-we-use-ai.geass.su/)**

## Sign the letter

People and organizations can sign by adding one entry to [`supporters.jsonc`](supporters.jsonc) and opening a pull request. No HTML changes or local setup required.

See [CONTRIBUTING.md](CONTRIBUTING.md) for examples and guidelines. Sign only for yourself or an organization you're authorized to represent. Signatures are reviewed before publication. For an optional avatar, add an image in `avatars/` and set `avatar` to its path, such as `/avatars/your-name.jpg`.

## Get the badge

Add this to your project's README:

```markdown
[![Yes, we use AI.](https://yes-we-use-ai.geass.su/badge.svg)](https://yes-we-use-ai.geass.su/en/)
```

[Russian badge](https://yes-we-use-ai.geass.su/badge-ru.svg) · [HTML and GitLab instructions](https://yes-we-use-ai.geass.su/en/#badge)

The badge shows support for the letter. It isn't a quality certification.

## PR browser previews

Each push to a pull request builds a Chromium preview: English and Russian, at 1440 px and 375 px wide. A bot updates its PR comment with a link to the latest screenshots and the commit ID. GitHub sign-in is required to download the artifact; screenshots are retained for 14 days. First-time fork checks may need a maintainer's approval in GitHub.

Previews do not deploy the PR. The screenshot job has read-only permissions; a separate trusted job posts the link without executing PR code.

## Publishing

Accepted changes on `main` are built by GitHub Actions and published to the `deploy` branch. The website updates automatically after a successful build. Pull requests are reviewed before merging and cannot deploy directly.

## Run locally

The static build only needs Python 3.10 or later.

```sh
python3 tools/build.py
python3 -m http.server 8766 --bind 127.0.0.1 --directory build
```

Open http://127.0.0.1:8766/ for Russian or `/en/` for English.

- `templates/ru.html`, `templates/en.html` — page templates; update both when editing the letter.
- `supporters.jsonc` — people and organizations supporting the letter, with commented examples.
- `style.css`, `language.js`, `*.svg` — shared styles, language switching, badge snippets, and artwork.
- `tools/build.py` — validates supporter entries and builds both pages.
- `tools/release.py` — creates the static release inventory; GitHub Actions publishes it after changes to `main`.
- `build/` — generated site; do not edit or commit.

Both languages and the signature lists work without JavaScript.

Optional local screenshots (Node.js 20 or later):

```sh
npm ci --ignore-scripts
npx playwright install chromium
npm run preview
npm run test:preview-comment
```

Four PNG files are written to ignored `output/pr-preview/`. Playwright is pinned in the lockfile and is only used for development and PR previews.
