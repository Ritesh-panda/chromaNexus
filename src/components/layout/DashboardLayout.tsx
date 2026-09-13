import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopBar } from '@/components/layout/TopBar';
import { Breadcrumb } from '@/components/layout/Breadcrumb';
import { useUI } from '@/contexts/UIContext';
import { GlobalSearchModal } from '@/components/dialogs/GlobalSearchModal';
import { UploadModal } from '@/components/dialogs/UploadModal';
import { ToastContainer } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';

export const DashboardLayout: React.FC = () => {
  const { sidebarOpen } = useUI();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 flex font-sans">
      {/* Sidebar Shell */}
      <Sidebar />

      {/* Main Content Area */}
      <div
        className={cn(
          'flex-1 flex flex-col min-w-0 transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-20'
        )}
      >
        <TopBar />

        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Breadcrumb />
          <Outlet />
        </main>
      </div>

      {/* Dialogs & Toasts */}
      <GlobalSearchModal />
      <UploadModal />
      <ToastContainer />
    </div>
  );
};
