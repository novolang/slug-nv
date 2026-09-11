# slug-nv

**Status: NOT IMPLEMENTED — interface only.**

Every public function below is published with its signature and its
effect row, and every body is `todo()`. Installing this package works;
calling it panics with `not implemented`.

## What this is

URL slugs, sans-IO: a title in, a slug a route table can actually use
out, and a list of notes saying what it cost.

- `slugpolicy` — every arbitrary choice a slug generator makes, as a
  value, with three named policies that are compatibility claims;
- `slugtrans` — the transliteration table, in two tiers, and where it
  stops;
- `slugmake` — `SlugOutcome`: the slug, and the notes;
- `slugroute` — the two facts a slug generator cannot know, and the
  numbering that has to match the renderer's.

```
novo pkg add slug-nv
novo pkg build
novo test
```

## The one example that will work

```novo ignore
use slugpolicy
use slugroute

// A post's permalink: slugged, kept off the route table's own words,
// and made unique against what the store already has.
fn permalink(title: Str, reserved: fn(Str) -> Bool, taken: fn(Str) -> Bool) -> Str
    slugroute.resolve(title, slugpolicy.url_policy(), reserved, taken).slug
```

## The load-bearing interface: `SlugOutcome`

```novo ignore
pub struct SlugOutcome
    slug: Str             // ALWAYS USABLE. Never empty.
    notes: [SlugNote]
```

`slugify` cannot fail, and it never answers the empty string. Every
problem is a note beside a slug the caller can already publish.

That is worth designing around rather than returning a `Str`, because
every reference implementation answers `""` for an input it could not
slug — `python-slugify("🎉🎉🎉")` is `""`, and so is the `slug` crate's
answer for a title in a script its table does not cover. The URL that
produces is the index page's, so the post overwrites the listing, and
nothing anywhere says so. `SlugPolicy.empty_fallback` makes that
impossible and `SlugNoteEmptyInput` makes it visible.

**`SlugNoteDropped` is the note nobody else reports, and it is the
argument for notes being a list.** A thirty-character title in a script
the loaded table does not cover comes out as the three ASCII characters
it happened to contain. That is a slug — not empty, unique, routes —
and it is useless, and the site owner hears about it from a reader.
`slugmake.needs_attention` is true for exactly the two notes that look
like success from the slug alone.

The notes are a **list** because several things happen at once: a long
Cyrillic title colliding with an existing post is transliterated,
truncated *and* suffixed, and an enum could report one of the three.

## The second decision: a slug is not a function of the title alone

Two facts are missing from every library that takes only a string, and
both live in a database this package cannot reach:

**Reserved.** A route table has words that are not posts — `/new`,
`/edit`, `/admin`, `/api`, and whatever else that application mounted.
A post titled "New" slugs to `new`, the literal route matches first,
and the post is unreachable for the life of the site.

**Taken.** `Hello, World!` and `hello world` both give `hello-world`,
and so do a post and its own translation. A generator that ignores that
overwrites a page.

So `slugroute.resolve` takes both as `fn(Str) -> Bool` — named
functions the caller supplies, the same shape cookie-nv uses for the
Public Suffix List and for the same reason: a list this package shipped
would be stale the day it published and wrong for every application
that mounted one more route. `common_reserved()` exists as a starting
point and its doc comment says it is not the answer.

The numbering is GitHub's and this project's site generator's: the
second occurrence is `-2`, not `-1`, because the first carries no
suffix and a `-1` implies a `-0` somewhere.

## The third: the transliteration table is tiered

`deunicode` — itself Perl's `Text::Unidecode` — covers essentially all
of Unicode in about 500 KB, most of it Han romanisation. A site
generator slugging English and Danish headings should not link 500 KB
to turn `å` into `aa`. So:

| tier | size | scripts |
| --- | --- | --- |
| `latin_table()`, compiled in | ~6 KB | Latin-1 Supplement, Latin Extended-A, the used part of Extended-B, Latin Extended Additional, Greek and Coptic, Cyrillic |
| `table_from_bytes(blob)` | the rest | Hebrew, Arabic, Devanagari, Georgian, Armenian, Thai, Kana, Han |

The compiled tier is every European language written in an alphabet.
The rest arrives as bytes **the host read**, because a `core` package
reads nothing — which is also what lets a program pick its tier at run
time rather than at link time. It is the same split unicode-nv makes,
for the same reason.

**Han is named rather than approximated.** 行 is `xing` or `hang` in
Mandarin depending on the word, and `gyou`, `kou` or `an` in Japanese.
`Text::Unidecode` picks one and is wrong about half the time. The
extended table carries Unidecode's answers, `SlugScriptHan` is a script
a caller can ask about before trusting the output, and a CJK site
almost certainly wants `SlugModeUnicode` and a percent-encoded path
instead.

A character maps to a **`Str`**, not a character: `ß` is `ss`, `æ` is
`ae`, `Ю` is `Yu`, `№` is `No`. A table that mapped character to
character would have had to drop all four.

## The Unicode-preserving mode, and punycode

`slugmake.slugify_unicode` keeps letters in any script and normalises
to NFC, for a site that serves `/статьи/первая-запись` on purpose.

