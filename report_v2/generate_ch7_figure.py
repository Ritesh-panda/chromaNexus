import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9

def create_fig7_1():
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 58)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')

    def draw_tier(y, h, title, subtitle, color, border_color, text_color='#1e293b'):
        rect = patches.FancyBboxPatch((4, y), 92, h, boxstyle="round,pad=1.2,rounding_size=2",
                                      facecolor=color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(10, y + h*0.62, title, ha='left', va='center', fontsize=9.5, fontweight='bold', color=text_color)
        ax.text(10, y + h*0.28, subtitle, ha='left', va='center', fontsize=7.5, color='#334155', style='italic')

    # Tier 5: E2E Functional Validation (Top)
    draw_tier(47, 9, "Tier 5: End-to-End Clinical Journey Validation (TC-01 to TC-20)",
              "Full user journeys: Patient registration, document vault, RAG chat, Odia voice consultation, 108 emergency triage.",
              "#f0fdf4", "#16a34a", "#14532d")

    # Tier 4: Adversarial Grounding & Safety Audits
    draw_tier(36, 9, "Tier 4: Adversarial Clinical Grounding & Abstention Audits",
              "Injected biomarker tests (Troponin), fictitious hospital checks, date manipulation, missing-data fail-closed abstention.",
              "#eff6ff", "#2563eb", "#1e40af")

    # Tier 3: Database Mutation Interceptor Boundary
    draw_tier(25, 9, "Tier 3: Database Protection & Isolation Boundary",
              "SQLAlchemy before_cursor_execute hook blocks mutating SQL statements against production DB during automated runs.",
              "#fef3c7", "#d97706", "#92400e")

    # Tier 2: Automated Backend Testing
    draw_tier(14, 9, "Tier 2: Backend Pytest Automated Test Matrix (190 Tests across 12 Suites)",
              "Structured queries, timeline engine, multi-facility conflict detection, FastEmbed vectors, BM25 Okapi, RRF fusion.",
              "#f8fafc", "#475569", "#0f172a")

    # Tier 1: Static Analysis & Type Checking (Base)
    draw_tier(3, 9, "Tier 1: Static Code Quality & Type Safety Verification",
              "Oxlint linter (0 errors across 77 frontend files), TypeScript strict compiler (0 errors across 2,931 modules).",
              "#f1f5f9", "#64748b", "#334155")

    # Right side badge
    rect_badge = patches.FancyBboxPatch((80, 48), 14, 7, boxstyle="round,pad=0.8,rounding_size=1.5",
                                       facecolor='#dcfce7', edgecolor='#16a34a', linewidth=1.5)
    ax.add_patch(rect_badge)
    ax.text(87, 51.5, "100% PASS\n190 / 190 Tests", ha='center', va='center', fontsize=7.5, fontweight='bold', color='#15803d')

    plt.tight_layout()
    plt.savefig('C:/chromaNexus/report_v2/figures/fig7_1_testing_pyramid.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    create_fig7_1()
    print("Generated fig7_1_testing_pyramid.png successfully!")
