from __future__ import annotations

from pathlib import Path

from deltatorrent.cli.main import main

FIXTURE = Path(__file__).parents[1] / "fixtures" / "models" / "tiny_qlora"


def test_qlora_import_and_tiny_train_cli(capsys: object) -> None:
    assert (
        main(
            [
                "qlora",
                "import",
                "--manifest",
                str(FIXTURE / "import.json"),
                "--allowed-root",
                str(FIXTURE.parent),
            ]
        )
        == 0
    )
    assert main(["qlora", "train", "--fixture", str(FIXTURE)]) == 0
