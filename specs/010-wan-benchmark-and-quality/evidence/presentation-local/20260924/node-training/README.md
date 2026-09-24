# Node training presentation integration [T051, HR010-001]

This is **LOCAL_DEMO_ONLY**, not a mandatory Feature010 gate or formal authority.
The original MNIST report is copied byte-for-byte from the run initiated through
authenticated public HTTPS. Its SHA-256 is in public-acceptance.json and manifest.json.
Private controller keys and tunnel credentials are excluded.

The four worker processes handled 60,000 training images; the common test set contains
10,000 images. Centralized and distributed accuracy was 82.05%, with byte-exact model
equality and the demonstrated validator crash/replay outcome RECOVERED_AND_APPLIED.
Read the original report's scope/limitations before interpreting the native and
Stage C traces. EEG is synthetic; QLoRA's historical reference is not a current run.

UI source installed from 7ee7bb8; serving/launcher corrections are recorded in
checks.json. demo-source.json records the user's existing dirty MNIST checkout;
integration left those files untouched. Local browser inspection covers navigation,
EN/RU, progress/results and recovery selection. The public smoke uses ordinary TLS
hostname/certificate verification with a public DNS IP override because host DNS
does not resolve the temporary hostname. It makes no external-browser assertion.

An actual owned demo process restart restored the previously saved report. The main
Controller instance and its existing canonical receipt were preserved. The remote
launcher restart action was exercised to deploy the new route, and subsequent start
recovered the presentation host without changing the working tunnel URL.

Self-review only; independent authorities, real WAN and qualifying Feature010
evidence remain outstanding. No protocol or arithmetic implementation was changed.
