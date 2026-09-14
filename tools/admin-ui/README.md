# Delta Admin UI

Delta Admin UI is an optional, browser-local static tool. It opens user-selected
JSON, performs structural JSON Schema validation, keeps edits in memory, and creates
a new file only after an explicit **Download new file** action.

The primary workflow is a guided controller form over one `DocumentDraft`. The form
patches known paths without rebuilding the JSON, so schema-allowed unknown values
remain intact. Pairwise answers and evidence are session-local presentation data and
are not added to the exported document without a reviewed mapping supported by the
selected schema. **Advanced JSON** is hidden by default and read-only.

It is not part of Delta core/runtime. It has no backend, login, credential flow,
analytics, automatic network requests, live Delta API, state-changing operation,
or authority to compute governance or protocol outcomes.

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

At viewport widths up to 900 px, primary navigation is available from the keyboard-
accessible **Menu** control in the top bar rather than being removed with the sidebar.

## Verification

Run the complete UI gate from this directory:

```powershell
npm run check
npm run audit:repository
npm audit --audit-level=high
npm run test:browser
```

`audit:repository` verifies that protected Delta components are unchanged and have
no reverse dependency on this package. The offline audit is part of `npm run check`.
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
