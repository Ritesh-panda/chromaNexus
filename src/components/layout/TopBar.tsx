import React, { useState } from 'react';
import { useUI } from '@/contexts/UIContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { MOCK_NOTIFICATIONS } from '@/constants/mockData';
import {
  Bell,
  Sun,
  Moon,
  Laptop,
  Search as SearchIcon,
  Upload,
  User,
  Settings,
  LogOut,
  ChevronDown,
  ShieldCheck,
  Check,
  Menu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export const TopBar: React.FC = () => {
  const { setSearchOpen, setUploadModalOpen, toggleSidebar } = useUI();
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [themeMenuOpen, setThemeMenuOpen] = useState(false);

  const unreadCount = MOCK_NOTIFICATIONS.filter((n) => !n.read).length;

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-30 h-14 w-full bg-[#FAF8F5]/90 dark:bg-[#121417]/90 backdrop-blur-md border-b border-[#E5E7EB] dark:border-[#2F3540] px-4 sm:px-6 flex items-center justify-between gap-3">
      {/* Mobile hamburger */}
      <button
        onClick={toggleSidebar}
        aria-label="Toggle navigation menu"
        className="lg:hidden p-1.5 rounded-xl text-[#6B7280] hover:text-[#1F2937] hover:bg-[#F3F1ED] dark:text-[#9CA3AF] dark:hover:text-[#F3F4F6] dark:hover:bg-[#23272E] transition-colors shrink-0"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Global search trigger */}
      <div className="flex items-center space-x-3 flex-1 max-w-md">
        <button
          onClick={() => setSearchOpen(true)}
          aria-label="Open global search"
          className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6] hover:border-[#D1D5DB] transition-all text-xs font-normal group shadow-[0_1px_2px_0_rgba(0,0,0,0.02)]"
        >
          <span className="flex items-center gap-2">
            <SearchIcon className="w-3.5 h-3.5 text-[#9CA3AF] group-hover:text-[#10B981] transition-colors" />
            <span>Search patient records, labs, reports...</span>
          </span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono bg-[#F3F1ED] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] rounded text-[#6B7280] dark:text-[#9CA3AF]">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-2">
        {/* Upload Button */}
        <button
          onClick={() => setUploadModalOpen(true)}
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#10B981] hover:bg-[#059669] text-white text-xs font-medium shadow-sm transition-all active:scale-95"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>Upload Record</span>
        </button>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => {
              setNotifOpen(!notifOpen);
              setProfileOpen(false);
              setThemeMenuOpen(false);
            }}
            className="relative p-2 rounded-xl text-[#6B7280] hover:text-[#1F2937] hover:bg-[#F3F1ED] dark:text-[#9CA3AF] dark:hover:text-[#F3F4F6] dark:hover:bg-[#23272E] transition-colors"
            aria-label="View notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#B91C1C] rounded-full ring-2 ring-white dark:ring-[#121417]" />
            )}
          </button>

          <AnimatePresence>
            {notifOpen && (
              <motion.div
                initial={{ opacity: 0, y: 6, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.98 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-2 w-80 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-xl p-3 z-50 space-y-2"
              >
                <div className="flex items-center justify-between pb-2 border-b border-[#E5E7EB] dark:border-[#2F3540]">
                  <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Notifications</span>
                  {unreadCount > 0 && (
                    <Badge variant="success" className="text-[10px] py-0 px-1.5">
                      {unreadCount} new
                    </Badge>
                  )}
                </div>

                <div className="space-y-1.5 max-h-60 overflow-y-auto">
                  {MOCK_NOTIFICATIONS.map((n) => (
                    <div
                      key={n.id}
                      className="p-2.5 rounded-xl hover:bg-[#FAF8F5] dark:hover:bg-[#23272E] transition-colors text-xs space-y-1 border border-transparent hover:border-[#E5E7EB] dark:hover:border-[#2F3540]"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] truncate">{n.title}</span>
                        <span className="text-[10px] text-[#9CA3AF] tabular-nums shrink-0">{n.timestamp}</span>
                      </div>
                      <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] line-clamp-2 leading-relaxed">{n.message}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Theme Picker Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setThemeMenuOpen(!themeMenuOpen);
              setNotifOpen(false);
              setProfileOpen(false);
            }}
            className="p-2 rounded-xl text-[#6B7280] hover:text-[#1F2937] hover:bg-[#F3F1ED] dark:text-[#9CA3AF] dark:hover:text-[#F3F4F6] dark:hover:bg-[#23272E] transition-colors"
            aria-label="Change interface theme"
          >
            {theme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
          </button>

          <AnimatePresence>
            {themeMenuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 6, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.98 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-2 w-36 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-xl p-1.5 z-50 space-y-0.5 text-xs font-medium"
              >
                {[
                  { id: 'light', label: 'Light', icon: <Sun className="w-3.5 h-3.5" /> },
                  { id: 'dark', label: 'Dark', icon: <Moon className="w-3.5 h-3.5" /> },
                  { id: 'system', label: 'System', icon: <Laptop className="w-3.5 h-3.5" /> },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setTheme(item.id as 'light' | 'dark' | 'system');
                      setThemeMenuOpen(false);
                    }}
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-xl hover:bg-[#FAF8F5] dark:hover:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      {item.icon} {item.label}
                    </span>
                    {theme === item.id && <Check className="w-3.5 h-3.5 text-[#10B981]" />}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setProfileOpen(!profileOpen);
              setNotifOpen(false);
              setThemeMenuOpen(false);
            }}
            className="flex items-center space-x-2 p-1 pl-1.5 pr-2 rounded-xl hover:bg-[#F3F1ED] dark:hover:bg-[#23272E] transition-colors"
            aria-label="User menu"
          >
            <Avatar src={user?.avatarUrl} name={user?.name || 'Alex Vance'} size="sm" />
            <span className="hidden md:block text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] max-w-[100px] truncate">
              {user?.name || 'Alex Vance'}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-[#9CA3AF]" />
          </button>

          <AnimatePresence>
            {profileOpen && (
              <motion.div
                initial={{ opacity: 0, y: 6, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 6, scale: 0.98 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 mt-2 w-52 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-xl p-2 z-50 space-y-1 text-xs"
              >
                <div className="px-2.5 py-2 border-b border-[#E5E7EB] dark:border-[#2F3540]">
                  <p className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] truncate">{user?.name || 'Alex Vance'}</p>
                  <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] truncate font-mono">{user?.email || 'patient@chronanexus.app'}</p>
                  <div className="mt-1 flex items-center gap-1 text-[10px] text-[#15803D]">
                    <ShieldCheck className="w-3 h-3" />
                    <span>Memory Synced</span>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setProfileOpen(false);
                    navigate('/profile');
                  }}
                  className="w-full flex items-center space-x-2.5 px-2.5 py-2 rounded-xl hover:bg-[#FAF8F5] dark:hover:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] transition-colors"
                >
                  <User className="w-3.5 h-3.5 text-[#6B7280] dark:text-[#9CA3AF]" />
                  <span>My Profile</span>
                </button>

                <button
                  onClick={() => {
                    setProfileOpen(false);
                    navigate('/settings');
                  }}
                  className="w-full flex items-center space-x-2.5 px-2.5 py-2 rounded-xl hover:bg-[#FAF8F5] dark:hover:bg-[#23272E] text-[#1F2937] dark:text-[#F3F4F6] transition-colors"
                >
                  <Settings className="w-3.5 h-3.5 text-[#6B7280] dark:text-[#9CA3AF]" />
                  <span>Settings & Privacy</span>
                </button>

                <div className="border-t border-[#E5E7EB] dark:border-[#2F3540] my-1" />

                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-2.5 px-2.5 py-2 rounded-xl text-[#B91C1C] hover:bg-[#FEF2F2] dark:hover:bg-rose-950/30 transition-colors font-medium"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Log Out</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};
