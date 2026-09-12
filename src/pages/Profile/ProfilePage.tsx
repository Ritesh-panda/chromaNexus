import React from 'react';
import { Card, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { useUser } from '@/contexts/UserContext';
import { useAuth } from '@/contexts/AuthContext';
import { User, Phone, ShieldCheck, Heart, AlertTriangle, Building2, Save } from 'lucide-react';
import { useUI } from '@/contexts/UIContext';

export const ProfilePage: React.FC = () => {
  const { patient, updatePatient } = useUser();
  const { user } = useAuth();
  const { addToast } = useUI();

  const handleSave = () => {
    addToast({
      type: 'success',
      title: 'Profile Updated',
      message: 'Personal medical profile changes saved successfully.',
    });
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <User className="w-6 h-6 text-blue-500" /> Patient Medical Profile
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Personal identification, emergency contact, and baseline biometric data.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card Summary */}
        <Card className="p-6 text-center space-y-4 border-slate-200 dark:border-slate-800 h-fit">
          <Avatar src={user?.avatarUrl} name={user?.name || 'Alex Vance'} size="xl" className="mx-auto" />
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">{user?.name || 'Alex Vance'}</h3>
            <p className="text-xs text-slate-400 font-mono">{user?.email}</p>
          </div>

          <div className="flex justify-center gap-2">
            <Badge variant="default">Blood Type: {patient.bloodGroup}</Badge>
            <Badge variant="success">Age: 38</Badge>
          </div>

          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-left text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Height / Weight:</span>
              <span className="font-semibold">{patient.heightCm} cm / {patient.weightKg} kg</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Primary Physician:</span>
              <span className="font-semibold text-right">{patient.primaryCarePhysician}</span>
            </div>
          </div>
        </Card>

        {/* Edit Details */}
        <Card className="lg:col-span-2 p-6 border-slate-200 dark:border-slate-800 space-y-6">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Personal Information</h3>
            <p className="text-xs text-slate-500">Demographic info synced with your patient memory graph.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Full Name" defaultValue={user?.name} />
            <Input label="Date of Birth" type="date" defaultValue={patient.dateOfBirth} />
            <Input label="Blood Group" defaultValue={patient.bloodGroup} />
            <Input label="Primary Care Physician" defaultValue={patient.primaryCarePhysician} />
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800 pt-4 space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Phone className="w-4 h-4 text-rose-500" /> Emergency Contact Details
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Input label="Contact Name" defaultValue={patient.emergencyContact.name} />
              <Input label="Relationship" defaultValue={patient.emergencyContact.relationship} />
              <Input label="Phone Number" defaultValue={patient.emergencyContact.phone} />
            </div>
          </div>

          <div className="border-t border-slate-100 dark:border-slate-800 pt-4 flex justify-end">
            <Button variant="primary" onClick={handleSave} leftIcon={<Save className="w-4 h-4" />}>
              Save Profile Changes
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
