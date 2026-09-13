import React from 'react';
import { AppProviders } from '@/app/providers';
import { AppRoutes } from '@/routes/AppRoutes';

export function App() {
  return (
    <AppProviders>
      <AppRoutes />
    </AppProviders>
  );
}

export default App;
