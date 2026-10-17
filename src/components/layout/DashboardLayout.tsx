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
  const { sidebarOpen, setSidebarOpen } = useUI();

  return (
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#121417] text-[#1F2937] dark:text-[#F3F4F6] flex font-sans">
      {/* Mobile backdrop overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-[#1F2937]/30 backdrop-blur-sm lg:hidden"
          aria-hidden="true"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div
        className={cn(
          'flex-1 flex flex-col min-w-0 transition-all duration-200',
          'lg:ml-0',
          sidebarOpen ? 'lg:ml-64' : 'lg:ml-[72px]'
        )}
      >
        <TopBar />

        <main className="flex-1 p-4 sm:p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Breadcrumb />
          <Outlet />
        </main>
      </div>

      {/* Dialogs & Notifications */}
      <GlobalSearchModal />
      <UploadModal />
      <ToastContainer />
    </div>
  );
};
