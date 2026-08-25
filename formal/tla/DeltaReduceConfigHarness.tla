---------------------- MODULE DeltaReduceConfigHarness --------------------
EXTENDS DeltaReduce

ConfigSafetyNext ==
    \/ ProposeRoundConfigAction
    \/ PersistConfigVoteAction
    \/ VoteTransportNext
    \/ FinalizeRoundConfigAction

ConfigSafetySpec == Init /\ [][ConfigSafetyNext]_ProtocolVariables

ConfigSafetyTypeOK == TypeOK

=============================================================================
