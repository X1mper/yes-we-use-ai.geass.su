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

## Run locally

Requires Python 3.10 or later. No third-party dependencies.

```sh
python3 tools/build.py
python3 -m http.server 8766 --bind 127.0.0.1 --directory build
```

Open http://127.0.0.1:8766/ for Russian or `/en/` for English.

- `templates/ru.html`, `templates/en.html` — page templates; update both when editing the letter.
- `supporters.jsonc` — people and organizations supporting the letter, with commented examples.
- `style.css`, `language.js`, `*.svg` — shared styles, language switching, badge snippets, and artwork.
- `tools/build.py` — validates supporter entries and builds both pages.
- `build/` — generated site; do not edit or commit.

Both languages and the signature lists work without JavaScript.
