"""Small canonical-input encoding fixture, derived from pinned native bytes."""
# ruff: noqa: E501 -- emitted Lean expressions are deliberately kept intact.

import json
from pathlib import Path

from derive_public_arithmetic_inputs import SOURCE, SOURCE_SHA256, derive
from formal_artifacts import canonical_json_bytes, load_json_strict

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/PublicArithmeticInputsVectors.lean"


def fields(value):
    return {key[1]: item for key, item in value[1]}


def number(value):
    return int(value[1])


def integer(value):
    return str(value) if value >= 0 else f"({value})"


def vector(values):
    return "[" + ",".join(integer(v) for v in values) + "]"


def rational(values):
    return "⟨" + ",".join(integer(v) for v in values) + "⟩"


def lean_value(value):
    kind, body = value
    if kind == "int":
        return f"(.integer {integer(int(body))})"
    if kind in ["str", "model"]:
        return f"(.{'text' if kind == 'str' else 'model'} {json.dumps(body)})"
    if kind == "fun":
        pairs = ",".join(f"({lean_value(k)},{lean_value(v)})" for k, v in body)
        return f"(.function (entries [{pairs}]))"
    raise ValueError("UNSUPPORTED_FIXTURE_VALUE")


def generate(target=TARGET, source=SOURCE):
    result = derive(source)  # Checks the separately pinned bytes and full graph first.
    bundle = load_json_strict(source)
    profile = json.loads(bundle["artifacts"][result["root"]["profile"]["id"]])["payload"]
    p = fields(result["inputs"])
    q = [number(v) for _, v in fields(p["q"])["t1"][1]]
    quanta = list(
        zip(
            [number(v) for _, v in fields(p["qN"])["d1"][1]],
            [number(v) for _, v in fields(p["qD"])["d1"][1]],
            strict=True,
        )
    )
    weight = [number(fields(p[k])["t1"]) for k in ["weightN", "weightD"]]
    model = [number(v) for _, v in p["model"][1]]
    optimizer = [number(v) for _, v in p["optimizer"][1]]

    def pairs(values):
        return "[" + ",".join(f'("s{i + 1}",{integer(v)})' for i, v in enumerate(values)) + "]"

    content = f'''import DeltaReduce.PublicArithmeticInputs

-- Generated from independently pinned fixture {SOURCE_SHA256}.
-- Mathematical image/codec example, not native producer authentication.
namespace DeltaReduce.PublicArithmeticInputsVectors
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs
set_option Elab.async false
set_option maxRecDepth 16000
set_option maxHeartbeats 5000000

def vocabulary : Vocabulary := {{
  ticket := fun n => if n == "t0000" then some "t1" else none
  domain := fun n => if n == "d1" then some "d1" else none
  shard := fun n => if n == "s1" then some "shard1" else if n == "s2" then some "shard2" else none
  tickets := ["t1"], domains := ["d1"], shards := ["shard1","shard2"]
  models := ["t1","d1","shard1","shard2"] }}

def nativeProfile : Profile := {{
  accumulatorBits := {profile["accumulator_bits"]}
  applyQuantum := {rational(profile["apply_quantum"])}
  domainWeights := [⟨"d1",{rational(profile["domain_weights"][0]["weight"])}⟩]
  learningRate := {rational(profile["learning_rate"])}, momentum := {rational(profile["momentum"])}
  weightDecay := {rational(profile["weight_decay"])}
  rounding := "{profile["rounding"]}", nesterov := {str(profile["nesterov"]).lower()}
  outputRange := "{profile["output_range"]}" }}

def fixtureImage : Image := {{
  tickets := [⟨"t0000","d1",{rational(weight)},{vector(q)}⟩]
  domains := [⟨"d1",{number(fields(p["denominator"])["d1"])},[{",".join(map(rational, quanta))}]⟩]
  shards := ["s1","s2"], profile := nativeProfile
  mixtureDenominator := {number(p["mixtureD"])}
  model := {pairs(model)}, optimizer := {pairs(optimizer)}, limit := {number(p["limit"])} }}

def expectedASCII : String := {json.dumps(canonical_json_bytes(result["inputs"]).decode("ascii"))}

theorem fullCanonicalInputBytes :
    (encodeImage vocabulary fixtureImage).map (fun e => e.preimage) =
      some (asciiBytes expectedASCII) := by decide +kernel

theorem missingTicketAliasRejected :
    (encodeImage {{vocabulary with ticket := fun _ => none}} fixtureImage).isNone = true := by decide +kernel

theorem extraConfiguredTicketRejected :
    (encodeImage {{vocabulary with tickets := ["t1","t2"]}} fixtureImage).isNone = true := by decide +kernel

theorem extraConfiguredDomainRejected :
    (encodeImage {{vocabulary with domains := ["d1","d2"]}} fixtureImage).isNone = true := by decide +kernel

theorem missingConfiguredShardRejected :
    (encodeImage {{vocabulary with shards := ["shard1"]}} fixtureImage).isNone = true := by decide +kernel

theorem duplicateShardAliasRejected :
    (encodeImage {{vocabulary with shard := fun _ => some "shard1"}} fixtureImage).isNone = true := by decide +kernel

theorem unknownModelNameRejected :
    (encodeImage {{vocabulary with models := ["t1","d1","shard1"]}} fixtureImage).isNone = true := by decide +kernel

theorem missingCoordinateDoesNotZipAway :
    vectorTable vocabulary.shard ["s1","s2"] [1] = none := by decide +kernel

theorem extraCoordinateDoesNotZipAway :
    vectorTable vocabulary.shard ["s1","s2"] [1,2,3] = none := by decide +kernel

theorem changedProfileChangesWholeBytes :
    ((encodeImage vocabulary {{fixtureImage with profile := {{nativeProfile with learningRate := ⟨1,1⟩}}}}).map
      (fun e => e.preimage)) ≠ some (asciiBytes expectedASCII) := by decide +kernel

theorem changedQuantumChangesWholeBytes :
    ((encodeImage vocabulary {{fixtureImage with domains := [⟨"d1",1,[⟨1,1⟩,⟨1,2⟩]⟩]}}).map
      (fun e => e.preimage)) ≠ some (asciiBytes expectedASCII) := by decide +kernel

theorem changedOptimizerChangesWholeBytes :
    ((encodeImage vocabulary {{fixtureImage with optimizer := [("s1",0),("s2",0)]}}).map
      (fun e => e.preimage)) ≠ some (asciiBytes expectedASCII) := by decide +kernel

theorem completeFieldCount : PublicArithmeticInputs.fieldNames.length = 23 := by decide +kernel

theorem longSequenceUsesCanonicalKeyOrder :
    PublicState.canonical [] (sequence ((List.range 12).map (fun n => .integer (Int.ofNat n)))) = true := by decide +kernel

end DeltaReduce.PublicArithmeticInputsVectors
'''
    tables = [
        ("ticketDomains vocabulary fixtureImage", "ticketDomain"),
        ("qTable vocabulary fixtureImage", "q"),
        ("weightTable Rational.numerator vocabulary fixtureImage", "weightN"),
        ("weightTable Rational.denominator vocabulary fixtureImage", "weightD"),
        ("denominatorTable vocabulary fixtureImage", "denominator"),
        ("quantumTable Rational.numerator vocabulary fixtureImage", "qN"),
        ("quantumTable Rational.denominator vocabulary fixtureImage", "qD"),
        ("mixtureTable Rational.numerator vocabulary fixtureImage", "piN"),
        ("mixtureTable Rational.denominator vocabulary fixtureImage", "piD"),
        ("currentTable vocabulary.shard fixtureImage.model", "model"),
        ("currentTable vocabulary.shard fixtureImage.optimizer", "optimizer"),
    ]
    components = "\n".join(
        f"def table{i} : Value := {lean_value(p[key])}\n"
        f"theorem computed{i} : {expr} = some table{i} := by decide +kernel\n"
        for i, (expr, key) in enumerate(tables)
    )
    components += f"""
def fixtureComponents : Components vocabulary fixtureImage := {{
  ticketNames := ["t1"], tickets := by decide +kernel
  domainNames := ["d1"], domains := by decide +kernel
  values := [{",".join(f"table{i}" for i in range(11))}]
  computed := by simp only [{",".join(f"computed{i}" for i in range(11))},collect,id,Bind.bind,Option.bind]
  size := by decide +kernel
  ticketSet := by decide +kernel
  domainSet := by decide +kernel
  shardSet := by decide +kernel }}

def expectedValue : Value := {lean_value(result["inputs"])}

theorem computedFields :
    Value.function (entries (fixtureComponents.fields.map (fun (k,x) => (.text k,x)))) = expectedValue := by rfl

theorem expectedCanonical : canonical vocabulary.models expectedValue = true := by decide +kernel

def fixtureEncoded : Encoded vocabulary fixtureImage :=
  ⟨fixtureComponents,by rw [computedFields]; exact expectedCanonical⟩

theorem encodedValue : fixtureEncoded.value = expectedValue := computedFields


"""
    content = content.replace(
        "theorem fullCanonicalInputBytes", components + "theorem fullCanonicalInputBytes"
    )
    content = content.replace(
        "some (asciiBytes expectedASCII) := by decide +kernel",
        "some expectedBytes := by\n  rw [encodeImageFromComputed fixtureEncoded]\n  simp only [Option.map_some,Encoded.preimage,encodedValue,expectedEncoding]",
        1,
    )
    start = content.index("theorem unknownModelNameRejected")
    end = content.index("theorem missingCoordinateDoesNotZipAway")
    content = (
        content[:start]
        + """theorem unknownModelNameRejected :
    canonical ["t1","d1","shard1"] table1 = false := by decide +kernel

"""
        + content[end:]
    )
    start = content.index("theorem changedProfileChangesWholeBytes")
    end = content.index("theorem completeFieldCount")
    content = (
        content[:start]
        + """theorem changedProfileChangesField :
    ({nativeProfile with learningRate := ⟨1,1⟩}).learningRate ≠ nativeProfile.learningRate := by decide +kernel

theorem changedQuantumChangesTable :
    quantumTable Rational.denominator vocabulary {fixtureImage with domains := [⟨"d1",1,[⟨1,1⟩,⟨1,2⟩]⟩]} ≠
      some table6 := by decide +kernel

theorem changedOptimizerChangesTable :
    currentTable vocabulary.shard [("s1",0),("s2",0)] ≠ some table10 := by decide +kernel

"""
        + content[end:]
    )
    encoded_fields = []
    proof = "(Eq.refl ([] : List Bytes))"
    chunks = []
    for index, (key, value) in enumerate(result["inputs"][1]):
        raw = canonical_json_bytes([key, value]).decode("ascii")
        chunks.append(raw)
        encoded_fields.append(
            f"def rawField{index} : Bytes := asciiBytes {json.dumps(raw)}\n"
            f"theorem fieldEncoding{index} : [91] ++ encode {lean_value(key)} ++ [44] ++ "
            f"encode {lean_value(value)} ++ [93] = rawField{index} := by decide +kernel\n"
        )
    assert '["fun",[' + ",".join(chunks) + "]]" == canonical_json_bytes(result["inputs"]).decode(
        "ascii"
    )
    for index in reversed(range(len(chunks))):
        proof = f"(congrPair List.cons fieldEncoding{index} {proof})"
    encoded_fields.append(
        'def expectedBytes : Bytes := asciiBytes "[\\"fun\\",[" ++ List.intercalate [44] ['
        + ",".join(f"rawField{i}" for i in range(len(chunks)))
        + "] ++ [93,93]\n"
        + "theorem expectedEncoding : encode expectedValue = expectedBytes := by\n"
        + f"  have parts := {proof}\n"
        + '  exact congrArg (fun xs : List Bytes => asciiBytes "[\\"fun\\",[" ++ List.intercalate [44] xs ++ [93,93]) parts\n'
    )
    content = content.replace(
        "theorem fullCanonicalInputBytes",
        "\n".join(encoded_fields) + "\ntheorem fullCanonicalInputBytes",
    )
    target.write_text(content, encoding="utf-8", newline="\n")
    return content


if __name__ == "__main__":
    generate()
    print("Canonical 23-field arithmetic-input Lean fixture generated")
