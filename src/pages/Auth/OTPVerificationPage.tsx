import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { ShieldCheck, ArrowRight, RotateCcw } from 'lucide-react';
import { useUI } from '@/contexts/UIContext';

export const OTPVerificationPage: React.FC = () => {
  const [otp, setOtp] = useState(['5', '8', '2', '9', '1', '4']);
  const [isVerifying, setIsVerifying] = useState(false);
  const { addToast } = useUI();
  const navigate = useNavigate();

  const handleOtpChange = (val: string, idx: number) => {
    if (val.length > 1) return;
    const newOtp = [...otp];
    newOtp[idx] = val;
    setOtp(newOtp);
    if (val && idx < 5) {
      const nextInput = document.getElementById(`otp-input-${idx + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleVerify = async () => {
    const code = otp.join('');
    if (code.length !== 6) return;
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      addToast({
        type: 'success',
        title: 'Identity Verified',
        message: 'Your ChronaNexus patient vault is now active.',
      });
      navigate('/dashboard');
    }, 1000);
  };

  return (
    <div className="space-y-5 text-center">
      <div className="w-11 h-11 rounded-2xl bg-[#ECFDF5] dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 text-[#10B981] flex items-center justify-center mx-auto">
        <ShieldCheck className="w-6 h-6" />
      </div>

      <div className="space-y-1">
        <h2 className="text-xl font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
          Enter 6-Digit Security PIN
        </h2>
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] max-w-xs mx-auto">
          We sent a verification code to your registered mobile device.
        </p>
      </div>

      {/* 6-Digit Input Boxes */}
      <div className="flex justify-center space-x-2 py-3">
        {otp.map((digit, idx) => (
          <input
            key={idx}
            id={`otp-input-${idx}`}
            type="text"
            maxLength={1}
            value={digit}
            onChange={(e) => handleOtpChange(e.target.value, idx)}
            className="w-10 sm:w-11 h-12 text-center text-lg font-semibold rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23] text-[#1F2937] dark:text-[#F3F4F6] focus:border-[#10B981] focus:ring-2 focus:ring-emerald-500/15 focus:outline-none transition-all tabular-nums"
          />
        ))}
      </div>

      <Button
        variant="primary"
        size="lg"
        className="w-full"
        isLoading={isVerifying}
        onClick={handleVerify}
        rightIcon={<ArrowRight className="w-4 h-4" />}
      >
        Verify & Access Vault
      </Button>

      <div className="flex items-center justify-center gap-1.5 text-xs text-[#6B7280] dark:text-[#9CA3AF] pt-1">
        <span>Didn't receive code?</span>
        <button
          type="button"
          onClick={() => addToast({ type: 'info', title: 'New OTP Sent', message: 'Check your mobile device.' })}
          className="font-medium text-[#10B981] hover:underline flex items-center gap-1"
        >
          <RotateCcw className="w-3 h-3" /> Resend Code
        </button>
      </div>
    </div>
  );
};
