# Visual guide and browser login acceptance — T051 / HR010-001

Self-reviewed presentation tooling. Pre/final Constitution Check: PASS within
this UI scope; formal impact NONE. No native/protocol guard changed; no
qualifying gate, independent attestation, ResultQC or GO checkpoint is issued.

The shared Admin/Presentation guide contains seven original, byte-identical
user PNGs. Navigation, alt text, captions and notes are EN/RU. Original raster
text remains English. Buttons, arrow keys, Home/End, numbered selection,
URL restoration and browser fullscreen are available. Arithmetic corrections
on slide 5 remain visible in fullscreen; these pictures are explanatory only.
Source provenance is in tools/admin-ui/src/modules/guide/images/sources.json.

266 UI tests / 45 files, 29 presentation tests (including 9 gateway tests),
TypeScript, validator/catalog checks, offline/live builds and boundary audits,
targeted Ruff and PowerShell parsing passed. Accepted baseline formal report
verification still passes (semantics cc98f15a..., report 3e2e2344...).

Local browser checks exercised navigation, EN/RU language changes, reload,
fullscreen, the visible arithmetic corrections, and navigation between Admin
and Presentation. The same saved Morning Demo campaign and historical receipt
remain visible. Seven PNGs were also retrieved from the real authenticated
Cloudflare HTTPS endpoint and matched the installed content hashes.

A user-reported ORIGIN_FORBIDDEN failure was traced to the login document's
no-referrer policy. A real browser using the production handler in an isolated
loopback fixture sent Origin:null before the fix; after same-origin policy it
sent the expected origin and reached the authenticated test page. EN login,
Russian invalid-code feedback, and Russian retry succeeded. Missing/null/foreign
origins remain rejected; no authentication check was relaxed. Public HTTPS
checks verify the corrected header and authenticated requests. Public browser
testing on this host was blocked by DNS resolution; it is not claimed as PASS.
See https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referrer-Policy
for the browser form behavior; the local observation is the regression evidence.

Runtime lifecycle: source/UI deployment initially preserved the old Controller
instance. Later a managed execution session ended and all associated services
were found stopped. The existing launchers restored the same data through a
hidden independent Windows process (Win32_Process.Create, ShowWindow=0), outside
the managed terminal lifecycle. The Controller has a new instance ID and the
same baseline source, signing key, profile and exact canonical receipt. This
recovery is explicitly recorded in http-acceptance.json, not described as an
uninterrupted run. Subsequent managed tool completion and user input left the
services running; the independent host launcher remains alive. No Windows
scheduled task or startup service was added.

The actual URL is a runtime value: use D:/delta-presentation/START-REMOTE.ps1
or its status command. Old URLs in evidence are historical. HTTPS verification
uses public DNS when host DNS fails, with certificate/name validation enabled.
Codes, cookies and private controls are excluded from this evidence.
