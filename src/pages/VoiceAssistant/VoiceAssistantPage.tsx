import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX, 
  PhoneOff, 
  PhoneCall, 
  Globe, 
  Sparkles, 
  ShieldAlert, 
  RefreshCw, 
  User, 
  Bot, 
  Clock, 
  MapPin, 
  Hospital,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { chatService } from '@/services/chat.service';
import { hospitalService } from '@/services/hospital.service';
import type { ChatMessage } from '@/types';

type CallState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface LanguageOption {
  code: string;
  speechCode: string;
  label: string;
  nativeLabel: string;
  flag: string;
  greeting: string;
}

const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en', speechCode: 'en-IN', label: 'English (India)', nativeLabel: 'English', flag: '🇮🇳', greeting: 'Hello! I am your clinical voice assistant. How are you feeling today?' },
  { code: 'or', speechCode: 'or-IN', label: 'Odia', nativeLabel: 'ଓଡ଼ିଆ', flag: '🇮🇳', greeting: 'ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କର ସ୍ୱାସ୍ଥ୍ୟ ସହାୟକ। ଆପଣଙ୍କୁ କିପରି ଲାଗୁଛି କୁହନ୍ତୁ।' },
  { code: 'hi', speechCode: 'hi-IN', label: 'Hindi', nativeLabel: 'हिन्दी', flag: '🇮🇳', greeting: 'नमस्ते! मैं आपका स्वास्थ्य सहायक हूँ। आज आप कैसा महसूस कर रहे हैं?' },
  { code: 'te', speechCode: 'te-IN', label: 'Telugu', nativeLabel: 'తెలుగు', flag: '🇮🇳', greeting: 'నమస్కారం! నేను మీ ఆరోగ్య సహాయకుడిని. మీకు ఎలా ఉంది?' },
  { code: 'ta', speechCode: 'ta-IN', label: 'Tamil', nativeLabel: 'தமிழ்', flag: '🇮🇳', greeting: 'வணக்கம்! நான் உங்கள் மருத்துவ உதவியாளர். உங்களுக்கு எப்படி இருக்கிறது?' },
  { code: 'bn', speechCode: 'bn-IN', label: 'Bengali', nativeLabel: 'বাংলা', flag: '🇮🇳', greeting: 'নমস্কার! আমি আপনার স্বাস্থ্য সহকারী। আজ আপনার কেমন লাগছে?' },
];

const WAITING_PHRASES: Record<string, string> = {
  en: "Checking your records, one moment please...",
  or: "ଟିକେ ଅପେକ୍ଷା କରନ୍ତୁ, ମୁଁ ଯାଞ୍ଚ କରୁଛି...",
  hi: "एक पल रुकिए, मैं जानकारी देख रहा हूँ...",
  te: "ఒక్క క్షణం, నేను సమాచారం చూస్తున్నాను...",
  ta: "ஒரு நிமிடம், விவரங்களைப் பார்க்கிறேன்...",
  bn: "একটু অপেক্ষা করুন, আমি তথ্য দেখছি..."
};

