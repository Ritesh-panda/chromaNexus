import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useUI } from '@/contexts/UIContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Mail, Lock, User as UserIcon, ArrowRight, Stethoscope, AlertCircle } from 'lucide-react';

export const SignupPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'patient' | 'doctor'>('patient');
  const [agreed, setAgreed] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const { signup } = useAuth();
  const { addToast } = useUI();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!name.trim() || !email.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setIsSubmitting(true);
    try {
      await signup({ name: name.trim(), email: email.trim().toLowerCase(), password, role });
      addToast({
        type: 'success',
        title: 'Account Created Successfully!',
        message: 'Proceeding to OTP Verification.',
      });
      navigate('/otp-verification');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : err.message || 'Failed to create account.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center sm:text-left">
        <h2 className="text-xl font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
          Create ChronaNexus Account
        </h2>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
          Initialize your privacy-first longitudinal medical intelligence vault.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/40 border border-rose-200/80 dark:border-rose-900/40 text-xs font-medium text-[#B91C1C] dark:text-rose-400 space-y-1.5">
          <div className="flex items-center gap-1.5 font-semibold">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Registration Error</span>
          </div>
          <p>{error}</p>
          {error.toLowerCase().includes('already exists') && (
            <div className="pt-1">
              <Link to="/login" className="font-semibold underline hover:text-[#991B1B]">
                Click here to sign in with this email &rarr;
              </Link>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3.5">
        {/* Role Selector Tabs */}
        <div>
          <label className="text-xs font-medium text-[#4B5563] dark:text-[#9CA3AF] mb-1.5 block">
            Account Type
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setRole('patient')}
              className={`flex items-center justify-center gap-2 p-2.5 rounded-xl border text-xs font-medium transition-colors ${
                role === 'patient'
                  ? 'bg-[#ECFDF5] dark:bg-emerald-950/40 border-[#10B981] text-[#15803D] dark:text-emerald-300 font-semibold'
                  : 'border-[#E5E7EB] dark:border-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5]'
              }`}
            >
              <UserIcon className="w-3.5 h-3.5" /> Patient / Personal
            </button>
            <button
              type="button"
              onClick={() => setRole('doctor')}
              className={`flex items-center justify-center gap-2 p-2.5 rounded-xl border text-xs font-medium transition-colors ${
                role === 'doctor'
                  ? 'bg-[#ECFDF5] dark:bg-emerald-950/40 border-[#10B981] text-[#15803D] dark:text-emerald-300 font-semibold'
                  : 'border-[#E5E7EB] dark:border-[#2F3540] text-[#6B7280] dark:text-[#9CA3AF] hover:bg-[#FAF8F5]'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5" /> Healthcare Provider
            </button>
          </div>
        </div>

        <Input
          label="Full Name"
          placeholder="e.g. Ritesh Ranjan Panda"
          value={name}
          onChange={(e) => setName(e.target.value)}
          leftIcon={<UserIcon className="w-4 h-4" />}
          required
        />

        <Input
          label="Email Address"
          type="email"
          placeholder="ritesh@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail className="w-4 h-4" />}
          required
        />

        <Input
          label="Password"
          type="password"
          placeholder="At least 6 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<Lock className="w-4 h-4" />}
          required
        />

        <div className="flex items-center gap-2 pt-1">
          <input
            id="terms"
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="w-4 h-4 rounded text-[#10B981] focus:ring-emerald-500 border-[#D1D5DB] dark:border-[#4B5563]"
            required
          />
          <label htmlFor="terms" className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            I agree to the{' '}
            <a href="#" className="text-[#10B981] hover:underline">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="#" className="text-[#10B981] hover:underline">
              HIPAA Privacy Notice
            </a>
          </label>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-2"
          isLoading={isSubmitting}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Create Patient Account
        </Button>
      </form>

      <div className="text-center text-xs text-[#6B7280] dark:text-[#9CA3AF] pt-2">
        Already registered?{' '}
        <Link to="/login" className="font-semibold text-[#10B981] hover:underline">
          Sign In
        </Link>
      </div>
    </div>
  );
};
