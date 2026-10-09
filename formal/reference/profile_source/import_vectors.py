"""Original Profile-v1 import metadata; synthetic, not lawful native history."""

import copy
import re

from formal.reference.profile_source import metadata as m
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.control_vectors import fields
from formal.reference.profile_source.origin_vectors import generate as origin_vectors
from formal.reference.profile_source.test_metadata import Package, identifier


def generate():
    base, originals = origin_vectors()
    pattern = r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)"
    base = re.sub(pattern, "", base, flags=re.MULTILINE)
    base = base.replace("import ProfileOrigin", "import ProfileImport")
    p = Package()
    activation = p.activate()
    manifest = {**p.manifest, "anchor": activation["anchor"]}
    p.manifest = manifest
    # The established Python metadata checker independently accepts this pair.
    p.check()
    variants = [
        manifest,
        {**manifest, "anchor": p.anchor},
        {**manifest, "validator_epoch_id": identifier("other-epoch")},
        {**manifest, "target_event_index": "3"},
        {**manifest, "schema_set_id": identifier("other-schema")},
    ]
    bad_cut = copy.deepcopy(manifest)
    bad_cut["journals"][0]["cut"]["ref"]["byte_length"] = "8"
    variants.append(bad_cut)
    lines = [
        base,
        "namespace ImportVectors",
        "open OriginVectors",
        f"def own : List Import.OwnJournal := [⟨{bs(b'v0')},{bs(b'consensus')},{bs(b'journal')}⟩]",
        "def trusted : Import.Trusted := ⟨known,bootRaw,trustedLog,own⟩",
    ]
    for i, v in enumerate(variants):
        lines.append(f"def m{i} : Control.Fields := {fields(v)}")
        lines.append(f"def r{i} : Bytes := {bs(m.canonical(v))}")
    lines += [
        "def package (f : Control.Fields) (raw : Bytes) : Import.Package :=",
        "  ⟨bootstrap,index,indexRaw,[f0,f1,f2],f,raw,store⟩",
        "def run (f : Control.Fields) (raw : Bytes) := "
        "Import.bindProfile hash trusted (package f raw)",
        "example : (run m0 r0).map (fun b => "
        "(b.origin.source.events.length,b.floor.rows.length,b.manifest.snapshot))",
        f"  = some (2,3,{bs(b'snapshot')}) := by decide +kernel",
    ]
    for i in range(1, len(variants)):
        lines.append(f"example : (run m{i} r{i}).isNone = true := by decide +kernel")
    lines += [
        "example : (Import.bindProfile hash trusted "
        "{package m0 r0 with artifacts := store ++ [[]]}).isNone = true := by decide +kernel",
        "example : (Import.bindProfile hash {trusted with ownJournals := []} "
        "(package m0 r0)).isNone = true := by decide +kernel",
        "example : (Import.bindProfile hash {trusted with ownJournals := "
        f"[⟨{bs(b'v0')},{bs(b'consensus')},[]⟩]}} "
        "(package m0 r0)).isNone = true := by decide +kernel",
        "example : (Import.bindProfile hash trusted "
        "{package m0 r0 with floorDescriptors := [f0,f1]}).isNone = true := by decide +kernel",
        "end ImportVectors",
    ]
    originals["original_import_manifests"] = [m.canonical(v).hex() for v in variants]
    originals["independent_own_journals"] = [
        {"actor": "v0", "journal": "consensus", "raw_hex": b"journal".hex()}
    ]
    return "\n".join(lines) + "\n", originals
