import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  ArrowRight,
  ShieldCheck,
  Brain,
  GitCommit,
  Bot,
  FolderLock,
  Stethoscope,
  CheckCircle2,
  Layers,
  Database,
  Cpu,
  Activity
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-20 pb-20">
      {/* Hero Section */}
      <section className="relative pt-16 sm:pt-20 pb-12 px-6 overflow-hidden">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white dark:bg-[#1B1E23] text-xs font-medium text-[#1F2937] dark:text-[#F3F4F6] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm"
          >
            <span className="w-2 h-2 rounded-full bg-[#10B981]" />
            <span>Longitudinal Medical Intelligence Platform</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="text-3xl sm:text-5xl md:text-6xl font-semibold tracking-tight text-[#1F2937] dark:text-[#F3F4F6] max-w-4xl mx-auto leading-[1.15]"
          >
            Transforming fragmented medical records into a{' '}
            <span className="text-[#10B981]">continuous patient memory.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="text-sm sm:text-base text-[#6B7280] dark:text-[#9CA3AF] max-w-2xl mx-auto leading-relaxed"
          >
            ChronaNexus understands clinical documentation, extracts structured medical entities, connects events across years, and enables natural language interaction with your complete health history.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15 }}
            className="flex flex-wrap items-center justify-center gap-3 pt-2"
          >
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate('/dashboard')}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Explore Live Platform
            </Button>
            <Button
              variant="secondary"
              size="lg"
              onClick={() => navigate('/signup')}
              leftIcon={<ShieldCheck className="w-4 h-4 text-[#10B981]" />}
            >
              Create Patient Memory
            </Button>
          </motion.div>

          {/* Interactive UI Mockup Hero Widget */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="pt-8 max-w-4xl mx-auto"
          >
            <div className="bg-white dark:bg-[#1B1E23] p-5 sm:p-6 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-md space-y-4 text-left">
              <div className="flex items-center justify-between border-b border-[#E5E7EB]/80 dark:border-[#2F3540] pb-3.5">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
                  <span className="text-xs font-mono font-medium text-[#6B7280] dark:text-[#9CA3AF]">
                    Patient Memory Graph • Alex Vance (38M)
                  </span>
                </div>
                <Badge variant="success">Active Memory Graph</Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <span className="text-xs font-medium text-[#6B7280] dark:text-[#9CA3AF] block mb-1">Longitudinal Documents</span>
                  <p className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">8 Connected Reports</p>
                  <p className="text-[11px] text-[#9CA3AF] mt-0.5">Spans 2019 — 2026</p>
                </div>
                <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <span className="text-xs font-medium text-[#6B7280] dark:text-[#9CA3AF] block mb-1">Active Condition</span>
                  <p className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Type 2 Diabetes</p>
                  <p className="text-[11px] text-[#15803D] dark:text-emerald-400 mt-0.5 tabular-nums">HbA1c: 7.2% ➔ 6.7%</p>
                </div>
                <div className="p-4 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540]">
                  <span className="text-xs font-medium text-[#6B7280] dark:text-[#9CA3AF] block mb-1">Clinical Decision Support</span>
                  <p className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6]">Physician Summary</p>
                  <p className="text-[11px] text-[#9CA3AF] mt-0.5">60-Sec Consultation Digest</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Problem Section */}
      <section id="problem" className="max-w-5xl mx-auto px-6">
        <div className="text-center space-y-2 max-w-2xl mx-auto mb-10">
          <Badge variant="warning">The Clinical Disconnect</Badge>
          <h2 className="text-2xl sm:text-3xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
            Medical records are fragmented and isolated.
          </h2>
          <p className="text-xs sm:text-sm text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
            Patients hold blood panels from one lab, MRI imaging from a hospital, and prescriptions from multiple clinics across years. None of them communicate.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
          <Card className="p-6 space-y-3.5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
            <h3 className="text-sm font-semibold text-[#B91C1C] flex items-center gap-2">
              <span>✕</span> Disconnected Static PDF Files
            </h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
              Files sit isolated in email attachments and folders. Every consultation requires starting from scratch, leading to duplicate testing and lost clinical history.
            </p>
            <div className="space-y-1.5 pt-1 text-xs font-mono text-[#6B7280] dark:text-[#9CA3AF]">
              <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540]">📄 2019_Dengue_Fever.pdf</div>
              <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540]">📄 2021_Cholesterol_Report.pdf</div>
              <div className="p-2.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E] border border-[#E5E7EB] dark:border-[#2F3540]">📄 2023_Diabetes_Prescription.pdf</div>
            </div>
          </Card>

          <Card className="p-6 space-y-3.5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
            <h3 className="text-sm font-semibold text-[#10B981] flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#10B981]" /> ChronaNexus Patient Memory
            </h3>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
              Documents are converted into structured clinical knowledge. ChronaNexus extracts diagnoses, dosages, and lab trends to construct an interconnected memory graph.
            </p>
            <div className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5 text-xs">
              <div className="flex items-center justify-between font-medium text-[#10B981]">
                <span>Patient ➔ Diagnoses ➔ Pharmacotherapy ➔ Lab Trajectory</span>
                <Badge variant="success" className="text-[10px] py-0">Machine Parsed</Badge>
              </div>
              <p className="text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">
                "Patient diagnosed Type 2 Diabetes in 2023, currently managed on Metformin with HbA1c controlled at 6.7%."
              </p>
            </div>
          </Card>
        </div>
      </section>

      {/* Six Core Systems */}
      <section id="features" className="max-w-5xl mx-auto px-6">
        <div className="text-center space-y-2 max-w-2xl mx-auto mb-10">
          <Badge variant="default">Core Architecture</Badge>
          <h2 className="text-2xl sm:text-3xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
            The Six Clinical Engines
          </h2>
          <p className="text-xs sm:text-sm text-[#6B7280] dark:text-[#9CA3AF]">
            Engineered from first principles for high-stakes healthcare documentation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[
            {
              title: 'Document Vault',
              desc: 'Securely store and organize PDFs, imaging, blood panels, and prescriptions with zero-trust encryption.',
              icon: <FolderLock className="w-5 h-5 text-[#10B981]" />,
            },
            {
              title: 'Medical Understanding',
              desc: 'Transforms unstructured scanned documents into verified clinical entities (diagnoses, drugs, dosages, lab values).',
              icon: <Brain className="w-5 h-5 text-[#10B981]" />,
            },
            {
              title: 'Patient Memory Engine',
              desc: 'The central graph storing continuous patient understanding over years, updating automatically with every upload.',
              icon: <Layers className="w-5 h-5 text-[#10B981]" />,
            },
            {
              title: 'Medical Timeline Engine',
              desc: 'Automatically constructs vertical and horizontal timelines of diagnoses, surgeries, and drug transitions.',
              icon: <GitCommit className="w-5 h-5 text-[#10B981]" />,
            },
            {
              title: 'Medical Intelligence Engine',
              desc: 'Natural language search and question-answering strictly grounded in your patient memory with source citations.',
              icon: <Bot className="w-5 h-5 text-[#10B981]" />,
            },
            {
              title: 'Doctor Summary Engine',
              desc: 'Generates a 60-second structured clinical summary for physicians before consultations at the click of a button.',
              icon: <Stethoscope className="w-5 h-5 text-[#10B981]" />,
            },
          ].map((sys, idx) => (
            <Card key={idx} hoverEffect className="p-5 space-y-2.5 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
              <div className="p-2.5 rounded-xl bg-[#F3F1ED] dark:bg-[#23272E] w-fit text-[#10B981]">{sys.icon}</div>
              <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6]">{sys.title}</h3>
              <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] leading-relaxed">{sys.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Architecture Overview */}
      <section id="architecture" className="max-w-5xl mx-auto px-6">
        <Card className="p-6 sm:p-8 space-y-6 border-[#E5E7EB] dark:border-[#2F3540] bg-white dark:bg-[#1B1E23]">
          <div className="text-center space-y-1.5 max-w-xl mx-auto">
            <Badge variant="success">System Pipeline</Badge>
            <h2 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
              Clinical Microservice Data Flow
            </h2>
            <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
              Every document moves through a modular, independently verifiable processing pipeline.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
            {[
              { step: '1. Ingestion', label: 'PDF / Image Upload', icon: <FolderLock className="w-4 h-4 text-[#10B981] mx-auto" /> },
              { step: '2. OCR Layer', label: 'Text Extraction', icon: <Cpu className="w-4 h-4 text-[#4B5563] mx-auto" /> },
              { step: '3. Extraction', label: 'Medical Entities', icon: <Brain className="w-4 h-4 text-[#10B981] mx-auto" /> },
              { step: '4. Memory', label: 'Graph Memory Sync', icon: <Database className="w-4 h-4 text-[#4B5563] mx-auto" /> },
              { step: '5. Timeline', label: 'Event Construction', icon: <GitCommit className="w-4 h-4 text-[#10B981] mx-auto" /> },
              { step: '6. AI Search', label: 'Citations & QA', icon: <Bot className="w-4 h-4 text-[#10B981] mx-auto" /> },
            ].map((st, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB] dark:border-[#2F3540] space-y-1.5">
                {st.icon}
                <span className="text-[11px] font-semibold text-[#1F2937] dark:text-[#F3F4F6] block">{st.step}</span>
                <span className="text-[10px] text-[#6B7280] dark:text-[#9CA3AF]">{st.label}</span>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* CTA Section */}
      <section className="max-w-4xl mx-auto px-6 text-center">
        <div className="bg-white dark:bg-[#1B1E23] p-8 sm:p-10 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-4">
          <div className="w-9 h-9 rounded-xl bg-[#ECFDF5] border border-emerald-200 text-[#10B981] flex items-center justify-center font-bold mx-auto">
            <Activity className="w-4 h-4" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] tracking-tight">
            Take control of your longitudinal health history.
          </h2>
          <p className="text-xs sm:text-sm text-[#6B7280] dark:text-[#9CA3AF] max-w-lg mx-auto leading-relaxed">
            Experience the future of medical intelligence. Private, structured, and instantly actionable.
          </p>
          <div className="flex justify-center pt-2">
            <Button size="lg" onClick={() => navigate('/dashboard')} rightIcon={<ArrowRight className="w-4 h-4" />}>
              Launch Dashboard Demo
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};
