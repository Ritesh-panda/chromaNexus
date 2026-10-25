"""
ChronaNexus Clinical Drug & Allergy Cross-Reactivity Catalog
===========================================================
Defines drug classes, active ingredients, common brand names, and immunological
cross-reactivity rules for deterministic patient allergy safety verification.

Enables the retrieval and clinical reasoning engine to detect dangerous prescriptions
(e.g., patient with Penicillin anaphylaxis asking about Amoxicillin or Augmentin).
"""

from typing import Dict, List, Set, Optional, Any
import re


# Drug Class Definitions with member medications and cross-reactive allergens
DRUG_CLASS_CATALOG: Dict[str, Dict[str, Any]] = {
    "penicillins": {
        "class_name": "Penicillin-Class Beta-Lactam Antibacterials",
        "primary_allergen": "Penicillin",
        "synonyms": ["penicillin", "penicillins", "natural penicillins", "aminopenicillins"],
        "members": {
            "penicillin", "penicillin v", "penicillin g", "amoxicillin", "ampicillin",
            "augmentin", "amoxicillin-clavulanate", "amoxicillin/clavulanate",
            "piperacillin", "zosyn", "piperacillin-tazobactam", "oxacillin", "nafcillin",
            "dicloxacillin", "methicillin", "amoxil"
        },
        "cross_reactivity_risk": {
            "cephalosporins": "moderate",  # ~2-5% shared beta-lactam ring cross-reactivity
            "carbapenems": "low"
        }
    },
    "cephalosporins": {
        "class_name": "Cephalosporin-Class Beta-Lactam Antibacterials",
        "primary_allergen": "Cephalosporins",
        "synonyms": ["cephalosporin", "cephalosporins"],
        "members": {
            "cephalexin", "keflex", "cefazolin", "cefuroxime", "ceftriaxone",
            "rocephin", "cefepime", "cefdinir", "cefpodoxime", "cefotaxime"
        },
        "cross_reactivity_risk": {
            "penicillins": "moderate"
        }
    },
    "sulfonamides": {
        "class_name": "Sulfonamide Antibacterials (Sulfa Drugs)",
        "primary_allergen": "Sulfa Drugs",
        "synonyms": ["sulfa", "sulfa drugs", "sulfonamides", "sulfonamide"],
        "members": {
            "sulfamethoxazole", "trimethoprim-sulfamethoxazole", "bactrim", "bactrim ds",
            "septra", "sulfadiazine", "sulfisoxazole"
        },
        "cross_reactivity_risk": {}
    },
    "nsaids": {
        "class_name": "Nonsteroidal Anti-inflammatory Drugs (NSAIDs)",
        "primary_allergen": "NSAIDs / Aspirin",
        "synonyms": ["nsaid", "nsaids", "aspirin", "anti-inflammatory"],
        "members": {
            "ibuprofen", "advil", "motrin", "naproxen", "aleve", "naprosyn",
            "aspirin", "acetylsalicylic acid", "meloxicam", "mobic",
            "celecoxib", "celebrex", "indomethacin", "diclofenac", "voltaren", "ketorolac"
        },
        "cross_reactivity_risk": {}
    },
    "fluoroquinolones": {
        "class_name": "Fluoroquinolone Antibacterials",
        "primary_allergen": "Fluoroquinolones",
        "synonyms": ["fluoroquinolone", "quinolone"],
        "members": {
            "ciprofloxacin", "cipro", "levofloxacin", "levaquin", "moxifloxacin", "avelox"
        },
        "cross_reactivity_risk": {}
    },
    "macrolides": {
        "class_name": "Macrolide Antibacterials",
        "primary_allergen": "Macrolides",
        "synonyms": ["macrolide", "macrolides"],
        "members": {
            "azithromycin", "zithromax", "z-pak", "clarithromycin", "biaxin", "erythromycin"
        },
        "cross_reactivity_risk": {}
    }
}


def find_drug_class(medication_name: str) -> Optional[Dict[str, Any]]:
    """
    Identifies the drug class for a medication name or active ingredient.
    Example: 'Amoxicillin' -> penicillins class dict.
    """
    if not medication_name:
        return None
    
    clean_name = medication_name.strip().lower()
    tokens = set(re.findall(r"\b[a-z0-9\-]+\b", clean_name))

    for class_key, class_info in DRUG_CLASS_CATALOG.items():
        # Check direct membership
        if clean_name in class_info["members"]:
            return class_info
        # Check token intersection
        if tokens.intersection(class_info["members"]):
            return class_info
        # Check synonyms
        if any(syn in clean_name for syn in class_info["synonyms"]):
            return class_info

    return None


