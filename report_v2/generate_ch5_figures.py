import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Global style setup
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9

def create_fig5_1():
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis('off')

    # Background canvas
    fig.patch.set_facecolor('#ffffff')

    # Boxes styling
    def draw_box(x, y, w, h, title, subtitle, color, text_color='#1e293b'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2,rounding_size=2",
                                      facecolor=color, edgecolor='#475569', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.62, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color=text_color)
        ax.text(x + w/2, y + h*0.30, subtitle, ha='center', va='center', fontsize=7.5, color='#334155', style='italic')

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(facecolor='#0284c7', edgecolor='#0369a1', width=1.5, headwidth=6, headlength=7))
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 2, label, ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#0369a1')

    # Step 1: Input Document
    draw_box(2, 28, 18, 16, "Medical PDF Upload", "Multi-page Encounter\nLab / Discharge", "#f8fafc")
    
    # Arrow to Dual Hashing
    draw_arrow(20, 36, 26, 36)

    # Step 2: Dual Cryptographic Hashing
    draw_box(26, 28, 22, 16, "Dual SHA-256 Hasher", "Binary Hash: Exact Dups\nText Hash: Re-prints", "#e0f2fe")
    
    # Branching
    # Conflict check
    draw_arrow(37, 28, 37, 14)
    draw_box(26, 2, 22, 10, "Hash Conflict Guard", "HTTP 409 Conflict\nZero Duplicate Storage", "#fee2e2", "#991b1b")

    # Proceed Arrow
    draw_arrow(48, 36, 54, 36, "Verified Unique")

    # Step 3: PyMuPDF Vector Cell Extraction
    draw_box(54, 28, 20, 16, "PyMuPDF Vector Parser", "Cell Boundary Tracing\nTable Structure Extraction", "#ecfdf5")

    # Arrow to Output Structuring
    draw_arrow(74, 36, 80, 36)

    # Step 4: Output Representation
    draw_box(80, 28, 18, 16, "Ingested Vault Record", "Atomic Markdown Tables\nAmbient Prose Chunks", "#eff6ff")

    # Explanatory lower banner
    rect_info = patches.FancyBboxPatch((54, 2), 44, 20, boxstyle="round,pad=1.2,rounding_size=2",
                                      facecolor='#f1f5f9', edgecolor='#94a3b8', linewidth=1)
    ax.add_patch(rect_info)
    ax.text(76, 17, "Vector Path Tracing vs. Traditional OCR", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1e293b')
    ax.text(76, 10, "• Identifies geometric cell coordinates directly from PDF drawing commands.\n• Prevents character splitting across numerical decimals and analyte units.\n• Formats lab panels into isolated, atomic markdown table rows.",
            ha='center', va='center', fontsize=7, color='#475569')

    plt.tight_layout()
    plt.savefig('C:/chromaNexus/report_v2/figures/fig5_1_ingestion.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_fig5_2():
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    def draw_box(x, y, w, h, title, subtitle, color, text_color='#1e293b'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2,rounding_size=2",
                                      facecolor=color, edgecolor='#475569', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.62, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color=text_color)
        ax.text(x + w/2, y + h*0.30, subtitle, ha='center', va='center', fontsize=7.5, color='#334155', style='italic')

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(facecolor='#0284c7', edgecolor='#0369a1', width=1.5, headwidth=6, headlength=7))
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 2, label, ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#0369a1')

    # Step 1: Raw Observation
    draw_box(2, 28, 18, 17, "Raw Extraction", "Term: 'FBS'\nVal: 7.2 | Unit: 'mmol/L'", "#f8fafc")
    draw_arrow(20, 36.5, 26, 36.5)

    # Step 2: Canonical Ontology Resolution
    draw_box(26, 28, 22, 17, "Ontology Alignment", "Exact & Fuzzy Catalog\nLOINC: 4548-4 / Fasting Glucose", "#e0f2fe")
    draw_arrow(48, 36.5, 54, 36.5)

    # Step 3: Stoichiometric Conversion
    draw_box(54, 28, 20, 17, "Stoichiometric Unit Map", "mmol/L -> mg/dL (x 18.0182)\n7.2 mmol/L = 129.7 mg/dL", "#fef3c7")
    draw_arrow(74, 36.5, 80, 36.5)

    # Step 4: Reference Range & Status
    draw_box(80, 28, 18, 17, "Clinical Status Flag", "Ref: 70 - 99 mg/dL\nFlag: HIGH (Hyperglycemic)", "#fee2e2", "#991b1b")

    # Three-Pillar Ontology Box below
    rect_loinc = patches.FancyBboxPatch((2, 4), 30, 18, boxstyle="round,pad=1.2,rounding_size=2", facecolor='#ecfdf5', edgecolor='#10b981', linewidth=1.5)
    ax.add_patch(rect_loinc)
    ax.text(17, 18, "LOINC Standard", ha='center', va='center', fontsize=9, fontweight='bold', color='#065f46')
    ax.text(17, 10, "Standardizes laboratory analytes\n(e.g., Creatinine, HbA1c, Lipids)\nwith canonical reference intervals.", ha='center', va='center', fontsize=7.5, color='#047857')

    rect_rxnorm = patches.FancyBboxPatch((35, 4), 30, 18, boxstyle="round,pad=1.2,rounding_size=2", facecolor='#f0fdf4', edgecolor='#16a34a', linewidth=1.5)
    ax.add_patch(rect_rxnorm)
    ax.text(50, 18, "RxNorm Standard", ha='center', va='center', fontsize=9, fontweight='bold', color='#14532d')
    ax.text(50, 10, "Standardizes active pharmaceutical\ningredients, brand synonyms, and\nclinical dosage forms (e.g., Metformin).", ha='center', va='center', fontsize=7.5, color='#15803d')

    rect_icd = patches.FancyBboxPatch((68, 4), 30, 18, boxstyle="round,pad=1.2,rounding_size=2", facecolor='#eff6ff', edgecolor='#2563eb', linewidth=1.5)
    ax.add_patch(rect_icd)
    ax.text(83, 18, "ICD-10-CM Standard", ha='center', va='center', fontsize=9, fontweight='bold', color='#1e40af')
    ax.text(83, 10, "Standardizes chronic diagnostic\nentities (e.g., E11.9 for Type 2\nDiabetes Mellitus).", ha='center', va='center', fontsize=7.5, color='#1d4ed8')

    plt.tight_layout()
    plt.savefig('C:/chromaNexus/report_v2/figures/fig5_2_normalization.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_fig5_3():
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    def draw_box(x, y, w, h, title, subtitle, color, text_color='#1e293b'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2,rounding_size=2",
                                      facecolor=color, edgecolor='#475569', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.62, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color=text_color)
        ax.text(x + w/2, y + h*0.30, subtitle, ha='center', va='center', fontsize=7.5, color='#334155', style='italic')

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(facecolor='#0284c7', edgecolor='#0369a1', width=1.5, headwidth=6, headlength=7))
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 2, label, ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#0369a1')

    # Step 1: SQL Execution Request
    draw_box(2, 28, 20, 17, "SQL Execution Call", "Engine.execute(statement)\nPytest Runner Active", "#f8fafc")
    draw_arrow(22, 36.5, 28, 36.5)

    # Step 2: SQLAlchemy Event Hook
    draw_box(28, 28, 22, 17, "before_cursor_execute", "Intercepts cursor query\nExtracts target DB URI", "#e0f2fe")
    draw_arrow(50, 36.5, 56, 36.5)

    # Step 3: Security Policy Decision
    draw_box(56, 28, 20, 17, "Context Evaluator", "Test Runner Flagged?\nTarget == chronanexus.db?", "#fef3c7")
    
    # Safe branch (SELECT)
    draw_arrow(76, 40, 82, 40, "SELECT")
    draw_box(82, 34, 16, 12, "Allow Query", "Safe read execution\nTest continues", "#ecfdf5", "#065f46")

    # Blocked branch (MUTATION)
    draw_arrow(66, 28, 66, 16, "MUTATION")
    draw_box(54, 4, 24, 12, "Raise MutationBlockedError", "Aborts statement\nPrevents test DB corruption", "#fee2e2", "#991b1b")

    # Lower info box
    rect_info = patches.FancyBboxPatch((2, 4), 48, 18, boxstyle="round,pad=1.2,rounding_size=2",
                                      facecolor='#f1f5f9', edgecolor='#94a3b8', linewidth=1)
    ax.add_patch(rect_info)
    ax.text(26, 18, "Deterministic Safety Isolation", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1e293b')
    ax.text(26, 10, "• Intercepts INSERT, UPDATE, DELETE, DROP, and ALTER statements.\n• Prevents automated test suites from mutating live clinic state.\n• Verified across all 190 unit and integration tests.",
            ha='center', va='center', fontsize=7.2, color='#475569')

    plt.tight_layout()
    plt.savefig('C:/chromaNexus/report_v2/figures/fig5_3_interceptor.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    create_fig5_1()
    create_fig5_2()
    create_fig5_3()
    print("Generated fig5_1, fig5_2, and fig5_3 successfully!")
