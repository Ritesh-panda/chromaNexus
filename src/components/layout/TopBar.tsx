import React, { useState } from 'react';
import { useUI } from '../../contexts/UIContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { Avatar } from '../ui/Avatar';
import { Badge } from '../ui/Badge';
import { Search } from '../ui/Search';
import { MOCK_NOTIFICATIONS } from '../../constants/mockData';
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
  Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export const TopBar: React.FC = () => {
  const { setSearchOpen, setUploadModalOpen } = useUI();
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
    <header className="sticky top-0 z-30 h-16 w-full glass-panel border-b border-slate-200 dark:border-slate-800/80 px-6 flex items-center justify-between">
      {/* Search trigger */}
      <div className="flex items-center space-x-4 flex-1 max-w-md">
        <button
          onClick={() => setSearchOpen(true)}
          className="w-full flex items-center justify-between px-4 py-2.5 rounded-2xl bg-slate-100/80 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/50 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-all text-xs font-medium group"
        >
          <span className="flex items-center gap-2">
            <SearchIcon className="w-4 h-4 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform" />
            <span>Search patient memory (Cmd + K)...</span>
          </span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-2 py-0.5 text-[10px] font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md text-slate-500">
            ⌘K
          </kbd>
        </button>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* Upload Button */}
        <button
          onClick={() => setUploadModalOpen(true)}
          className="hidden sm:inline-flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-md shadow-blue-500/20 transition-all active:scale-95"
        >
          <Upload className="w-4 h-4" />
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
            className="relative p-2.5 rounded-2xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-rose-500 rounded-full ring-2 ring-white dark:ring-slate-900 animate-pulse" />
            )}
          </button>

          <AnimatePresence>
            {notifOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 mt-2 w-80 glass-card border border-slate-200 dark:border-slate-800 p-4 shadow-2xl z-50 space-y-3"
              >
                <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Notifications</h4>
                  <Badge variant="default">{unreadCount} New</Badge>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {MOCK_NOTIFICATIONS.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => {
                        if (n.actionUrl) navigate(n.actionUrl);
                        setNotifOpen(false);
                      }}
                      className="p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 cursor-pointer transition-colors space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">{n.title}</span>
                        <span className="text-[10px] text-slate-400">{n.timestamp}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2">{n.message}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Theme Selector */}
        <div className="relative">
          <button
            onClick={() => {
              setThemeMenuOpen(!themeMenuOpen);
              setNotifOpen(false);
              setProfileOpen(false);
            }}
            className="p-2.5 rounded-2xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {theme === 'dark' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>

          <AnimatePresence>
            {themeMenuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 mt-2 w-40 glass-card border border-slate-200 dark:border-slate-800 p-2 shadow-2xl z-50 space-y-1"
              >
                {[
                  { id: 'light', label: 'Light', icon: <Sun className="w-4 h-4" /> },
                  { id: 'dark', label: 'Dark', icon: <Moon className="w-4 h-4" /> },
                  { id: 'system', label: 'System', icon: <Laptop className="w-4 h-4" /> },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setTheme(item.id as 'light' | 'dark' | 'system');
                      setThemeMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                      theme === item.id
                        ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      {item.icon} {item.label}
                    </span>
                    {theme === item.id && <Check className="w-3.5 h-3.5" />}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setProfileOpen(!profileOpen);
              setNotifOpen(false);
              setThemeMenuOpen(false);
            }}
            className="flex items-center space-x-2 p-1.5 rounded-2xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <Avatar src={user?.avatarUrl} name={user?.name || 'Alex Vance'} size="sm" />
            <span className="hidden md:inline-block text-xs font-semibold text-slate-800 dark:text-slate-200">
              {user?.name || 'Alex Vance'}
            </span>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </button>

          <AnimatePresence>
            {profileOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 mt-2 w-56 glass-card border border-slate-200 dark:border-slate-800 p-2 shadow-2xl z-50 space-y-1"
              >
                <div className="p-2 border-b border-slate-100 dark:border-slate-800">
                  <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{user?.name || 'Alex Vance'}</p>
                  <p className="text-[11px] text-slate-400 truncate">{user?.email || 'alex.vance@example.com'}</p>
                  <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 text-[10px] font-semibold border border-emerald-200 dark:border-emerald-800/40">
                    <ShieldCheck className="w-3 h-3" /> Isolated Patient Vault
                  </div>
                </div>

                <button
                  onClick={() => {
                    navigate('/profile');
                    setProfileOpen(false);
                  }}
                  className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <User className="w-4 h-4 text-blue-500" />
                  <span>My Health Profile</span>
                </button>

                <button
                  onClick={() => {
                    navigate('/settings');
                    setProfileOpen(false);
                  }}
                  className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <Settings className="w-4 h-4 text-purple-500" />
                  <span>Account Settings</span>
                </button>

                <div className="pt-1 border-t border-slate-100 dark:border-slate-800">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-xl text-xs font-medium text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Log Out</span>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
};
