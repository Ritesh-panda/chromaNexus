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
        title: 'Identity Verified!',
        message: 'Your ChronaNexus patient vault is now active.',
      });
      navigate('/dashboard');
    }, 1000);
  };

  return (
    <div className="space-y-6 text-center">
      <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto">
        <ShieldCheck className="w-6 h-6" />
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          Enter 6-Digit Security PIN
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
          We sent a verification code to your registered mobile device.
        </p>
      </div>

      {/* 6-Digit Input Boxes */}
      <div className="flex justify-center space-x-2 py-4">
        {otp.map((digit, idx) => (
          <input
            key={idx}
            id={`otp-input-${idx}`}
            type="text"
            maxLength={1}
            value={digit}
            onChange={(e) => handleOtpChange(e.target.value, idx)}
            className="w-11 h-12 text-center text-lg font-bold rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#0B0F19] text-slate-900 dark:text-slate-100 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 focus:outline-none transition-all"
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

      <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
        <span>Didn't receive code?</span>
        <button
          type="button"
          onClick={() => addToast({ type: 'info', title: 'New OTP Sent', message: 'Check your mobile SMS.' })}
          className="font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Resend Code
        </button>
      </div>
    </div>
  );
};
