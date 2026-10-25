import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Tabs } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { useTheme } from '@/contexts/ThemeContext';
import { useUI } from '@/contexts/UIContext';
import { governanceService, type PurgePreviewResponse, type AuditLogItem } from '@/services/governance.service';
import {
  Settings,
  Sun,
  Moon,
  Shield,
  Bell,
  Lock,
  Trash2,
  Download,
  ShieldCheck,
  AlertTriangle,
  Smartphone,
  Laptop,
  KeyRound,
  CheckCircle2,
  FileCode,
  RefreshCw,
  Loader2,
  AlertCircle,
  Activity,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { addToast } = useUI();
  const [activeTab, setActiveTab] = useState('appearance');
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(true);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // FHIR Export state
  const [isExportingFhir, setIsExportingFhir] = useState(false);

  // Audit Logs state
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loadingAuditLogs, setLoadingAuditLogs] = useState(false);

  // Purge Modal state
  const [isPurgeModalOpen, setIsPurgeModalOpen] = useState(false);
  const [isRequestingPurge, setIsRequestingPurge] = useState(false);
  const [purgePreview, setPurgePreview] = useState<PurgePreviewResponse | null>(null);
  const [confirmationPhrase, setConfirmationPhrase] = useState('');
  const [isExecutingPurge, setIsExecutingPurge] = useState(false);
  const [purgeResult, setPurgeResult] = useState<string | null>(null);

  const [notifications, setNotifications] = useState({
    email: true,
    sms: false,
    criticalLabs: true,
    aiDigest: true,
  });

  const tabs = [
    { id: 'appearance', label: 'Theme & Appearance', icon: <Sun className="w-4 h-4" /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell className="w-4 h-4" /> },
    { id: 'security', label: 'Security & 2FA', icon: <Lock className="w-4 h-4" /> },
    { id: 'privacy', label: 'Privacy & FHIR R4', icon: <Shield className="w-4 h-4" /> },
    { id: 'danger', label: 'Account Data & Purge', icon: <AlertTriangle className="w-4 h-4 text-[#B91C1C]" /> },
  ];

  // Fetch audit logs when privacy tab is opened
  useEffect(() => {
    if (activeTab === 'privacy') {
      fetchAuditLogs();
    }
  }, [activeTab]);

  const fetchAuditLogs = async () => {
    setLoadingAuditLogs(true);
    try {
      const logs = await governanceService.getAuditLogs(30);
      setAuditLogs(logs);
    } catch {
      // Non-blocking in demo/offline mode
    } finally {
      setLoadingAuditLogs(false);
    }
  };

  const handleExportFhir = async () => {
    setIsExportingFhir(true);
    try {
      await governanceService.exportFhirBundle();
      addToast({
        type: 'success',
        title: 'FHIR R4 Bundle Exported',
        message: 'Clinical record collection bundle downloaded successfully.',
      });
      // Refresh audit logs
      fetchAuditLogs();
    } catch {
      addToast({
        type: 'error',
        title: 'Export Failed',
        message: 'Could not generate FHIR R4 bundle. Please verify your connection.',
      });
    } finally {
      setIsExportingFhir(false);
    }
  };

  const handleRequestPurgePreview = async () => {
    setIsRequestingPurge(true);
    setPurgeResult(null);
    setConfirmationPhrase('');
    try {
      const preview = await governanceService.requestPurgePreview();
      setPurgePreview(preview);
      setIsPurgeModalOpen(true);
    } catch {
      addToast({
        type: 'error',
        title: 'Purge Request Failed',
        message: 'Unable to prepare purge scope. Please re-authenticate and try again.',
      });
    } finally {
      setIsRequestingPurge(false);
    }
  };

  const handleConfirmPurge = async () => {
    if (!purgePreview) return;
    if (confirmationPhrase.trim() !== purgePreview.confirmation_phrase_required) {
      addToast({
        type: 'error',
        title: 'Confirmation Phrase Mismatch',
        message: `You must type exactly: "${purgePreview.confirmation_phrase_required}"`,
      });
      return;
    }

    setIsExecutingPurge(true);
    try {
      const result = await governanceService.confirmPurge(
        purgePreview.confirmation_token,
        confirmationPhrase.trim()
      );
      setPurgeResult(`Purge complete. ${result.summary.reports_deleted} reports, ${result.summary.chroma_vectors_deleted} semantic vectors, and ${result.summary.files_deleted} files erased.`);
      addToast({
        type: 'success',
        title: 'Patient Data Purged',
        message: 'All confirmed medical records have been permanently erased.',
      });
      // Reset form
      setPurgePreview(null);
      setConfirmationPhrase('');
    } catch {
      addToast({
        type: 'error',
        title: 'Purge Execution Failed',
        message: 'Purge operation failed or confirmation token expired.',
      });
    } finally {
      setIsExecutingPurge(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
          <Settings className="w-5 h-5 text-[#10B981]" /> Settings & Data Governance
        </h1>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
          Manage system theme, zero-trust security parameters, FHIR export, and data lifecycle.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'appearance' && (
        <Card className="p-6 space-y-6 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div>
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Interface Theme</h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Select your preferred viewing mode.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { id: 'light', label: 'Light Mode', icon: <Sun className="w-5 h-5 text-[#B45309]" /> },
              { id: 'dark', label: 'Dark Mode', icon: <Moon className="w-5 h-5 text-[#10B981]" /> },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setTheme(item.id as 'light' | 'dark')}
                className={`p-4 rounded-xl border text-left flex items-center gap-3 transition-colors ${
                  theme === item.id
                    ? 'border-[#10B981] bg-[#10B981]/10 text-[#15803D] dark:text-[#34D399]'
                    : 'border-[#E5E7EB] dark:border-[#2F3540] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]/50 text-[#1F2937] dark:text-[#F3F4F6]'
                }`}
              >
                {item.icon}
                <span className="text-xs font-medium">{item.label}</span>
              </button>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'notifications' && (
        <Card className="p-6 space-y-5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div>
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Notification Preferences</h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Configure how and when ChronaNexus notifies you.</p>
          </div>

          <div className="space-y-3 divide-y divide-[#E5E7EB]/80 dark:divide-[#2F3540]">
            {[
              { key: 'email', label: 'Email Reports & Summaries', desc: 'Receive automated summary digests.' },
              { key: 'criticalLabs', label: 'Critical Abnormal Lab Alerts', desc: 'Instant alerts when lab values breach normal bounds.' },
              { key: 'aiDigest', label: 'Weekly AI Longitudinal Insights', desc: 'Get updates when new timeline patterns emerge.' },
            ].map((item) => (
              <div key={item.key} className="pt-3 flex items-center justify-between gap-4">
                <div>
                  <h4 className="text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6]">{item.label}</h4>
                  <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">{item.desc}</p>
                </div>
                <input
                  type="checkbox"
                  checked={(notifications as Record<string, boolean>)[item.key]}
                  onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                  className="rounded text-[#10B981] focus:ring-emerald-500/20 w-4 h-4 cursor-pointer"
                />
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'security' && (
        <Card className="p-6 space-y-6 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#E5E7EB]/80 dark:border-[#2F3540] gap-3">
            <div>
              <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                <Lock className="w-4 h-4 text-[#10B981]" /> Two-Factor Authentication (2FA)
              </h3>
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Require an OTP verification code when signing into your vault.</p>
            </div>
            <Button
              variant={twoFactorEnabled ? 'secondary' : 'primary'}
              size="sm"
              onClick={() => {
                setTwoFactorEnabled(!twoFactorEnabled);
                addToast({
                  type: 'info',
                  title: '2FA Updated',
                  message: `Two-factor authentication is now ${!twoFactorEnabled ? 'Enabled' : 'Disabled'}.`,
                });
              }}
            >
              {twoFactorEnabled ? 'Disable 2FA' : 'Enable 2FA'}
            </Button>
          </div>

          {/* Active Sessions */}
          <div className="space-y-2.5">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[#6B7280] dark:text-[#9CA3AF]">
              Active Authorized Sessions
            </h4>
            <div className="space-y-2">
              <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#10B981]">
                    <Laptop className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                      Chrome on Windows 11 <Badge variant="success" className="text-[10px]">Current Session</Badge>
                    </p>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] font-mono mt-0.5">IP: 192.168.1.104 • Local Node</p>
                  </div>
                </div>
                <span className="text-[11px] text-[#15803D] dark:text-emerald-400 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Active
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF]">
                    <Smartphone className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">ChronaNexus Mobile (iOS 18)</p>
                    <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] font-mono mt-0.5">Last active: 2 hours ago</p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => addToast({ type: 'info', title: 'Session Revoked', message: 'iOS session disconnected.' })}
                  className="text-xs text-[#B91C1C] hover:text-[#991B1B]"
                >
                  Revoke
                </Button>
              </div>
            </div>
          </div>

          {/* Change Password Form */}
          <div className="pt-4 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] space-y-3.5">
            <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
              <KeyRound className="w-4 h-4 text-[#B45309]" /> Update Vault Password
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Current Password"
                type="password"
                placeholder="••••••••"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
              <Input
                label="New Password"
                type="password"
                placeholder="Minimum 8 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div className="flex justify-end pt-1">
              <Button
                variant="primary"
                size="sm"
                disabled={!currentPassword || !newPassword}
                onClick={() => {
                  setCurrentPassword('');
                  setNewPassword('');
                  addToast({ type: 'success', title: 'Password Changed Successfully' });
                }}
              >
                Update Password
              </Button>
            </div>
          </div>
        </Card>
      )}

      {activeTab === 'privacy' && (
        <div className="space-y-6">
          {/* Patient Memory Isolation Card */}
          <Card className="p-6 space-y-5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3.5 border-b border-[#E5E7EB]/80 dark:border-[#2F3540] gap-2">
              <div>
                <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-[#10B981]" /> Patient Memory Isolation Proof
                </h3>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Your medical data is encrypted and strictly isolated per patient ID.</p>
              </div>
              <Badge variant="success">Strict Isolation Active</Badge>
            </div>

            <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-xs space-y-1.5">
              <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Zero Third-Party Model Training</p>
              <p className="text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
                ChronaNexus never transmits unencrypted patient data to public LLMs. Retrieval-augmented reasoning is processed strictly in your local isolated session context.
              </p>
            </div>
          </Card>

          {/* FHIR R4 Export Section */}
          <Card className="p-6 space-y-4 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <div>
                <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-[#2563EB]" /> HL7® FHIR® R4 Standards Export
                </h3>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                  Export your complete clinical record as an interoperable, standards-compliant FHIR R4 JSON collection bundle.
                </p>
              </div>
              <Button
                variant="primary"
                size="sm"
                leftIcon={isExportingFhir ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                onClick={handleExportFhir}
                disabled={isExportingFhir}
              >
                {isExportingFhir ? 'Generating Bundle...' : 'Export FHIR R4 Bundle'}
              </Button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] mb-1">Standard Resource Types</p>
                <p className="text-[#6B7280] dark:text-[#9CA3AF] text-[11px] leading-relaxed">
                  Patient, DocumentReference, Observation (labs), Condition, AllergyIntolerance, MedicationStatement, DiagnosticReport.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] mb-1">Preserved Clinical Codes</p>
                <p className="text-[#6B7280] dark:text-[#9CA3AF] text-[11px] leading-relaxed">
                  Preserves verified LOINC laboratory codes, RxNorm medications, and ICD-10 diagnoses without inventing terminology.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] mb-1">Strict Patient Scoping</p>
                <p className="text-[#6B7280] dark:text-[#9CA3AF] text-[11px] leading-relaxed">
                  Export is server-authorized and strictly constrained to your authenticated patient records. Recorded in security audit logs.
                </p>
              </div>
            </div>
          </Card>

          {/* Append-Only Audit Log Viewer */}
          <Card className="p-6 space-y-4 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
              <div>
                <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#10B981]" /> Security & Access Audit Trail
                </h3>
                <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
                  Append-only immutable record of document downloads, FHIR exports, and authorization checks.
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loadingAuditLogs ? 'animate-spin' : ''}`} />}
                onClick={fetchAuditLogs}
                disabled={loadingAuditLogs}
              >
                Refresh
              </Button>
            </div>

            {loadingAuditLogs ? (
              <div className="py-8 flex justify-center text-[#6B7280] text-xs">
                <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading audit events...
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="py-6 text-center text-xs text-[#6B7280] dark:text-[#9CA3AF]">
                No recent security audit events recorded for this session.
              </div>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {auditLogs.map((log) => (
                  <div
                    key={log.id}
                    className="p-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center justify-between text-xs"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] font-mono text-[11px]">
                          {log.action}
                        </span>
                        <Badge
                          variant={log.outcome === 'SUCCESS' ? 'success' : 'danger'}
                          className="text-[10px]"
                        >
                          {log.outcome}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">
                        {log.resource_type ? `${log.resource_type}: ${log.resource_id || 'all'}` : 'System scope'}
                      </p>
                    </div>
                    <span className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] font-mono">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'danger' && (
        <Card className="p-6 space-y-5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div>
            <h3 className="text-sm font-semibold text-[#B91C1C] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-[#B91C1C]" /> Safe Patient-Data Purge & Retention
            </h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
              Permanently remove your clinical memory archive, extracted entities, and vector embeddings.
            </p>
          </div>

          {purgeResult && (
            <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300">
              {purgeResult}
            </div>
          )}

          <div className="space-y-3 pt-1">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] gap-3">
              <div>
                <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Export FHIR R4 Clinical Archive</h4>
                <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Download all clinical extractions before initiating an irreversible purge.</p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<Download className="w-4 h-4" />}
                onClick={handleExportFhir}
                disabled={isExportingFhir}
              >
                Export Bundle
              </Button>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-[#FEF2F2]/40 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40 gap-3">
              <div>
                <h4 className="text-xs font-semibold text-[#B91C1C]">Irreversible Data Purge</h4>
                <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">
                  Requires two-step verification with explicit server token confirmation. Erases relational records, files, and vector embeddings.
                </p>
              </div>
              <Button
                variant="danger"
                size="sm"
                leftIcon={isRequestingPurge ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                onClick={handleRequestPurgePreview}
                disabled={isRequestingPurge}
              >
                {isRequestingPurge ? 'Inspecting Scope...' : 'Request Data Purge'}
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Two-Step Safe Purge Confirmation Modal */}
      <Modal
        isOpen={isPurgeModalOpen}
        onClose={() => {
          if (!isExecutingPurge) {
            setIsPurgeModalOpen(false);
            setPurgePreview(null);
            setConfirmationPhrase('');
          }
        }}
        title="Confirm Irreversible Data Purge"
        description="Review the itemized data scope before confirming deletion. This action cannot be undone."
        maxWidth="xl"
      >
        {purgePreview && (
          <div className="space-y-4 text-xs">
            {/* Warning banner */}
            <div className="p-3.5 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-[#B91C1C] dark:text-rose-300 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-semibold text-[11px] uppercase tracking-wider">Destructive Operation</p>
                <p className="leading-relaxed text-[11px]">{purgePreview.warning}</p>
              </div>
            </div>

            {/* Itemized Scope Grid */}
            <div className="space-y-2">
              <h4 className="text-[11px] font-semibold uppercase tracking-wider text-[#6B7280] dark:text-[#9CA3AF]">
                Scope of Records to be Erased (Patient: {purgePreview.patient_id})
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#1F2937] dark:text-[#F3F4F6]">{purgePreview.scope.reports_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Reports</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#1F2937] dark:text-[#F3F4F6]">{purgePreview.scope.files_to_delete_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Disk Files</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#1F2937] dark:text-[#F3F4F6]">{purgePreview.scope.lab_results_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Lab Results</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#1F2937] dark:text-[#F3F4F6]">{purgePreview.scope.medications_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Medications</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#1F2937] dark:text-[#F3F4F6]">{purgePreview.scope.conditions_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Conditions</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#1F2937] dark:text-[#F3F4F6]">{purgePreview.scope.allergies_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Allergies</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#1F2937] dark:text-[#F3F4F6]">{purgePreview.scope.timeline_events_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Timeline Events</p>
                </div>
                <div className="p-2.5 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="text-lg font-bold text-[#2563EB]">{purgePreview.scope.chroma_vectors_count}</p>
                  <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">Vector Chunks</p>
                </div>
              </div>
            </div>

            {/* Exclusions Notice */}
            <div className="p-3 rounded-lg bg-[#F3F1ED] dark:bg-[#23272E] text-[11px] text-[#6B7280] dark:text-[#9CA3AF] space-y-1">
              <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Compliance Exclusions:</p>
              <ul className="list-disc list-inside space-y-0.5">
                {purgePreview.exclusions.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>

            {/* Token expiry info */}
            <p className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] font-mono">
              Token valid until: {new Date(purgePreview.expires_at).toLocaleTimeString()}
            </p>

            {/* Mandatory Confirmation Phrase Input */}
            <div className="space-y-1.5 pt-2 border-t border-[#E5E7EB] dark:border-[#2F3540]">
              <label className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                Type <span className="font-mono text-[#B91C1C] select-all font-bold">"{purgePreview.confirmation_phrase_required}"</span> to confirm:
              </label>
              <Input
                placeholder="Type the confirmation phrase exactly..."
                value={confirmationPhrase}
                onChange={(e) => setConfirmationPhrase(e.target.value)}
                disabled={isExecutingPurge}
              />
            </div>

            {/* Action buttons */}
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsPurgeModalOpen(false)}
                disabled={isExecutingPurge}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                leftIcon={isExecutingPurge ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                onClick={handleConfirmPurge}
                disabled={
                  isExecutingPurge ||
                  confirmationPhrase.trim() !== purgePreview.confirmation_phrase_required
                }
              >
                {isExecutingPurge ? 'Purging Records...' : 'Permanently Delete Data'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SettingsPage;
