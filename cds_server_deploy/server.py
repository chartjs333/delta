import sys
import os
import subprocess
from pathlib import Path

# ==============================================================================
# AUTO-PROVISIONING LOCAL VIRTUAL ENVIRONMENT (.venv)
# Ensures dependencies are installed in a dedicated local .venv without user friction
# ==============================================================================
def _ensure_local_venv():
    if os.environ.get("SKIP_VENV_BOOTSTRAP") == "1":
        return

    app_dir = Path(__file__).resolve().parent
    venv_dir = app_dir / ".venv"
    is_windows = sys.platform == "win32"
    venv_bin = venv_dir / ("Scripts" if is_windows else "bin")
    venv_python = venv_bin / ("python.exe" if is_windows else "python")

    # Check if current interpreter is already inside the project's .venv
    try:
        is_in_local_venv = (
            Path(sys.prefix).resolve() == venv_dir.resolve() or
            Path(sys.executable).resolve() == venv_python.resolve()
        )
    except Exception:
        is_in_local_venv = False

    if is_in_local_venv:
        return

    # 1. Automatically create .venv if absent
    if not venv_python.exists():
        print("=" * 60)
        print(f"[*] Initializing local Python virtual environment in .venv...")
        try:
            import venv
            venv.create(venv_dir, with_pip=True)
            print("[*] Virtual environment created successfully.")
        except Exception as e:
            print(f"[!] Warning: Could not create venv automatically ({e}).")
            print(f"[!] On Debian/Ubuntu: sudo apt install python3-venv python3-pip")
            print(f"[*] Continuing with current Python environment...")
            return

    # 2. Verify and install dependencies inside .venv if needed
    try:
        subprocess.check_call([str(venv_python), "-c", "import numpy"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("[*] Installing required dependencies in .venv...")
        req_file = app_dir / "requirements.txt"
        if not req_file.exists():
            req_file = app_dir.parent / "requirements.txt"
        
        try:
            if req_file.exists():
                print(f"[*] Installing dependencies from {req_file.name}...")
                subprocess.check_call([str(venv_python), "-m", "pip", "install", "-q", "-r", str(req_file)])
            else:
                print(f"[*] Installing numpy>=1.20.0...")
                subprocess.check_call([str(venv_python), "-m", "pip", "install", "-q", "numpy>=1.20.0"])
            print("[*] Dependencies installed successfully.")
        except Exception as e:
            print(f"[!] Warning: Failed to install requirements ({e}).")
        print("=" * 60)

    # 3. Transparently switch execution into the local virtual environment
    script_path = str(Path(__file__).resolve())
    args = [str(venv_python), "-u", script_path] + sys.argv[1:]
    if not is_windows:
        os.execv(str(venv_python), args)
    else:
        ret = subprocess.call(args)
        sys.exit(ret)

_ensure_local_venv()

import json
import urllib.parse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
DEMO_DIR = Path(__file__).resolve().parent
STATIC_DIR = DEMO_DIR / "static"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

from pipeline_service import ClinicalDecisionSupportPipeline

PORT = int(os.environ.get("PORT", 8005))
HOST = os.environ.get("HOST", "0.0.0.0")
BASE_PATH = os.environ.get("BASE_PATH", "/delta-reduce-demo").strip().rstrip("/")

pipeline = ClinicalDecisionSupportPipeline()

def format_cli_report(res: Dict[str, Any], raw_text: str = "") -> str:
    """Formats clinical decision-support pipeline output into a clean terminal report with offsets."""
    lines = []
    lines.append("=" * 76)
    lines.append("   DELTA-REDUCE CLINICAL DECISION SUPPORT PROTOTYPE — CLI TEST REPORT")
    lines.append("=" * 76)
    
    st = res.get("status", "UNKNOWN")
    lat = res.get("latency_ms", 0)
    audit = res.get("audit_trail", {})
    model = audit.get("model", "N/A")
    gate = audit.get("formal_gate_status", "N/A")
    core = audit.get("revision_core", "6.2")
    
    lines.append(f"STATUS: {st} | Latency: {lat}ms | Model: {model} | Core: {core} | Gate: {gate}")
    reason_codes = res.get("reason_codes", [])
    if reason_codes:
        lines.append(f"REASON CODES: {', '.join(str(code) for code in reason_codes)}")
    if raw_text:
        preview = raw_text.strip().replace("\n", " ")
        if len(preview) > 110:
            preview = preview[:107] + "..."
        lines.append(f"INPUT:  \"{preview}\"")
    lines.append("-" * 76)

    # Clinical Features with character offsets [start:end]
    feats = res.get("clinical_features", [])
    lines.append(f"EXTRACTED CLINICAL FEATURES ({len(feats)}):")
    if feats:
        for f in feats:
            feat_name = f.get("feature", "Unknown")
            stat = f.get("status", "Present")
            subj = f.get("subject", "Patient")
            span = f.get("source_text", "")
            s_offset = f.get("start", -1)
            e_offset = f.get("end", -1)
            offset_str = f"[offset {s_offset}:{e_offset}]" if s_offset >= 0 and e_offset >= s_offset else "[offset N/A]"
            lines.append(f"  • {feat_name:<28} | {stat:<8} ({subj:<7}) | \"{span}\" {offset_str}")
    else:
        lines.append("  (None extracted or approved by formal gate)")
    lines.append("")

    # Molecular Findings
    mol = res.get("molecular_findings", {})
    m_s = mol.get("start", -1)
    m_e = mol.get("end", -1)
    m_offset_str = f"[offset {m_s}:{m_e}]" if m_s >= 0 and m_e >= m_s else ""
    lines.append("MOLECULAR EVIDENCE (Revision 6.2 Deterministic Normalization):")
    lines.append(f"  • Gene:            {mol.get('gene', 'N/A')}")
    lines.append(f"  • Raw Variant:     {mol.get('raw_input', 'N/A')} {m_offset_str}")
    lines.append(f"  • Normalized HGVS: {mol.get('normalized_hgvs', 'N/A')}")
    lines.append(f"  • Transcript:      {mol.get('transcript', 'N/A')}")
    lines.append(f"  • Classification:  {mol.get('classification', 'N/A')}")
    lines.append(f"  • Zygosity:        {mol.get('zygosity', 'N/A')}")
    lines.append(f"  • Parental Origin: {mol.get('parental_origin', 'N/A')}")
    lines.append(f"  • Phase:           {mol.get('phase', 'N/A')}")
    lines.append("")

    # Phenotype Differential (Decoupled Top-5)
    ranking = res.get("phenotype_ranking", []) or []
    lines.append("PHENOTYPE DIFFERENTIAL (Frozen MoFE Decoupled Top-5):")
    classifier_safety = res.get("classifier_safety", {}) or {}
    if classifier_safety:
        lines.append(
            "  Safety status: "
            f"{classifier_safety.get('status', 'UNKNOWN')} | "
            f"Top candidate: {classifier_safety.get('top_candidate', 'N/A')} | "
            f"Classifier score: {classifier_safety.get('classifier_score_pct', 'N/A')}"
        )
    if ranking:
        for idx, r in enumerate(ranking[:5], 1):
            g = r.get("gene", "N/A")
            pct = r.get("score_pct", 0.0)
            name = r.get("full_name", "")
            lines.append(f"  {idx}. {g:<8} — {pct:5.1f}%  ({name})")
    else:
        lines.append("  (Phenotype model ranking unavailable)")
    lines.append("")

    # Concordance
    conc = res.get("concordance", {})
    c_status = conc.get("status", "N/A")
    c_disc = conc.get("discordance_detected", False)
    lines.append(f"CONCORDANCE: {c_status} (Discordance Detected: {c_disc})")
    reasons = conc.get("reasons", [])
    if reasons:
        for r in reasons:
            lines.append(f"  ⚠ {r}")
    lines.append("")

    # Safety Alerts
    alerts = res.get("safety_alerts", [])
    lines.append(f"SAFETY ALERTS ({len(alerts)}):")
    for a in alerts:
        t = a.get("type", "info").upper()
        lines.append(f"  [{t}] {a.get('title', '')}: {a.get('detail', '')}")

    lines.append("=" * 76)
    return "\n".join(lines)

class ClinicalDemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _get_normalized_path(self) -> str:
        p = self.path.split("?")[0]
        # Strip X-Forwarded-Prefix if sent by gateway (prefix displacement)
        fwd_prefix = self.headers.get("X-Forwarded-Prefix", "").strip().rstrip("/")
        if fwd_prefix and p.startswith(fwd_prefix):
            p = p[len(fwd_prefix):] or "/"

        # Strip BASE_PATH or well-known prefixes (e.g. /delta-reduce-demo)
        candidate_prefixes = [BASE_PATH, "/delta-reduce-demo"]
        for cp in candidate_prefixes:
            if cp and p.startswith(cp):
                p = p[len(cp):] or "/"
                break
        return p.rstrip("/") if p != "/" else "/"

    def _resolve_case_text(self, case_param: str = "", offset_param: str = "") -> Tuple[Optional[str], Optional[str]]:
        examples = self._load_examples()
        if not examples:
            return None, None
        
        # 1. Check direct 0-based offset/index parameter
        if offset_param != "":
            try:
                idx = int(offset_param)
                if 0 <= idx < len(examples):
                    return examples[idx].get("text"), examples[idx].get("id")
            except ValueError:
                pass

        # 2. Check case parameter
        if case_param != "":
            # Numeric: 1..5 (1-based index) or 0 (0-based index)
            if case_param.isdigit():
                idx = int(case_param)
                if 1 <= idx <= len(examples):
                    return examples[idx - 1].get("text"), examples[idx - 1].get("id")
                elif idx == 0 and len(examples) > 0:
                    return examples[0].get("text"), examples[0].get("id")
            
            # Keyword / ID matching
            cp = case_param.lower().strip()
            for ex in examples:
                ex_id = ex.get("id", "").lower()
                ex_title = ex.get("title", "").lower()
                if cp == ex_id or cp in ex_id or cp in ex_title:
                    return ex.get("text"), ex.get("id")
        
        return None, None

    def do_GET(self):
        try:
            raw_path = self.path.split("?")[0]
            # Redirect bare prefix e.g. /delta-reduce-demo to /delta-reduce-demo/
            candidate_bases = [BASE_PATH, "/delta-reduce-demo"]
            for cb in candidate_bases:
                if cb and raw_path == cb:
                    self.send_response(301)
                    self.send_header("Location", f"{cb}/")
                    self.end_headers()
                    return

            norm_path = self._get_normalized_path()
            if norm_path == "/api/examples":
                self._send_json_response(self._load_examples())
            elif norm_path == "/api/status":
                self._send_json_response({
                    "status": "ready",
                    "version": "1.0",
                    "core": "Revision 6.2",
                    "schema": "1.1",
                    "nlp_model": getattr(pipeline, "model_name", "gemma-4-26b-a4b-it"),
                    "safety_v2": {
                        "loaded": getattr(pipeline, "safety_artifacts_loaded", False),
                        "error": getattr(pipeline, "safety_artifact_error", ""),
                        "manifest": getattr(pipeline, "safety_manifest", {}),
                    },
                    "base_path": BASE_PATH
                })
            elif norm_path == "/api/test":
                qs = self.path.split("?", 1)[1] if "?" in self.path else ""
                query = urllib.parse.parse_qs(qs)
                case_val = query.get("case", [""])[0]
                offset_val = query.get("offset", query.get("index", [""]))[0]
                text_val = query.get("text", [""])[0]
                format_val = query.get("format", [""])[0].lower()

                resolved_text = None
                case_id = None
                if text_val:
                    resolved_text = text_val
                elif case_val or offset_val:
                    resolved_text, case_id = self._resolve_case_text(case_val, offset_val)

                if not resolved_text:
                    # Return interactive CLI usage guide and available presets
                    examples = self._load_examples()
                    presets = [{"case": i + 1, "offset": i, "id": ex.get("id"), "title": ex.get("title")} for i, ex in enumerate(examples)]
                    guide = {
                        "endpoint": "/api/test",
                        "description": "DeltaReduce CDS CLI / Curl testing endpoint (no browser required)",
                        "supported_parameters": {
                            "case": "1..5 or preset ID (prkn, gch1, atp13a2, gba1, conflict)",
                            "offset": "0..4 (0-based preset offset)",
                            "text": "Raw clinical text to analyze directly",
                            "format": "'text' for formatted terminal report, 'json' for full JSON"
                        },
                        "curl_examples": {
                            "preset_terminal_report": f"curl \"http://localhost:{PORT}/api/test?case=1&format=text\"",
                            "preset_json": f"curl \"http://localhost:{PORT}/api/test?case=1\"",
                            "offset_curl": f"curl \"http://localhost:{PORT}/api/test?offset=0&format=text\"",
                            "gateway_subpath_curl": f"curl \"http://localhost:{PORT}{BASE_PATH}/api/test?case=1&format=text\"",
                            "post_plain_text": f"curl -X POST http://localhost:{PORT}/api/test -H \"Accept: text/plain\" -d \"Male, 32yo early-onset parkinsonism, resting tremor, PRKN c.1072delT.\"",
                            "post_json": f"curl -X POST http://localhost:{PORT}/api/test -H \"Content-Type: application/json\" -d '{{\"text\": \"...\", \"format\": \"text\"}}'"
                        },
                        "available_presets": presets
                    }
                    if format_val == "text" or "text/plain" in self.headers.get("Accept", ""):
                        txt_guide = (
                            "============================================================================\n"
                            " DELTA-REDUCE CDS CLI / CURL TESTING GUIDE\n"
                            "============================================================================\n"
                            "Usage:\n"
                            f"  curl \"http://localhost:{PORT}/api/test?case=1&format=text\"\n"
                            f"  curl \"http://localhost:{PORT}/api/test?offset=0&format=text\"\n"
                            f"  curl \"http://localhost:{PORT}{BASE_PATH}/api/test?case=1&format=text\"\n"
                            f"  curl -X POST http://localhost:{PORT}/api/test -H \"Accept: text/plain\" -d \"Male 32yo parkinsonism...\"\n\n"
                            "Available Presets (case 1..5 / offset 0..4):\n"
                        )
                        for p in presets:
                            txt_guide += f"  [{p['case']}] offset={p['offset']} | id={p['id']}: {p['title']}\n"
                        txt_guide += "============================================================================\n"
                        self._send_text_response(txt_guide)
                    else:
                        self._send_json_response(guide)
                    return

                res = pipeline.analyze_case(resolved_text)
                if case_id:
                    res["case_id"] = case_id

                if format_val == "text" or "text/plain" in self.headers.get("Accept", ""):
                    self._send_text_response(format_cli_report(res, resolved_text))
                else:
                    res["cli_report"] = format_cli_report(res, resolved_text)
                    self._send_json_response(res)
                return

            elif norm_path == "/" or norm_path == "":
                self.path = "/index.html"
                return super().do_GET()
            else:
                self.path = norm_path
                return super().do_GET()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_POST(self):
        try:
            norm_path = self._get_normalized_path()
            if norm_path == "/api/test":
                content_length = int(self.headers.get("Content-Length", 0))
                post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

                qs = self.path.split("?", 1)[1] if "?" in self.path else ""
                query = urllib.parse.parse_qs(qs)

                text_val = ""
                case_val = query.get("case", [""])[0]
                offset_val = query.get("offset", query.get("index", [""]))[0]
                format_val = query.get("format", [""])[0].lower()

                content_type = self.headers.get("Content-Type", "")
                if post_body:
                    clean_body = post_body.strip()
                    if clean_body.startswith(r'{\"') or r'\"' in clean_body:
                        clean_body = clean_body.replace(r'\"', '"')
                    if "application/json" in content_type or clean_body.startswith("{"):
                        try:
                            payload = json.loads(clean_body)
                            text_val = payload.get("text", "")
                            if not case_val and payload.get("case") is not None:
                                case_val = str(payload.get("case"))
                            if not offset_val and payload.get("offset") is not None:
                                offset_val = str(payload.get("offset"))
                            if not format_val and payload.get("format"):
                                format_val = str(payload.get("format")).lower()
                        except Exception:
                            text_val = post_body.strip()
                    elif "application/x-www-form-urlencoded" in content_type:
                        form = urllib.parse.parse_qs(post_body)
                        if "text" in form:
                            text_val = form.get("text", [""])[0]
                        elif "=" not in post_body:
                            text_val = post_body.strip()
                        if not case_val and form.get("case"):
                            case_val = form.get("case", [""])[0]
                        if not offset_val and form.get("offset"):
                            offset_val = form.get("offset", [""])[0]
                        if not format_val and form.get("format"):
                            format_val = form.get("format", [""])[0].lower()
                    else:
                        text_val = post_body.strip()

                resolved_text = None
                case_id = None
                if text_val:
                    resolved_text = text_val
                elif case_val or offset_val:
                    resolved_text, case_id = self._resolve_case_text(case_val, offset_val)

                if not resolved_text:
                    self._send_json_response({
                        "error": "Missing input. Provide clinical text in POST body, or JSON {'text': '...'}, or pass ?case=1",
                        "usage": f"curl -X POST http://localhost:{PORT}/api/test -d \"Male, 32yo early-onset parkinsonism, resting tremor, PRKN c.1072delT.\""
                    }, status_code=400)
                    return

                res = pipeline.analyze_case(resolved_text)
                if case_id:
                    res["case_id"] = case_id

                if format_val == "text" or "text/plain" in self.headers.get("Accept", ""):
                    self._send_text_response(format_cli_report(res, resolved_text))
                else:
                    res["cli_report"] = format_cli_report(res, resolved_text)
                    self._send_json_response(res)
                return

            elif norm_path == "/api/analyze":
                content_length = int(self.headers.get("Content-Length", 0))
                post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    if post_body.strip().startswith("{"):
                        payload = json.loads(post_body)
                        text = payload.get("text", "")
                    else:
                        text = post_body.strip()
                    result = pipeline.analyze_case(text)
                    self._send_json_response(result)
                except Exception as e:
                    self._send_json_response({
                        "status": "ABSTAIN",
                        "abstention": {"is_withheld": True, "reason": f"Analysis failed: {str(e)}"},
                        "audit_trail": {"error": str(e)}
                    }, status_code=200)

            elif norm_path == "/api/recalculate":
                content_length = int(self.headers.get("Content-Length", 0))
                post_body = self.rfile.read(content_length).decode("utf-8")
                try:
                    state = json.loads(post_body)
                    updated = pipeline.recalculate_case(state)
                    self._send_json_response(updated)
                except Exception as e:
                    self._send_json_response({
                        "status": "ERROR",
                        "abstention": {"is_withheld": True, "reason": f"Recalculation error: {str(e)}"}
                    }, status_code=200)
            else:
                self.send_error(404, f"Endpoint not found: {self.path}")
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _send_text_response(self, text_body: str, status_code: int = 200):
        try:
            body = text_body.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Forwarded-Prefix")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Forwarded-Prefix")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Forwarded-Prefix")
            self.end_headers()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _load_examples(self):
        ex_path = DEMO_DIR / "examples.json"
        if ex_path.exists():
            try:
                return json.loads(ex_path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

def run_server():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, ClinicalDemoHandler)
    print(f"============================================================")
    print(f"  DeltaReduce Demo v1.0: Clinical Decision Support Prototype")
    print(f"  Server listening on http://{HOST}:{PORT}")
    print(f"  Gateway Sub-path: {BASE_PATH}/")
    print(f"  Core: Revision 6.2 | Contract: Schema 1.1 | Model: {pipeline.model_name}")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
