# ChronaNexus Forensic Audit Dossier ? Frontend & User-Visible Audit

**Document ID:** `10_FRONTEND_AND_API_AUDIT.md`  
**Audit Standard:** Zero-Fabrication Forensic Audit  
**Date of Execution:** 2026-10-18T17:30:00+05:30  

---

## 1. Frontend Route Inventory & API Connectivity

The frontend is a Single Page Application (SPA) built with React 19, Vite, and Tailwind CSS 4 (`src/App.tsx`):

| Route Path | Page Component | Stated Purpose | Backend API Target | Fallback on Failure | Verified Status |
|---|---|---|---|---|---|
| `/` | `LandingPage.tsx` | Marketing & platform introduction | None (Static) | N/A | `VERIFIED ? STATIC` |
| `/login` | `LoginPage.tsx` | User authentication | `POST /auth/login` | Mock auth token | `PARTIALLY VERIFIED` |
| `/signup` | `SignupPage.tsx` | Account registration | `POST /auth/register` | Mock registration | `PARTIALLY VERIFIED` |
| `/dashboard` | `DashboardPage.tsx` | Overview: vitals, recent reports, stats | `GET /patients/me`, `GET /reports` | `MOCK_PATIENT`, `MOCK_REPORTS` | `PARTIALLY VERIFIED` |
| `/vault` | `VaultPage.tsx` | Document upload dropzone & vault | `POST /documents/upload` | Simulated progress | `PARTIALLY VERIFIED` |
| `/reports` | `ReportsPage.tsx` | Filterable medical report repository | `GET /reports` | `MOCK_REPORTS` | `PARTIALLY VERIFIED` |
| `/timeline` | `TimelinePage.tsx` | Longitudinal medical history timeline | `GET /timeline` | `MOCK_TIMELINE_EVENTS` | `PARTIALLY VERIFIED` |
| `/chat` | `ChatPage.tsx` | Clinical AI Assistant conversational RAG | `POST /chat/conversations/...` | Mock echo reply | `PARTIALLY VERIFIED` |
| `/doctor-summary`| `DoctorSummaryPage.tsx`| One-click 60-second physician handover | `POST /summaries/generate` | `MOCK_SUMMARY` | `PARTIALLY VERIFIED` |
| `/profile` | `ProfilePage.tsx` | Patient demographics, conditions, meds | `GET /patients/me` | `MOCK_PATIENT` | `PARTIALLY VERIFIED` |
| `/settings` | `SettingsPage.tsx` | Notification & privacy preferences | `PUT /users/me` | Local state update | `PARTIALLY VERIFIED` |

---

## 2. Forensic Analysis of the Silent Mock Fallback Defect

### Code Evidence
In `src/services/report.service.ts:45`:
```typescript
async getReports(category?: string, search?: string): Promise<MedicalReport[]> {
  try {
    const response = await api.get('/reports', { params });
    return response.data;
  } catch {
    // SILENT CATCH: Fall back to hardcoded mock reports
    let reports = [...MOCK_REPORTS];
    return reports;
  }
}
```

In `src/services/patient.service.ts:16`:
```typescript
async getProfile(): Promise<{ user: User; patient: Patient }> {
  try {
    const [userRes, patientRes] = await Promise.all([
      api.get<User>('/users/me'),
      api.get<Patient>('/patients/me'),
    ]);
    if (userRes.data && patientRes.data) return { user: userRes.data, patient: patientRes.data };
  } catch {
    // SILENT CATCH: Fall back to hardcoded mock patient
  }
  return { user: MOCK_USER, patient: MOCK_PATIENT };
}
```

### User Impact & Deception Risk
If the FastAPI backend is completely offline or terminates with HTTP 500 errors, the web application renders green success badges, populated charts, and medical reports. The user has **no indication that the backend is down or that data is not persisting**.

### Recommended Remediation
Remove automatic mock fallbacks from production API services. Display an explicit error toast (`useToast()`) and render `<ErrorState message="Backend service unavailable" retry={refetch} />`.
