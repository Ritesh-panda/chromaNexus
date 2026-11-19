import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

# Set global style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9

output_dir = r"C:\chromaNexus\report_v2\figures"
os.makedirs(output_dir, exist_ok=True)

# -------------------------------------------------------------
# 1. Figure 3.2: UML Activity Diagram (Multi-Modal Workflow)
# -------------------------------------------------------------
def generate_fig3_2():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 85)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    # Swimlanes
    swimlanes = [
        ("Actor: Clinician / Patient", 0, 27, '#f8fafc', '#94a3b8'),
        ("Gateway & Frontend Client", 27, 27, '#f1f5f9', '#94a3b8'),
        ("Processing & Verification Pipeline", 54, 30, '#e2e8f0', '#94a3b8'),
        ("Data & Knowledge Stores", 84, 26, '#f8fafc', '#94a3b8')
    ]
    for title, x, w, bg, edge in swimlanes:
        rect = patches.Rectangle((x, 2), w, 81, facecolor=bg, edgecolor=edge, linewidth=1.2, linestyle='--')
        ax.add_patch(rect)
        ax.text(x + w/2, 80.5, title, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1e293b')

    # Helper functions
    def draw_action(x, y, w, h, text, sub=""):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=2.5",
                                      facecolor='#ffffff', edgecolor='#2563eb', linewidth=1.4)
        ax.add_patch(rect)
        if sub:
            ax.text(x + w/2, y + h*0.62, text, ha='center', va='center', fontsize=8, fontweight='bold', color='#1e293b')
            ax.text(x + w/2, y + h*0.28, sub, ha='center', va='center', fontsize=6.8, color='#475569', style='italic')
        else:
            ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=8, fontweight='bold', color='#1e293b')

    def draw_decision(x, y, size, label):
        poly = patches.Polygon([[x, y+size/2], [x+size/2, y+size], [x+size, y+size/2], [x+size/2, y]],
                               facecolor='#fef3c7', edgecolor='#d97706', linewidth=1.3)
        ax.add_patch(poly)
        ax.text(x + size/2, y + size/2, label, ha='center', va='center', fontsize=6.8, fontweight='bold', color='#92400e')

    def draw_arrow(x1, y1, x2, y2, label="", color='#0284c7'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(facecolor=color, edgecolor=color, width=1.3, headwidth=5, headlength=6))
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 1.2, label, ha='center', va='bottom', fontsize=7, fontweight='bold', color=color)

    # Initial State
    start_circle = patches.Circle((13.5, 75), radius=1.8, facecolor='#1e293b', edgecolor='#0f172a')
    ax.add_patch(start_circle)
    ax.text(13.5, 78, "Start", ha='center', fontsize=7.5, fontweight='bold')

    # Actions in Swimlane 1 & 2
    draw_action(4, 64, 19, 6.5, "Upload PDF Document", "Encounter / Lab Records")
    draw_arrow(13.5, 73.2, 13.5, 70.5)

    draw_arrow(23, 67.25, 30, 67.25)
    draw_action(30, 64, 21, 6.5, "Validate & Hash Payload", "SHA-256 Fingerprint")

    draw_arrow(51, 67.25, 57, 67.25)
    draw_decision(57, 63.5, 7.5, "Dup?")

    # Decision branches
    draw_arrow(64.5, 67.25, 87, 67.25, "[Is Unique]")
    draw_action(87, 64, 20, 6.5, "Store Raw Blob", "PostgreSQL / SQLite")

    draw_arrow(60.75, 63.5, 60.75, 57.5, "[Duplicate]")
    draw_action(48, 52, 25.5, 5.5, "Reject & Surface Error", "HTTP 409 Conflict")
    draw_arrow(48, 54.75, 13.5, 54.75)
    draw_arrow(13.5, 54.75, 13.5, 64)

    # Ingestion flow
    draw_arrow(97, 64, 97, 56)
    draw_action(87, 50, 20, 6, "Vector Indexing", "ChromaDB Embeddings")

    draw_arrow(87, 53, 76, 53)
    draw_action(56, 49.5, 20, 7, "Extract Tables & NER", "PyMuPDF + LOINC Map")

    # Natural language query branch
    draw_action(4, 40, 19, 6.5, "Submit Clinical Query", "Voice / Natural Language")
    draw_arrow(23, 43.25, 30, 43.25)
    draw_action(30, 40, 21, 6.5, "Authenticate & Route", "Bearer JWT Claims")

    draw_arrow(51, 43.25, 57, 43.25)
    draw_action(57, 39.5, 23, 7.5, "Dual-Channel Retrieval", "Semantic BGE + Lexical BM25")
    draw_arrow(80, 43.25, 87, 43.25)
    draw_action(87, 39.5, 20, 7.5, "Query Vector Store", "Reciprocal Rank Fusion")
    draw_arrow(97, 39.5, 97, 34)

    # Verification loop
    draw_action(57, 26, 23, 8, "Asymmetric Verification", "Symbolic Guard + Neural NLI")
    draw_arrow(87, 30, 80, 30)

    draw_decision(64.5, 15, 8, "Pass?")
    draw_arrow(68.5, 26, 68.5, 23)

    # Outcomes
    draw_arrow(64.5, 19, 45, 19, "[Refuted]")
    draw_action(30, 16, 21, 6, "Withhold Claim", "Emit Fail-Closed Audit")

    draw_arrow(72.5, 19, 87, 19, "[Verified]")
    draw_action(87, 16, 20, 6, "Compose Response", "Link Audit Provenance")

    # Final Display
    draw_arrow(40.5, 16, 13.5, 16)
    draw_arrow(87, 16, 75, 10)
    draw_arrow(75, 10, 23, 10)
    draw_action(4, 7, 19, 6.5, "Review Grounded Answer", "Interactive Citation Audit")

    # End State
    end_outer = patches.Circle((13.5, 3), radius=2.2, facecolor='#ffffff', edgecolor='#1e293b', linewidth=1.5)
    end_inner = patches.Circle((13.5, 3), radius=1.3, facecolor='#1e293b', edgecolor='#1e293b')
    ax.add_patch(end_outer)
    ax.add_patch(end_inner)
    draw_arrow(13.5, 7, 13.5, 5.2)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig3_2_activity.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig3_2_activity.png")

