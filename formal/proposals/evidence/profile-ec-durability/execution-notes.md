# Mandatory gate execution

T047/T053 / ISC-S16-D01. The exact sequential `Makefile` formal-check recipes
were invoked with `D:/delta/.venv/Scripts/python.exe` because GNU make was not
installed. No recipe or predicate was bypassed; execution stops on the first
failed prerequisite. `mandatory-gates.json` binds each final command output and
records later gates that were not reached.

The first attempt used Python's Windows cp1252 default for implicit text reads.
It failed the contracts stage on UTF-8 Lean source decoding and mojibake in
byte-comparison tests. Its actual failure output and receipt are retained as
`windows-default-encoding-failure.txt` and `windows-default-encoding-gates.json`.
This attempt is not represented as PASS.

The repeat used `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` with the same unchanged
sources and recipes. The pinned Java, TLA tools and Lake were supplied through
`JAVA`, `TLA2TOOLS_JAR`, `LAKE`, and Lean's existing bin directory in PATH.
Source/proof changes were not made to accommodate the environment failure.

The scoped EC component receipt remains distinct from mandatory gate results.
No successful component, retry or process review closes R2.3 or grants Formal GO.
