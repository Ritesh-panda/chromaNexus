import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { authService } from '../../services/auth.service';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setIsLoading(true);
    try {
      await authService.requestPasswordReset(email);
      setSent(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link to="/login" className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline">
        <ArrowLeft className="w-4 h-4" /> Back to Sign In
      </Link>

      <div className="space-y-2">
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          Reset Your Password
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Enter your registered email address to receive password reset instructions.
        </p>
      </div>

      {sent ? (
        <div className="p-6 glass-card border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/20 text-center space-y-3 rounded-2xl">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
          <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">Check Your Inbox</h4>
          <p className="text-xs text-slate-600 dark:text-slate-300">
            We sent a password reset link to <strong className="text-slate-800 dark:text-slate-100">{email}</strong>.
          </p>
          <Button variant="outline" size="sm" onClick={() => setSent(false)} className="mt-2">
            Resend Email
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="w-4 h-4" />}
            required
          />

          <Button type="submit" variant="primary" size="lg" className="w-full" isLoading={isLoading}>
            Send Reset Instructions
          </Button>
        </form>
      )}
    </div>
  );
};
