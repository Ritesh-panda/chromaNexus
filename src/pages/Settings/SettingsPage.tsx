import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
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
  Check,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { addToast } = useUI();
  const [activeTab, setActiveTab] = useState('appearance');

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
    { id: 'danger', label: 'Danger Zone', icon: <AlertTriangle className="w-4 h-4 text-rose-500" /> },
  ];

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Settings className="w-6 h-6 text-purple-500" /> Settings & Data Governance
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Manage system theme, zero-trust security parameters, and data isolation preferences.
        </p>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={(id) => setActiveTab(id)} />

      {/* Tab Content Panels */}
      {activeTab === 'appearance' && (
        <Card className="p-6 space-y-6 border-slate-200 dark:border-slate-800">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Interface Theme</h3>
            <p className="text-xs text-slate-500">Select how ChronaNexus looks on your device.</p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[
              { id: 'light', label: 'Light Mode', icon: <Sun className="w-6 h-6 text-amber-500" /> },
              { id: 'dark', label: 'Dark Mode', icon: <Moon className="w-6 h-6 text-blue-400" /> },
              { id: 'system', label: 'System Default', icon: <Globe className="w-6 h-6 text-purple-400" /> },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setTheme(item.id as 'light' | 'dark' | 'system');
                  addToast({ type: 'success', title: `Theme switched to ${item.label}` });
                }}
                className={`p-6 rounded-2xl border text-center space-y-2 flex flex-col items-center justify-center transition-all ${
                  theme === item.id
                    ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/40 text-blue-600 font-bold'
                    : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50'
                }`}
              >
                {item.icon}
                <span className="text-xs font-semibold">{item.label}</span>
              </button>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'notifications' && (
        <Card className="p-6 space-y-6 border-slate-200 dark:border-slate-800">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Notification Preferences</h3>
            <p className="text-xs text-slate-500">Configure how and when ChronaNexus notifies you.</p>
          </div>

          <div className="space-y-4 divide-y divide-slate-100 dark:divide-slate-800">
            {[
              { key: 'email', label: 'Email Reports & Summaries', desc: 'Receive automated summary digests.' },
              { key: 'criticalLabs', label: 'Critical Abnormal Lab Alerts', desc: 'Instant alerts when lab values breach normal bounds.' },
              { key: 'aiDigest', label: 'Weekly AI Longitudinal Insights', desc: 'Get updates when new timeline patterns emerge.' },
            ].map((item) => (
              <div key={item.key} className="pt-3 flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">{item.label}</h4>
                  <p className="text-[11px] text-slate-500">{item.desc}</p>
                </div>
                <input
                  type="checkbox"
                  checked={(notifications as any)[item.key]}
                  onChange={(e) => setNotifications({ ...notifications, [item.key]: e.target.checked })}
                  className="rounded text-blue-600 w-4 h-4"
                />
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'privacy' && (
        <Card className="p-6 space-y-6 border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" /> Patient Memory Isolation Proof
              </h3>
              <p className="text-xs text-slate-500">Your medical data is encrypted and isolated per patient ID.</p>
            </div>
            <Badge variant="success">Strict Isolation Active</Badge>
          </div>

          <div className="p-4 rounded-2xl bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-200/50 dark:border-emerald-900/30 text-xs text-emerald-800 dark:text-emerald-300 space-y-2">
            <p className="font-bold">Zero Third-Party Training Assurance</p>
            <p className="text-slate-600 dark:text-slate-400">
              ChronaNexus NEVER sends unencrypted records to public models. All clinical reasoning is grounded locally within your private session memory.
            </p>
          </div>
        </Card>
      )}

      {activeTab === 'danger' && (
        <Card className="p-6 space-y-6 border-red-200 dark:border-red-950/60 bg-rose-50/10 dark:bg-rose-950/10">
          <div>
            <h3 className="text-base font-bold text-rose-600 dark:text-rose-400 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" /> Danger Zone Actions
            </h3>
            <p className="text-xs text-slate-500">Export or permanently delete your complete patient memory graph.</p>
          </div>

          <div className="space-y-4 pt-2">
            <div className="flex items-center justify-between p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <div>
                <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">Export Complete Patient Memory</h4>
                <p className="text-[11px] text-slate-500">Download all structured JSON extractions and raw reports.</p>
              </div>
              <Button variant="outline" size="sm" leftIcon={<Download className="w-4 h-4" />}>
                Export Data Archive
              </Button>
            </div>

            <div className="flex items-center justify-between p-4 rounded-2xl bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40">
              <div>
                <h4 className="text-xs font-bold text-red-600">Delete Entire Medical Account</h4>
                <p className="text-[11px] text-slate-500">Permanently erase all documents, memory graphs, and timelines.</p>
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
