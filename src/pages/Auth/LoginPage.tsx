import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useUI } from '@/contexts/UIContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Mail, Lock, ArrowRight, AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const { addToast } = useUI();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email.trim() || !password) {
      setError('Please fill in both email and password.');
      return;
    }
    setIsSubmitting(true);
    try {
      await login({ email: email.trim().toLowerCase(), password, rememberMe });
      addToast({
        type: 'success',
        title: 'Welcome back',
        message: 'Authenticated securely into ChronaNexus Vault.',
      });
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 401) {
        setError(typeof detail === 'string' ? detail : 'Invalid email or password. Please verify your credentials or create a new account.');
      } else {
        setError(typeof detail === 'string' ? detail : err.message || 'Unable to connect to service. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center sm:text-left">
        <h2 className="text-xl font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
          Sign in to ChronaNexus
        </h2>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
          Access your continuous longitudinal medical memory vault.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/40 border border-rose-200/80 dark:border-rose-900/40 text-xs font-medium text-[#B91C1C] dark:text-rose-400 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p>{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3.5">
        <Input
          label="Email Address"
          type="email"
          placeholder="name@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail className="w-4 h-4" />}
          required
        />

        <Input
          label="Password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<Lock className="w-4 h-4" />}
          required
        />

        <div className="flex items-center justify-between text-xs pt-0.5">
          <label className="flex items-center gap-2 cursor-pointer text-[#4B5563] dark:text-[#9CA3AF]">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded text-[#10B981] focus:ring-emerald-500 border-[#D1D5DB] dark:border-[#4B5563]"
            />
            Remember me
          </label>
          <Link to="/forgot-password" className="font-medium text-[#10B981] hover:underline">
            Forgot Password?
          </Link>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-2"
          isLoading={isSubmitting}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Sign In
        </Button>
      </form>

      <div className="text-center text-xs text-[#6B7280] dark:text-[#9CA3AF] pt-2">
        Don't have an account?{' '}
        <Link to="/signup" className="font-semibold text-[#10B981] hover:underline">
          Create Patient Account
        </Link>
      </div>
    </div>
  );
};
