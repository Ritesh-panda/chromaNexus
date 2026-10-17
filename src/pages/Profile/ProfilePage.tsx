import React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { useUser } from '@/contexts/UserContext';
import { useAuth } from '@/contexts/AuthContext';
import { User, Phone, Save } from 'lucide-react';
import { useUI } from '@/contexts/UIContext';

export const ProfilePage: React.FC = () => {
  const { patient } = useUser();
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
        <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
          <User className="w-5 h-5 text-[#10B981]" /> Patient Medical Profile
        </h1>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
          Personal identification, emergency contact, and baseline biometric data.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card Summary */}
        <Card className="p-6 text-center space-y-4 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23] h-fit">
          <Avatar src={user?.avatarUrl} name={user?.name || 'Alex Vance'} size="xl" className="mx-auto" />
          <div>
            <h3 className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{user?.name || 'Alex Vance'}</h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] font-mono mt-0.5">{user?.email}</p>
          </div>

          <div className="flex justify-center gap-2">
            <Badge variant="default">Blood Type: {patient.bloodGroup}</Badge>
            <Badge variant="success">Age: 38</Badge>
          </div>

          <div className="pt-4 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] text-left text-xs space-y-2.5">
            <div className="flex items-center justify-between text-[#6B7280] dark:text-[#9CA3AF]">
              <span>Height / Weight:</span>
              <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">
                {patient.heightCm} cm / {patient.weightKg} kg
              </span>
            </div>
            <div className="flex items-center justify-between text-[#6B7280] dark:text-[#9CA3AF]">
              <span>Primary Physician:</span>
              <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] text-right">
                {patient.primaryCarePhysician}
              </span>
            </div>
          </div>
        </Card>

        {/* Edit Details */}
        <Card className="lg:col-span-2 p-6 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23] space-y-6">
          <div className="border-b border-[#E5E7EB]/80 dark:border-[#2F3540] pb-3.5">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Personal Information</h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">Demographic data synced with your patient memory graph.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Full Name" defaultValue={user?.name} />
            <Input label="Date of Birth" type="date" defaultValue={patient.dateOfBirth} />
            <Input label="Blood Group" defaultValue={patient.bloodGroup} />
            <Input label="Primary Care Physician" defaultValue={patient.primaryCarePhysician} />
          </div>

          <div className="border-t border-[#E5E7EB]/80 dark:border-[#2F3540] pt-4 space-y-4">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Phone className="w-4 h-4 text-[#B91C1C]" /> Emergency Contact Details
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Input label="Contact Name" defaultValue={patient.emergencyContact.name} />
              <Input label="Relationship" defaultValue={patient.emergencyContact.relationship} />
              <Input label="Phone Number" defaultValue={patient.emergencyContact.phone} />
            </div>
          </div>

          <div className="border-t border-[#E5E7EB]/80 dark:border-[#2F3540] pt-4 flex justify-end">
            <Button variant="primary" onClick={handleSave} leftIcon={<Save className="w-4 h-4" />}>
              Save Profile Changes
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
