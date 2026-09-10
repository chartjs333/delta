import json
import sys
from pathlib import Path

# Add root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_service import ClinicalDecisionSupportPipeline

def test_pipeline():
    p = ClinicalDecisionSupportPipeline()
    ex_file = Path(__file__).resolve().parent / "examples.json"
    examples = json.loads(ex_file.read_text(encoding="utf-8"))

    print(f"Loaded {len(examples)} demo examples.")
    for ex in examples:
        print(f"\n==================================================")
        print(f"CASE: {ex['title']}")
        print(f"INPUT: {ex['text']}")
        res = p.analyze_case(ex['text'])
        print(f"STATUS: {res['status']} | LATENCY: {res['latency_ms']} ms")
        print(f"EXTRACTED FEATURES ({len(res['clinical_features'])}):")
        for f in res['clinical_features']:
            print(f"  • {f['feature']} | Status: {f['status']} | Subject: {f['subject']} | Span: \"{f['source_text']}\"")
        
        mol = res['molecular_findings']
        print(f"MOLECULAR FINDING:")
        print(f"  • Gene: {mol['gene']}")
        print(f"  • Raw Input: {mol['raw_input']}")
        print(f"  • Normalized HGVS: {mol['normalized_hgvs']}")
        print(f"  • Transcript: {mol['transcript']}")
        print(f"  • Classification: {mol['classification']}")
        print(f"  • Zygosity: {mol['zygosity']}")
        print(f"  • Parental Origin: {mol['parental_origin']}")
        print(f"  • Phase: {mol['phase']}")

        if res.get('phenotype_ranking'):
            print(f"PHENOTYPE RANKING (Decoupled Top-5):")
            for idx, r in enumerate(res['phenotype_ranking']):
                print(f"  {idx+1}. {r['gene']} — {r['score_pct']}% ({r['full_name']})")
        else:
            print(f"PHENOTYPE RANKING: Unavailable ({res.get('phenotype_model_status')})")

        # Test recalculation
        recalc = p.recalculate_case(res)
        print(f"RECALCULATION: Concordance={recalc['concordance']['status']}")

        conc = res['concordance']
        print(f"CONCORDANCE: {conc['status']} (Discordance detected: {conc['discordance_detected']})")
        if conc['reasons']:
            print(f"  Reasons: {conc['reasons']}")

        print(f"SAFETY ALERTS ({len(res['safety_alerts'])}):")
        for a in res['safety_alerts']:
            print(f"  [{a['type'].upper()}] {a['title']}: {a['detail']}")

        abst = res['abstention']
        print(f"ABSTENTION: Withheld={abst['is_withheld']} (Reason: {abst['reason']})")
        
        audit = res['audit_trail']
        print(f"AUDIT TRAIL: Model={audit['model']} | Schema={audit['schema']} | Gate={audit['formal_gate_status']} | Core={audit['revision_core']}")

    print("\nAll 5 cases executed successfully!")

if __name__ == "__main__":
    test_pipeline()
