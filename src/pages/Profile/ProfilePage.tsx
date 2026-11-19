import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { useUser } from '@/contexts/UserContext';
import { useAuth } from '@/contexts/AuthContext';
import { User, Phone, Save, CheckCircle2 } from 'lucide-react';
import { useUI } from '@/contexts/UIContext';

export const ProfilePage: React.FC = () => {
  const { patient, updatePatient } = useUser();
  const { user } = useAuth();
  const { addToast } = useUI();

  const [fullName, setFullName] = useState(user?.name || '');
  const [dob, setDob] = useState(patient?.dateOfBirth || '');
  const [bloodGroup, setBloodGroup] = useState(patient?.bloodGroup || '');
  const [heightCm, setHeightCm] = useState(patient?.heightCm ? String(patient.heightCm) : '');
  const [weightKg, setWeightKg] = useState(patient?.weightKg ? String(patient.weightKg) : '');
  const [physician, setPhysician] = useState(patient?.primaryCarePhysician || '');
  const [contactName, setContactName] = useState(patient?.emergencyContact?.name || '');
  const [contactRel, setContactRel] = useState(patient?.emergencyContact?.relationship || '');
  const [contactPhone, setContactPhone] = useState(patient?.emergencyContact?.phone || '');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user?.name) setFullName(user.name);
    if (patient) {
      setDob(patient.dateOfBirth || '');
      setBloodGroup(patient.bloodGroup || '');
      setHeightCm(patient.heightCm ? String(patient.heightCm) : '');
      setWeightKg(patient.weightKg ? String(patient.weightKg) : '');
      setPhysician(patient.primaryCarePhysician || '');
      setContactName(patient.emergencyContact?.name || '');
      setContactRel(patient.emergencyContact?.relationship || '');
      setContactPhone(patient.emergencyContact?.phone || '');
    }
  }, [user, patient]);

  const calculateAge = (dobString?: string): number | null => {
    if (!dobString) return null;
    const birth = new Date(dobString);
    if (isNaN(birth.getTime())) return null;
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age >= 0 ? age : null;
  };

  const calculatedAge = calculateAge(dob);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updatePatient({
        dateOfBirth: dob || undefined,
        bloodGroup: bloodGroup || undefined,
        heightCm: heightCm ? parseFloat(heightCm) : undefined,
        weightKg: weightKg ? parseFloat(weightKg) : undefined,
        primaryCarePhysician: physician || undefined,
        emergencyContact: {
          name: contactName,
          relationship: contactRel,
          phone: contactPhone,
        },
      });
      addToast({
        type: 'success',
        title: 'Profile Updated',
        message: 'Personal medical profile changes saved successfully.',
      });
    } catch {
      addToast({
        type: 'error',
        title: 'Save Failed',
        message: 'Unable to save profile changes.',
      });
    } finally {
      setIsSaving(false);
    }
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
          <Avatar src={user?.avatarUrl} name={fullName || 'Patient'} size="xl" className="mx-auto" />
          <div>
            <h3 className="text-base font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{fullName || 'Patient'}</h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] font-mono mt-0.5">{user?.email}</p>
          </div>

          <div className="flex justify-center flex-wrap gap-2">
            <Badge variant="default">
              Blood Type: {bloodGroup || 'Not recorded'}
            </Badge>
            {calculatedAge !== null ? (
              <Badge variant="success">Age: {calculatedAge}</Badge>
            ) : (
              <Badge variant="secondary">Age: Not recorded</Badge>
            )}
          </div>

          <div className="pt-4 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] text-left text-xs space-y-2.5">
            <div className="flex items-center justify-between text-[#6B7280] dark:text-[#9CA3AF]">
              <span>Height / Weight:</span>
              <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">
                {heightCm || '--'} cm / {weightKg || '--'} kg
              </span>
            </div>
            <div className="flex items-center justify-between text-[#6B7280] dark:text-[#9CA3AF]">
              <span>Primary Physician:</span>
              <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6] text-right truncate max-w-[150px]">
                {physician || 'Not assigned'}
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
            <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
            <Input label="Date of Birth" type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
            <Input label="Blood Group" placeholder="e.g. O+, A-, B+" value={bloodGroup} onChange={(e) => setBloodGroup(e.target.value)} />
            <Input label="Primary Care Physician" placeholder="e.g. Dr. Jane Doe" value={physician} onChange={(e) => setPhysician(e.target.value)} />
            <Input label="Height (cm)" type="number" placeholder="175" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
            <Input label="Weight (kg)" type="number" placeholder="70" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} />
          </div>

          <div className="border-t border-[#E5E7EB]/80 dark:border-[#2F3540] pt-4 space-y-4">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
              <Phone className="w-4 h-4 text-[#B91C1C]" /> Emergency Contact Details
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Input label="Contact Name" placeholder="Full Name" value={contactName} onChange={(e) => setContactName(e.target.value)} />
              <Input label="Relationship" placeholder="e.g. Spouse, Parent" value={contactRel} onChange={(e) => setContactRel(e.target.value)} />
              <Input label="Phone Number" placeholder="+1 (555) 000-0000" value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
            </div>
          </div>

          <div className="border-t border-[#E5E7EB]/80 dark:border-[#2F3540] pt-4 flex justify-end">
            <Button variant="primary" onClick={handleSave} isLoading={isSaving} leftIcon={<Save className="w-4 h-4" />}>
              Save Profile Changes
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
export default ProfilePage;
