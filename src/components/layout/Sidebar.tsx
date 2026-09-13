import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useUI } from '@/contexts/UIContext';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard,
  FolderLock,
  FileCheck,
  GitCommit,
  Bot,
  Stethoscope,
  User,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Shield,
  HeartPulse
} from 'lucide-react';
import { cn } from '@/utils/cn';

export interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
}

export const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: 'Medical Vault', path: '/vault', icon: <FolderLock className="w-5 h-5" />, badge: '8' },
  { label: 'Reports', path: '/reports', icon: <FileCheck className="w-5 h-5" /> },
  { label: 'Timeline', path: '/timeline', icon: <GitCommit className="w-5 h-5" /> },
  { label: 'AI Assistant', path: '/chat', icon: <Bot className="w-5 h-5" />, badge: 'AI' },
  { label: 'Doctor Summary', path: '/doctor-summary', icon: <Stethoscope className="w-5 h-5" /> },
  { label: 'Profile', path: '/profile', icon: <User className="w-5 h-5" /> },
  { label: 'Settings', path: '/settings', icon: <Settings className="w-5 h-5" /> },
];

export const Sidebar: React.FC = () => {
  const { sidebarOpen, toggleSidebar } = useUI();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <aside
      className={cn(
        'fixed top-0 left-0 z-40 h-screen transition-all duration-300 glass-panel border-r border-slate-200 dark:border-slate-800/80 flex flex-col justify-between p-4',
        sidebarOpen ? 'w-64' : 'w-20'
      )}
    >
      <div>
        {/* Logo Section */}
        <div className="flex items-center justify-between pb-6 mb-2 border-b border-slate-200/60 dark:border-slate-800/60">
          <NavLink to="/dashboard" className="flex items-center space-x-3 overflow-hidden">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 via-blue-500 to-emerald-400 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/25 shrink-0">
              <HeartPulse className="w-6 h-6 animate-pulse" />
            </div>
            {sidebarOpen && (
              <div className="flex flex-col">
                <span className="text-lg font-extrabold tracking-tight text-slate-900 dark:text-slate-100 font-sans">
                  Chrona<span className="text-blue-600 dark:text-blue-400">Nexus</span>
                </span>
                <span className="text-[10px] font-semibold tracking-widest uppercase text-emerald-600 dark:text-emerald-400">
                  Medical Intelligence
                </span>
              </div>
            )}
          </NavLink>

          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title={sidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1 mt-4">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center space-x-3 px-3.5 py-3 rounded-2xl text-sm font-medium transition-all duration-200 group relative',
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100'
                )
              }
            >
              <div className="shrink-0">{item.icon}</div>
              {sidebarOpen && <span className="flex-1 truncate">{item.label}</span>}
              {sidebarOpen && item.badge && (
                <span className="px-2 py-0.5 text-[10px] font-extrabold rounded-full bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300">
                  {item.badge}
                </span>
              )}
              {!sidebarOpen && (
                <div className="absolute left-16 z-50 hidden group-hover:block px-3 py-1.5 bg-slate-900 text-white text-xs font-semibold rounded-xl whitespace-nowrap shadow-lg">
                  {item.label}
                </div>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Footer / Privacy Status & Logout */}
      <div className="pt-4 border-t border-slate-200/60 dark:border-slate-800/60 space-y-3">
        {sidebarOpen && (
          <div className="p-3 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/30 flex items-center space-x-2.5">
            <Shield className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <div className="text-[11px] leading-tight">
              <p className="font-semibold text-emerald-800 dark:text-emerald-300">HIPAA Compliant</p>
              <p className="text-emerald-600/80 dark:text-emerald-400/80">Local AI Privacy Active</p>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          className={cn(
            'w-full flex items-center space-x-3 px-3.5 py-3 rounded-2xl text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors',
            !sidebarOpen && 'justify-center'
          )}
          title="Log Out"
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {sidebarOpen && <span>Log Out</span>}
        </button>
      </div>
    </aside>
  );
};
