# slug-nv

A slug is the human-readable part of a URL: the `hello-world` in
`/posts/hello-world`. Making one means turning a title into a string
that is safe in a path, readable, and different from every other slug
the site already serves. This package does that for novo-lang. The
transliteration answers come from
[`deunicode`](https://docs.rs/deunicode), itself derived from Perl's
[`Text::Unidecode`](https://metacpan.org/pod/Text::Unidecode), and the
heading-anchor rule is GitHub's. It is built on
[unicode-nv](https://novo-lang.org/packages/unicode-nv).

## What it is

**Slugging** a title is four steps. Characters outside the target
alphabet are **transliterated**, which means replaced by the letters
that approximate them: `å` becomes `aa`, `ß` becomes `ss`, `Ю` becomes
`Yu`. What is left is lowercased. Runs of anything that is not a letter
or a digit collapse to a **separator**, usually a hyphen. The result is
trimmed and, if the caller set a limit, truncated.

A **policy** is all of those choices as one value: the separator, the
case rule, whether to keep non-ASCII letters, the length limit, where
truncation cuts, what to answer when nothing survives, and whether to
expand `&` into a word.

A character that the transliteration table does not cover is
**dropped**. Dropping is the failure that looks like a success: a
thirty-character title in an uncovered script comes out as the three
ASCII characters it happened to contain, which is a slug that routes
and means nothing.

Two facts about a slug live in the application rather than in the
title. A slug is **reserved** when the route table already mounts that
word, so a post titled "New" that slugs to `new` is unreachable behind
the `/new` route. A slug is **taken** when another page already has it,
which is what `Hello, World!` and `hello world` both do.

An **anchor** is the same operation applied to a heading, so that a
table of contents can compute the fragment the renderer will emit.

## Install

```
novo pkg add slug-nv
```

## Example

```novo
use slugpolicy
use slugmake
use slugroute

// The store's answer to "does anything already have this slug".
fn not_taken(candidate: Str) -> Bool
    false

// The route table's answer to "is this one of my own words".
fn is_reserved(candidate: Str) -> Bool
    slugroute.reserved_in(slugroute.common_reserved(), candidate)

fn main() [io]
    // Slug a title on its own. This never fails and never answers the
    // empty string; anything that went wrong is in `notes`.
    let outcome = slugmake.slugify("Hello, World!", slugpolicy.url_policy())
    println(outcome.slug)
    if slugmake.needs_attention(outcome)
        println("the slug lost something the title carried")

    // The same title as a permalink: kept off the route table's own
    // words, and numbered against what the store already holds.
    let resolved = slugroute.resolve("Hello, World!", slugpolicy.url_policy(),
                                     is_reserved, not_taken)
    println(resolved.slug)
```

Build and test with `novo pkg build` and `novo test`.

## What the package contains

| Module | Contents |
| --- | --- |
| `slugpolicy` | Every choice a slug generator makes, as one value, with three named policies. |
| `slugtrans` | The transliteration table in two tiers, the script a character belongs to, and the symbol word list. |
| `slugmake` | Slugging a title, and the notes saying what it cost. |
| `slugroute` | Reserved words, collisions, the numbering, and slugging a list of headings in document order. |

## How to choose an entry point

**`slugmake.slugify` is the whole of it for a caller with no route
table.** A title and a policy in, a slug and its notes out.
`slugify_into` appends to a buffer you own.

**`slugroute.resolve` is what a permalink wants.** It slugs, checks the
result against the reserved predicate, then numbers it against the
taken predicate.

**`slugroute.number_in_order` slugs a whole list at once.** It is the
call a page's table of contents makes: every heading in document order,
with duplicates numbered as they appear.

**`slugmake.slugify_unicode` keeps letters in any script.** It is the
one function here that takes a `UniData`, because normalising and case
mapping outside ASCII are that table. See rule 8.

**`slugmake.slugify_with` takes a transliteration table you chose.**
Use it with `slugtrans.table_from_bytes` when the compiled-in Latin
table is not enough.

**`slugpolicy.github_policy()` is a compatibility claim, not a
preference.** Use it for heading anchors, so a table of contents
computes the fragment GitHub renders for an ASCII heading.
`url_policy()` collapses every run of punctuation to one hyphen, trims
the ends, limits the length and expands symbols, for permalinks.
`unicode_policy()` keeps non-ASCII letters.

## The rules a user needs

1. **`slugify` cannot fail and never answers the empty string.** When
   nothing survives, the answer is `SlugPolicy.empty_fallback`, which
   defaults to `n-a`, and `SlugNoteEmptyInput` is reported. An empty
   slug is a URL that collides with the index page, and the reference
   implementations all return one.
2. **Read the notes, or at least call `needs_attention`.** It is true
   for exactly the two notes that look like success from the slug
   alone: the input that produced nothing, and the input that was
   partly dropped.
3. **Notes are a list because several things happen at once.** A long
   Cyrillic title colliding with an existing post is transliterated,
   truncated and suffixed. An enum could report one of the three.
4. **A slug is not a function of the title alone.** `slugroute.resolve`
   takes the reserved and taken predicates as functions the caller
   supplies. A list of reserved words shipped by this package would be
   stale on the day it published and wrong for every application that
   mounted one more route. `common_reserved()` is a starting point and
   says so.
5. **The second occurrence is numbered `-2`, not `-1`.** The first
   carries no suffix, so a `-1` would imply a `-0` somewhere. This is
   the numbering of the novo-lang Markdown renderer's heading anchors.
   GitHub's renderer numbers duplicates from `-1`.
   `SlugResolved.suffix` is 0 when nothing collided, and
   `slugroute.split_suffix` reads a suffix of 2 to 999 back.
6. **A character maps to a string, not to a character.** `ß` is `ss`,
   `æ` is `ae`, `Ю` is `Yu`, `№` is `No`. A table mapping character to
   character would have had to drop all four. The answers are
   deunicode's, except that Danish and Norwegian `å` and `ø` are `aa`
   and `oe`, Russian follows the BGN/PCGN romanisation without its
   diacritics and apostrophes, and `№` is `No`.
7. **The transliteration table is tiered.** `latin_table()` is compiled
   in and covers the European alphabets. `table_from_bytes` takes the
   rest as bytes the host read, which is how a `core` package reaches
   a large table without performing any input. `slugtrans.covers`
   answers whether a given table knows a character, and
   `uncovered_count` answers how much of a title it would drop. A
   loaded table answers from its own entries first and from the
   compiled tier after.
8. **Only `slugify_unicode` takes a `UniData`.** The signature is the
   disclosure that NFC normalisation and non-ASCII case mapping cost
   the 245 KB Unicode table. The ASCII path uses this package's own
   table and needs nothing from unicode-nv.
9. **Han is transliterated by a table that cannot be right.** 行 is
   `xing` or `hang` in Mandarin depending on the word, and `gyou`, `kou`
   or `an` in Japanese. The extended table carries Unidecode's single
   answer. `slugtrans.script_of` reports `SlugScriptHan` so a caller can
   check before trusting the output, and a CJK site probably wants
   `SlugModeUnicode` with a percent-encoded path instead.
10. **Symbol expansion is a language decision.** `&` is `and` in
    English and `und` in German, so the list is data rather than part
    of the transliteration table. `slugtrans.word_substitutions` is the
    English list and `word_substitutions_for` takes a language tag.
    `SlugPolicy.expand_symbols` turns it on.
11. **`SlugTruncateWord` cuts at the last separator before the limit.**
    `SlugTruncateCluster` cuts at the limit exactly, on a grapheme
    cluster boundary. The limit is counted in grapheme clusters, and 0
    means no limit.
12. **A Unicode slug is a valid path segment, not a valid host
    label.** A host label is a different grammar with a 63-byte limit
    that `max_len` does not model.
    [punycode-nv](https://novo-lang.org/packages/punycode-nv)'s
    `punyidna.host_to_ascii` is the wire form for a hostname.
13. **`slugmake.is_canonical` checks that a string is already what a
    policy would produce.** It is how a compatibility claim becomes a
    test rather than a comment. `slugpolicy.same_output` compares two
    policies. A slug is its own slug under the policy that made it.
14. **`slugroute.collides_on_case` answers whether two slugs differ
    only by case.** A path is case-sensitive on most servers and
    case-insensitive in most people's heads, which is why every named
    policy lowercases.
15. **`SlugPolicy.collapse_runs` chooses between two punctuation
    rules.** On, every run of characters that are not letters or digits
    becomes one separator: `Rust & C++` is `rust-c`. Off is GitHub's
    rule: each space is one separator, a hyphen and an underscore are
    kept, and other punctuation is removed, so `Rust & C++` is
    `rust--c`.
16. **Only `slugify_unicode` lowers a letter outside ASCII.** `slugify`
    under `unicode_policy()` keeps the letters of any script but has no
    case tables, so `Мир` stays `Мир`.

## What is not included

- **Reading a database, a filesystem or a clock.** The two facts a slug
  generator cannot know arrive as predicates the caller supplies.
- **A shipped list of reserved route names.** See rule 4.
- **Punycode and IDNA.** See rule 12.
- **Percent-encoding.** A slug under `SlugModeAscii` needs none. A
  Unicode slug that has to go into a URL is percent-encoded by whatever
  builds the URL.
- **Running on a microcontroller.** The package makes no such claim and
  carries no device probe. A slug is a new string by construction,
  because transliterating one character can produce two, the notes are
  a list, and the extended table is a blob a host read. Firmware that
  wants a filename-safe key wants a fixed-buffer function over a byte
  range, which would be a different surface.
- **A full Unicode transliteration table compiled in.** `deunicode`
  covers essentially all of Unicode in about 500 KB, most of it Han
  romanisation. A site slugging English and Danish headings should not
  link it.

## Related packages

- [unicode-nv](https://novo-lang.org/packages/unicode-nv) is the only
  dependency, and only the Unicode-preserving mode pays for it. Its
  `uclass` predicates take a codepoint and no table, and they are what
  "keep the letters" means past ASCII.
- [punycode-nv](https://novo-lang.org/packages/punycode-nv) encodes a
  hostname label. This package does not depend on it; a caller that
  needs a host label calls it directly.
- [markdown-nv](https://novo-lang.org/packages/markdown-nv) generates
  heading anchors as part of rendering. A table of contents built with
  `github_policy()` computes the same fragments.
- [i18n-nv](https://novo-lang.org/packages/i18n-nv) is message
  catalogues and plural rules. It is the package for text a person
  reads, where this one is for text a router reads.

## Tests

```bash
novo test tests/slugtrans_tests.nv      # the table, its tiers and its scripts
novo test tests/slugmake_tests.nv       # the pipeline and every note
novo test tests/slugroute_tests.nv      # reserved words, collisions, numbering
novo test tests/slugtable_tests.nv      # the compiled table, the README's rules, every policy field
novo test tests/differential_tests.nv   # 305 titles against python-slugify
bash tests/coverage.sh                  # line coverage over src/, merged across the suites
```

The references are deunicode for the transliteration answers,
python-slugify for the pipeline, and GitHub's heading-anchor rule for
`github_policy`. The suites check these things:

- The compiled table holds the 1,696 answers `tools/trans_table.py`
  wrote from deunicode 1.6.0 and its overrides, checked by count and
  checksum, and the README's own examples: `å` is `aa`, `ß` is `ss`,
  `Ю` is `Yu`, `№` is `No`.
- 305 titles, five of them the examples in python-slugify's README and
  the rest seeded titles whose every character has the same answer in
  both tables, give python-slugify's slug under `url_policy()` without
  its symbol expansion and length limit. `tools/differential.py`
  writes that suite.
- Every named policy answers its own slug unchanged, an all-emoji title
  answers the fallback rather than the empty string, a title partly
  outside the table reports how much was dropped, a truncation cuts at
  a word boundary and keeps the full slug in its note, the second
  collision is numbered 2, and a reserved word is refused before a
  collision is checked.

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
