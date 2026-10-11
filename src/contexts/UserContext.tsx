import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Patient } from '@/types';
import { MOCK_PATIENT } from '@/constants/mockData';
import { patientService } from '@/services/patient.service';

interface UserContextType {
  patient: Patient;
  updatePatient: (updated: Partial<Patient>) => void;
  refreshProfile: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [patient, setPatient] = useState<Patient>(MOCK_PATIENT);

  const fetchProfile = async () => {
    try {
      const profile = await patientService.getProfile();
      if (profile.patient) {
        setPatient(profile.patient);
      }
    } catch {
      // Keep existing patient state
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const updatePatient = async (updated: Partial<Patient>) => {
    setPatient((prev) => ({ ...prev, ...updated }));
    try {
      await patientService.updatePatient(updated);
    } catch {
      // Ignore
    }
  };

  return (
    <UserContext.Provider value={{ patient, updatePatient, refreshProfile: fetchProfile }}>
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
