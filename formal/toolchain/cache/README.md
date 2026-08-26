# Local verified artifact cache

This directory intentionally does not contain large binaries in Git. Populate it with:

```text
tla2tools.jar
OpenJDK17U-jre_x64_linux_hotspot_17.0.20.1_1.tar.gz
lean-4.32.1-linux.zip
```

Run `python formal/toolchain/prepare_cache.py --download` while online, then run the same command without `--download` to verify an offline cache. Files that do not match the locks are rejected and never installed.
