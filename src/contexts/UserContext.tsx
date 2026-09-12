import React, { createContext, useContext, useState } from 'react';
import type { Patient } from '@/types';
import { MOCK_PATIENT } from '@/constants/mockData';

interface UserContextType {
  patient: Patient;
  updatePatient: (updated: Partial<Patient>) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [patient, setPatient] = useState<Patient>(MOCK_PATIENT);

  const updatePatient = (updated: Partial<Patient>) => {
    setPatient((prev) => ({ ...prev, ...updated }));
  };

  return (
    <UserContext.Provider value={{ patient, updatePatient }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = (): UserContextType => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};
