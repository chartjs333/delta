"""Exact Python/kernel source join; synthetic values, not full imported authority."""

from hashlib import sha256

from formal.reference.profile_source import configuration_units as cu
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.control_vectors import fields
from formal.reference.profile_source.test_genesis import (
    bind_configuration_package,
    configuration_package,
)


def generate():
    parts = configuration_package()
    _, p, config_raw, _ = parts
    joined = bind_configuration_package(parts)
    bound = joined.origin
    initial = bound.initial_configuration
    row = m.load(bound.genesis.original)
    config = cu.decode(config_raw)
    wrong = dict(config, parent_checkpoint_id=bound.genesis.optimizer_id)
    wrong_raw = cu.encode(wrong)
    table = {
        raw: sha256(raw).digest()
        for raw in (
            p.boot_raw,
            p.index_raw,
            *(raw for _, raw in p.artifacts),
            bound.genesis.model_preimage,
            bound.genesis.optimizer_preimage,
        )
    }
    names = (
        "runtime_build_id",
        "formal_semantics_id",
        "schema_set_id",
        "signature_codec_id",
        "producer_rules_id",
    )
    pins = "⟨" + ",".join(bs(p.boot[name].encode()) for name in names) + "⟩"

    def lists(xs):
        return "[" + ",".join(bs(x.encode()) for x in xs) + "]"

    descriptor = (
        "⟨"
        + ",".join(
            (
                bs(row["formal_semantics_id"].encode()),
                bs(row["origin_id"].encode()),
                bs(row["validator_epoch_id"].encode()),
                row["height"],
                lists(row["model_values"]),
                lists(row["optimizer_values"]),
            )
        )
        + "⟩"
    )
    storage = config["availability_policy"]["storage_binding"]
    enrollment = (
        "⟨"
        + ",".join(
            (
                bs(config["formal_semantics_id"].encode()),
                bs(config["validator_epoch_id"].encode()),
                lists(config["validator_ids"]),
                bs(storage["storage_epoch_id"].encode()),
                bs(storage["storage_registry_id"].encode()),
            )
        )
        + "⟩"
    )
    lines = [
        "import ProfileGenesis",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace GenesisVectors",
        f"def pins : Origin.Pins := {pins}",
        f"def known : Origin.Independent := ⟨{bs(sha256(p.boot_raw).digest())},"
        f"{bs(sha256(p.index_raw).digest())},pins⟩",
        f"def bootstrap : Control.Fields := {fields(p.boot)}",
        f"def index : Control.Fields := {fields(p.index)}",
        f"def configuration : Control.Fields := {fields(m.load(initial))}",
        f"def bootRaw : Bytes := {bs(p.boot_raw)}",
        f"def indexRaw : Bytes := {bs(p.index_raw)}",
        "def store : List Bytes := [" + ",".join(bs(raw) for _, raw in p.artifacts) + "]",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  []",
        f"def descriptor : Genesis.Descriptor := {descriptor}",
        f"def enrolled : Configuration.Enrollment := {enrollment}",
        f"def configRaw : Bytes := {bs(config_raw)}",
        "def bound (k : Origin.Independent) (g : Genesis.Descriptor) := do",
        "  let origin ← Origin.bind hash k bootstrap index bootRaw indexRaw store",
        "  Genesis.bind hash origin g configuration",
        "def joined (k : Origin.Independent) (g : Genesis.Descriptor) (raw : Bytes) := do",
        "  let origin ← Origin.bind hash k bootstrap index bootRaw indexRaw store",
        "  Genesis.bindConfiguration hash origin g configuration enrolled raw",
        f"example : Genesis.json descriptor = {bs(bound.genesis.original)} := by decide +kernel",
        "example : (bound known descriptor).map (fun x =>",
        "  (x.model.length,x.optimizer.length,x.current.checkpoint,x.current.qc,",
        "   x.units.quantum.numerator,x.units.quantum.denominator)) =",
        f"  some (4,4,{bs(bound.genesis.checkpoint_id.encode())},[],3,7) := by decide +kernel",
        "example : (bound {known with bootstrapDigest := []} descriptor).isNone = true "
        ":= by decide +kernel",
        "example : (bound known {descriptor with height := 1}).isNone = true := by decide +kernel",
        "example : (bound known {descriptor with modelValues := []}).isNone = true "
        ":= by decide +kernel",
        "example : (joined known descriptor configRaw).map (fun pair =>",
        "  (pair.2.body.parent,pair.2.numeric.quantum.numerator,",
        "   pair.2.numeric.quantum.denominator)) =",
        f"  some ({bs(bound.genesis.checkpoint_id.encode())},3,7) := by decide +kernel",
        f"example : (joined known descriptor {bs(wrong_raw)}).isNone = true := by decide +kernel",
        "end GenesisVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_GENESIS_VALUES_AND_METADATA_NOT_FULL_LAWFUL_IMPORT",
        "bootstrap": p.boot_raw.hex(),
        "index": p.index_raw.hex(),
        "initial_configuration": initial.hex(),
        "genesis": bound.genesis.original.hex(),
        "configuration": config_raw.hex(),
        "wrong_parent_configuration": wrong_raw.hex(),
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
    }
