# SDK and remote demo acceptance — T051 / HR010-001

Self-reviewed presentation tooling only. No qualifying gate, independent review,
BenchmarkResultQC or Feature010 checkpoint is issued. Formal impact NONE.
Pre/final Constitution Check: PASS for this bounded tooling change. The accepted
baseline report verifies GO (`3e2e2344…`, semantics `cc98f15a…`); this does not
authorize the separate arithmetic/model-binding candidate.

The Admin SDK documents existing ModelPlugin, DatasetProvider, ModelPluginRunner
and DeltaPlugin contracts in English/Russian. The complete downloadable Python
example runs against the actual baseline registries. It produces centroids
[-3, 3] and accuracy_ppm 1000000 on four distinct synthetic evaluation points.
It explicitly does not run consensus, HTTP, Java, WAL or scientific qualification.

262 UI tests in 44 files, 26 presentation tests, TypeScript, offline/live audits,
repository-boundary audit, validator/catalog synchronization and targeted Ruff
checks pass. After the repeat-start fixes, targeted UI tests and live install
checks passed again. The installed Admin source is in installed-admin-ui.json.
Local browser review verified EN/RU SDK layout, shared campaign data, the new
host-storage wording and the actual external execution in Presentation.

Actual Cloudflare HTTPS run: `934a9d51-e5aa-46da-bbc3-963b9f409914`, job
`6b50d8294e51413ca8708439076aacb9`. Training completed through the existing
Controller and separate Python Worker. The external canonical receipt bytes
equal the local bytes; SHA-256:
`ec715072b34d3add3e3cd7c191341e491e70866c40663752a91f7a5b6bf0230d`.
The run is in Morning Demo and visible from Admin/Presentation. Controller
instance `7e879144-c460-4e52-9dbb-b2b5060ac6c2` and clean baseline source c8aea649
remained unchanged.

The remote acceptance exercised anonymous denial, EN/RU login, signed cookie,
authenticated HTML/assets, profile GET/PUT, cross-origin and missing-marker
rejection, private-control/shutdown denial, real training and receipt equality.
It used the actual public Cloudflare endpoint and a Cloudflare DNS A record with
normal TLS hostname/certificate validation. The host's default DNS returned
NXDOMAIN for new Quick Tunnel domains; external browser acceptance on this host
is therefore **BLOCKED_HOST_DNS**, not PASS. No system DNS, TLS trust or hosts
file was changed. The launcher reports this limitation explicitly.

Real tunnel stop/start changed its public hostname; repeat start preserved the
current gateway PID/instance. The access code stayed on disk. Two startup issues
were repaired during acceptance: Windows venv launcher/child PID ownership and
reapplying an ACL without copying SACL/owner fields requiring extra privileges.
The old baseline Controller was not restarted. Current address is a live runtime
property: use START-REMOTE.ps1, not a historical URL in these evidence files.

No password, cookie, local control secret or private key is in this evidence.
checks.json distinguishes public HTTPS evidence from local browser observations.
The one-shot acceptance driver and credentials stay in the private local tunnel
data directory; its source hash is recorded for inspection on the host.
