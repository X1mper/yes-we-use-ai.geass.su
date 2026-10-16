#!/usr/bin/env python3
"""Validate community data and build the static site. Python 3.10+, stdlib only."""
import html
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build'


def text(value, field, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{field}: expected nonempty text, at most {limit} characters')
    if value != value.strip() or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError(f'{field}: surrounding whitespace/control characters are not allowed')
    return value


def https_url(value, field):
    text(value, field, 300)
    url = urlsplit(value)
    if (url.scheme != 'https' or not url.hostname or url.username or url.password
            or any(c.isspace() for c in value) or any(c in value for c in '\\<>"')):
        raise ValueError(f'{field}: use a public HTTPS URL without credentials')
    # Accessing port also rejects malformed ports.
    if url.port not in (None, 443):
        raise ValueError(f'{field}: nonstandard ports are not allowed')
    return value


def load_supporters(path):
    records = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(records, list):
        raise ValueError('supporters.json must be an array')
    seen_names, seen_urls = set(), set()
    for i, record in enumerate(records):
        label = f'supporters[{i}]'
        if not isinstance(record, dict) or set(record) - {'type', 'name', 'url', 'description'}:
            raise ValueError(f'{label}: unknown field or invalid record')
        if not {'type', 'name', 'url'} <= set(record):
            raise ValueError(f'{label}: type, name and url are required')
        if record['type'] not in ('person', 'organization'):
            raise ValueError(f'{label}.type: use person or organization')
        text(record['name'], f'{label}.name', 100)
        https_url(record['url'], f'{label}.url')
        if 'description' in record:
            text(record['description'], f'{label}.description', 140)
        identity = (record['type'], unicodedata.normalize('NFKC', record['name']).casefold())
        parsed = urlsplit(record['url'])
        url_key = (parsed.hostname.casefold(), parsed.path.rstrip('/'), parsed.query, parsed.fragment)
        if identity in seen_names or url_key in seen_urls:
            raise ValueError(f'{label}: duplicate name or URL')
        seen_names.add(identity)
        seen_urls.add(url_key)
    return records


def render_supporters(records, lang):
    parts = []
    groups = [('person', 'Люди' if lang == 'ru' else 'People'),
              ('organization', 'Организации' if lang == 'ru' else 'Organizations')]
    for kind, title in groups:
        parts.append(f'<h3>{title}</h3>')
        entries = sorted((r for r in records if r['type'] == kind), key=lambda r: r['name'].casefold())
        if not entries:
            empty = 'Здесь пока нет подписей. Можно стать первым.' if lang == 'ru' else 'No signatures yet. You can be the first.'
            parts.append(f'<p class="muted">{empty}</p>')
            continue
        parts.append('<ul class="supporter-list">')
        for entry in entries:
            name, url = html.escape(entry['name']), html.escape(entry['url'], quote=True)
            description = ('<span>' + html.escape(entry['description']) + '</span>') if entry.get('description') else ''
            parts.append(f'<li><a href="{url}" rel="nofollow ugc">{name}</a>{description}</li>')
        parts.append('</ul>')
    return '\n'.join(parts)


def build():
    config = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
    if not isinstance(config, dict) or set(config) != {'repository'}:
        raise ValueError('site.json must contain only repository')
    repository = config['repository']
    if not isinstance(repository, str) or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('repository must be https://github.com/OWNER/REPO')
    records = load_supporters(ROOT / 'supporters.json')
    # Render and validate everything before replacing the previous output.
    pages = {}
    for lang in ('ru', 'en'):
        source = (ROOT / 'templates' / f'{lang}.html').read_text(encoding='utf-8')
        replacements = {
            '{{SUPPORTERS}}': render_supporters(records, lang),
            '{{REPOSITORY}}': html.escape(repository, quote=True),
            '{{EDIT_SUPPORTERS}}': html.escape(repository + '/edit/main/supporters.json', quote=True),
            '{{CONTRIBUTING}}': html.escape(repository + '/blob/main/CONTRIBUTING.md', quote=True),
        }
        markers = set(re.findall(r'\{\{[^{}]*\}\}', source))
        if markers != set(replacements):
            raise ValueError(f'{lang}: missing or unknown template markers')
        # Match original template once. Never reinterpret submitted text as a template.
        pages[lang] = re.sub(r'\{\{[^{}]*\}\}', lambda match: replacements[match[0]], source)
    OUT.mkdir(exist_ok=True)
    for lang, source in pages.items():
        target = OUT / ('index.html' if lang == 'ru' else 'en/index.html')
        target.parent.mkdir(exist_ok=True)
        target.write_text(source, encoding='utf-8')
    for name in ('style.css', 'language.js', 'favicon.svg', 'badge.svg', 'badge-ru.svg', 'hero.svg'):
        shutil.copyfile(ROOT / name, OUT / name)
    print(f'Built RU/EN with {len(records)} supporter(s) → {OUT}')


if __name__ == '__main__':
    try:
        build()
    except (ValueError, OSError, TypeError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        sys.exit(1)
