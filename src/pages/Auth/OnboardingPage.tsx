import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/contexts/UserContext';
import { useUI } from '@/contexts/UIContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import {
  User,
  Heart,
  Phone,
  Stethoscope,
  ShieldAlert,
  ArrowRight,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export const OnboardingPage: React.FC = () => {
  const { user } = useAuth();
  const { updatePatient } = useUser();
  const { addToast } = useUI();
  const navigate = useNavigate();

  const [dob, setDob] = useState('');
  const [gender, setGender] = useState<'male' | 'female' | 'other'>('male');
  const [bloodGroup, setBloodGroup] = useState('O+');
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [pcp, setPcp] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactRel, setContactRel] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [allergiesText, setAllergiesText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const parsedAllergies = allergiesText
        ? allergiesText.split(',').map((a) => a.trim()).filter(Boolean)
        : [];

      await updatePatient({
        dateOfBirth: dob || undefined,
        gender,
        bloodGroup: bloodGroup || undefined,
        heightCm: heightCm ? parseFloat(heightCm) : undefined,
        weightKg: weightKg ? parseFloat(weightKg) : undefined,
        primaryCarePhysician: pcp || undefined,
        emergencyContact: {
          name: contactName,
          relationship: contactRel,
          phone: contactPhone,
        },
        knownAllergies: parsedAllergies,
      });

      addToast({
        type: 'success',
        title: 'Profile Configured Successfully!',
        message: 'Your personal health records vault is ready.',
      });
      navigate('/dashboard');
    } catch {
      addToast({
        type: 'error',
        title: 'Setup Incomplete',
        message: 'Proceeding to dashboard. You can complete your profile anytime.',
      });
      navigate('/dashboard');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = () => {
    navigate('/dashboard');
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-[#15803D] dark:text-emerald-300 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" /> Initial Patient Setup
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
          Welcome, {user?.name || 'Patient'}!
        </h1>
        <p className="text-xs sm:text-sm text-[#6B7280] dark:text-[#9CA3AF] max-w-md mx-auto">
          Set up your baseline health biometrics and emergency contacts to personalize your longitudinal memory graph.
        </p>
      </div>

      <Card className="p-6 sm:p-8 bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm rounded-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Section 1: Demographics & Biometrics */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2 border-b border-[#E5E7EB] dark:border-[#2F3540] pb-2">
              <Heart className="w-4 h-4 text-[#10B981]" /> Baseline Biometrics
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Date of Birth"
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                required
              />

              <div>
                <label className="text-xs font-medium text-[#4B5563] dark:text-[#9CA3AF] mb-1.5 block">
                  Biological Gender
                </label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value as any)}
                  className="w-full h-10 px-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-xs sm:text-sm text-[#1F2937] dark:text-[#F3F4F6] focus:border-[#10B981] focus:outline-none"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other / Prefer not to say</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-[#4B5563] dark:text-[#9CA3AF] mb-1.5 block">
                  Blood Group
                </label>
                <select
                  value={bloodGroup}
                  onChange={(e) => setBloodGroup(e.target.value)}
                  className="w-full h-10 px-3 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] text-xs sm:text-sm text-[#1F2937] dark:text-[#F3F4F6] focus:border-[#10B981] focus:outline-none font-semibold text-[#10B981]"
                >
                  <option value="O+">O Positive (O+)</option>
                  <option value="O-">O Negative (O-)</option>
                  <option value="A+">A Positive (A+)</option>
                  <option value="A-">A Negative (A-)</option>
                  <option value="B+">B Positive (B+)</option>
                  <option value="B-">B Negative (B-)</option>
                  <option value="AB+">AB Positive (AB+)</option>
                  <option value="AB-">AB Negative (AB-)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <Input
                  label="Height (cm)"
                  type="number"
                  placeholder="e.g. 175"
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                />
                <Input
                  label="Weight (kg)"
                  type="number"
                  placeholder="e.g. 72"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Section 2: Healthcare Provider */}
          <div className="space-y-4 pt-2">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2 border-b border-[#E5E7EB] dark:border-[#2F3540] pb-2">
              <Stethoscope className="w-4 h-4 text-[#2563EB]" /> Primary Care Physician
            </h3>

            <Input
              label="Doctor / Physician Name"
              placeholder="e.g. Dr. Rajesh Sharma, MD"
              value={pcp}
              onChange={(e) => setPcp(e.target.value)}
              leftIcon={<Stethoscope className="w-4 h-4" />}
            />
          </div>

          {/* Section 3: Emergency Contact */}
          <div className="space-y-4 pt-2">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2 border-b border-[#E5E7EB] dark:border-[#2F3540] pb-2">
              <Phone className="w-4 h-4 text-[#B91C1C]" /> Emergency Contact
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <Input
                label="Contact Name"
                placeholder="e.g. Elena Vance"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
              />
              <Input
                label="Relationship"
                placeholder="e.g. Spouse / Parent"
                value={contactRel}
                onChange={(e) => setContactRel(e.target.value)}
              />
              <Input
                label="Phone Number"
                placeholder="+91 98765 43210"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
              />
            </div>
          </div>

          {/* Section 4: Allergies */}
          <div className="space-y-4 pt-2">
            <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2 border-b border-[#E5E7EB] dark:border-[#2F3540] pb-2">
              <ShieldAlert className="w-4 h-4 text-amber-500" /> Known Drug Allergies
            </h3>

            <Input
              label="Allergies (comma-separated)"
              placeholder="e.g. Penicillin, Sulfa drugs (or leave empty if none)"
              value={allergiesText}
              onChange={(e) => setAllergiesText(e.target.value)}
              leftIcon={<ShieldAlert className="w-4 h-4" />}
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-4 border-t border-[#E5E7EB] dark:border-[#2F3540] flex flex-col sm:flex-row items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleSkip}
              className="text-xs text-[#6B7280] dark:text-[#9CA3AF] hover:underline order-2 sm:order-1"
            >
              Skip setup for now &rarr;
            </button>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full sm:w-auto order-1 sm:order-2"
              isLoading={isSubmitting}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Save & Open My Health Vault
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
export default OnboardingPage;

