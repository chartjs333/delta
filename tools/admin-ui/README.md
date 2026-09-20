# Delta Admin UI

Delta Admin UI is an optional, browser-local static tool. It opens user-selected
JSON, performs structural JSON Schema validation, keeps edits in memory, and creates
a new file only after an explicit **Download new file** action.

The primary workflow is a guided controller form over one `DocumentDraft`. The form
patches known paths without rebuilding the JSON, so schema-allowed unknown values
remain intact. Pairwise answers and evidence are session-local presentation data and
are not added to the exported document without a reviewed mapping supported by the
selected schema. **Advanced JSON** is hidden by default and read-only.

It is not part of Delta core/runtime and has no authority to compute governance or
protocol outcomes. The default artifact remains an offline-only static application.
A separately built HTTP-live entry can submit declarative Step 5C intents to the
same-origin Controller host; it never holds a signing key, bearer token, worker
handle, or consensus authority.

## Opt-in local startup

Nothing starts this UI from the repository root, node, worker, or native runtime.
An operator must opt in from this directory:

```powershell
cd tools/admin-ui
npm ci --ignore-scripts
npm run dev -- --host 127.0.0.1
```

Open the localhost URL printed by Vite. The server only supplies development
assets; the application performs its document workflow entirely in the browser.
Do not expose this MVP as a remote administration service: it intentionally has no
authentication or authorization surface.

For reviewable static assets:

```powershell
cd tools/admin-ui
npm ci --ignore-scripts
npm run build
```

The output is `tools/admin-ui/dist/`. Its relative Vite base permits serving the
files from an explicitly chosen static location. Loading the built application does
not contact Delta, GitHub, schema URLs, analytics, or any other network service.

JSON Schema validation uses AJV standalone code generated at build time. The
production browser bundle does not call `eval` or the `Function` constructor and
does not require CSP `unsafe-eval`. After changing a bundled schema, run
`npm run generate:validators` and commit the regenerated validator; `npm run check`
rejects stale generated code.

## Explicit HTTP-live startup

Live mode is a separate entry and output directory. It is never imported by the
offline `index.html` entry and cannot weaken the offline `connect-src 'none'` CSP.

```powershell
cd tools/admin-ui
npm ci --ignore-scripts
npm run build:live
```

The output is `tools/admin-ui/dist-live/live.html`. Serve it from the same origin
as the Controller HTTP host. Plain HTTP is accepted only when the page host is
exactly `127.0.0.1`; every remote deployment requires HTTPS. Its CSP permits
connections only to `'self'`.

The live adapter calls only relative `/api/v1/...` paths and sends
`X-Delta-Request: 1`. It has no API for a JavaScript token and does not read
cookies, Web Storage, or IndexedDB. In the shipped loopback profile the Controller
derives `AuthenticatedSubject` from the accepted `127.0.0.1` socket peer. A direct
remote browser deployment is not included: the remote Controller API requires a
Bearer header that this untrusted bundle deliberately cannot construct. A future
remote browser deployment therefore needs a separately reviewed same-origin
authentication gateway that owns its browser session and injects the Controller
Bearer credential server-side. The intent's `declared_operator` remains untrusted
client metadata in every profile.

Before exposing live capabilities or making an execution API request, the adapter
performs one same-origin, no-store `GET /readyz` handshake per page session. It
fails closed unless the Controller is `READY`, advertises HTTP protocol
`deltareduce.step5c.http.v1`, contract schema `1.0.0`, the accepted formal semantics
ID, and a lowercase 40-character Git build ID. That public build ID is not a
credential: the adapter caches it only in memory and requires submission admission
lineage, `policy_context.controller_commit`, and terminal receipt
`controller_commit`/`producer_commit` to remain bound to the same runtime build.
Execution status schema/terminal metadata must be coherent, and the full terminal
receipt's RFC 8785 JCS SHA-256 digest must match the digest advertised by status.
Reload the page to establish a new handshake after a Controller restart or upgrade.

For an explicitly selected development session:

```powershell
npm run dev:live
```

Open the printed `http://127.0.0.1:.../live.html` URL. The Controller endpoints
must be served on that same origin. A development reverse proxy, if used, must
preserve that same-origin boundary.

At viewport widths up to 900 px, primary navigation is available from the keyboard-
accessible **Menu** control in the top bar rather than being removed with the sidebar.

## Verification

Run the complete UI gate from this directory:

```powershell
npm run check
npm run check:live
npm run audit:repository
npm audit --audit-level=high
npm run test:browser
```

`audit:repository` verifies that protected Delta components are unchanged and that
they have no reverse dependency on this package. The offline audit is part of `npm run check`;
the live audit verifies the separate CSP, loopback-or-HTTPS rule, same-origin
transport, and absence of script-visible credentials.
`test:browser` builds production assets and exercises desktop/mobile installed Chrome.

The pinned native typecheck uses TypeScript 7.0.2. In a managed runner where that
executable cannot access `/proc/self/exe`, use `npm run check:substitution`, which
runs TypeScript 5.9.3 instead. That result is evidence for a substitution only and
must not be reported as a passed native TypeScript 7 gate.

## Disablement

The UI is disabled by default because no Delta build, test, startup unit, or runtime
configuration references it. To disable an opted-in session:

1. Stop the manually started Vite process.
2. Stop serving any explicitly published static `dist/` assets.
3. Leave Delta nodes, workers, and native processes unchanged; they do not use the UI.

Removing local generated `node_modules/` or `dist/` directories is optional cleanup
and has no effect on Delta state. The source package can remain present and dormant.

## Rollback

Rollback is source-only: revert the Admin UI feature commit, or remove the
`tools/admin-ui/` package and its `specs/admin-ui/` implementation evidence in a
reviewed follow-up commit. No schema migration, protocol rollback, runtime restart,
WAL action, credential rotation, or data repair is required because the MVP never
changes those surfaces.

Documents downloaded from the UI are new local files owned by the operator. Rollback
does not delete them and never overwrites their original source files.
