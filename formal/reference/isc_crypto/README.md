# ISC crypto reference — REFERENCE_ONLY_NOT_PRODUCTION

This isolated target exercises the draft K/E/R/V/M/G bytes in ADR 0014 and
the selected strict pure Ed25519 profile. The continuous ISC-S16-C01 assignment
authorizes reference conformance only. It does not approve the draft for deployment,
assign a formal semantics ID, or implement consensus admission.

`evidence.json` and `probe_library.py` preserve the initial STOP and its public
identity-key witness. The accepted coordinator handoff
`ISC-S16-CONTINUITY-CRYPTO-REMEDIATION.json` permits bounded preparation of the exact
upstream library in a local cache. The earlier pipelined no-download restriction
existed; applying it to this continuous assignment was the worker's interpretation.

`codec.py` contains closed canonical encoders and decoders. Registry checks bind
supplied K/E bytes, IDs, epoch, roles and distinct validators; they do not establish
trust in those supplied objects. `sodium_reference.py` loads an explicit absolute
library path only after its SHA-256 matches a supplied pin, requires version 1.0.22,
and checks canonical nonidentity prime-order A/Rpoint plus S < L before detached
verification. It signs only public synthetic seeds for conformance. No runtime
target imports this directory.

## Reproduce the local library preparation

`library-provenance.json` pins the official 1.0.22 source/MSVC archives, signatures,
upstream source commit, selected DLL member and hash, signing fingerprints and the
actual GPG verification status. Archives and binaries remain in
`.cache/isc-s16-libsodium-1.0.22/` and are not committed.

1. Fetch the four exact asset URLs in `library-provenance.json` into that cache.
   Check each exact length and SHA-256 before continuing; avoid mutable stable/latest.
2. Obtain the public key from <https://doc.libsodium.org/installation> and import
   it with existing GPG into a dedicated cache homedir. Check primary fingerprint
   `54A2B8892CC3D6A597B92B6C210627AABA709FE1` and signing-subkey fingerprint
   `0C7983A8FD9A104C623172CB62F25B592B6F76DA`. Do not use an arbitrary keyserver.
3. Verify both archive signatures using `gpg --no-options --homedir <cache-home>
   --batch --no-auto-key-retrieve --no-autostart --status-fd 1 --verify <archive.sig>
   <archive>`. Require exit zero and VALIDSIG for the pinned signing key. The first
   local import reported an unavailable gpg-agent after importing the public key;
   subsequent public verification with `--no-autostart` succeeded for both archives.
4. Only after verification, extract exactly
   `libsodium/x64/Release/v143/dynamic/libsodium.dll` from the MSVC ZIP into the
   dedicated cache and verify the DLL SHA-256 recorded in provenance. Do not install
   globally or modify PATH. The local package is vendor authenticated; this is not
   a reproducible-build attestation or proof of native binary correctness.

## Run

From the repository root in PowerShell, with the verified cache present:

```powershell
$env:ISC_SODIUM_DLL = (Resolve-Path '.cache/isc-s16-libsodium-1.0.22/x64-release-v143-libsodium.dll').Path
.venv/Scripts/python.exe -m unittest discover -s formal/reference/isc_crypto -p 'test_*.py' -v
.venv/Scripts/ruff.exe check --isolated --select B,E,F,I,RUF,UP --line-length 100 --target-version py312 formal/reference/isc_crypto
.venv/Scripts/ruff.exe format --isolated --line-length 100 --check formal/reference/isc_crypto
.venv/Scripts/mypy.exe --strict --explicit-package-bases formal/reference/isc_crypto/codec.py formal/reference/isc_crypto/sodium_reference.py
```

Crypto tests fail when the backend or provenance is unavailable; they never skip
or substitute OpenSSL. Public RFC 8032 seeds and synthetic fixture IDs are test
material, not deployment keys or an assigned semantics value. Exact known-answer
vectors check deterministic signing and pure Ed25519 rather than ph/ctx/prehash.

## Limits

No trusted-bootstrap provisioning, native round-context calculation, original
physical-slot lineage verification, PB/parent admission, quorum, WAL, consensus
invocation, key custody, production dependency or ABI integration is provided.
Canonical bytes and a valid detached signature alone do not authorize an ISC.
Library authentication uses the upstream package signer only, not a new Delta
consensus trust root. No R2.3/R3, native guard removal, independent attestation,
deployment qualification or Formal GO is claimed. Full formal and production gates
remain separate; this target does not alter their historical evidence.
