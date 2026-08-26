from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.worker.repository import ClaimDisposition, TicketResultRepository

from tests.integration.test_local_round_engine import prepare_round


def test_two_concurrent_claims_have_exactly_one_winner(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="concurrent-claim")
    repository = TicketResultRepository(tmp_path / "repository")
    barrier = Barrier(2)

    def claim() -> tuple[str, str]:
        barrier.wait()
        try:
            decision = repository.claim(prepared.ticket)
            return "decision", decision.disposition.value
        except DeltaError as exc:
            return "error", exc.code.value

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(claim) for _ in range(2)]
        results = sorted(future.result() for future in futures)

    assert results == sorted(
        [
            ("decision", ClaimDisposition.CLAIMED.value),
            ("error", ErrorCode.TICKET_ALREADY_IN_PROGRESS.value),
        ]
    )
