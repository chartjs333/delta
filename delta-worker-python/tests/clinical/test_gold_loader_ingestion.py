from __future__ import annotations

import openpyxl
from deltatorrent.clinical.gold_loader import load_gold_records


def test_famhx_text_adds_pedigree_without_patient_phenotype(tmp_path) -> None:
    workbook_path = tmp_path / "LRRK2.xlsx"
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["pmid", "family_id", "patient_id", "aao", "famhx"])
    worksheet.append(
        [
            "123",
            "family_a",
            "patient_1",
            64,
            "no (but dominant family history of parkinsonian symptoms)",
        ]
    )
    workbook.save(workbook_path)

    records = load_gold_records(gene_files={"LRRK2": workbook_path})

    assert len(records) == 1
    assert records[0].family_history == "positive"
    assert "AUTOSOMAL_DOMINANT_PEDIGREE" in records[0].pedigree_features
    assert "PARKINSONISM" not in records[0].phenotype_features


def test_lrrk2_tremor_column_maps_yes_to_patient_tremor(tmp_path) -> None:
    workbook_path = tmp_path / "LRRK2.xlsx"
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["pmid", "family_id", "individual_id", "clinical_info", "tremor_HP:0001337"])
    worksheet.append(["1", "fam_a", "patient_yes", "yes", "yes"])
    worksheet.append(["1", "fam_a", "patient_no", "yes", "no"])
    worksheet.append(["1", "fam_a", "patient_unknown", "yes", "-99"])
    workbook.save(workbook_path)

    records = load_gold_records(gene_files={"LRRK2": workbook_path})

    by_individual = {record.individual_id: record for record in records}
    assert "TREMOR_OTHER" in by_individual["patient_yes"].phenotype_features
    assert "TREMOR_OTHER" not in by_individual["patient_no"].phenotype_features
    assert "TREMOR_OTHER" not in by_individual["patient_unknown"].phenotype_features
