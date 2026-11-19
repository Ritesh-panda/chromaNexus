import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { VitalsTrendChart } from '@/components/charts/VitalsTrendChart';
import { useUI } from '@/contexts/UIContext';
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/contexts/UserContext';
import { reportService } from '@/services/report.service';
import { patientService } from '@/services/patient.service';
import { timelineService } from '@/services/timeline.service';
import type { MedicalReport, Disease, Medication, TimelineEvent } from '@/types';
import {
  MOCK_REPORTS,
  MOCK_DISEASES,
  MOCK_MEDICATIONS,
  MOCK_TIMELINE_EVENTS,
} from '@/constants/mockData';
import {
  FileText,
  Pill,
  GitCommit,
  Bot,
  Upload,
  Stethoscope,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  Eye,
  FolderLock,
  Radio,
  ExternalLink
} from 'lucide-react';
import { motion } from 'framer-motion';
import { alertService, type HealthAlert } from '@/services/alert.service';

export const DashboardPage: React.FC = () => {
  const { setUploadModalOpen } = useUI();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { patient } = useUser();

  const [reports, setReports] = useState<MedicalReport[]>([]);
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [healthAlerts, setHealthAlerts] = useState<HealthAlert[]>([]);

  useEffect(() => {
    let isMounted = true;
    const loadDashboardData = async () => {
      try {
        const [reps, dis, meds, timeline, alerts] = await Promise.all([
          reportService.getReports(),
          patientService.getDiagnoses(),
          patientService.getMedications(),
          timelineService.getTimelineEvents(),
          alertService.getHealthAlerts()
        ]);
        const isDemo = user?.email === 'alex.vance@example.com';
        if (isMounted) {
          setReports(isDemo ? (reps && reps.length > 0 ? reps : MOCK_REPORTS) : (reps || []));
          setDiseases(isDemo ? (dis && dis.length > 0 ? dis : MOCK_DISEASES) : (dis || []));
          setMedications(isDemo ? (meds && meds.length > 0 ? meds : MOCK_MEDICATIONS) : (meds || []));
          setTimelineEvents(isDemo ? (timeline && timeline.length > 0 ? timeline : MOCK_TIMELINE_EVENTS) : (timeline || []));
          setHealthAlerts(alerts || []);
        }
      } catch {
        const isDemo = user?.email === 'alex.vance@example.com';
        if (isMounted) {
          setReports(isDemo ? MOCK_REPORTS : []);
          setDiseases(isDemo ? MOCK_DISEASES : []);
          setMedications(isDemo ? MOCK_MEDICATIONS : []);
          setTimelineEvents(isDemo ? MOCK_TIMELINE_EVENTS : []);
        }
      }
    };
    loadDashboardData();
    return () => { isMounted = false; };
  }, []);

  const dedupedDiseases = React.useMemo(() => {
    const map = new Map<string, Disease>();
    for (const d of diseases) {
      let key = d.name.toLowerCase().trim();
      if (key.includes('type 2 diabetes') || key === 'diabetes') {
        key = 'type 2 diabetes mellitus';
      }
      if (!map.has(key)) {
        map.set(key, d);
      } else {
        if (!map.get(key)!.icdCode && d.icdCode) {
          map.set(key, d);
        }
      }
    }
    return Array.from(map.values());
  }, [diseases]);

  const activeDiseases = React.useMemo(() => {
    return dedupedDiseases.filter(d => d.status === 'active' || d.status === 'chronic');
  }, [dedupedDiseases]);

  const dedupedMedications = React.useMemo(() => {
    const map = new Map<string, Medication>();
    for (const m of medications) {
      const key = m.name.toLowerCase().trim();
      if (!map.has(key)) {
        map.set(key, m);
      } else {
        if ((m.dosage?.length || 0) > (map.get(key)!.dosage?.length || 0)) {
          map.set(key, m);
        }
      }
    }
    return Array.from(map.values());
  }, [medications]);

  const activeMeds = React.useMemo(() => {
    return dedupedMedications.filter(m => m.status === 'active');
  }, [dedupedMedications]);

  const recentReports = reports.slice(0, 4);
  const recentTimeline = timelineEvents.slice(0, 3);

  const calculateAge = (dobString?: string): number | null => {
    if (!dobString) return null;
    const dob = new Date(dobString);
    if (isNaN(dob.getTime())) return null;
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
      age--;
    }
    return age >= 0 ? age : null;
  };

  const patientAge = calculateAge(patient?.dateOfBirth);

  return (
    <div className="space-y-6 sm:space-y-8 pb-12">
      {/* 1. Apple Health Patient At-A-Glance Inset Card */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] rounded-2xl p-6 sm:p-7 shadow-[0_1px_3px_0_rgba(0,0,0,0.02)]"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#10B981]">
                Longitudinal Health Record
              </span>
              <Badge variant="success">Patient Memory Active</Badge>
              {patient?.id && (
                <Badge variant="secondary" className="font-mono text-[11px]">ID: {patient.id}</Badge>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
              {user?.name || 'Patient'}
            </h1>
            <p className="text-xs sm:text-sm text-[#6B7280] dark:text-[#9CA3AF]">
              Comprehensive medical trajectory containing{' '}
              <strong className="text-[#1F2937] dark:text-[#F3F4F6] font-medium">{reports.length} verified clinical records</strong>{' '}
              indexed across longitudinal care history.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Button
              variant="secondary"
              size="md"
              onClick={() => navigate('/chat')}
              leftIcon={<Bot className="w-4 h-4 text-[#10B981]" />}
            >
              Ask Assistant
            </Button>
            <Button
              variant="primary"
              size="md"
              onClick={() => setUploadModalOpen(true)}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              Upload Record
            </Button>
          </div>
        </div>

        {/* Clinical Snapshot Pills Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-5 text-xs">
          <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540]">
            <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] block mb-1">Blood Group & Age</span>
            <div className="flex items-center gap-2 font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
              <span className="text-base text-[#10B981]">{patient.bloodGroup || 'Not recorded'}</span>
              {patientAge !== null && (
                <>
                  <span>•</span>
                  <span>{patientAge} yrs</span>
                </>
              )}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540]">
            <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] block mb-1">Primary Care Physician</span>
            <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate">
              {patient.primaryCarePhysician || 'Not assigned'}
            </p>
          </div>

          <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540]">
            <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] block mb-1">Active Conditions</span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {activeDiseases.length === 0 ? (
                <span className="text-[#9CA3AF]">None active</span>
              ) : (
                activeDiseases.slice(0, 2).map((d) => {
                  let shortName = d.name;
                  if (shortName.toLowerCase().includes('type 2 diabetes')) {
                    shortName = 'Type 2 Diabetes';
                  } else if (shortName.length > 18) {
                    shortName = shortName.slice(0, 16) + '...';
                  }
                  return (
                    <span
                      key={d.id}
                      title={d.name}
                      className="font-medium text-[#1F2937] dark:text-[#F3F4F6] bg-white dark:bg-[#1B1E23] px-2 py-0.5 rounded-md border border-[#E5E7EB] dark:border-[#2F3540] text-[11px]"
                    >
                      {shortName}
                    </span>
                  );
                })
              )}
              {activeDiseases.length > 2 && (
                <Badge variant="secondary" className="text-[10px] py-0 px-1.5">+{activeDiseases.length - 2}</Badge>
              )}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540]">
            <span className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] block mb-1">Known Allergies</span>
            <div className="flex items-center gap-1.5 text-[#B91C1C] dark:text-red-400 font-medium">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span className="truncate">
                {patient.knownAllergies && patient.knownAllergies.length > 0
                  ? patient.knownAllergies[0]
                  : 'No known drug allergies (NKDA)'}
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* 2. Middle Section: Balanced 60/40 Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8">
        {/* Left Column (7/12 ~ 60%): Vitals Trajectory & Recent Verified Records */}
        <div className="lg:col-span-7 space-y-6 sm:space-y-8">
          {/* Longitudinal Vital & Lab Trajectory */}
          <Card className="p-5 sm:p-6 border-[#E5E7EB] dark:border-[#2F3540] space-y-4 bg-white dark:bg-[#1B1E23]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540] gap-2">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#10B981]" /> Longitudinal Biomarker Trajectory
                </CardTitle>
                <CardDescription>Illustrative biomarker trend (HbA1c & Cholesterol) across records</CardDescription>
              </div>
              <Badge variant="secondary" className="self-start sm:self-auto text-[10px]">Illustrative Demo Trajectory</Badge>
            </div>
            <VitalsTrendChart />
          </Card>

          {/* Recent Verified Medical Records */}
          <Card className="p-5 sm:p-6 border-[#E5E7EB] dark:border-[#2F3540] space-y-4 bg-white dark:bg-[#1B1E23]">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[#10B981]" /> Verified Medical Records
                </CardTitle>
                <CardDescription>Latest clinical documents indexed in patient memory</CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate('/reports')}>
                View Directory ({reports.length})
              </Button>
            </div>

            {recentReports.length === 0 ? (
              <div className="py-8 text-center space-y-2">
                <div className="w-10 h-10 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
                  <FileText className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">No medical records uploaded yet</p>
                <p className="text-[11px] text-slate-400 max-w-xs mx-auto">Upload your first prescription or laboratory report to automatically generate your timeline.</p>
                <Button variant="secondary" size="sm" onClick={() => setUploadModalOpen(true)} leftIcon={<Upload className="w-3.5 h-3.5" />}>
                  Upload Document
                </Button>
              </div>
            ) : (
            <div className="divide-y divide-[#E5E7EB]/70 dark:divide-[#2F3540]">
              {recentReports.map((report) => (
                <div
                  key={report.id}
                  className="py-3.5 first:pt-0 last:pb-0 flex items-center justify-between gap-3 group"
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-center text-[#10B981] shrink-0 mt-0.5">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs sm:text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate group-hover:text-[#10B981] transition-colors">
                        {report.title}
                      </p>
                      <div className="flex items-center gap-2 text-[11px] text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                        <span className="truncate">{report.hospitalName}</span>
                        <span>•</span>
                        <span className="font-mono tabular-nums">{report.reportDate}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {typeof report.confidenceScore === 'number' && report.confidenceScore > 0 && (
                      <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-mono text-[#15803D] dark:text-emerald-400 bg-[#ECFDF5] dark:bg-emerald-950/40 px-2 py-0.5 rounded-md border border-emerald-200/50 dark:border-emerald-800/40">
                        <ShieldCheck className="w-3 h-3" /> {Math.round(report.confidenceScore * 100)}%
                      </span>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate('/reports')}
                      leftIcon={<Eye className="w-3.5 h-3.5" />}
                    >
                      Inspect
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            )}
          </Card>
        </div>

        {/* Right Column (5/12 ~ 40%): Active Pharmacotherapy & Quick Shortcuts */}
        <div className="lg:col-span-5 space-y-6 sm:space-y-8">
          {/* Active Care Regimen */}
          <Card className="p-5 sm:p-6 border-[#E5E7EB] dark:border-[#2F3540] space-y-4 bg-white dark:bg-[#1B1E23]">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Pill className="w-4 h-4 text-[#10B981]" /> Active Pharmacotherapy
                </CardTitle>
                <CardDescription>Current medications and dosages</CardDescription>
              </div>
              <Badge variant="success">{activeMeds.length} Active Rx</Badge>
            </div>

            {activeMeds.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
                No active medications recorded yet. Prescriptions uploaded to your vault will automatically appear here.
              </div>
            ) : (
            <div className="space-y-2.5">
              {activeMeds.slice(0, 4).map((med) => (
                <div
                  key={med.id}
                  className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs"
                >
                  <div className="min-w-0 pr-2">
                    <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate">
                      {med.name}
                    </p>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                      {med.dosage} • {med.frequency}
                    </p>
                  </div>
                  <span className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] shrink-0 font-medium bg-white dark:bg-[#1B1E23] px-2 py-1 rounded-lg border border-[#E5E7EB] dark:border-[#2F3540]">
                    {med.prescribingDoctor?.split(' ')[1] || 'Jenkins'}
                  </span>
                </div>
              ))}
            </div>
            )}
          </Card>

          {/* Clinical Workflows & Shortcuts */}
          <Card className="p-5 sm:p-6 border-[#E5E7EB] dark:border-[#2F3540] space-y-4 bg-white dark:bg-[#1B1E23]">
            <div className="pb-2 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <CardTitle className="flex items-center gap-2">
                <Stethoscope className="w-4 h-4 text-[#10B981]" /> Clinical Workflows
              </CardTitle>
              <CardDescription>Direct shortcuts to essential patient services</CardDescription>
            </div>

            <div className="space-y-2 pt-1">
              <button
                onClick={() => navigate('/doctor-summary')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B] border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] transition-colors group"
              >
                <span className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#10B981]">
                    <Stethoscope className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Physician Clinical Summary</p>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Structured digest for consultations & PDF export</p>
                  </div>
                </span>
                <ArrowRight className="w-4 h-4 text-[#9CA3AF] group-hover:text-[#10B981] group-hover:translate-x-0.5 transition-all" />
              </button>

              <button
                onClick={() => navigate('/vault')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B] border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] transition-colors group"
              >
                <span className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#10B981]">
                    <FolderLock className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Medical Document Vault</p>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Encrypted records, OCR, and vector indices</p>
                  </div>
                </span>
                <ArrowRight className="w-4 h-4 text-[#9CA3AF] group-hover:text-[#10B981] group-hover:translate-x-0.5 transition-all" />
              </button>

              <button
                onClick={() => navigate('/chat')}
                className="w-full flex items-center justify-between p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-[#F3F1ED] dark:hover:bg-[#2D323B] border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] transition-colors group"
              >
                <span className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#10B981]">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">AI Assistant Inquiry</p>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Grounded queries across longitudinal memory</p>
                  </div>
                </span>
                <ArrowRight className="w-4 h-4 text-[#9CA3AF] group-hover:text-[#10B981] group-hover:translate-x-0.5 transition-all" />
              </button>
            </div>
          </Card>

          {/* Live Public Health Advisories Card (MoHFW & WHO) */}
          <Card className="p-5 sm:p-6 border-[#E5E7EB] dark:border-[#2F3540] space-y-4 bg-white dark:bg-[#1B1E23]">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Radio className="w-4 h-4 text-emerald-500 animate-pulse" /> Live Health Advisories
                </CardTitle>
                <CardDescription>Verified bulletins from WHO & MoHFW</CardDescription>
              </div>
              <Badge variant="success" className="text-[10px]">Real-Time RSS</Badge>
            </div>

            <div className="space-y-2.5">
              {healthAlerts.length === 0 ? (
                <div className="py-4 text-center text-xs text-[#9CA3AF]">
                  Fetching latest public health bulletins...
                </div>
              ) : (
                healthAlerts.slice(0, 3).map((al) => (
                  <div
                    key={al.id}
                    className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-xs text-[#1F2937] dark:text-[#F3F4F6] line-clamp-1">
                        {al.title}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 font-medium shrink-0">
                        {al.category.split(' ')[0]}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] line-clamp-2 leading-relaxed">
                      {al.summary}
                    </p>
                    <div className="flex items-center justify-between pt-1 text-[10px] text-[#9CA3AF]">
                      <span>{al.source}</span>
                      <a
                        href={al.link}
                        target="_blank"
                        rel="noreferrer"
                        className="text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-0.5 font-medium"
                      >
                        Read Bulletin <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Bottom Section: Recent Longitudinal Milestones Snapshot */}
      <Card className="p-5 sm:p-6 border-[#E5E7EB] dark:border-[#2F3540] space-y-4 bg-white dark:bg-[#1B1E23]">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GitCommit className="w-4 h-4 text-[#10B981]" /> Recent Longitudinal Milestones
            </CardTitle>
            <CardDescription>Chronological care timeline across verified healthcare encounters</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate('/timeline')} rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
            Full Timeline
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recentTimeline.map((item, idx) => (
            <div
              key={item.id || idx}
              onClick={() => navigate('/timeline')}
              className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] hover:border-[#10B981]/50 cursor-pointer transition-colors space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-semibold text-[#10B981]">{item.date}</span>
                <Badge variant="secondary" className="text-[10px] py-0">{item.type.replace('_', ' ')}</Badge>
              </div>
              <h4 className="text-xs sm:text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] group-hover:text-[#10B981] transition-colors truncate">
                {item.title}
              </h4>
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] line-clamp-2 leading-relaxed">
                {item.description}
              </p>
              <div className="text-[11px] text-[#9CA3AF] pt-2 border-t border-[#E5E7EB]/70 dark:border-[#2F3540] flex items-center justify-between">
                <span>{item.facility || 'Clinical Facility'}</span>
                <span className="text-[#10B981] font-medium flex items-center gap-1">Details ➔</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