def check_drug_allergy_conflict(
    candidate_drug: str,
    patient_allergy_names: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Evaluates whether a candidate drug (e.g. 'Amoxicillin') conflicts with any of the
    patient's documented allergies (e.g. 'Penicillin (Severe: Anaphylaxis)').

    Returns conflict details dict if a match or cross-reactivity is detected, otherwise None.
    
    IMPORTANT CLINICAL SAFETY NOTICE:
    Advisories produced by this function are heuristic clinical decision support warnings
    derived from recorded patient profile data and reference catalogs. They are NOT
    clinically validated nor definitive prescribing or administration decisions.
    Licensed clinician or pharmacist review is strictly required for all medication decisions.
    """
    if not candidate_drug or not patient_allergy_names:
        return None

    clean_drug = candidate_drug.strip().lower()
    if len(clean_drug) < 3:
        return None

    drug_class = find_drug_class(clean_drug)

    for allergy_str in patient_allergy_names:
        if not allergy_str:
            continue
        clean_allergy = allergy_str.strip().lower()

        # Check if allergy is explicitly marked as resolved or inactive
        if "resolved" in clean_allergy or "inactive" in clean_allergy:
            continue

        allergy_tokens = set(re.findall(r"\b[a-z0-9\-]+\b", clean_allergy))

        # 1. Direct name match (e.g. allergy to 'Amoxicillin' and candidate is 'Amoxicillin')
        if clean_drug in allergy_tokens:
            return {
                "conflict_type": "DIRECT_MATCH",
                "candidate_drug": candidate_drug,
                "allergen": allergy_str,
                "severity": "high",
                "is_definitive_decision": False,
                "requires_clinical_review": True,
                "explanation": (
                    f"CLINICAL SAFETY WARNING: Candidate medication '{candidate_drug}' directly matches "
                    f"recorded patient allergy '{allergy_str}'. Automated clinical decision support warning "
                    f"based on recorded patient data; NOT a definitive prescribing decision. Clinician/pharmacist review required."
                )
            }

        # 2. Class-level member conflict (e.g. allergy to 'Penicillin' and candidate is 'Amoxicillin')
        if drug_class:
            primary_allergen_lower = drug_class["primary_allergen"].lower()
            if primary_allergen_lower in clean_allergy or any(syn in clean_allergy for syn in drug_class["synonyms"]):
                return {
                    "conflict_type": "CLASS_CROSS_REACTIVITY",
                    "candidate_drug": candidate_drug,
                    "allergen": allergy_str,
                    "drug_class": drug_class["class_name"],
                    "severity": "severe",
                    "is_definitive_decision": False,
                    "requires_clinical_review": True,
                    "explanation": (
                        f"CLINICAL SAFETY WARNING (CLASS CROSS-REACTIVITY): Candidate medication '{candidate_drug}' "
                        f"belongs to {drug_class['class_name']}. Recorded patient profile documents an allergy to '{allergy_str}'. "
                        f"Potential immunological cross-reactivity detected. This decision-support advisory is based on recorded patient "
                        f"data and catalog rules; it is NOT clinically validated nor a definitive prescribing decision. "
                        f"Clinician or pharmacist review is required prior to prescription or administration."
                    )
                }

            # 3. Inter-class cross-reactivity risk (e.g. Cephalosporin candidate with documented Penicillin allergy)
            for cross_key, risk_level in drug_class.get("cross_reactivity_risk", {}).items():
                if cross_key in DRUG_CLASS_CATALOG:
                    target_catalog = DRUG_CLASS_CATALOG[cross_key]
                    target_allergen_lower = target_catalog["primary_allergen"].lower()
                    if target_allergen_lower in clean_allergy or any(syn in clean_allergy for syn in target_catalog["synonyms"]):
                        return {
                            "conflict_type": "POTENTIAL_CLASS_CROSS_REACTIVITY",
                            "candidate_drug": candidate_drug,
                            "allergen": allergy_str,
                            "drug_class": drug_class["class_name"],
                            "cross_reactive_class": target_catalog["class_name"],
                            "severity": "moderate" if risk_level == "low" else "high",
                            "is_definitive_decision": False,
                            "requires_clinical_review": True,
                            "explanation": (
                                f"CLINICAL SAFETY WARNING (POTENTIAL INTER-CLASS CROSS-REACTIVITY): Candidate medication '{candidate_drug}' "
                                f"belongs to {drug_class['class_name']}, which has documented {risk_level} cross-reactivity risk with "
                                f"{target_catalog['class_name']} ('{allergy_str}'). Clinician or pharmacist review is advised."
                            )
                        }

    return None
