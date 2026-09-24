import DeltaReduce.Quorum
import DeltaReduce.FixedPoint
import DeltaReduce.ArithmeticKernel
import DeltaReduce.ParameterKernel
import DeltaReduce.ParameterKernelVectors
import DeltaReduce.ArithmeticBinding
import DeltaReduce.NativeGraphVectors
import DeltaReduce.Hierarchy
import DeltaReduce.Coverage
import DeltaReduce.Apply
import DeltaReduce.Examples

/-!
# DeltaReduce v1 parametric proof bundle

The imported modules cover the registered integer/quorum obligations. Amendment
0001 adds PO-A4's checked operation graph and PO-AB1's conditional typed graph
uniqueness and conditional certified PARAMETER conversion/schema placement.
PO-AB1 Apply/recovery and the concrete decoder/admission refinement remain open.
A successful build of these imports is not Formal GO.
Concrete instantiations live in `DeltaReduce.Examples`.
-/
