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


def avatar_path(value):
    if not isinstance(value, str) or not re.fullmatch(
            r'/avatars/[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.(?:png|jpe?g|webp)', value):
        raise ValueError('avatar: use /avatars/name.png, .jpg, .jpeg or .webp')
    path = ROOT / value.lstrip('/')
    if (ROOT / 'avatars').is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError(f'avatar: missing file or symlink: {value}')
    if not 0 < path.stat().st_size <= 1024 * 1024:
        raise ValueError(f'avatar: file must be at most 1 MiB: {value}')
    with path.open('rb') as image:
        header = image.read(12)
    if path.suffix == '.png':
        valid = header.startswith(b'\x89PNG\r\n\x1a\n')
    elif path.suffix == '.webp':
        valid = header[:4] == b'RIFF' and header[8:12] == b'WEBP'
    else:
        valid = header.startswith(b'\xff\xd8\xff')
    if not valid:
        raise ValueError(f'avatar: image header does not match extension: {value}')
    return path


def parse_jsonc(source):
    # Match quoted strings before comments so URLs and escaped quotes stay intact.
    tokens = r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/'
    def strip_comment(match):
        token = match[0]
        if token.startswith('"'):
            return token
        # Preserve line/column offsets for useful JSON error messages.
        return ''.join(c if c in '\r\n' else ' ' for c in token)
    return json.loads(re.sub(tokens, strip_comment, source))


def load_supporters(path):
    records = parse_jsonc(path.read_text(encoding='utf-8-sig'))
    if not isinstance(records, list):
        raise ValueError('supporters.jsonc must be an array')
    seen_names, seen_urls = set(), set()
    for i, record in enumerate(records):
        label = f'supporters[{i}]'
        if not isinstance(record, dict) or set(record) - {'type', 'name', 'url', 'description', 'avatar'}:
            raise ValueError(f'{label}: unknown field or invalid record')
        if not {'type', 'name', 'url'} <= set(record):
            raise ValueError(f'{label}: type, name and url are required')
        if record['type'] not in ('person', 'organization'):
            raise ValueError(f'{label}.type: use person or organization')
        text(record['name'], f'{label}.name', 100)
        https_url(record['url'], f'{label}.url')
        if 'description' in record:
            text(record['description'], f'{label}.description', 140)
        if 'avatar' in record:
            avatar_path(record['avatar'])
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
            avatar = ''
            if entry.get('avatar'):
                src = html.escape(entry['avatar'], quote=True)
                avatar = f'<img class="supporter-avatar" src="{src}" width="52" height="52" alt="" loading="lazy" decoding="async">'
            parts.append(f'<li>{avatar}<div><a href="{url}" title="{name}" rel="nofollow ugc">{name}</a>{description}</div></li>')
        parts.append('</ul>')
    return '\n'.join(parts)


def build():
    config = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
    if not isinstance(config, dict) or set(config) != {'repository'}:
        raise ValueError('site.json must contain only repository')
    repository = config['repository']
    if not isinstance(repository, str) or not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('repository must be https://github.com/OWNER/REPO')
    records = load_supporters(ROOT / 'supporters.jsonc')
    # Render and validate everything before replacing the previous output.
    pages = {}
    for lang in ('ru', 'en'):
        source = (ROOT / 'templates' / f'{lang}.html').read_text(encoding='utf-8')
        replacements = {
            '{{SUPPORTERS}}': render_supporters(records, lang),
            '{{REPOSITORY}}': html.escape(repository, quote=True),
            '{{EDIT_SUPPORTERS}}': html.escape(repository + '/edit/main/supporters.jsonc', quote=True),
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
    avatar_output = OUT / 'avatars'
    if avatar_output.exists():
        shutil.rmtree(avatar_output)
    for value in sorted({entry['avatar'] for entry in records if entry.get('avatar')}):
        avatar_output.mkdir(exist_ok=True)
        shutil.copyfile(avatar_path(value), OUT / value.lstrip('/'))
    print(f'Built RU/EN with {len(records)} supporter(s) → {OUT}')


if __name__ == '__main__':
    try:
        build()
    except (ValueError, OSError, TypeError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        sys.exit(1)
