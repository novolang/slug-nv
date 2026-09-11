# Changelog

All notable changes to slug-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## 0.0.1 — 2026-09-11

The **interface**: every signature and every effect row, and no bodies.
`stability = "draft"`, and the release is recorded `implemented = false`.

### Added

- `slugpolicy` — every arbitrary choice as a value, with
  `github_policy`, `url_policy` and `unicode_policy` as compatibility
  claims rather than defaults somebody liked, and `is_canonical` and
  `same_output` as the checks a migration makes.
- `slugtrans` — the transliteration table in two tiers: a compiled
  Latin, Greek and Cyrillic one, and everything else parsed from bytes
  a host read. `script_of` and `covers` so a caller can ask before it
  trusts the output.
- `slugmake` — `SlugOutcome`, a slug that is always usable and a list
  of notes saying what it cost.
- `slugroute` — the reserved set and the taken set as named predicates,
  and GitHub's duplicate numbering.

### Known

- **`SlugOutcome` is the load-bearing interface, and `slug` is never
  the empty string.** Every reference implementation answers `""` for
  an input it could not slug, and the URL that produces is the index
  page's.
- **`SlugNoteDropped` is the note nobody else reports**: a title in an
  uncovered script produces a slug that is not empty, routes, and is
  useless.
- **A slug is not a function of the title alone.** Reserved and taken
  are both facts in a database, so they arrive as `fn(Str) -> Bool`.
- **The second occurrence is `-2`, not `-1`**, because the first
  carries no suffix — GitHub's numbering, and the site generator's.
- **A character maps to a `Str`**: `ß` is `ss`, `Ю` is `Yu`.
- **Han is named rather than approximated.** `Text::Unidecode` picks
  one romanisation and is wrong about half the time; the script is
  askable and a CJK site wants the Unicode mode instead.
- **Only `slugify_unicode` takes `UniData`**, and the signature is the
  disclosure: the ASCII path needs nothing from unicode-nv.
- **punycode-nv is named, not depended on.** A slug is a path segment;
  a host label is a different grammar with a 63-byte limit.
- **`@tier(embedded)` is not claimed** — a slug is a new string by
  construction, and a device variant would be a different surface.
