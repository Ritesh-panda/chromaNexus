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
  ShieldCheck,
  Activity,
  X
} from 'lucide-react';
import { cn } from '@/utils/cn';

export interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: string;
}

export const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
  { label: 'Medical Vault', path: '/vault', icon: <FolderLock className="w-4 h-4" />, badge: '8' },
  { label: 'Reports', path: '/reports', icon: <FileCheck className="w-4 h-4" /> },
  { label: 'Timeline', path: '/timeline', icon: <GitCommit className="w-4 h-4" /> },
  { label: 'AI Assistant', path: '/chat', icon: <Bot className="w-4 h-4" />, badge: 'AI' },
  { label: 'Doctor Summary', path: '/doctor-summary', icon: <Stethoscope className="w-4 h-4" /> },
  { label: 'Profile', path: '/profile', icon: <User className="w-4 h-4" /> },
  { label: 'Settings', path: '/settings', icon: <Settings className="w-4 h-4" /> },
];

export const Sidebar: React.FC = () => {
  const { sidebarOpen, toggleSidebar, setSidebarOpen } = useUI();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleNavClick = () => {
    if (window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };

  return (
    <aside
      aria-label="Main navigation"
      aria-expanded={sidebarOpen}
      className={cn(
        'fixed top-0 left-0 z-40 h-screen transition-all duration-200 bg-white dark:bg-[#1B1E23] border-r border-[#E5E7EB] dark:border-[#2F3540] flex flex-col justify-between p-3.5',
        sidebarOpen
          ? 'w-64 translate-x-0'
          : '-translate-x-full lg:translate-x-0 lg:w-[72px]'
      )}
    >
      <div>
        {/* Brand Section */}
        <div className="flex items-center justify-between pb-4 mb-2 border-b border-[#E5E7EB]/80 dark:border-[#2F3540]">
          <NavLink
            to="/dashboard"
            className="flex items-center space-x-2.5 overflow-hidden group"
            onClick={handleNavClick}
          >
            <div className="w-9 h-9 rounded-xl bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 flex items-center justify-center text-[#10B981] font-semibold shrink-0">
              <Activity className="w-4 h-4" />
            </div>
            {sidebarOpen && (
              <div className="flex flex-col">
                <span className="text-sm font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
                  Chrona<span className="text-[#10B981]">Nexus</span>
                </span>
                <span className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF] tracking-wide">
                  Healthcare Intelligence
                </span>
              </div>
            )}
          </NavLink>

          <button
            onClick={() => {
              if (window.innerWidth < 1024) {
                setSidebarOpen(false);
              } else {
                toggleSidebar();
              }
            }}
            className="p-1 rounded-lg text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] hover:bg-[#F3F1ED] dark:hover:bg-[#23272E] transition-colors"
            aria-label={sidebarOpen ? 'Close navigation' : 'Expand navigation'}
            title={sidebarOpen ? 'Collapse Sidebar' : 'Expand Sidebar'}
          >
            <span className="lg:hidden">
              <X className="w-4 h-4" />
            </span>
            <span className="hidden lg:block">
              {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </span>
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-0.5 mt-3" aria-label="Application pages">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={handleNavClick}
              aria-label={item.label}
              className={({ isActive }) =>
                cn(
                  'flex items-center space-x-3 px-3 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-150 group relative',
                  isActive
                    ? 'bg-[#F3F1ED] dark:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] font-semibold'
                    : 'text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5] dark:hover:bg-[#23272E]/60 hover:text-[#1F2937] dark:hover:text-[#F3F4F6]'
                )
              }
            >
              <div className="shrink-0 text-current">{item.icon}</div>
              {sidebarOpen && <span className="flex-1 truncate">{item.label}</span>}
              {sidebarOpen && item.badge && (
                <span className="px-1.5 py-0.2 text-[10px] font-medium rounded-full bg-[#ECFDF5] text-[#15803D] dark:bg-emerald-950/40 dark:text-emerald-300">
                  {item.badge}
                </span>
              )}
              {!sidebarOpen && (
                <div className="absolute left-14 z-50 hidden lg:group-hover:block px-2.5 py-1 bg-[#1F2937] text-white text-xs font-medium rounded-lg whitespace-nowrap shadow-md pointer-events-none">
                  {item.label}
                </div>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Footer / Privacy Status & Logout */}
      <div className="pt-3 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] space-y-2">
        {sidebarOpen && (
          <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/60 border border-[#E5E7EB] dark:border-[#2F3540] flex items-center space-x-2">
            <ShieldCheck className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
            <div className="text-[10px] leading-tight text-[#4B5563] dark:text-[#9CA3AF]">
              <span className="font-semibold block text-[#1F2937] dark:text-[#F3F4F6]">HIPAA Compliant</span>
              <span>Encrypted Patient Memory</span>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          aria-label="Log out"
          className={cn(
            'w-full flex items-center space-x-3 px-3 py-2 rounded-xl text-xs sm:text-sm font-medium text-[#B91C1C] dark:text-rose-400 hover:bg-[#FEF2F2] dark:hover:bg-rose-950/30 transition-colors',
            !sidebarOpen && 'justify-center'
          )}
          title="Log Out"
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {sidebarOpen && <span>Log Out</span>}
        </button>
      </div>
    </aside>
  );
};
