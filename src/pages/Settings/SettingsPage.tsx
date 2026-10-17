import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Tabs } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { useTheme } from '@/contexts/ThemeContext';
import { useUI } from '@/contexts/UIContext';
import {
  Settings,
  Sun,
  Moon,
  Shield,
  Bell,
  Lock,
  Globe,
  Trash2,
  Download,
  ShieldCheck,
  AlertTriangle,
  Smartphone,
  Laptop,
  KeyRound,
  CheckCircle2
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { addToast } = useUI();
  const [activeTab, setActiveTab] = useState('appearance');
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(true);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

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
    { id: 'privacy', label: 'Privacy & Governance', icon: <Shield className="w-4 h-4" /> },
    { id: 'danger', label: 'Account Data', icon: <AlertTriangle className="w-4 h-4 text-[#B91C1C]" /> },
  ];

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
          <Settings className="w-5 h-5 text-[#10B981]" /> Settings & Data Governance
        </h1>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
          Manage system theme, zero-trust security parameters, and data isolation preferences.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={(id) => setActiveTab(id)} />

      {/* Tab Content Panels */}
      {activeTab === 'appearance' && (
        <Card className="p-6 space-y-6 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div>
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Interface Theme</h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Select how ChronaNexus appears on this device.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            {[
              { id: 'light', label: 'Warm Light Mode', icon: <Sun className="w-5 h-5 text-[#B45309]" /> },
              { id: 'dark', label: 'Dark Mode', icon: <Moon className="w-5 h-5 text-[#2563EB]" /> },
              { id: 'system', label: 'System Default', icon: <Globe className="w-5 h-5 text-[#6B7280]" /> },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setTheme(item.id as 'light' | 'dark' | 'system');
                  addToast({ type: 'success', title: `Theme switched to ${item.label}` });
                }}
                className={`p-5 rounded-2xl border text-center space-y-2 flex flex-col items-center justify-center transition-all ${
                  theme === item.id
                    ? 'border-[#10B981] bg-[#ECFDF5]/50 dark:bg-emerald-950/20 text-[#1F2937] dark:text-[#F3F4F6] shadow-sm font-semibold'
                    : 'border-[#E5E7EB] dark:border-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]'
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
        <Card className="p-6 space-y-5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3.5 border-b border-[#E5E7EB]/80 dark:border-[#2F3540] gap-2">
            <div>
              <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-[#10B981]" /> Patient Memory Isolation Proof
              </h3>
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Your medical data is encrypted and isolated per patient ID.</p>
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
      )}

      {activeTab === 'danger' && (
        <Card className="p-6 space-y-5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div>
            <h3 className="text-sm font-semibold text-[#B91C1C] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-[#B91C1C]" /> Account & Data Retention
            </h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Export or permanently remove your patient memory archive.</p>
          </div>

          <div className="space-y-3 pt-1">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] gap-3">
              <div>
                <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Export Complete Patient Memory</h4>
                <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Download all structured JSON extractions and raw reports.</p>
              </div>
              <Button variant="secondary" size="sm" leftIcon={<Download className="w-4 h-4" />}>
                Export Archive
              </Button>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl bg-[#FEF2F2]/40 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40 gap-3">
              <div>
                <h4 className="text-xs font-semibold text-[#B91C1C]">Delete Entire Medical Account</h4>
                <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF]">Permanently erase all documents, memory graphs, and timelines.</p>
              </div>
              <Button
                variant="danger"
                size="sm"
                leftIcon={<Trash2 className="w-4 h-4" />}
                onClick={() => addToast({ type: 'error', title: 'Account Deletion Requested', message: 'Action canceled for demo safety.' })}
              >
                Delete Memory
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
