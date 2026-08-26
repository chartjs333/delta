# Dependency update policy

Feature 001 uses one committed root `uv.lock` for the virtual workspace and the
`delta-worker-python` package.

- Resolution changes are made intentionally with `uv lock --upgrade-package <name>` or a
  reviewed full `uv lock --upgrade`.
- CI and reproducibility runs use `uv sync --frozen` and never mutate the lock.
- Runtime dependencies must be justified by a task and remain inside the owning component.
- `delta-protocol` has no runtime dependency or code generator dependency.
- Native/JVM dependencies are forbidden until their owning feature creates a pinned toolchain
  manifest.
- Lock changes include the corresponding quality, offline and artifact-safety evidence.

The lock resolves build and development tools as well as direct runtime dependencies, so a
successful offline run can consume a pre-populated verified cache without contacting a package
index.

Feature 001 pins PyTorch 2.6.0 from the explicit official `pytorch-cpu` wheel index; CUDA wheels
and host-provided PyTorch installations are not part of the reference class. NumPy is locked
because the safe-tensor encoder uses its CPU byte bridge, and `safetensors` is the only tensor
checkpoint codec. Neither `torch.save` nor a pickle-compatible codec is allowed.
