import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useUI } from '@/contexts/UIContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Mail, Lock, ArrowRight, KeyRound } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('alex.vance@example.com');
  const [password, setPassword] = useState('Password123!');
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const { addToast } = useUI();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Please fill in both email and password.');
      return;
    }
    setIsSubmitting(true);
    try {
      await login({ email, password, rememberMe });
      addToast({
        type: 'success',
        title: 'Welcome back',
        message: 'Authenticated securely into ChronaNexus Vault.',
      });
      navigate('/dashboard');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Invalid credentials');
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
        <div className="p-3 rounded-xl bg-[#FEF2F2] dark:bg-rose-950/40 border border-rose-200/80 dark:border-rose-900/40 text-xs font-medium text-[#B91C1C] dark:text-rose-400">
          {error}
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
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          leftIcon={<Lock className="w-4 h-4" />}
          required
        />

        <div className="flex items-center justify-between text-xs pt-1">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded text-[#10B981] focus:ring-emerald-500/20"
            />
            <span className="text-[#6B7280] dark:text-[#9CA3AF] font-medium">Remember me</span>
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

      {/* Quick Demo Login Option */}
      <div className="pt-3.5 border-t border-[#E5E7EB]/80 dark:border-[#2F3540] space-y-2.5">
        <button
          type="button"
          onClick={() => {
            setEmail('alex.vance@example.com');
            setPassword('Demo123!');
          }}
          className="w-full py-2 px-3 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] text-xs font-medium hover:bg-[#F3F1ED] transition-colors flex items-center justify-center gap-2"
        >
          <KeyRound className="w-3.5 h-3.5 text-[#10B981]" /> Autofill Demo Credentials (Alex Vance)
        </button>

        <p className="text-center text-xs text-[#6B7280] dark:text-[#9CA3AF]">
          Don't have an account?{' '}
          <Link to="/signup" className="font-semibold text-[#10B981] hover:underline">
            Create Patient Account
          </Link>
        </p>
      </div>
    </div>
  );
};
