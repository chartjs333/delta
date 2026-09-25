import DeltaReduce.Quorum
import DeltaReduce.FixedPoint
import DeltaReduce.ArithmeticKernel
import DeltaReduce.ParameterKernel
import DeltaReduce.ApplyKernel
import DeltaReduce.ApplyKernelVectors
import DeltaReduce.RecoveryKernel
import DeltaReduce.RecoveryKernelVectors
import DeltaReduce.ParameterKernelVectors
import DeltaReduce.ArithmeticBinding
import DeltaReduce.NativeGraphVectors
import DeltaReduce.NativeVoteVectors
import DeltaReduce.NativeReplay
import DeltaReduce.NativeReplayVectors
import DeltaReduce.PublicJournal
import DeltaReduce.PublicJournalVectors
import DeltaReduce.PublicRecovery
import DeltaReduce.PublicRecoveryVectors
import DeltaReduce.PublicReachability
import DeltaReduce.PublicReachabilityExamples
import DeltaReduce.PublicSnapshot
import DeltaReduce.PublicSnapshotVectors
import DeltaReduce.PublicState
import DeltaReduce.PublicStateVectors
import DeltaReduce.Hierarchy
import DeltaReduce.Coverage
import DeltaReduce.Apply
import DeltaReduce.Examples

/-!
# DeltaReduce v1 parametric proof bundle

The imported modules cover the registered integer/quorum obligations. Amendment
0001 adds PO-A4's checked operation graph and PO-AB1's conditional typed graph
uniqueness and conditional certified PARAMETER conversion/schema placement.
PO-AB1 full APPLY identity is conditional on named codec/trust/hash adapters.
The checked replay kernel remains a sublayer: its native recovery bridge and
the concrete decoder/admission refinement remain open.
A successful build of these imports is not Formal GO.
Concrete instantiations live in `DeltaReduce.Examples`.
-/
