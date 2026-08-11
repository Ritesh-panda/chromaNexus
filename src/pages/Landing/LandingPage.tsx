import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Brain,
  GitCommit,
  Bot,
  FileCheck,
  FolderLock,
  Stethoscope,
  Activity,
  CheckCircle2,
  Lock,
  Layers,
  Database,
  Cpu
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="space-y-24 pb-20">
      {/* Hero Section */}
      <section className="relative pt-16 pb-12 px-6 hero-gradient overflow-hidden">
        <div className="max-w-7xl mx-auto text-center space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card text-xs font-bold text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/60 shadow-lg"
          >
            <Sparkles className="w-4 h-4 text-emerald-500 animate-spin" />
            <span>AI-Powered Longitudinal Medical Intelligence Platform</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 max-w-5xl mx-auto leading-[1.1]"
          >
            From Scattered Medical PDFs to a{' '}
            <span className="bg-gradient-to-r from-blue-600 via-indigo-500 to-emerald-500 bg-clip-text text-transparent">
              Continuous Patient Memory.
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-base sm:text-xl text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed"
          >
            ChronaNexus isn’t just a document storage tool. It understands clinical records, extracts structured medical knowledge, connects events across time, and enables natural language interaction with your complete health history.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-wrap items-center justify-center gap-4 pt-4"
          >
            <Button
              variant="primary"
              size="lg"
              onClick={() => navigate('/dashboard')}
              rightIcon={<ArrowRight className="w-5 h-5" />}
            >
              Explore Live Platform
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => navigate('/signup')}
              leftIcon={<ShieldCheck className="w-5 h-5 text-emerald-500" />}
            >
              Create Free Patient Memory
            </Button>
          </motion.div>

          {/* Interactive UI Mockup Hero Widget */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="pt-10 max-w-5xl mx-auto"
          >
            <div className="glass-card p-4 sm:p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl space-y-4 text-left">
              <div className="flex items-center justify-between border-b border-slate-200/60 dark:border-slate-800/60 pb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full bg-rose-500" />
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span className="text-xs font-mono font-semibold text-slate-400 pl-2">
                    ChronaNexus Patient Memory Engine • Alex Vance (38M)
                  </span>
                </div>
                <Badge variant="success">Active Memory Graph</Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-2xl bg-blue-50/50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40">
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-400 block mb-1">Longitudinal Records</span>
                  <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">8 Connected Reports</p>
                  <p className="text-[11px] text-slate-500 mt-1">Span 2019 — 2026</p>
                </div>
                <div className="p-4 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/40">
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 block mb-1">Active Conditions</span>
                  <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">Type 2 Diabetes</p>
                  <p className="text-[11px] text-slate-500 mt-1">HbA1c Improved: 7.2% ➔ 6.7%</p>
                </div>
                <div className="p-4 rounded-2xl bg-purple-50/50 dark:bg-purple-950/30 border border-purple-100 dark:border-purple-900/40">
                  <span className="text-xs font-bold text-purple-600 dark:text-purple-400 block mb-1">AI Decision Support</span>
                  <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">One-Click Summary</p>
                  <p className="text-[11px] text-slate-500 mt-1">60-Sec Physician Overview</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Problem Section */}
      <section id="problem" className="max-w-7xl mx-auto px-6">
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-16">
          <Badge variant="warning">The Healthcare Problem</Badge>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-slate-100">
            Medical Records are Broken & Isolated.
          </h2>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
            A patient typically holds blood tests from one clinic, MRI scans from another hospital, and prescriptions from multiple doctors across years. None of them communicate.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          {/* Yesterday: Disconnected PDFs */}
          <Card className="p-8 space-y-4 border-rose-200/60 dark:border-rose-900/30 bg-rose-50/20 dark:bg-rose-950/10">
            <h3 className="text-xl font-bold text-rose-600 dark:text-rose-400 flex items-center gap-2">
              <span>❌</span> Disconnected PDF Files
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Files sit isolated in email attachments and physical folders. Every new doctor visit requires starting from scratch, leading to duplicate testing and missed clinical context.
            </p>
            <div className="space-y-2 pt-2 text-xs font-mono text-slate-500">
              <div className="p-3 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">📄 2019_Dengue_Fever.pdf</div>
              <div className="p-3 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">📄 2021_Cholesterol_Report.pdf</div>
              <div className="p-3 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800">📄 2023_Diabetes_Prescription.pdf</div>
            </div>
          </Card>

          {/* Today: ChronaNexus Memory */}
          <Card className="p-8 space-y-4 border-emerald-200/60 dark:border-emerald-900/30 bg-emerald-50/20 dark:bg-emerald-950/10">
            <h3 className="text-xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-500" /> ChronaNexus Patient Memory
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Documents are processed into structured clinical knowledge. ChronaNexus extracts diseases, dosages, and lab trends to build an interconnected longitudinal memory graph.
            </p>
            <div className="p-4 rounded-xl bg-white/80 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between font-bold text-blue-600 dark:text-blue-400">
                <span>Patient ➔ Diseases ➔ Medications ➔ Lab Trends</span>
                <Badge variant="success font-mono">Machine Understandable</Badge>
              </div>
              <p className="text-slate-500 dark:text-slate-400">
                "Patient took Cholecalciferol in 2020, diagnosed Type 2 Diabetes in 2023, now controlled on Metformin with HbA1c 6.7%."
              </p>
            </div>
          </Card>
        </div>
      </section>

      {/* 6 Core Systems */}
      <section id="features" className="max-w-7xl mx-auto px-6">
        <div className="text-center space-y-4 max-w-3xl mx-auto mb-16">
          <Badge variant="default">Platform Capabilities</Badge>
          <h2 className="text-3xl sm:text-5xl font-extrabold text-slate-900 dark:text-slate-100">
            The Six Core Intelligence Engines
          </h2>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400">
            Built from the ground up to handle high-stakes clinical documentation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              title: 'Document Vault',
              desc: 'Securely store and organize PDFs, DICOM imaging, blood panels, and prescriptions with zero-trust encryption.',
              icon: <FolderLock className="w-6 h-6 text-blue-500" />,
            },
            {
              title: 'Medical Understanding Engine',
              desc: 'Transforms unstructured scanned documents into verified clinical entities (diseases, drugs, dosages, lab values).',
              icon: <Brain className="w-6 h-6 text-emerald-500" />,
            },
            {
              title: 'Patient Memory Engine',
              desc: 'The central graph storing continuous patient understanding over years, updating automatically with every upload.',
              icon: <Layers className="w-6 h-6 text-purple-500" />,
            },
            {
              title: 'Medical Timeline Engine',
              desc: 'Automatically constructs vertical & horizontal timelines of diagnoses, surgeries, and drug transitions.',
              icon: <GitCommit className="w-6 h-6 text-amber-500" />,
            },
            {
              title: 'Medical Intelligence Engine',
              desc: 'Natural language search and question-answering strictly grounded in your patient memory with source citations.',
              icon: <Bot className="w-6 h-6 text-cyan-500" />,
            },
            {
              title: 'Doctor Summary Engine',
              desc: 'Generates a 60-second structured clinical summary for physicians before consultations at the click of a button.',
              icon: <Stethoscope className="w-6 h-6 text-rose-500" />,
            },
          ].map((sys, idx) => (
            <Card key={idx} hoverEffect className="p-6 space-y-3 border-slate-200 dark:border-slate-800">
              <div className="p-3 rounded-2xl bg-slate-100 dark:bg-slate-800/80 w-fit">{sys.icon}</div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">{sys.title}</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{sys.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Architecture Overview */}
      <section id="architecture" className="max-w-7xl mx-auto px-6">
        <Card className="p-8 md:p-12 space-y-8 hero-gradient border-slate-200 dark:border-slate-800">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <Badge variant="success">System Pipeline</Badge>
            <h2 className="text-3xl font-extrabold text-slate-900 dark:text-slate-100">
              Enterprise Microservice Data Flow
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300">
              Every document moves through a modular, independently deployable processing pipeline.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
            {[
              { step: '1. Ingestion', label: 'PDF / Image Upload', icon: <FolderLock className="w-5 h-5 text-blue-500 mx-auto" /> },
              { step: '2. OCR Layer', label: 'Text Extraction', icon: <Cpu className="w-5 h-5 text-purple-500 mx-auto" /> },
              { step: '3. Extraction', label: 'Medical Entities', icon: <Brain className="w-5 h-5 text-emerald-500 mx-auto" /> },
              { step: '4. Memory', label: 'Graph Memory Sync', icon: <Database className="w-5 h-5 text-amber-500 mx-auto" /> },
              { step: '5. Timeline', label: 'Event Construction', icon: <GitCommit className="w-5 h-5 text-rose-500 mx-auto" /> },
              { step: '6. AI Search', label: 'Citations & QA', icon: <Bot className="w-5 h-5 text-cyan-500 mx-auto" /> },
            ].map((st, i) => (
              <div key={i} className="p-4 rounded-2xl glass-card border border-slate-200/80 dark:border-slate-800/80 space-y-2">
                {st.icon}
                <span className="text-[11px] font-bold text-slate-900 dark:text-slate-100 block">{st.step}</span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">{st.label}</span>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* CTA Section */}
      <section className="max-w-5xl mx-auto px-6 text-center">
        <div className="glass-card p-12 rounded-3xl border border-blue-500/20 dark:border-blue-500/30 hero-gradient space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-slate-100">
            Take Control of Your Medical History Today.
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300 max-w-xl mx-auto">
            Experience the future of longitudinal medical intelligence. Private, structured, and instant.
          </p>
          <div className="flex justify-center gap-4 pt-2">
            <Button size="lg" onClick={() => navigate('/dashboard')} rightIcon={<ArrowRight className="w-5 h-5" />}>
              Launch Dashboard Demo
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};
