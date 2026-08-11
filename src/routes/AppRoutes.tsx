import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import { LandingLayout } from '../components/layout/LandingLayout';
import { AuthLayout } from '../components/layout/AuthLayout';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { ProtectedRoute } from './ProtectedRoute';

// Pages
import { LandingPage } from '../pages/Landing/LandingPage';
import { LoginPage } from '../pages/Auth/LoginPage';
import { SignupPage } from '../pages/Auth/SignupPage';
import { ForgotPasswordPage } from '../pages/Auth/ForgotPasswordPage';
import { OTPVerificationPage } from '../pages/Auth/OTPVerificationPage';

import { DashboardPage } from '../pages/Dashboard/DashboardPage';
import { VaultPage } from '../pages/Vault/VaultPage';
import { ReportsPage } from '../pages/Reports/ReportsPage';
import { TimelinePage } from '../pages/Timeline/TimelinePage';
import { AIChatPage } from '../pages/Chat/AIChatPage';
import { DoctorSummaryPage } from '../pages/DoctorSummary/DoctorSummaryPage';
import { ProfilePage } from '../pages/Profile/ProfilePage';
import { SettingsPage } from '../pages/Settings/SettingsPage';
import { NotFoundPage } from '../pages/NotFound/NotFoundPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Landing Route */}
      <Route element={<LandingLayout />}>
        <Route path="/" element={<LandingPage />} />
      </Route>

      {/* Auth Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/otp-verification" element={<OTPVerificationPage />} />
      </Route>

      {/* Authenticated Dashboard Routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/vault" element={<VaultPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/chat" element={<AIChatPage />} />
          <Route path="/doctor-summary" element={<DoctorSummaryPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>

      {/* 404 Routes */}
      <Route path="/not-found" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/not-found" replace />} />
    </Routes>
  );
};
