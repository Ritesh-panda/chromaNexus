import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { authService } from '@/services/auth.service';

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
    <div className="space-y-5">
      <Link to="/login" className="inline-flex items-center gap-1.5 text-xs font-medium text-[#10B981] hover:underline">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign In
      </Link>

      <div className="space-y-1">
        <h2 className="text-xl font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
          Reset Your Password
        </h2>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
          Enter your registered email address to receive password reset instructions.
        </p>
      </div>

      {sent ? (
        <div className="p-6 bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] text-center space-y-2.5 rounded-2xl">
          <CheckCircle2 className="w-8 h-8 text-[#10B981] mx-auto" />
          <h4 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Check Your Inbox</h4>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
            We sent a password reset link to <strong className="text-[#1F2937] dark:text-[#F3F4F6]">{email}</strong>.
          </p>
          <Button variant="secondary" size="sm" onClick={() => setSent(false)} className="mt-2">
            Resend Email
          </Button>
        </div>
      ) : (
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

          <Button type="submit" variant="primary" size="lg" className="w-full mt-1" isLoading={isLoading}>
            Send Reset Instructions
          </Button>
        </form>
      )}
    </div>
  );
};
