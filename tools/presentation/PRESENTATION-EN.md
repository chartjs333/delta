# DeltaReduce: five-minute live demo

Open **http://127.0.0.1:8870/?lang=en**. The language selector at the top right
switches between English and Russian without restarting or resubmitting a job.
The selection is remembered. `START.cmd` opens English explicitly.

1. **Overview.** “This is our working local lab. The Controller is online. We can
   submit an actual training job, inspect its execution receipt, and demonstrate
   controller failures in Docker.”
2. **Run training.** Click the purple button. “The browser sends a training intent
   to the Controller. A separate Python Worker executes a nearest-centroid model
   on synthetic tabular data, using the CPU.” Watch the live log complete.
3. **Download result.** “The result includes the intent, admission, execution ID
   and receipt. Their lineage is checked. The duration shown is measured.”
4. **Run Docker scenarios.** “These are four real processes using temporary test
   signing keys. With four available, we have four signatures. After one failure,
   three remain. After two failures, quorum is absent and the operation is blocked.
   Restarting a controller restores three; its generation and test key change.”
5. **Run history.** Show both saved results. “History survives an interface restart.
   We can download the original records for inspection.”
6. **Feature010 readiness.** “The presentation uses SIMULATED_LOCAL infrastructure.
   These runs do not qualify the full benchmark. Real independent authorities,
   real WAN qualification and the complete native/scientific pipeline are separate
   requirements.”

The GPU card reports the physical device visible on this computer. The training
example on this screen uses CPU; it is not a GPU scientific benchmark. Training
and Docker are separate demonstrations, not a joined Java/native/WAL training run.
The downloaded JSON retains the original evidence, including original log text.
Language changes affect only its display in the application.

If the computer has restarted, open Docker Desktop, then run
`D:\delta-presentation\START.cmd`. Existing history is retained. The advanced
Controller UI is at http://127.0.0.1:8865/.
