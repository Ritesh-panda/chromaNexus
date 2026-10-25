# ChronaNexus Forensic Audit Dossier ? Dependency & License Audit

**Document ID:** `12_DEPENDENCY_AND_LICENSE_AUDIT.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Third-Party Installed Dependencies & Licenses

| Dependency Name | Version | License | License Category | Ingestion / Integration Point | Compliance Risk |
|---|---|---|---|---|---|
| **PyMuPDF** (`fitz`) | 1.24.1 | **AGPL-3.0 / Commercial** | Strong Copyleft | `backend/app/ai/extractors/pdf_extractor.py` | **HIGH** if deployed as closed-source service |
| **pypdf** | 4.1.0 | BSD-3-Clause | Permissive | `pdf_extractor.py` fallback | None |
| **FastAPI** | 0.110.0 | MIT | Permissive | `backend/app/main.py` | None |
| **SQLAlchemy** | 2.0.29 | MIT | Permissive | `backend/app/core/database.py` | None |
| **Alembic** | 1.13.1 | MIT | Permissive | `backend/alembic/` | None |
| **React** | 19.0.0 | MIT | Permissive | `src/main.tsx` | None |
| **Tailwind CSS** | 4.0.0 | MIT | Permissive | `src/index.css` | None |
| **Recharts** | 2.15.0 | MIT | Permissive | `src/components/charts/` | None |
| **Lucide React** | 0.468.0 | ISC | Permissive | `src/components/` | None |
| **Axios** | 1.7.9 | MIT | Permissive | `src/services/axios.ts` | None |

---

## 2. Audit of the 14 Studied Reference Repositories

In `docs/open-source-analysis/08_OPEN_SOURCE_LICENSE_REGISTER.md`, 14 open-source repositories were researched:

| Repository Name | Actual License | Status in ChronaNexus | Code Reused? | Risk Assessment |
|---|---|---|---|---|
| **OpenEMR** | GPL-2.0+ | Studied architecture | **NO** ? Zero lines copied | Copyleft if copied |
| **Medplum** | Apache-2.0 | Studied FHIR schema | **NO** ? Zero lines copied | Permissive |
| **LibreHealth** | MPL-2.0 | Studied UI layouts | **NO** ? Zero lines copied | Weak copyleft |
| **Fasten Health** | MIT | Studied patient portal | **NO** ? Zero lines copied | Permissive |
| **HealthWallet.me** | **GPL-3.0 / Restrictive** | Studied PDF parsing | **NO ? STRICTLY AVOIDED** | **CRITICAL COPYLEFT RISK** |
| **Paperless-ngx** | GPL-3.0 | Studied document OCR | **NO** ? Zero lines copied | Copyleft if copied |
| **LangChain / LlamaIndex** | MIT / Apache-2.0 | Studied chunking patterns | **NO** ? Custom chunker implemented | Permissive |

---

## 3. Strict Legal Warning Regarding HealthWallet.me

1. **Inconsistency Flagged:** Previous research notes identified conflicting license headers in HealthWallet.me (GPL-3.0 vs proprietary non-commercial clauses).
2. **Finding:** Forensic inspection of ChronaNexus working tree confirms that **no source code, modules, or assets were copied from HealthWallet.me**. ChronaNexus implemented its own clean-room PyMuPDF extraction and boundary chunker.
3. **Binding Rule:** ChronaNexus developers must continue to **strictly avoid copying any code from HealthWallet.me** or other copyleft repositories without explicit legal clearance.
