# Assignment-time environment audit

**Observed at**: 2026-09-20T14:08:03Z
**Scope**: local host and repository-visible names only
**Authority**: diagnostic observation; never an execution authorization

This narrative accompanies the machine-readable
`environment-audit.json`. Commands with relative paths run from the repository root;
the record contains exact arguments, exit status, normalized output and SHA-256 for
each sanitized observation. This audit does not
publish credential values, private key bytes, GPU UUIDs, account identifiers or
model/data content. Negative findings are scoped to what was visible during this
assignment and do not prove that an external organization has no such resource.

## Reproducible read-only observations

| Check | Exact source/argument summary | Exit | Sanitized output SHA-256 |
| --- | --- | ---: | --- |
| Physical GPU | `nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader,nounits` | 0 | `4751cda0c7ba984319705eb68de1c20fdc5bcdaf39ac410b7f0c9ea8ed1a9429` |
| Host CUDA toolkit | `nvcc --version` | 0 | `47cdb0797dad2e5b53fb5e5cf272bee96fd928f35ac0e932ee1c146ce003649d` |
| Current-worktree Torch | `.venv/Scripts/python.exe -c <version/CUDA/runtime query>` | 0 | `555e2e3bced121b735101765986a912c0e58af9e2f653a82df6f33e22973c35f` |
| Separate untracked Torch | `D:/delta/out/gpu-venv/Scripts/python.exe -c <version/CUDA/memory query>` | 0 | `03711970a3486c8ffc8cad08f8e5d3b17122e170d4125940049dc6ab2aff7f47` |
| Historical literal threshold | checked PowerShell `Int64` subtraction from 8,589,934,592 bytes | 0 | `31ded22d2d1a08d447349e956316103decaaf630815027b87272306955009331` |
| Historical campaign image | `docker image inspect sha256:0bb88834d973ca1b450fcc2a05333c6fe45510bee289912a5391274c351c4a4d --format {{.Id}}` | 1 (not found) | `04da0e890b769f6ace7858005812532d03ab70e734fec663dea80157ec88e176` |
| Model cache names | `%USERPROFILE%/.cache/huggingface/hub`, filter `models--*` | 0 | `9209bad85bc2abf81b3990e368120fa58929e13eddd0bfc289bb6880270a5959` |
| Dataset cache names | recursive `%USERPROFILE%/.cache/huggingface`, names `wikitext|lambada|hellaswag` | 0 | `72abe435e5e3ee24d7fcb9d2467aacaaf12b1cbc0958b64715c5e1a7574ba3ef` |
| Repository Actions names | checked names-only queries for `chartjs333/delta`; values are never requested | 0 | `252e0266066c07f7619c2200732a01ea94ac26ccde633e5e12bf2c12c55493be` |
| Controller authority | untracked-path state plus public register/approval lineage and identity comparison; no private key bytes are read | 0 | `5ebc9e6908ef6e1e72ecb11e38223140ed1753f569152bb8e5f92ff9e593b657` |
| Remote inventory paths | `rg --files configs .github deploy` filtered for pilot/WAN/TLS/inventory/Campaign 02 | 0 | `f7258b425c35342be6f504443b2c64a4de54c359af5657cbbaacfe91b2b2d0e5` |

## Admission interpretation

Physical hardware presence does not make the current CPU-only worktree an eligible
Campaign 02 environment. The separate local CUDA environment, cached model name and
demo/controller artifacts are untracked and are not bound to a current-lineage
definition, independent custody, execution authority or immutable datasets. The
absence of repository-visible remote configuration also cannot be replaced by a
generic cloud credential, local NIC, VM/VPN adapter or fabricated endpoint.

The only sound result from these observations is to keep Feature 010 at
`STOPPED_BEFORE_PRIMARY_EXECUTION` and Feature 011 at
`BLOCKED_ON_FEATURE010_GO` until the exact external requirements in
`reconciliation-status.json` are independently supplied and reviewed.