It is **the one call that takes `udata.UniData`**, and the signature is
the disclosure: NFC normalisation and case mapping outside ASCII *are*
that 245 KB table. The ASCII path needs nothing from unicode-nv at all,
and it is the path a site generator takes for every heading it slugs.

Its output is a valid path **segment**. It is not a valid hostname
label — punycode-nv's `punyidna.host_to_ascii` is the wire form for
that, and this package does not encode it, because a host label is a
different grammar with a 63-byte limit `max_len` does not model.

## The named policies are compatibility claims

`github_policy()` produces the same bytes as GitHub's heading anchors
and as this project's own renderer. That matters because a table of
contents computes the fragment the renderer will emit, and if the two
disagree every link in the index is dead. A policy is the right shape
for a claim like that: it can be tested against a corpus, and it does
not move when somebody improves the default.

`url_policy()` is what a permalink wants — GitHub's, plus an 80-cluster
limit that cuts at a word boundary and the symbol expansions, because a
post titled `Rust & C++` should be `rust-and-c-plus-plus` and not
`rust-c`.

Symbol expansion is a **language** decision, not a script one — `&` is
`und` in German — so the list is data (`slugtrans.word_substitutions`)
and a caller passes its own.

## The layer, and why

`core`. A slug is arithmetic over a string the caller already holds.
The two things a slug generator is usually asked to know about the
world arrive as predicates, so nothing here reads a database, a
filesystem or a clock. There is no effect-polymorphic function: a title
is a value, not a stream.

## `@tier(embedded)` is not claimed

There is no device consumer. A slug is a new string by construction —
transliterating one character can produce two — the notes are a list,
and the extended table is a blob a host read. A firmware that needed a
filename-safe key would want a fixed-buffer `slugify_into` over a byte
range, which is a different surface rather than an annotation on this
one. The honest form is the absence of the claim.

## The reference implementation

`deunicode` (and `Text::Unidecode` behind it) for the transliteration
answers; `python-slugify` and the `slug` crate for the pipeline and its
test suite; GitHub's heading-anchor algorithm for `github_policy` and
for the duplicate numbering. Where the references disagree the test
case says which one this package follows.

## Dependencies

`unicode-nv ^0.0.1`, and **only the Unicode-preserving mode pays for
it**: `slugify_unicode` takes a `udata.UniData` in its signature, and
`uclass`'s predicates — which take a codepoint and no table — are what
"keep the letters" means past ASCII. The ASCII path uses this package's
own table and nothing else.

punycode-nv is named and not depended on: a slug is a path segment, a
host label is a different grammar, and the caller that needs one calls
`punyidna.host_to_ascii` itself.

## The consumers, and what adopting this would take

**`orbit/static-site-generator`** is the consumer this package is
measured against, and it has the whole problem already, hand-written in
`src/main.nv`:

- `slug_heading(t: Str) -> Str` (24 lines) is `github_policy` applied
  to one string. Its own comment says it **must stay byte-identical to
  the renderer's charmap in `bin/novo_rt.c`** — which is exactly the
  compatibility claim `slugpolicy.is_canonical` and the named policy
  exist to make testable rather than to leave as a comment.
- `nth_suffix(seen: [Str], slug: Str) -> Str` is `slugroute.unique`
  over a list, and the caller keeps the `seen` array by hand. The whole
  loop — every heading in a page, numbered in document order — is
  `slugroute.number_in_order`.
- Neither reports anything. A heading in Japanese, or one that is only
  an emoji, currently produces an empty fragment, and the generator
  writes `<h2 id="">`. That is the `SlugNoteEmptyInput` case, and it is
  live in the tree today.

Adopting it deletes both functions and closes that gap; the policy is
`github_policy()` and the compatibility claim becomes a test.

**`orbit/website`** and the registry's package pages want the same
thing for their own headings, and `url_policy` for the permalinks.

**novim** and **novoterm** are not consumers.

## What a row wanted to widen

Nothing. Every function here is `[]`.

Two things the plan's row did not anticipate:

**"URL slugs for the site generator" is one policy, not the package.**
The row implies a function; what the consumer actually has is two
functions, a compatibility constraint against a C renderer, and a
collision loop with its own state. The package is shaped around that,
and `slugpolicy` exists because the alternative — a default somebody
liked — cannot carry a compatibility claim.

**The transliteration table is the package's biggest open question,
and it is a data question rather than an interface one.** The tier
split is in the interface (`SlugTable`, `latin_table`,
`table_from_bytes`, `covers`, `script_of`), but the actual 6 KB of
compiled table and the blob format are the implementation lane's, and
the size of the compiled tier is the number to revisit at 0.1.0: if
Greek and Cyrillic push it past what an embedded-adjacent consumer
would tolerate, the split moves to Latin-only compiled and everything
else in the blob, with no signature changing.

## The surface

| module | `pub fn` | `pub struct` | `pub enum` | `pub alias` |
| --- | --- | --- | --- | --- |
| `slugpolicy` | 7 | 1 | 3 | — |
| `slugtrans` | 12 | 1 | 1 | — |
| `slugmake` | 11 | 1 | 1 | — |
| `slugroute` | 10 | 1 | — | 2 |
| **total** | **40** | **4** | **5** | **2** |
