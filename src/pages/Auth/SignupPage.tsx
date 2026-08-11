import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUI } from '../../contexts/UIContext';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Mail, Lock, User as UserIcon, ArrowRight, ShieldCheck, Stethoscope, CheckCircle2 } from 'lucide-react';

export const SignupPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'patient' | 'doctor'>('patient');
  const [agreed, setAgreed] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { signup } = useAuth();
  const { addToast } = useUI();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) return;
    setIsSubmitting(true);
    try {
      await signup({ name, email, password, role });
      addToast({
        type: 'success',
        title: 'Account Created Successfully!',
        message: 'Proceeding to OTP Verification.',
      });
      navigate('/otp-verification');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center sm:text-left">
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          Create ChronaNexus Account
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Initialize your privacy-first longitudinal medical intelligence vault.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Role Selector Tabs */}
        <div>
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 block">
            Account Type
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setRole('patient')}
              className={`flex items-center justify-center gap-2 p-3 rounded-2xl border text-xs font-semibold transition-all ${
                role === 'patient'
                  ? 'bg-blue-50 dark:bg-blue-950/60 border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-50'
              }`}
            >
              <UserIcon className="w-4 h-4" /> Patient / Personal
            </button>
            <button
              type="button"
              onClick={() => setRole('doctor')}
              className={`flex items-center justify-center gap-2 p-3 rounded-2xl border text-xs font-semibold transition-all ${
                role === 'doctor'
                  ? 'bg-blue-50 dark:bg-blue-950/60 border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-50'
              }`}
            >
              <Stethoscope className="w-4 h-4" /> Healthcare Provider
            </button>
          </div>
        </div>

        <Input
          label="Full Name"
          placeholder="e.g. Dr. Alex Vance"
          value={name}
          onChange={(e) => setName(e.target.value)}
          leftIcon={<UserIcon className="w-4 h-4" />}
          required
        />

        <Input
          label="Email Address"
          type="email"
          placeholder="alex@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail className="w-4 h-4" />}
          required
        />

        <Input
          label="Password"
          type="password"
          placeholder="Minimum 8 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<Lock className="w-4 h-4" />}
          required
        />

        {/* Terms Checkbox */}
        <label className="flex items-start space-x-2 cursor-pointer text-xs text-slate-600 dark:text-slate-400">
          <input
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="rounded text-blue-600 focus:ring-blue-500 mt-0.5"
            required
          />
          <span>
            I agree to the <a href="#" className="text-blue-600 hover:underline">Terms of Service</a> and acknowledge the <a href="#" className="text-blue-600 hover:underline">HIPAA Data Privacy Notice</a>.
          </span>
        </label>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full"
          isLoading={isSubmitting}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Create Account & Verify OTP
        </Button>
      </form>

      <p className="text-center text-xs text-slate-500 dark:text-slate-400 pt-2">
        Already have an account?{' '}
        <Link to="/login" className="font-bold text-blue-600 dark:text-blue-400 hover:underline">
          Sign In
        </Link>
      </p>
    </div>
  );
};
