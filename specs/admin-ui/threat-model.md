# Threat Model: Browser-local JSON MVP

## Assets and boundary

The MVP processes user-selected JSON documents and schema bytes in the browser.
Those bytes, every string inside them, filenames, URLs, references, and future
fixture content are untrusted. The protected assets are browser availability,
document confidentiality and integrity, the original local file, and an operator's
ability to distinguish local data from governance or Delta authority.

## Mandatory MVP limits

Limits are checked before or during bounded parsing/validation. Exceeding any limit
returns a typed, non-crashing error and no partial authority/result claim.

| Input property | Maximum |
| --- | ---: |
| JSON or schema file size | 5 MiB (5,242,880 bytes) |
| JSON nesting depth | 64 levels |
| Aggregate object/array/value nodes | 100,000 |
| Individual UTF-8 string value | 1 MiB (1,048,576 bytes) |
| Displayed or actionable URL length | 2,048 characters |

Archive/compressed input is not accepted. Base64-looking content is never decoded
automatically and remains subject to the string and document limits.

## Required controls

- Parse data only as JSON; never use `eval`, dynamic code generation, template
  execution, or executable deserialization.
- Render all document/schema strings as inert text. Never inject them as raw HTML,
  CSS, script, SVG markup, Markdown HTML, or framework template source.
- Do not fetch URL values, previews, images, scripts, styles, or remote schemas.
- Do not resolve external `$ref`. Only frozen bundled schemas or resources explicitly
  selected by the user in the same local session may be resolved.
- Render URLs as text by default. A link may become actionable only after explicit
  user action, parsing through the platform URL parser, and an allowlist permitting
  `https:`. Reject credentials in URLs and all other schemes for MVP.
- Keep processing bounded and cancellable enough that a rejected or expensive
  document does not make the shell unusable.
- Do not put document contents, schema contents, custody metadata, public-key bodies,
  URLs, or evidence references into analytics, telemetry, or exception reports.
- Export only after explicit user action, to a new download. Never silently overwrite,
  autosave, or write back to the selected source.

## Security test cases

The implementation suite covers every limit boundary, deeply nested arrays/objects,
node-count expansion, very long strings, Base64-like values, HTML/script strings,
event-handler text, `javascript:`/`data:`/credential-bearing URLs, remote `$ref`,
malformed UTF-8 input, and repeated validation cancellation/recovery.

## Deferred surfaces

Authentication, authorization, backend/API traffic, CORS/CSRF, session management,
remote persistence, live events, and state-changing commands are out of MVP scope.
Adding any of them requires a new integration threat model and formal-impact review.
