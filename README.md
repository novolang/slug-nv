# slug-nv

A slug is the human-readable part of a URL: the `hello-world` in
`/posts/hello-world`. Making one means turning a title into a string
that is safe in a path, readable, and different from every other slug
the site already serves. This package does that for novo-lang. The
transliteration answers come from
[`deunicode`](https://docs.rs/deunicode) and Perl's
[`Text::Unidecode`](https://metacpan.org/pod/Text::Unidecode) behind it,
and the anchor algorithm is GitHub's. It is built on
[unicode-nv](https://novo-lang.org/packages/unicode-nv).

**Status: NOT IMPLEMENTED — interface only.** Every function is declared
with its full signature, but every body is a `todo()` that panics when
called. The package is published so its design can be reviewed and
depended on before it is implemented. Version 0.1.0 will be the first
working release.

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

Build and test with `novo pkg build` and `novo test`. Today `novo test`
fails on purpose: every test reaches a
`not implemented: slug-nv.<module>.<fn>` panic. The tests are the
specification the implementation will have to satisfy.

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
preference.** Use it for heading anchors, so a table of contents and a
renderer agree. `url_policy()` is that plus a length limit and symbol
expansion, for permalinks. `unicode_policy()` keeps non-ASCII letters.

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
   GitHub's numbering and this project's site generator's.
   `SlugResolved.suffix` is 0 when nothing collided.
6. **A character maps to a string, not to a character.** `ß` is `ss`,
   `æ` is `ae`, `Ю` is `Yu`, `№` is `No`. A table mapping character to
   character would have had to drop all four.
7. **The transliteration table is tiered.** `latin_table()` is compiled
   in and covers the European alphabets. `table_from_bytes` takes the
   rest as bytes the host read, which is how a `core` package reaches
   a large table without performing any input. `slugtrans.covers`
   answers whether a given table knows a character, and
   `uncovered_count` answers how much of a title it would drop.
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
13. **`slugpolicy.is_canonical` checks that a string is already what a
    policy would produce.** It is how a compatibility claim becomes a
    test rather than a comment. `same_output` compares two policies.
14. **`slugroute.collides_on_case` answers whether two slugs differ
    only by case.** A path is case-sensitive on most servers and
    case-insensitive in most people's heads, which is why every named
    policy lowercases.

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

The references are `deunicode` and `Text::Unidecode` behind it for the
transliteration answers, `python-slugify` and the Rust `slug` crate for
the pipeline and its test suite, and GitHub's heading-anchor algorithm
for `github_policy` and the duplicate numbering. Where the references
disagree, the test case names the one this package follows.

```bash
novo test tests/slugtrans_tests.nv   #  8 tests: the table, its tiers and its scripts
novo test tests/slugmake_tests.nv    # 11 tests: the pipeline and every note
novo test tests/slugroute_tests.nv   #  7 tests: reserved words, collisions, numbering
```

The suite asserts that an all-emoji title answers the fallback rather
than the empty string, that a title partly outside the table reports
how much was dropped, that `ß` becomes `ss` rather than being dropped,
that a truncation cuts at a word boundary and keeps the full slug in
its note, that the second collision is numbered 2, that a reserved word
is refused before a collision is checked, and that
`github_policy()` output is canonical under itself.

The tests compile today and fail at run, each on the
`not implemented: slug-nv.<module>.<fn>` panic that is its body. That
is the expected state of an interface release. They turn green one at a
time as bodies land.

## Implementation status

Nothing is implemented. The table lists the surface an implementation
has to fill.

| Item | Implemented |
| --- | --- |
| `slugpolicy.github_policy`, `.url_policy`, `.unicode_policy` | no |
| `slugpolicy.with_separator`, `.with_max_len`, `.same_output`, `.is_canonical` | no |
| `slugtrans.latin_table`, `.table_from_bytes`, `.pack_bytes`, `.covers` | no |
| `slugtrans.script_of`, `.script_is_compiled`, `.uncovered_count` | no |
| `slugtrans.char_ascii`, `.transliterate`, `.transliterate_into` | no |
| `slugtrans.word_substitutions`, `.word_substitutions_for` | no |
| `slugmake.slugify`, `.slugify_with`, `.slugify_with_words`, `.slugify_unicode`, `.slugify_into` | no |
| `slugmake.is_clean`, `.needs_attention`, `.dropped_count` | no |
| `slugmake.truncate_at`, `.tidy`, `.join` | no |
| `slugroute.resolve`, `.resolve_with`, `.number_in_order` | no |
| `slugroute.unique`, `.unique_numbered`, `.split_suffix` | no |
| `slugroute.common_reserved`, `.reserved_in`, `.is_safe_segment`, `.collides_on_case` | no |

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
