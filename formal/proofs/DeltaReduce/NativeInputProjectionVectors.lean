import DeltaReduce.NativeInputProjection
import DeltaReduce.NativeGraphVectors

namespace DeltaReduce.NativeInputProjectionVectors
open NativeBinding NativeInputProjection NativeGraphVectors
set_option maxRecDepth 12000
set_option maxHeartbeats 6000000
set_option synthInstance.maxSize 2048

def limit127 : ModelLimit := ⟨127,by decide,by decide⟩

theorem originalInputBlocks :
    (loadCorpus fixtureBinding).map (fun c => c.inputs.map (fun a =>
      (a.domain,a.shard,a.denominator,a.quantum,a.cells.map (fun x => (x.contribution.ticket,x.contribution.weight,x.value))))) =
    some [("d1","s1",1,⟨1,2⟩,[("t0000",⟨1,1⟩,1)]),
      ("d1","s2",1,⟨1,2⟩,[("t0000",⟨1,1⟩,-2)])] := by decide

theorem projectedNativeInputTables :
    ((loadCorpus fixtureBinding).bind (fun c => (projectInputs c limit127).map
      (fun p => (p.tickets,p.domains,p.weights.denominator,p.model.cells,p.optimizer.cells)))) =
      some ([⟨"t0000","d1",⟨1,1⟩,[1,-2]⟩], [⟨"d1",1,[⟨1,2⟩,⟨1,2⟩]⟩],1,
        [("s1",20),("s2",-20)],[("s1",2),("s2",-2)]) := by decide

def cell (ticket : String) (n d q : Int) : Cell :=
  ⟨⟨ticket,⟨n,d⟩,⟨[],.qShard,0⟩⟩,q⟩

def twoShardInputs : List AssignmentInput := [
  ⟨"d1","s1",3,⟨1,2⟩,[cell "t1" 1 3 9,cell "t2" 2 3 (-3)]⟩,
  ⟨"d1","s2",3,⟨3,4⟩,[cell "t1" 1 3 6,cell "t2" 2 3 12]⟩,
  ⟨"d2","s1",2,⟨1,5⟩,[cell "t3" 1 2 20]⟩,
  ⟨"d2","s2",2,⟨2,5⟩,[cell "t3" 1 2 (-10)]⟩]

theorem multipleTicketsAndDomains :
    collect (deriveTicket twoShardInputs ["s1","s2"])
      [⟨"t1","d1"⟩,⟨"t2","d1"⟩,⟨"t3","d2"⟩] =
      some [⟨"t1","d1",⟨1,3⟩,[9,6]⟩,⟨"t2","d1",⟨2,3⟩,[-3,12]⟩,⟨"t3","d2",⟨1,2⟩,[20,-10]⟩] := by decide

theorem domainSpecificDenominatorsAndQuanta :
    collect (deriveDomain twoShardInputs ["s1","s2"]) ["d1","d2"] =
      some [⟨"d1",3,[⟨1,2⟩,⟨3,4⟩]⟩,⟨"d2",2,[⟨1,5⟩,⟨2,5⟩]⟩] := by decide

theorem conflictingShardWeightsRejected :
    ticketWeight [⟨"d1","s1",3,⟨1,2⟩,[cell "t1" 1 3 9]⟩,
      ⟨"d1","s2",3,⟨1,2⟩,[cell "t1" 2 3 9]⟩] "t1" = none := by decide

theorem equivalentButDifferentCanonicalWeightsRejected :
    ticketWeight [⟨"d1","s1",2,⟨1,2⟩,[cell "t1" 1 2 9]⟩,
      ⟨"d1","s2",2,⟨1,2⟩,[cell "t1" 2 4 9]⟩] "t1" = none := by decide

theorem conflictingDomainDenominatorsRejected :
    domainDenominator [⟨"d1","s1",3,⟨1,2⟩,[]⟩,⟨"d1","s2",6,⟨1,2⟩,[]⟩] "d1" = none := by decide

theorem duplicateAssignmentRejected :
    qAt (twoShardInputs ++ twoShardInputs) "t1" "d1" "s1" = none := by decide

theorem missingShardRejected : qAt twoShardInputs "t1" "d1" "s3" = none := by decide
theorem wrongDomainRejected : qAt twoShardInputs "t1" "d2" "s1" = none := by decide
theorem missingTicketRejected : qAt twoShardInputs "missing" "d1" "s1" = none := by decide
theorem emptyUniformRejected : uniform ([] : List Int) = none := by decide
theorem negativeLimitRejected : (modelLimit (-1)).isNone = true := by decide
theorem zeroLimitRejected : (modelLimit 0).isNone = true := by decide
theorem tooWideLimitRejected : (modelLimit 9223372036854775808).isNone = true := by decide
theorem signedInt64LimitRepresentable : (modelLimit 9223372036854775807).isSome = true := by decide

theorem noScalarRowTruncation :
    (scalarRows [⟨"t1",⟨1,1⟩,⟨[],.qShard,0⟩⟩] [⟨1,1,[2,3]⟩]).isNone = true := by decide
theorem noRowCountTruncation :
    (scalarRows [] [⟨1,1,[2]⟩]).isNone = true := by decide
theorem noWeightSubstitution :
    (scalarRows [⟨"t1",⟨1,1⟩,⟨[],.qShard,0⟩⟩] [⟨2,1,[2]⟩]).isNone = true := by decide

end DeltaReduce.NativeInputProjectionVectors
