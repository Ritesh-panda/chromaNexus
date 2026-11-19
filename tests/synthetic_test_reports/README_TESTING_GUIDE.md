# ChronaNexus — 10 Synthetic Medical Reports

All records are fictional and for software testing only. They are not medical advice or real patient records.

Patient: TEST PATIENT 001 | Record ID: SYN-0001
Date range: 12 Jan 2024 to 14 Oct 2026
Files: 10 individual PDFs

## Suggested tests
- PDF extraction, dates, patient identity, document type and section detection
- Timeline ordering across encounters, labs, diagnosis and medication changes
- Lab trend extraction: HbA1c, glucose, renal markers and lipid profile
- Medication start and dose-change tracking
- Radiology impression extraction
- Allergy logic: explicit NKDA in latest note versus earlier missing allergy field
- Provenance: source PDF, date, section and table row

## Expected timeline
- 12-Jan-2024: fatigue and polydipsia; no diabetes diagnosis in that note
- 18-Jan-2024: fasting glucose 128 mg/dL; CBC also available
- 25-Jan-2024: HbA1c 6.7%
- 05-Feb-2024: synthetic type 2 diabetes diagnosis; metformin 500 mg once daily started
- 20-May-2024: lipid profile
- 06-May-2025: HbA1c 7.4%, fasting glucose 154 mg/dL
- 12-May-2025: metformin increased to 500 mg twice daily
- 03-Sep-2025: chest X-ray, no acute cardiopulmonary abnormality
- 14-Oct-2026: HbA1c 6.8%, fasting glucose 132 mg/dL; metformin listed as current

Values, dates and clinical content are fabricated. Reference ranges are illustrative. Do not use these records for clinical care.
