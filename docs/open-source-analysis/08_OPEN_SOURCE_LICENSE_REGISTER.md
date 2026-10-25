# ChronaNexus — Open-Source License Register & Legal Assessment

> **Document ID:** `08_OPEN_SOURCE_LICENSE_REGISTER.md`  
> **Source Documents:** `open-source-references/*/LICENSE*`, `REPOSITORY_MANIFEST.md`  
> **Date:** 2026-10-17  
> **Author:** Open-Source Software Analyst & Legal Risk Specialist  
> **Status:** Authoritative Licensing Inventory  

---

## 1. Purpose & Legal Disclaimer

This document records the exact licensing terms, OSI-compliance status, component-level restrictions, and reuse boundaries for all 14 reference repositories collected in `C:\chromaNexus\open-source-references\`.

> [!WARNING]
> **Legal Disclaimer:** The findings in this document represent technical copyright analysis by software engineers and do not constitute formal legal advice. Where legal uncertainty exists, recommendations default to the most conservative posture to protect ChronaNexus from copyright infringement and license contagion.

---

## 2. Master Repository License Register

| # | Repository Name | Local Directory Path | Root License & Version | OSI Approved? | Commercial Use Permitted? | Copyleft Type | Recommended Reuse Level in ChronaNexus |
|---|---|---|---|---|---|---|---|
| 1 | **Health Assistant** | `open-source-references\health-assistant\` | **Apache-2.0** | **YES** | **YES** | None (Permissive) | **DIRECT CODE ADAPTATION & ASSET REUSE** |
| 2 | **HealthWallet.me** | `open-source-references\healthwallet-me\` | **GPL-3.0** | **YES** | Conditional (Copyleft) | Strong Copyleft | **ARCHITECTURE REFERENCE ONLY** |
| 3 | **Fasten Health (On-Prem)** | `open-source-references\fasten-health\` | **GPL-3.0** | **YES** | Conditional (Copyleft) | Strong Copyleft | **ARCHITECTURE REFERENCE / SEPARATE CONTAINER** |
| 4 | **OwnChart** | `open-source-references\ownchart\` | **PolyForm Noncommercial 1.0.0** | **NO** | **NO (FORBIDDEN)** | Noncommercial Source-Available | **STRICT ARCHITECTURE REFERENCE ONLY (ZERO CODE)** |
| 5 | **ArogyaSutra (DoJ)** | `open-source-references\arogya-sutra\` | **MIT** | **YES** | **YES** | None (Permissive) | **DIRECT CODE ADAPTATION** |
| 6 | **Paperless-ngx** | `open-source-references\paperless-ngx\` | **GPL-3.0** | **YES** | Conditional (Copyleft) | Strong Copyleft | **ARCHITECTURE REFERENCE / CLEAN-ROOM REWRITE** |
| 7 | **RAGFlow** | `open-source-references\ragflow\` | **Apache-2.0** | **YES** | **YES** | None (Permissive) | **DIRECT CODE ADAPTATION & SDK CLIENT** |
| 8 | **OpenEMR** | `open-source-references\openemr\` | **GPL-2.0 / GPL-3.0** | **YES** | Conditional (Copyleft) | Strong Copyleft | **ARCHITECTURE REFERENCE ONLY** |
| 9 | **OpenMRS** | `open-source-references\openmrs\` | **MPL-2.0** | **YES** | **YES** | Weak (File-Level Copyleft) | **ARCHITECTURE REFERENCE ONLY** |
| 10 | **Medplum** | `open-source-references\medplum\` | **Apache-2.0** | **YES** | **YES** | None (Permissive) | **DIRECT NPM IMPORT & CODE REUSE** |
| 11 | **OHIF Viewer** | `open-source-references\ohif-viewer\` | **MIT** | **YES** | **YES** | None (Permissive) | **DEFERRED (Phase 4 Direct Reuse)** |
| 12 | **Orthanc** | `open-source-references\orthanc\` | **GPL-3.0 (with OpenSSL exception)** | **YES** | Conditional (Copyleft) | Strong Copyleft | **DEFERRED (Phase 4 Separate Service)** |
| 13 | **GNU Health** | `open-source-references\gnu-health\` | **GPL-3.0+** | **YES** | Conditional (Copyleft) | Strong Copyleft | **ARCHITECTURE REFERENCE ONLY** |
| 14 | **ArogyaSutra (IITP)** | `open-source-references\arogyasutra-iitp\` | **No Root License (All Rights Reserved)** | **NO** | **NO (UNKNOWN)** | Unlicensed Proprietary | **RESEARCH ONLY / ZERO CODE ADOPTION** |

---

## 3. Deep-Dive Legal Assessment by License Category

### 3.1 Category A: Fully Permissive Licenses (Apache-2.0 & MIT)
*Repositories:* **Health Assistant**, **Medplum**, **RAGFlow**, **ArogyaSutra (DoJ)**, **OHIF Viewer**.

- **Legal Posture:** Permissive licenses grant perpetual, worldwide, royalty-free rights to use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software.
- **Requirements:**
  1. Retain the original copyright notices and disclaimers.
  2. For Apache-2.0 works: Include a copy of the Apache-2.0 license, retain any `NOTICE` file content, and state clearly if any files were modified.
  3. Patent grants: Apache-2.0 includes an express mutual patent grant that protects adopters from patent claims by contributors.
- **Application to ChronaNexus:** Code and data assets from Health Assistant (LOINC biomarker catalogs, RRF search tools), Medplum (TypeScript FHIR models), RAGFlow (BM25 algorithms), and ArogyaSutra DoJ (Self-RAG prompts) can be safely adapted and incorporated directly into ChronaNexus's codebase.

---

### 3.2 Category B: Strong Copyleft Licenses (GNU GPL-2.0 & GPL-3.0)
*Repositories:* **HealthWallet.me**, **Fasten Health**, **Paperless-ngx**, **OpenEMR**, **Orthanc**, **GNU Health**.

- **Legal Posture:** GPL requires that any "derivative work" or combined software based on the licensed code must also be licensed under the GPL and make its complete source code available upon distribution.
- **The "Viral" Boundary:**
  - *Direct Source Copying:* Copying source files from Fasten Health, Paperless, or HealthWallet into ChronaNexus would legally compel ChronaNexus to be licensed under GPL-3.0.
  - *Network Service Boundary:* Under standard GPL-3.0 (unlike AGPL), running an independent GPL program as a separate service or Docker container communicating over HTTP/REST does *not* infect the caller with copyleft obligations.
- **Application to ChronaNexus:**
  - **Do NOT copy source code** from these repositories into ChronaNexus.
  - Paperless-ngx, Fasten Health, and Orthanc may be run as separate network-isolated services if needed in future phases.
  - Algorithms and patterns (such as Paperless's deskewing logic or HealthWallet's SQLite schema) may be studied and implemented as **clean-room original code** in Python without copyright infringement.

---

### 3.3 Category C: Source-Available / Noncommercial Licenses
*Repository:* **OwnChart** (PolyForm Noncommercial License 1.0.0).

- **Legal Posture:** **PolyForm Noncommercial is NOT an open-source license.** Section 5 explicitly limits permitted use to noncommercial purposes. Section 5.1 defines commercial use as including any deployment by a business, any hosted service, any commercial derivative product, or any institutional deployment.
- **Hazard Analysis:** If ChronaNexus ever incorporates code from OwnChart, ChronaNexus could never be commercialized, deployed by a clinic, integrated into a healthcare enterprise, or offered as a paid service without explicit written permission and licensing fees paid to Nick Dawson.
- **Application to ChronaNexus:**
  - **ZERO lines of code or data files may be copied from OwnChart.**
  - OwnChart's high-level architectural philosophy (combining life events with health records) is an uncopyrightable concept and can be implemented completely independently from scratch.

---

### 3.4 Category D: Unlicensed / Missing License
*Repository:* **ArogyaSutra (IITP-CSE)**.

- **Legal Posture:** Although public on GitHub, the repository lacks a root `LICENSE` file. Under international copyright law (Berne Convention), the absence of a license means all rights are reserved by the authors (IIT Patna).
- **Application to ChronaNexus:** Zero code or weights may be copied or distributed from this repository. It serves solely as an academic research reference.

---

## 4. Third-Party Dependency & Model Licensing Cautions

1. **Neural Embedding Weights (`BAAI/bge-small-en-v1.5`):**
   - The proposed local embedding model BGE-small-en-v1.5 is licensed under **Apache-2.0**. It is 100% commercially usable and free of restrictive dataset constraints.
2. **ONNX Runtime:**
   - Distributed under **MIT License**. Fully compatible.
3. **Clinical Terminologies (LOINC, SNOMED-CT, RxNorm):**
   - LOINC is free for commercial and noncommercial use worldwide under the Regenstrief Institute LOINC License.
   - RxNorm is produced by the US National Library of Medicine (NLM) and is in the public domain.
   - SNOMED-CT requires an affiliate license in non-member countries; ChronaNexus avoids direct bundling of raw SNOMED distribution tables and relies on LOINC and ICD-10.
