"""T047/T053, scope 13: exact approved retention source bytes, not origin authority.

The enclosing original RoundConfig and its producing prefix must still be
independently verified. A successful local resolution is deliberately not an
admissible snapshot, a configuration certificate or a physical-retention claim.
"""

from dataclasses import dataclass
from hashlib import sha256

from formal.reference.isc_crypto.codec import _closed, _decimal, _id, _label, _require
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.storage_source.codec import (
    REGISTRY_DOMAIN,
    Bootstrap,
    Context,
    Witness,
    authenticate_witness,
    canonical,
    content_id,
    context,
    load,
    registry,
)

CONTRACT = (
    "12326b892690705b7141fcd32bf3f32cf07d092e:"
    "formal/proposals/retention-policy-source-binding-v1.md"
)
DOMAIN = "deltareduce.storage-retention-policy-source.v1"
SOURCE_KEYS = {"obligation_ref", "retention_epoch_id", "schema_version", "type_name"}
BINDING_KEYS = {
    "retention_epoch_id",
    "retention_policy_source",
    "storage_epoch_id",
    "storage_registry_id",
    "threshold",
}


def decode_source(raw: bytes) -> dict:
    """Strict original J(R); duplicate members reject before typed construction."""
    obj = _closed(load(raw), SOURCE_KEYS)
    _require(obj["schema_version"] == "1.0.0", "retention source schema")
    _require(obj["type_name"] == "STORAGE_RETENTION_POLICY_SOURCE", "retention source type")
    _label(obj["retention_epoch_id"])
    ref = _closed(obj["obligation_ref"], {"byte_length", "sha256"})
    _decimal(ref["byte_length"], positive=True)
    _id("sha256:" + ref["sha256"] if type(ref["sha256"]) is str else None)
    return obj


@dataclass(frozen=True)
class Resolution:
    original_source: bytes
    original_declaration: bytes
    source_id: str
    retention_epoch_id: str
    declaration_sha256: str


def resolve(contract: str, raw: bytes, declaration: bytes, retention_epoch: str) -> Resolution:
    """Trust-side codec selection, then actual bytes; no file/path/boolean oracle.

    This checks only the exact source association inside R. The enclosing bundle
    owns original occurrence and complete approved-budget accounting. E is never
    decoded, normalized, executed or fetched here; it may contain arbitrary bytes.
    """
    _require(contract == CONTRACT, "independently selected retention codec")
    obj = decode_source(raw)
    _label(retention_epoch)
    _require(obj["retention_epoch_id"] == retention_epoch, "original retention epoch")
    _require(type(declaration) is bytes, "complete original declaration bytes required")
    ref = obj["obligation_ref"]
    _require(len(declaration) == int(ref["byte_length"]), "complete declaration byte length")
    digest = sha256(declaration).hexdigest()
    _require(digest == ref["sha256"], "original declaration digest")
    return Resolution(raw, declaration, content_id(DOMAIN, raw), retention_epoch, digest)


@dataclass(frozen=True)
class StorageBinding:
    original_binding: bytes
    source: Resolution
    storage_epoch_id: str
    storage_registry_id: str
    threshold: int


def bind_policy(
    contract: str, bootstrap: Bootstrap, original_binding: bytes, declaration: bytes
) -> StorageBinding:
    """Decode the one approved future storage_binding, preserving its exact bytes.

    Call with the exact embedded object from a separately checked original config.
    This function does not invent a complete enclosing RoundConfig wire grammar.
    """
    obj = _closed(load(original_binding), BINDING_KEYS)
    _label(obj["storage_epoch_id"])
    _id(obj["storage_registry_id"])
    raw_registry, keys = registry(bootstrap)
    _require(
        obj["storage_epoch_id"] == bootstrap.storage_epoch_id
        and obj["storage_registry_id"] == content_id(REGISTRY_DOMAIN, raw_registry),
        "original independently enrolled storage authority",
    )
    threshold = _decimal(obj["threshold"], positive=True)
    _require(threshold < 2**32 and threshold <= len(keys), "original storage threshold")
    source = resolve(
        contract, canonical(obj["retention_policy_source"]), declaration, obj["retention_epoch_id"]
    )
    return StorageBinding(
        original_binding, source, obj["storage_epoch_id"], obj["storage_registry_id"], threshold
    )


@dataclass(frozen=True)
class BoundWitness:
    binding: StorageBinding
    witness: Witness


def authenticate_bound_witness(
    contract: str,
    bootstrap: Bootstrap,
    backend: SodiumReference,
    value: Context,
    original_binding: bytes,
    declaration: bytes,
    original_certificate: bytes,
    original_inventory: tuple[bytes, ...],
) -> BoundWitness:
    """Compose byte resolution and S authentication, without erasing deliveries.

    Context and original_binding are still component inputs. Their common
    original configuration/pre-cut provenance is not proved by this function.
    """
    binding = bind_policy(contract, bootstrap, original_binding, declaration)
    expected = context(bootstrap, value)
    _require(
        binding.source.retention_epoch_id == expected["retention_epoch_id"]
        and binding.storage_epoch_id == expected["storage_epoch_id"]
        and binding.storage_registry_id == expected["storage_registry_id"]
        and binding.threshold == value.threshold,
        "original policy/statement association",
    )
    witness = authenticate_witness(
        bootstrap, backend, value, original_certificate, original_inventory
    )
    return BoundWitness(binding, witness)
