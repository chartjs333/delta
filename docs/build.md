# Build and component orchestration

Feature 001 establishes repository boundaries without introducing native or JVM production
code. The root is a virtual `uv` workspace; the only executable component is
`delta-worker-python`.

```text
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy delta-worker-python/src
uv run pytest delta-worker-python/tests
python specs/001-reproducible-training-baseline/scripts/verify_formal_prerequisite.py --check-only
```

`make prerequisite`, `make protocol-check`, `make python-check` and `make conformance`
provide the Linux/CI orchestration aliases. They do not silently invoke CMake, Gradle or a
host compiler before the owning feature exists.

Future toolchain inputs are declared, not inferred:

- C++ compiler/CMake presets begin in feature 003;
- JDK 25 reference and JDK 26 compatibility manifests begin in feature 003;
- Python 3.12 and the committed `uv.lock` are authoritative for feature 001.

The placeholder component READMEs are ownership contracts, not buildable targets.
