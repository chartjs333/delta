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
Controller UI is at http://127.0.0.1:8865/?lang=en#/live-execution.

For the Admin UI segment, click **Open Admin UI**. The same language is carried
over, and the top-right selector supports English and Russian without resetting
the form. **Presentation** returns to the main application in the selected language.

The live Admin opens in **Simple mode**. Keep the prepared synthetic CPU example,
give the run a name, and click **Start training**. Status updates automatically;
**Download receipt** appears only after the existing adapter checks the returned
receipt. **Prepare another run** clears the form after a terminal run. On an
uncertain submission, inspect the technical views instead of blindly resubmitting.
Opening the other execution views preserves this guided run during the session;
leaving the execution page or reloading stops automatic updates. The technical
status list can still inspect runs retained by the current adapter session.

**How DeltaReduce works** opens a six-stage protocol explanation. Click a stage
to explain workers, content IDs, input agreement, shards, aggregation and the
certified checkpoint. This diagram is educational, not a progress display for
the CPU example. The example does not produce ISC, ApplyQC or a current checkpoint.

- **Workloads:** inspect the catalog and model/data compatibility. Sample receipt
  buttons explicitly load examples; they are not fresh execution evidence.
- **Live execution → ExecutionIntent builder:** keep the default synthetic
  10-gene workload and `PLUGIN_BOUNDARY`, then **Submit to Controller**.
  Use **Refresh status** to observe completion and **Load terminal receipt** to
  show the intent/admission/execution lineage. This is actual CPU plugin execution.
- **Controllers:** create a local document and inspect the registry form.
  This is a local worksheet, not live membership or independent authority.
- **Campaigns** is currently unavailable from the local source; it is not an
  implemented campaign execution screen.

Technical IDs, operation codes and original evidence retain their original values.


## Connected Admin walkthrough

Open <http://127.0.0.1:8870/admin/?lang=en#/campaigns>.
Create/select a campaign, choose the supported synthetic 10-gene workload in
Workloads, then select **Use in campaign** and **Start training** in Live execution.
Return to Campaigns to reopen the same execution, download its receipt, or click
**Present this run**. Presentation checks the same Controller result and offers
the same canonical receipt. The local profile saves definitions and run links on
disk; it does not store an authenticated account or grant controller authority.

Click ⓘ beside any field for its purpose and an example. Switch the language to
Russian to show the same workflow and localized guidance. Identifiers and evidence
stay unchanged. Wait for the saved indicator before reloading a changed form.
If another tab changed the profile, reload to resolve the explicit revision conflict.
Controller register entries describe governance; the actual execution target is
the existing local Controller/Worker. Scientific and governance qualification
remain outside this local demonstration.
