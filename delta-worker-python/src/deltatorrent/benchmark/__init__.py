"""Feature 010 benchmark-governance foundation.

This package deliberately contains contracts, planning, and offline verification
only.  It has no authority to execute a primary benchmark or mutate consensus
state.
"""

from deltatorrent.benchmark.canonical import ContractEncodingError
from deltatorrent.benchmark.contracts import ContractError

__all__ = ["ContractEncodingError", "ContractError"]
