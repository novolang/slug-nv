#!/usr/bin/env python3
"""Write tests/differential_tests.nv from python-slugify's answers.

python-slugify (MIT) is run with its defaults: lower case, every run of
characters that are not letters or digits one hyphen, the ends
trimmed, no length limit.  That is `url_policy()` without its symbol
expansion and its length limit, which the suite builds.

The two agree only where their tables agree.  python-slugify
transliterates with Unidecode, and this package with deunicode and the
overrides tools/trans_table.py names, so a title is kept only when
every character in it has the same answer from both, read from
Unidecode and from this package's own generated table.  python-slugify
also removes a comma between two digits and decodes HTML entities,
which this package does not do, and the generator writes neither.

Run from the package root, with python-slugify and Unidecode
installed:
    python3 tools/differential.py
"""
import json
import random
import re
import subprocess

from slugify import slugify
from unidecode import unidecode

SEED = 20260927
COUNT = 300
OUT = 'tests/differential_tests.nv'

WORDS = ['hello', 'World', 'Novo', 'release', '0.13', 'Café', 'déjà', 'été', 'naïve',
         'Ångström', 'Straße', 'Łódź', 'Škoda', 'Crème', 'brûlée', 'Zürich', 'São', 'Paulo',
         'Ελλάδα', 'Αθήνα', 'Москва', 'книга', 'Kraków', 'façade', 'œuvre', 'Æsir',
         'jalapeño', 'piñata', 'C', 'v2', 'x86_64', 'IPv6', 'über', 'Ørsted']
PUNCT = [' ', ' ', ' ', '  ', ' - ', ', ', '. ', '! ', '? ', ': ', '; ', ' / ', ' (', ') ',
         ' "', '" ', "'", ' * ', '...', ' _ ', ' — ', ' – ', '\t']


def table():
    """This package's compiled answers, read back from src/slugtrans.nv."""
    src = open('src/slugtrans.nv', encoding='utf-8').read()
    out = {}
    for cp, text in re.findall(r'0x([0-9A-Fa-f]+) +=> Some\("((?:[^"\\\\]|\\\\.)*)"\)', src):
        out[int(cp, 16)] = text.replace('\\\\"', '"').replace('\\\\\\\\', '\\\\')
    return out


def agrees(title, ours):
    for ch in title:
        cp = ord(ch)
        if cp < 0x80:
            continue
        if cp not in ours or ours[cp].lower() != unidecode(ch).lower():
            return False
    return True


def main():
    ours = table()
    rng = random.Random(SEED)
    rows, tried = [], 0
    while len(rows) < COUNT and tried < 100000:
        tried += 1
        parts = []
        for _ in range(rng.randint(1, 6)):
            parts.append(rng.choice(WORDS))
            parts.append(rng.choice(PUNCT))
        title = ''.join(parts[:-1]) if rng.random() < 0.7 else ''.join(parts)
        if title in [r[0] for r in rows] or not agrees(title, ours):
            continue
        rows.append((title, slugify(title)))
    documented = [("This is a test ---", "this-is-a-test"),
                  ("C'est déjà l'été.", "c-est-deja-l-ete"),
                  ("jaja---lol-méméméoo--a", "jaja-lol-mememeoo-a"),
                  ("___This is a test___", "this-is-a-test"),
                  ("10 amazing secrets", "10-amazing-secrets")]
    for title, expected in documented:
        assert slugify(title) == expected, title
    out = ['// differential_tests.nv — slugmake against python-slugify.',
           '//',
           '// Written by tools/differential.py; do not edit by hand.  The first',
           '// rows are cases from python-slugify\'s README, and the rest are %d' % len(rows),
           '// seeded titles whose every character has the same answer in both',
           '// transliteration tables.  Each is slugged under `url_policy()` without',
           '// its symbol expansion and its length limit, which is python-slugify\'s',
           '// default behaviour.',
           '',
           'use std.test',
           'use slugpolicy',
           'use slugmake',
           '',
           'fn rows() -> [(Str, Str)]',
           '    [']
    everything = documented + rows
    for i, (title, expected) in enumerate(everything):
        comma = ',' if i < len(everything) - 1 else ''
        text = json.dumps(title, ensure_ascii=False).replace('$', '\\\\$')
        out.append('        (%s, %s)%s' % (text, json.dumps(expected), comma))
    out += ['    ]',
            '',
            '// python-slugify\'s defaults, as a policy.',
            'fn plain() -> slugpolicy.SlugPolicy',
            '    let u = slugpolicy.url_policy()',
            '    SlugPolicy { separator: u.separator, case: u.case, mode: u.mode, max_len: 0, truncate: u.truncate, empty_fallback: u.empty_fallback, collapse_runs: u.collapse_runs, trim_separators: u.trim_separators, expand_symbols: false }',
            '',
            '@test',
            'fn test_every_row_agrees_with_python_slugify() [io]',
            '    for row in rows()',
            '        let (title, expected) = row',
            '        test.case(title)',
            '        test.assert_eq(slugmake.slugify(title, plain()).slug, expected)',
            '']
    open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
    subprocess.run(['novo', 'fmt', OUT], check=True, stdout=subprocess.DEVNULL)
    print('%d rows' % len(everything))


if __name__ == '__main__':
    main()
