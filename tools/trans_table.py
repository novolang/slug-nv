#!/usr/bin/env python3
"""Write the compiled transliteration table at the end of src/slugtrans.nv.

The answers are deunicode's (BSD-3-Clause; Copyright (c) 2015 Amit
Chowdhury, 2018-2021 Kornel Lesinski, 2020-2021 Hunter WB), version
1.6.0, read from `src/mapping.txt` and `src/pointers.bin` of the crate,
for the blocks the compiled tier covers.  A character deunicode does
not know is left out.  OVERRIDES replaces a few answers, each for the
reason given beside it.  Everything from the line
`// The compiled table.` to the end of src/slugtrans.nv is replaced,
and the file is passed through `novo fmt` afterwards.

The script prints the table's size and a checksum, which
tests/slugtable_tests.nv asserts.

Run from the package root:
    python3 tools/trans_table.py [deunicode-1.6.0 directory]
With no argument the crate is fetched from crates.io.
"""
import io
import subprocess
import sys
import tarfile
import urllib.request

VERSION = '1.6.0'
URL = 'https://crates.io/api/v1/crates/deunicode/%s/download' % VERSION
MARK = '// The compiled table.'
TARGET = 'src/slugtrans.nv'

# The blocks of the compiled tier: Latin-1 Supplement, Latin
# Extended-A and -B, the combining diacritical marks (so a decomposed
# letter loses its mark), Greek and Coptic, Cyrillic and its
# supplement, Latin Extended Additional, Greek Extended, General
# Punctuation, the currency signs and the letterlike symbols.
RANGES = [(0x00A0, 0x024F), (0x0300, 0x036F), (0x0370, 0x03FF), (0x0400, 0x052F),
          (0x1E00, 0x1EFF), (0x1F00, 0x1FFF), (0x2000, 0x206F), (0x20A0, 0x20CF),
          (0x2100, 0x214F)]

# Danish and Norwegian spell these letters out in ASCII by convention,
# and a Danish reader expects `aa` and `oe` rather than a bare vowel.
DANISH = {0x00C5: 'Aa', 0x00E5: 'aa', 0x00D8: 'Oe', 0x00F8: 'oe'}
# Russian by the BGN/PCGN romanisation without its diacritics and
# apostrophes: deunicode writes `Iu`, `Ia` and `I` and marks the soft
# sign with an apostrophe, which a slug turns into a separator.
RUSSIAN = {0x0401: 'Yo', 0x0419: 'Y', 0x042C: '', 0x042E: 'Yu', 0x042F: 'Ya',
           0x0451: 'yo', 0x0439: 'y', 0x044C: '', 0x044E: 'yu', 0x044F: 'ya'}
# The numero sign is the abbreviation `No`, which deunicode leaves empty.
SYMBOLS = {0x2116: 'No'}
OVERRIDES = {**DANISH, **RUSSIAN, **SYMBOLS}


def crate_files(arg):
    if arg:
        return (open(arg + '/src/mapping.txt', 'rb').read(),
                open(arg + '/src/pointers.bin', 'rb').read())
    data = urllib.request.urlopen(URL).read()
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar:
        root = 'deunicode-%s/src/' % VERSION
        return (tar.extractfile(root + 'mapping.txt').read(),
                tar.extractfile(root + 'pointers.bin').read())


def decoder(mapping, pointers):
    def answer(cp):
        a, b, n = pointers[3 * cp], pointers[3 * cp + 1], pointers[3 * cp + 2]
        if n <= 2:
            return bytes([a, b])[:n].decode('ascii')
        off = a | (b << 8)
        if off + n > len(mapping):
            return None
        return mapping[off:off + n].decode('ascii')
    return answer


def quote(s):
    escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')
    return '"' + escaped + '"'


def main():
    mapping, pointers = crate_files(sys.argv[1] if len(sys.argv) > 1 else '')
    answer = decoder(mapping, pointers)
    rows = []
    for lo, hi in RANGES:
        for cp in range(lo, hi + 1):
            text = OVERRIDES.get(cp, answer(cp))
            if text is None:
                continue
            # A slug is one line; deunicode's line and paragraph
            # separators become spaces.
            text = text.replace('\n', ' ')
            rows.append((cp, text))
    checksum = 0
    for cp, text in rows:
        for ch in text:
            checksum = (checksum * 31 + ord(ch) + cp) % 1000000007
    lines = [MARK, '//',
             '// Written by tools/trans_table.py from deunicode %s, with the' % VERSION,
             '// overrides that script names.  %d characters.' % len(rows), '',
             'const COMPILED: Int = %d' % len(rows), '',
             '// The compiled answer for `ch`, or `None` for a character the',
             '// compiled tier does not cover.',
             'fn compiled(ch: Int) -> ?Str', '    match ch']
    for cp, text in rows:
        lines.append('        0x%04X => Some(%s)' % (cp, quote(text)))
    lines += ['        _ => None', '']
    src = open(TARGET).read()
    head = src[:src.index(MARK)] if MARK in src else src.rstrip('\n') + '\n\n'
    open(TARGET, 'w').write(head + '\n'.join(lines))
    subprocess.run(['novo', 'fmt', TARGET], check=True, stdout=subprocess.DEVNULL)
    print('%d characters, checksum %d' % (len(rows), checksum))


if __name__ == '__main__':
    main()