# -------------------------------------------------------------
# 2. Figure 4.5: UML Class Diagram
# -------------------------------------------------------------
def generate_fig4_5():
    fig, ax = plt.subplots(figsize=(11, 8.2), dpi=300)
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 85)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    def draw_class(x, y, w, h, class_name, stereotype, attrs, methods, header_color='#e0f2fe', edge_color='#0284c7'):
        # Border
        rect = patches.Rectangle((x, y), w, h, facecolor='#ffffff', edgecolor=edge_color, linewidth=1.4)
        ax.add_patch(rect)
        # Header box
        header_h = h * 0.28
        h_rect = patches.Rectangle((x, y + h - header_h), w, header_h, facecolor=header_color, edgecolor=edge_color, linewidth=1.4)
        ax.add_patch(h_rect)
        
        # Titles
        ax.text(x + w/2, y + h - header_h*0.35, f"<<{stereotype}>>", ha='center', va='center', fontsize=6.8, style='italic', color='#0369a1')
        ax.text(x + w/2, y + h - header_h*0.75, class_name, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0f172a')
        
        # Separator line between attrs and methods
        split_y = y + (h - header_h) * 0.45
        ax.plot([x, x + w], [split_y, split_y], color=edge_color, linewidth=0.8, linestyle=':')
        
        # Attributes
        curr_y = y + h - header_h - 2.5
        for attr in attrs:
            ax.text(x + 1.2, curr_y, attr, ha='left', va='center', fontsize=6.8, color='#334155', fontfamily='monospace')
            curr_y -= 2.2
            
        # Methods
        curr_y = split_y - 2.5
        for method in methods:
            ax.text(x + 1.2, curr_y, method, ha='left', va='center', fontsize=6.8, color='#1e293b', fontfamily='monospace')
            curr_y -= 2.2

    def draw_assoc(x1, y1, x2, y2, label="", mult1="", mult2=""):
        ax.plot([x1, x2], [y1, y2], color='#475569', linewidth=1.2)
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 1.5, label, ha='center', fontsize=7, color='#0f172a', style='italic')
        if mult1:
            ax.text(x1 + 1.5, y1 - 2, mult1, fontsize=7, fontweight='bold', color='#475569')
        if mult2:
            ax.text(x2 - 3.5, y2 - 2, mult2, fontsize=7, fontweight='bold', color='#475569')

    # Class 1: User / Clinician
    draw_class(4, 56, 30, 25, "UserAccount", "Entity",
               ["- id: UUID", "- email: String", "- role: RoleEnum", "- hashed_pw: String"],
               ["+ verify_token(): Boolean", "+ get_records(): List[Record]", "+ sign_summary(): Token"])

    # Class 2: MedicalDocument
    draw_class(40, 56, 32, 25, "MedicalDocument", "Entity",
               ["- doc_id: UUID", "- sha256_hash: String", "- upload_ts: DateTime", "- encounter_dt: Date"],
               ["+ calculate_hash(): String", "+ extract_tables(): List[Table]", "+ vectorize_text(): Vector"])

    # Class 3: ExtractedTable
    draw_class(77, 56, 29, 25, "ClinicalLabRecord", "Entity",
               ["- record_id: UUID", "- analyte: String", "- value: Float", "- loinc_code: String"],
               ["+ map_loinc(): String", "+ evaluate_bounds(): Status", "+ get_trend(): Delta"])

    # Class 4: ClaimVerifier
    draw_class(4, 12, 32, 30, "EvidenceVerifier", "Service",
               ["- alpha_sym: Float = 0.5", "- beta_neu: Float = 0.5", "- min_conf: Float = 0.85"],
               ["+ extract_claims(txt): List", "+ verify_symbolic(c): Bool", "+ score_nli(c, ev): Float", "+ execute_fusion(): Result"])

    # Class 5: ClinicalTimelineEngine
    draw_class(41, 12, 31, 30, "TimelineEngine", "Service",
               ["- patient_id: UUID", "- memory_window: Int", "- catalog_cache: Dict"],
               ["+ build_chronology(): Tree", "+ detect_anomalies(): List", "+ generate_digest(): String"])

    # Class 6: EmergencyTriageCoordinator
    draw_class(77, 12, 29, 30, "TriageCoordinator", "Service",
               ["- session_id: UUID", "- emergency_mode: Bool", "- radius_km: Float = 15.0"],
               ["+ assess_symptoms(): Level", "+ find_hospitals(): List", "+ dispatch_108_alert(): Ack"])

    # Associations
    draw_assoc(34, 68, 40, 68, "owns", "1", "0..*")
    draw_assoc(72, 68, 77, 68, "contains", "1", "1..*")
    draw_assoc(20, 56, 20, 42, "verifies", "1", "1..*")
    draw_assoc(56, 56, 56, 42, "aggregates", "1..*", "1")
    draw_assoc(36, 27, 41, 27, "queries", "1", "1")
    draw_assoc(72, 27, 77, 27, "escalates", "0..1", "1")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig4_5_class_diagram.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig4_5_class_diagram.png")