function sanitizeForSpeech(raw: string): string {
  return raw
    // Strip markdown table borders & dividers (|---|---|)
    .replace(/\|[\s-:]+\|[\s-|:]+/g, ' ')
    // Replace table row pipe formatting with spaces
    .replace(/\|/g, ' ')
    // Remove markdown headers (##, ###)
    .replace(/#{1,6}\s+/g, '')
    // Remove horizontal rules (--- or ***)
    .replace(/[-*_]{3,}/g, ' ')
    // Remove bold/italics
    .replace(/[*_]{1,2}(.*?)[*_]{1,2}/g, '$1')
    // Remove bullet points
    .replace(/^[ \t]*[•\-*+][ \t]+/gm, '')
    // Remove URLs
    .replace(/https?:\/\/\S+/g, '')
    // Normalize whitespace
    .replace(/\s+/g, ' ')
    .trim();
}

function isConversationalChitChat(text: string): boolean {
  const t = text.toLowerCase().trim();
  const patterns = [
    /\b(how are you|how do you do|how is it going|how are things|how're you)\b/,
    /\b(i am|i'm|feeling)\s+(fine|good|well|better|okay|ok|great|alright|happy)\b/,
    /^(hi|hello|hey|namaste|greetings|good\s+(morning|afternoon|evening))\b/,
    /\b(thank\s*(you|u)|thanks|thankyou)\b/,
    /\b(who are you|what is your name|what can you do|what are you)\b/,
    /\b(chit\s*chat|small talk|just talking|talk to me)\b/,
    /\b(that'?s not|never mind)\b/,
    // Multilingual Indic greetings & wellness check-ins
    /(ଭଲ ଅଛି|ଭଲ ଲାଗୁଛି|କେମିତି ଅଛନ୍ତି|ନମସ୍କାର|ଧନ୍ୟବାଦ|ତୁମେ କିଏ)/,
    /(मैं ठीक हूँ|अच्छा लग रहा है|सब ठीक है|आप कैसे हैं|नमस्ते|धन्यवाद|शुक्रिया|आप कौन हैं)/,
    /(ভালো আছি|ভালো লাগছে|কেমন আছেন|নমস্কার|ধন্যবাদ)/,
    /(బాగున్నాను|బాగుంది|ఎలా ఉన్నారు|నమస్కారం|ధన్యవాదాలు)/,
    /(நன்றாக இருக்கிறேன்|எப்படி இருக்கிறீர்கள்|வணக்கம்|நன்றி)/
  ];
  return patterns.some((p) => p.test(t));
}

const QUICK_PROMPTS: Record<string, string[]> = {
  en: [
    "I am feeling sick and weak",
    "What are my active medications?",
    "What is my latest HbA1c reading?",
    "Find nearby emergency hospitals",
    "How is my overall health?"
  ],
  or: [
    "ମୁଁ ଅସୁସ୍ଥ ଅଛି",
    "ମୋର ଔଷଧଗୁଡ଼ିକ କ'ଣ ଅଛି?",
    "ମୋର ରକ୍ତ ଶର୍କରା କେତେ ଅଛି?",
    "ନିକଟସ୍ଥ ଡାକ୍ତରଖାନା ଖୋଜନ୍ତୁ",
    "ମୋତେ ମୁଣ୍ଡ ବିନ୍ଧା ହେଉଛି"
  ],
  hi: [
    "मेरी तबीयत खराब है",
    "मेरी सक्रिय दवाइयां क्या हैं?",
    "मेरा ब्लड शुगर और HbA1c क्या है?",
    "पास का आपातकालीन अस्पताल खोजें",
    "मुझे बहुत तेज बुखार है"
  ],
  te: [
    "నాకు ఒంట్లో బాగాలేదు",
    "నా ప్రస్తుత మందులు ఏమిటి?",
    "సమీప ఆసుపత్రులను కనుగొనండి"
  ],
  ta: [
    "எனக்கு உடம்பு சரியில்லை",
    "எனது தற்போதைய மருந்துகள் என்ன?",
    "அருகிலுள்ள மருத்துவமனையைக் கண்டறியவும்"
  ],
  bn: [
    "আমি অসুস্থ বোধ করছি",
    "আমার ওষুধগুলো কি কি?",
    "কাছের হাসপাতাল খুঁজুন"
  ]
};

export const VoiceAssistantPage: React.FC = () => {
  const [selectedLang, setSelectedLang] = useState<LanguageOption>(SUPPORTED_LANGUAGES[0]);
  const [callState, setCallState] = useState<CallState>('idle');
  const [callDuration, setCallDuration] = useState<number>(0);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [isSpeakerMuted, setIsSpeakerMuted] = useState<boolean>(false);
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  const [conversationHistory, setConversationHistory] = useState<Array<{ sender: 'user' | 'ai'; text: string; time: string }>>([]);
  const [threadId, setThreadId] = useState<string>(() => `voice_session_${Date.now()}`);
  const [isEmergency, setIsEmergency] = useState<boolean>(false);
  const [userLocation, setUserLocation] = useState<string>('Detecting location...');

  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const timerRef = useRef<any>(null);
  const isCallActiveRef = useRef<boolean>(false);

  // Initialize SpeechSynthesis and Location
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
    }

    // Auto-detect IP location on page mount
    hospitalService.detectIpLocation().then((loc) => {
      if (loc) {
        setUserLocation(loc.displayName || `${loc.city}, ${loc.region}`);
      }
    });

    return () => {
      stopVoiceCall();
    };
  }, []);

  // Timer Effect
  useEffect(() => {
    if (callState !== 'idle') {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setCallDuration(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [callState]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const speakFallbackWebSpeech = (cleanSpeech: string, onEndCallback?: () => void) => {
    if (!synthRef.current || isSpeakerMuted) {
      if (onEndCallback) onEndCallback();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    utterance.lang = selectedLang.speechCode;
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    const voices = synthRef.current.getVoices();
    let matchedVoice = voices.find((v) => 
      v.lang.toLowerCase() === selectedLang.speechCode.toLowerCase() ||
      v.lang.toLowerCase().replace('_', '-') === selectedLang.speechCode.toLowerCase()
    );

    if (!matchedVoice) {
      matchedVoice = voices.find((v) => 
        v.lang.toLowerCase().includes('in') ||
        v.name.toLowerCase().includes('india') ||
        v.name.toLowerCase().includes('hindi') ||
        v.name.toLowerCase().includes('swara') ||
        v.name.toLowerCase().includes('heera')
      );
    }
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onend = () => {
      if (isCallActiveRef.current) {
        setCallState('listening');
        if (onEndCallback) onEndCallback();
        startRecognition();
      }
    };

    utterance.onerror = (e) => {
      console.warn('Speech synthesis notice:', e);
      if (isCallActiveRef.current) {
        setCallState('listening');
        if (onEndCallback) onEndCallback();
        startRecognition();
      }
    };

    synthRef.current.speak(utterance);
  };

  const speakText = async (text: string, onEndCallback?: () => void) => {
    if (isSpeakerMuted) {
      if (onEndCallback) onEndCallback();
      return;
    }

    // Stop ongoing audio elements or browser synthesis
    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      } catch {}
      audioRef.current = null;
    }
    if (synthRef.current) {
      synthRef.current.cancel();
    }

    // Clean all markdown table syntax, dashes, and bullets for natural human voice
    const cleanSpeech = sanitizeForSpeech(text);
    if (!cleanSpeech) {
      if (onEndCallback) onEndCallback();
      return;
    }

    setCallState('speaking');

    // Attempt high-fidelity Microsoft Edge Neural TTS endpoint (Odia, Bengali, Hindi, Telugu, Tamil)
    try {
      const response = await fetch('/api/v1/voice/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: cleanSpeech,
          language: selectedLang.code,
        }),
      });

      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          audioRef.current = null;
          if (isCallActiveRef.current) {
            setCallState('listening');
            if (onEndCallback) onEndCallback();
            startRecognition();
          }
        };

        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          audioRef.current = null;
          speakFallbackWebSpeech(cleanSpeech, onEndCallback);
        };

        await audio.play();
        return;
      }
    } catch (err) {
      console.warn('Edge-TTS neural endpoint unavailable, falling back to Web Speech API:', err);
    }

    // Fallback to browser SpeechSynthesis
    speakFallbackWebSpeech(cleanSpeech, onEndCallback);
  };

  const startRecognition = () => {
    if (!isCallActiveRef.current) return;

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
    }

    const recognition = new SpeechRecognition();
    recognition.lang = selectedLang.speechCode;
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => {
      if (callState !== 'speaking' && callState !== 'thinking' && isCallActiveRef.current) {
        setCallState('listening');
      }
    };

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join('');
      setCurrentTranscript(transcript);

      if (event.results[0].isFinal) {
        handleUserSpeech(transcript);
      }
    };

    recognition.onerror = (event: any) => {
      if (event.error === 'no-speech' && isCallActiveRef.current && callState === 'listening') {
        setTimeout(() => {
          if (isCallActiveRef.current && callState === 'listening' && !isMuted) {
            try { recognition.start(); } catch {}
          }
        }, 400);
      }
    };

    recognition.onend = () => {
      if (isCallActiveRef.current && callState === 'listening' && !isMuted) {
        setTimeout(() => {
          if (isCallActiveRef.current && callState === 'listening' && !isMuted) {
            try { recognition.start(); } catch {}
          }
        }, 300);
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch (err) {
      console.error('Error starting recognition:', err);
    }
  };

  const handleUserSpeech = async (speechText: string) => {
    const trimmed = speechText.trim();
    if (!trimmed) return;

    // Stop recognition while AI thinks & speaks
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
    }

    const userTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setConversationHistory((prev) => [...prev, { sender: 'user', text: trimmed, time: userTime }]);
    setCurrentTranscript('');
    setCallState('thinking');

    // Only play record-lookup audio filler if the query is an actual clinical/record question.
    // For natural greetings and conversational chit-chat, skip the filler so it responds cleanly and immediately.
    const isChitChat = isConversationalChitChat(trimmed);
    if (!isChitChat && synthRef.current && !isSpeakerMuted) {
      const filler = WAITING_PHRASES[selectedLang.code] || WAITING_PHRASES.en;
      try {
        const waitUtterance = new SpeechSynthesisUtterance(filler);
        waitUtterance.lang = selectedLang.speechCode;
        waitUtterance.rate = 1.05;
        const voices = synthRef.current.getVoices();
        const matched = voices.find((v) => v.lang.toLowerCase().includes('in') || v.name.toLowerCase().includes('india'));
        if (matched) waitUtterance.voice = matched;
        synthRef.current.speak(waitUtterance);
      } catch {}
    }

    try {
      // Pass source="voice" so LLM generates a concise spoken conversational answer without markdown tables
      const response: ChatMessage = await chatService.sendMessage(trimmed, threadId, selectedLang.code, 'voice');
      const aiTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setConversationHistory((prev) => [...prev, { sender: 'ai', text: response.text, time: aiTime }]);

      if (response.isEmergency) {
        setIsEmergency(true);
      }

      // Speak final conversational response out loud
      speakText(response.text);
    } catch (err: any) {
      console.error('Voice query processing error:', err);
      const fallbackText = selectedLang.code === 'or' 
        ? 'କ୍ଷମା କରିବେ, ମୁଁ ଏହା ବୁଝିପାରିଲି ନାହିଁ। ଦୟାକରି ଆଉ ଥରେ କୁହନ୍ତୁ।'
        : selectedLang.code === 'hi'
        ? 'क्षमा करें, मैं समझ नहीं पाया। कृपया दोबारा बोलें।'
        : 'I apologize, there was an issue processing your query. Please speak again.';
      speakText(fallbackText);
    }
  };

  const startVoiceCall = () => {
    isCallActiveRef.current = true;
    setCallState('listening');
    setConversationHistory([]);
    setIsEmergency(false);
    const newThread = `voice_session_${Date.now()}`;
    setThreadId(newThread);

    // Initial warm assistant greeting
    const greeting = selectedLang.greeting;
    const aiTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setConversationHistory([{ sender: 'ai', text: greeting, time: aiTime }]);
    speakText(greeting);
  };

  const stopVoiceCall = () => {
    isCallActiveRef.current = false;
    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      } catch {}
      audioRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }
    if (synthRef.current) {
      try {
        synthRef.current.cancel();
      } catch {}
    }
    setCallState('idle');
    setCurrentTranscript('');
  };

  const toggleMute = () => {
    if (isMuted) {
      setIsMuted(false);
      if (callState === 'listening') {
        startRecognition();
      }
    } else {
      setIsMuted(true);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
    }
  };

  const toggleSpeaker = () => {
    if (!isSpeakerMuted) {
      if (audioRef.current) {
        try {
          audioRef.current.pause();
        } catch {}
      }
      if (synthRef.current) synthRef.current.cancel();
      setIsSpeakerMuted(true);
    } else {
      setIsSpeakerMuted(false);
    }
  };

  const handleLanguageChange = (lang: LanguageOption) => {
    setSelectedLang(lang);
    if (callState !== 'idle') {
      stopVoiceCall();
    }
  };

  const handleQuickPromptClick = (prompt: string) => {
    if (callState === 'idle') {
      setCallState('thinking');
      const newThread = `voice_session_${Date.now()}`;
      setThreadId(newThread);
      handleUserSpeech(prompt);
    } else {
      handleUserSpeech(prompt);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto px-4 sm:px-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" /> Real-Time Multilingual Voice AI
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1F2937] dark:text-[#F3F4F6]">
            Clinical Voice Assistant
          </h1>
          <p className="text-sm text-[#6B7280] dark:text-[#9CA3AF] mt-1">
            Speak naturally in your native language for symptom triage, medication checks, and emergency alerts.
          </p>
        </div>

        {/* Location Badge */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white dark:bg-[#1E222B] border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-medium text-[#4B5563] dark:text-[#D1D5DB] shadow-sm">
            <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="truncate max-w-[180px]">{userLocation}</span>
          </div>
        </div>
      </div>

      {/* Language Selector Bar */}
      <div className="p-3 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
            Active Consultation Language:
          </span>
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {SUPPORTED_LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang)}
              className={`px-3 py-1 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 shrink-0 ${
                selectedLang.code === lang.code
                  ? 'bg-emerald-600 text-white font-semibold shadow-sm'
                  : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-white border border-[#E5E7EB] dark:border-[#2F3540]'
              }`}
            >
              <span>{lang.flag}</span>
              <span>{lang.nativeLabel}</span>
              <span className="text-[10px] opacity-75">({lang.label.split(' ')[0]})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Red-Flag Emergency Banner (if detected) */}
      {isEmergency && (
        <div className="p-4 rounded-2xl bg-red-600 text-white shadow-xl animate-pulse flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white text-red-600 font-bold flex items-center justify-center text-lg shrink-0">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-sm">Critical Symptoms Detected!</h3>
              <p className="text-xs text-red-100">
                Please seek immediate medical attention. Call emergency services right now.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a
              href="tel:108"
              className="px-4 py-2 rounded-xl bg-white text-red-600 font-bold text-xs shadow-md hover:bg-red-50 flex items-center gap-1.5"
            >
              <PhoneCall className="w-4 h-4" /> Call 108 Emergency
            </a>
            <a
              href="/hospitals"
              className="px-3.5 py-2 rounded-xl bg-red-800 text-white font-medium text-xs hover:bg-red-900 flex items-center gap-1"
            >
              <Hospital className="w-4 h-4" /> View Hospitals
            </a>
          </div>
        </div>
      )}

      {/* Main Interactive Voice Orb Arena */}
      <div className="relative overflow-hidden p-8 sm:p-12 rounded-3xl bg-gradient-to-b from-white via-white to-[#F9FAFB] dark:from-[#1B1E23] dark:via-[#1B1E23] dark:to-[#16181D] border border-[#E5E7EB] dark:border-[#2F3540] shadow-xl flex flex-col items-center justify-center text-center">
        {/* Background glow effects */}
        <div
          className={`absolute w-72 h-72 rounded-full blur-3xl opacity-20 pointer-events-none transition-all duration-700 ${
            callState === 'listening'
              ? 'bg-cyan-500 scale-125 opacity-30'
              : callState === 'thinking'
              ? 'bg-purple-500 scale-110 opacity-30 animate-spin'
              : callState === 'speaking'
              ? 'bg-amber-500 scale-125 opacity-40'
              : 'bg-emerald-500 scale-100 opacity-15'
          }`}
        />

        {/* State Badge & Call Duration */}
        <div className="flex items-center gap-2 mb-8 z-10">
          <Badge
            variant={
              callState === 'listening'
                ? 'success'
                : callState === 'thinking'
                ? 'warning'
                : callState === 'speaking'
                ? 'info'
                : 'secondary'
            }
            className="text-xs px-3 py-1 font-semibold flex items-center gap-1.5"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                callState === 'listening'
                  ? 'bg-emerald-500 animate-ping'
                  : callState === 'speaking'
                  ? 'bg-amber-400 animate-bounce'
                  : callState === 'thinking'
                  ? 'bg-purple-500 animate-spin'
                  : 'bg-gray-400'
              }`}
            />
            {callState === 'listening'
              ? 'Listening to you...'
              : callState === 'thinking'
              ? 'Analyzing clinical records...'
              : callState === 'speaking'
              ? 'ChronaNexus is Speaking...'
              : 'Voice Assistant Ready'}
          </Badge>

          {callState !== 'idle' && (
            <div className="flex items-center gap-1 text-xs font-mono font-medium text-[#6B7280] dark:text-[#9CA3AF] px-2.5 py-1 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540]">
              <Clock className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              {formatTimer(callDuration)}
            </div>
          )}
        </div>

        {/* The Central Voice Orb */}
        <div className="relative my-4 z-10 flex items-center justify-center cursor-pointer" onClick={callState === 'idle' ? startVoiceCall : stopVoiceCall}>
          {/* Animated Wave Rings */}
          {callState !== 'idle' && (
            <>
              <div
                className={`absolute w-48 h-48 rounded-full border border-emerald-500/20 dark:border-emerald-400/20 animate-ping`}
                style={{ animationDuration: '3s' }}
              />
              <div
                className={`absolute w-56 h-56 rounded-full border border-emerald-500/10 dark:border-emerald-400/10 animate-pulse`}
              />
            </>
          )}

          {/* Core Visual Orb */}
          <div
            className={`w-36 h-36 sm:w-44 sm:h-44 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 ${
              callState === 'listening'
                ? 'bg-gradient-to-tr from-cyan-500 via-teal-400 to-emerald-500 shadow-cyan-500/40 scale-105'
                : callState === 'thinking'
                ? 'bg-gradient-to-tr from-purple-600 via-indigo-500 to-pink-500 shadow-purple-500/40 animate-pulse scale-95'
                : callState === 'speaking'
                ? 'bg-gradient-to-tr from-amber-500 via-rose-500 to-violet-600 shadow-amber-500/40 scale-110'
                : 'bg-gradient-to-tr from-emerald-600 via-teal-700 to-slate-800 shadow-emerald-600/20 hover:scale-105'
            }`}
          >
            <div className="w-28 h-28 sm:w-36 sm:h-36 rounded-full bg-white/10 backdrop-blur-md flex flex-col items-center justify-center text-white border border-white/20">
              <Mic
                className={`w-10 h-10 sm:w-12 sm:h-12 transition-transform duration-300 ${
                  callState === 'listening'
                    ? 'scale-110 text-white drop-shadow-md'
                    : callState === 'speaking'
                    ? 'scale-105 text-white animate-pulse'
                    : 'text-white/80'
                }`}
              />
              <span className="text-[10px] font-bold tracking-wider uppercase mt-1">
                {callState === 'idle' ? 'Tap to Call' : selectedLang.code.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Live Audio Waveform Simulation */}
        <div className="flex items-center gap-1.5 h-8 my-4 z-10">
          {[40, 70, 95, 60, 85, 45, 90, 75, 30, 80, 65, 40].map((h, i) => (
            <div
              key={i}
              className={`w-1 rounded-full transition-all duration-150 ${
                callState === 'speaking'
                  ? 'bg-amber-400 animate-pulse'
                  : callState === 'listening'
                  ? 'bg-emerald-500'
                  : 'bg-gray-300 dark:bg-gray-700'
              }`}
              style={{
                height: callState === 'idle' ? '4px' : `${Math.max(6, (h * (callState === 'speaking' ? 0.9 : 0.6)))}px`,
                animationDelay: `${i * 80}ms`
              }}
            />
          ))}
        </div>

        {/* Live Spoken Transcript */}
        <div className="min-h-[50px] max-w-xl mx-auto z-10 px-4">
          {currentTranscript ? (
            <p className="text-base sm:text-lg font-semibold text-[#1F2937] dark:text-[#F3F4F6] animate-fade-in">
              "{currentTranscript}"
            </p>
          ) : callState === 'listening' ? (
            <p className="text-sm text-[#9CA3AF] italic">
              Speak now in {selectedLang.label}...
            </p>
          ) : callState === 'thinking' ? (
            <p className="text-sm text-purple-600 dark:text-purple-400 font-medium">
              Consulting medical guidelines & clinical history...
            </p>
          ) : callState === 'speaking' ? (
            <p className="text-sm text-amber-600 dark:text-amber-400 font-medium">
              Audio playback active...
            </p>
          ) : (
            <p className="text-sm text-[#6B7280] dark:text-[#9CA3AF]">
              Tap the orb to start live voice consultation with ChronaNexus AI.
            </p>
          )}
        </div>

        {/* Voice Call Control Buttons */}
        <div className="flex items-center gap-3 mt-6 z-10">
          {callState === 'idle' ? (
            <Button
              size="lg"
              onClick={startVoiceCall}
              className="px-8 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-lg shadow-emerald-600/30 flex items-center gap-2"
            >
              <Mic className="w-5 h-5" /> Start Voice Consultation
            </Button>
          ) : (
            <>
              {/* Mute Mic */}
              <button
                onClick={toggleMute}
                title={isMuted ? 'Unmute Microphone' : 'Mute Microphone'}
                className={`w-12 h-12 rounded-2xl flex items-center justify-center border transition-all ${
                  isMuted
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-500'
                    : 'bg-white dark:bg-[#23272E] border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6]'
                }`}
              >
                {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              {/* End Call Button */}
              <button
                onClick={stopVoiceCall}
                title="End Voice Call"
                className="w-14 h-14 rounded-2xl bg-red-600 hover:bg-red-700 text-white flex items-center justify-center shadow-lg shadow-red-600/30 transition-transform active:scale-95"
              >
                <PhoneOff className="w-6 h-6" />
              </button>

              {/* Mute Speaker */}
              <button
                onClick={toggleSpeaker}
                title={isSpeakerMuted ? 'Unmute Audio Speaker' : 'Mute Audio Speaker'}
                className={`w-12 h-12 rounded-2xl flex items-center justify-center border transition-all ${
                  isSpeakerMuted
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-500'
                    : 'bg-white dark:bg-[#23272E] border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6]'
                }`}
              >
                {isSpeakerMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Suggested Spoken Phrases / Quick Chips */}
      <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm">
        <div className="text-xs font-semibold text-[#6B7280] dark:text-[#9CA3AF] mb-2.5">
          Or tap a phrase to speak it in {selectedLang.label}:
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {(QUICK_PROMPTS[selectedLang.code] || QUICK_PROMPTS.en).map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleQuickPromptClick(prompt)}
              className="px-3 py-1.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] hover:bg-emerald-500/10 hover:text-emerald-600 dark:hover:text-emerald-400 border border-[#E5E7EB] dark:border-[#2F3540] text-xs font-medium text-[#4B5563] dark:text-[#D1D5DB] transition-all flex items-center gap-1.5"
            >
              <span>💬</span>
              <span>{prompt}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Spoken Dialogue Transcript History */}
      {conversationHistory.length > 0 && (
        <div className="p-4 rounded-2xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#E5E7EB]/70 dark:border-[#2F3540]/70">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#6B7280] dark:text-[#9CA3AF] flex items-center gap-1.5">
              <span>🎙️</span> Spoken Consultation Transcript
            </h3>
            <span className="text-[11px] text-[#9CA3AF]">
              {conversationHistory.length} exchanges
            </span>
          </div>

          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {conversationHistory.map((item, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-2xl text-xs sm:text-sm flex flex-col ${
                  item.sender === 'user'
                    ? 'bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-500/20 text-[#1F2937] dark:text-[#F3F4F6] ml-8'
                    : 'bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] mr-8'
                }`}
              >
                <div className="flex items-center justify-between mb-1 text-[11px] font-semibold text-[#6B7280] dark:text-[#9CA3AF]">
                  <span className="flex items-center gap-1">
                    {item.sender === 'user' ? <User className="w-3 h-3 text-emerald-600" /> : <Bot className="w-3 h-3 text-emerald-600" />}
                    {item.sender === 'user' ? 'You (Spoken)' : 'ChronaNexus Assistant'}
                  </span>
                  <span>{item.time}</span>
                </div>
                <p className="whitespace-pre-line leading-relaxed">{item.text}</p>
                {item.sender === 'ai' && (
                  <div className="mt-2 pt-1 border-t border-black/5 dark:border-white/5 flex items-center justify-end">
                    <button
                      onClick={() => speakText(item.text)}
                      className="text-[11px] text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1"
                    >
                      <Volume2 className="w-3 h-3" /> Replay Voice
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
export default VoiceAssistantPage;
