#!/usr/bin/env python3
"""Validate the generated static site and write its release inventory (stdlib only)."""
from svg_avatar import validate_svg
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys

OUT = Path(__file__).resolve().parents[1] / 'build'
BASE_FILES = frozenset({
    'index.html', 'en/index.html', 'style.css', 'language.js',
    'favicon.svg', 'hero.svg', 'badge.svg', 'badge-ru.svg',
})
AVATAR = re.compile(r'avatars/[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.(?:png|jpg|jpeg|webp|svg)')
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
MAX_COUNT = 4096


def release(source_commit):
    if not re.fullmatch(r'[0-9a-f]{40}', source_commit):
        raise ValueError('source commit must be 40 lowercase hexadecimal characters')
    if OUT.is_symlink() or not OUT.is_dir():
        raise ValueError('build must be a real directory')
    files = {}
    total = 0
    for path in sorted(OUT.rglob('*')):
        name = path.relative_to(OUT).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f'symlink is forbidden: {name}')
        if stat.S_ISDIR(mode):
            if name not in {'en', 'avatars'}:
                raise ValueError(f'unexpected directory: {name}')
            continue
        if not stat.S_ISREG(mode):
            raise ValueError(f'not a regular file: {name}')
        if name == 'release.json':
            continue
        if name not in BASE_FILES and not AVATAR.fullmatch(name):
            raise ValueError(f'unexpected file: {name}')
        size = path.stat().st_size
        if not 0 < size <= MAX_FILE:
            raise ValueError(f'file must be nonempty and at most 2 MiB: {name}')
        if name.startswith('avatars/') and path.suffix == '.svg':
            validate_svg(path.read_bytes())
        total += size
        if total > MAX_TOTAL or len(files) >= MAX_COUNT:
            raise ValueError('release exceeds total size or file count limit')
        files[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'size': size}
    if not BASE_FILES <= files.keys():
        raise ValueError('missing required files: ' + ', '.join(sorted(BASE_FILES - files.keys())))
    manifest = {'schema': 1, 'source_commit': source_commit, 'files': files}
    (OUT / 'release.json').write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(f'Release inventory: {len(files)} files, {total} bytes')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    args = parser.parse_args()
    try:
        release(args.source_commit)
    except (ValueError, OSError) as error:
        print(f'Release failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