# -------------------------------------------------------------
# 3. Figure 4.6: UML Component Diagram
# -------------------------------------------------------------
def generate_fig4_6():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 85)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    def draw_component(x, y, w, h, name, desc="", color='#f0fdf4', edge='#16a34a'):
        # Main box
        rect = patches.Rectangle((x, y), w, h, facecolor=color, edgecolor=edge, linewidth=1.4)
        ax.add_patch(rect)
        # Component icon tabs (UML standard)
        tab_w = 4
        tab_h = 2.2
        t1 = patches.Rectangle((x - 2, y + h - 5), tab_w, tab_h, facecolor=color, edgecolor=edge, linewidth=1.2)
        t2 = patches.Rectangle((x - 2, y + h - 9.5), tab_w, tab_h, facecolor=color, edgecolor=edge, linewidth=1.2)
        ax.add_patch(t1)
        ax.add_patch(t2)
        # Text
        ax.text(x + w/2, y + h*0.62, f"<<component>>\n{name}", ha='center', va='center', fontsize=8.5, fontweight='bold', color='#14532d')
        if desc:
            ax.text(x + w/2, y + h*0.25, desc, ha='center', va='center', fontsize=7, color='#1e293b', style='italic')

    def draw_interface(x, y, name, is_provided=True):
        if is_provided:
            circle = patches.Circle((x, y), radius=1.6, facecolor='#ffffff', edgecolor='#0284c7', linewidth=1.4)
            ax.add_patch(circle)
            ax.text(x, y + 2.8, name, ha='center', fontsize=7, fontweight='bold', color='#0369a1')
        else: # socket
            arc = patches.Arc((x, y), 3.2, 3.2, angle=0, theta1=90, theta2=270, edgecolor='#0284c7', linewidth=1.4)
            ax.add_patch(arc)
            ax.text(x, y + 2.8, name, ha='center', fontsize=7, fontweight='bold', color='#0369a1')

    def draw_port(x, y):
        sq = patches.Rectangle((x - 1, y - 1), 2, 2, facecolor='#ffffff', edgecolor='#475569', linewidth=1)
        ax.add_patch(sq)

    def draw_conn(x1, y1, x2, y2, style='-'):
        ax.plot([x1, x2], [y1, y2], color='#0284c7', linewidth=1.3, linestyle=style)

    # Subsystems
    # 1. UI Component
    draw_component(4, 52, 28, 26, "Presentation Subsystem", "React 19, Tailwind, Audio Capture", '#f8fafc', '#475569')
    draw_port(32, 65)

    # Interface IClientGateway
    draw_interface(41, 65, "IClientGateway", is_provided=True)
    draw_conn(33, 65, 39.4, 65)

    # 2. Gateway Component
    draw_component(49, 52, 29, 26, "API Gateway Kernel", "FastAPI Router, Auth, Rate Limiter", '#eff6ff', '#2563eb')
    draw_port(49, 65)
    draw_conn(42.6, 65, 48, 65)
    draw_port(63.5, 52)

    # Interface IPipeline
    draw_interface(63.5, 42, "IPipelineService", is_provided=True)
    draw_conn(63.5, 51, 63.5, 43.6)

    # 3. Reasoning Kernel
    draw_component(49, 8, 30, 26, "Clinical Reasoning Kernel", "Dual-Channel RAG & Hybrid NLI", '#fefce8', '#ca8a04')
    draw_port(63.5, 34)
    draw_conn(63.5, 40.4, 63.5, 35)

    # 4. Storage Subsystem
    draw_component(85, 48, 22, 30, "Persistence Subsystem", "SQLite Relational + ChromaDB", '#faf5ff', '#9333ea')
    draw_port(85, 63)
    draw_interface(80, 63, "IDataAccess", is_provided=True)
    draw_conn(78, 63, 78.4, 63)
    draw_conn(81.6, 63, 84, 63)

    # Connecting Reasoning to Storage
    draw_port(79, 21)
    draw_conn(79, 21, 96, 21)
    draw_conn(96, 21, 96, 48)

    # 5. External Services
    draw_component(4, 8, 28, 26, "External Connectors", "Edge-TTS + Overpass Geocoder", '#fff1f2', '#e11d48')
    draw_port(32, 21)
    draw_interface(40, 21, "IExternalServices", is_provided=True)
    draw_conn(33, 21, 38.4, 21)
    draw_conn(41.6, 21, 48, 21)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig4_6_component_diagram.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig4_6_component_diagram.png")

# -------------------------------------------------------------
# 4. Figure 6.3: UML State Machine Diagram
# -------------------------------------------------------------
def generate_fig6_3():
    fig, ax = plt.subplots(figsize=(11, 7.2), dpi=300)
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 80)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    def draw_state(x, y, w, h, name, entry="", do="", exit_act=""):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1,rounding_size=3",
                                      facecolor='#ffffff', edgecolor='#0284c7', linewidth=1.4)
        ax.add_patch(rect)
        # Header line
        hdr_h = 4.5
        ax.text(x + w/2, y + h - hdr_h/2, name, ha='center', va='center', fontsize=8.2, fontweight='bold', color='#0f172a')
        ax.plot([x, x + w], [y + h - hdr_h, y + h - hdr_h], color='#0284c7', linewidth=1)
        
        curr_y = y + h - hdr_h - 2.5
        if entry:
            ax.text(x + 1.5, curr_y, f"entry / {entry}", ha='left', va='center', fontsize=6.8, color='#334155')
            curr_y -= 2.2
        if do:
            ax.text(x + 1.5, curr_y, f"do / {do}", ha='left', va='center', fontsize=6.8, color='#334155')
            curr_y -= 2.2
        if exit_act:
            ax.text(x + 1.5, curr_y, f"exit / {exit_act}", ha='left', va='center', fontsize=6.8, color='#334155')

    def draw_transition(x1, y1, x2, y2, label="", color='#0284c7'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(facecolor=color, edgecolor=color, width=1.3, headwidth=5, headlength=6))
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 1.3, label, ha='center', va='bottom', fontsize=6.8, fontweight='bold', color=color)

    # Initial state
    init_dot = patches.Circle((10, 68), radius=1.8, facecolor='#1e293b', edgecolor='#0f172a')
    ax.add_patch(init_dot)

    # State 1: RAW_CLAIM
    draw_state(20, 60, 24, 15, "UNVERIFIED_CLAIM", "normalize_text()", "extract_entities()", "")
    draw_transition(11.8, 68, 20, 68, "ingest_text")

    # State 2: SYMBOLIC_EVAL
    draw_state(54, 60, 26, 15, "SYMBOLIC_EVALUATION", "load_regex_rules()", "check_units_bounds()", "")
    draw_transition(44, 68, 54, 68, "parse_syntax")

    # Decision Pseudostate (Choice)
    choice = patches.Polygon([[88, 68], [91, 71], [94, 68], [91, 65]], facecolor='#fef3c7', edgecolor='#d97706', linewidth=1.2)
    ax.add_patch(choice)
    draw_transition(80, 68, 88, 68)

    # State 3: REFUTED (if symbolic fail)
    draw_state(83, 38, 25, 14, "SYMBOLIC_REFUTED", "", "log_bounds_violation()", "emit_alert()")
    draw_transition(91, 65, 91, 52, "[Contradiction Found]")

    # State 4: RETRIEVAL_FUSION
    draw_state(45, 36, 27, 16, "EVIDENCE_FUSION", "query_vector_store()", "calc_rrf_rank(k=60)", "pair_chunks()")
    draw_transition(88, 68, 72, 48, "[Consistent]")

    # State 5: NEURAL_NLI
    draw_state(8, 36, 27, 16, "NEURAL_NLI_SCORING", "stream_local_slm()", "compute_entailment()", "")
    draw_transition(45, 44, 35, 44, "top_evidence_ready")

    # Final Verification States
    draw_state(8, 8, 27, 14, "GROUNDED_VERIFIED", "stamp_provenance()", "attach_citation_tag()", "")
    draw_transition(21.5, 36, 21.5, 22, "[F1 >= 0.85]")

    draw_state(45, 8, 27, 14, "FAIL_CLOSED_WITHHELD", "emit_warning_notice()", "prompt_clinician_audit()", "")
    draw_transition(28, 36, 48, 22, "[F1 < 0.85]")

    # End State
    end_outer = patches.Circle((95, 15), radius=2.2, facecolor='#ffffff', edgecolor='#1e293b', linewidth=1.5)
    end_inner = patches.Circle((95, 15), radius=1.3, facecolor='#1e293b', edgecolor='#1e293b')
    ax.add_patch(end_outer)
    ax.add_patch(end_inner)

    draw_transition(35, 15, 45, 15)
    draw_transition(72, 15, 92.5, 15, "export_audit")
    draw_transition(95, 38, 95, 17.5)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fig6_3_state_machine.png"), dpi=300, bbox_inches='tight')
    plt.close()
    print("Created fig6_3_state_machine.png")

if __name__ == '__main__':
    generate_fig3_2()
    generate_fig4_5()
    generate_fig4_6()
    generate_fig6_3()
