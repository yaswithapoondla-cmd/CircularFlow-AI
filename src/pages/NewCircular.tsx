import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, PenLine, ArrowLeft, FileText, Loader2,
  AlertCircle, Lock, UserCheck, ShieldAlert, Eye,
  Download, RefreshCw, CheckCircle2, ChevronRight,
  Building, Users, CalendarDays, Tag, Info, X,
  FileCheck, Zap, Save,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useDatabase } from '../context/DatabaseContext';
import type { CircularCategory, PriorityLevel } from '../types';
import {
  generateCircularWithAI,
  downloadCircularPDF,
  saveCircular,
  type GeneratedCircularContent,
} from '../lib/circularGen';

// ── Types ─────────────────────────────────────────────────────────────────────
type CreationMode = 'ai' | 'manual' | null;

const DEPARTMENTS = [
  'Office of the Registrar',
  'Department of Computer Science & Engineering',
  'Academic Affairs',
  'Finance & Audit',
  'IT & Cyber Security',
  'Human Resources',
  'Executive Office',
  'Student Welfare',
  'Library & Information Services',
  'Operations & Facilities',
];

const PRIORITIES = ['Critical', 'High', 'Medium', 'Low'];
const CATEGORIES = [
  'Policy & Compliance',
  'Academic Affairs',
  'Safety & Security',
  'Financial & Delegation',
  'Operations & Logistics',
  'IT & Data Governance',
  'HR & Workforce',
];

function generateRefNo() {
  return `CIRC-2026-${Math.floor(100 + Math.random() * 900)}`;
}
function todayStr() {
  return new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' });
}
function todayISO() {
  return new Date().toISOString().split('T')[0];
}

// ── Sub-components ────────────────────────────────────────────────────────────

interface FieldProps {
  label: string;
  required?: boolean;
  children: React.ReactNode;
  hint?: string;
}
function Field({ label, required, children, hint }: FieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-slate-300 flex items-center gap-1">
        {label}
        {required && <span className="text-red-400">*</span>}
      </label>
      {children}
      {hint && <p className="text-[11px] text-slate-500">{hint}</p>}
    </div>
  );
}

function inputCls(extra = '') {
  return `w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 focus:border-indigo-500 text-xs text-slate-100 placeholder:text-slate-600 focus:outline-none transition-colors ${extra}`;
}

function selectCls() {
  return `w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 focus:border-indigo-500 text-xs text-slate-100 focus:outline-none transition-colors`;
}

// ── Circular Preview (document-style) ────────────────────────────────────────

function CircularPreview({ c, onClose }: { c: GeneratedCircularContent; onClose?: () => void }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl text-slate-900 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#1a2a6c] to-[#2563eb] px-6 py-4 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/vignan-logo.jpg" alt="Vignan" className="h-12 w-12 object-contain bg-white rounded-lg p-0.5" />
            <div>
              <div className="text-xs font-bold tracking-wider uppercase text-blue-200">Vignan's Foundation for Science, Technology & Research</div>
              <div className="text-[10px] text-blue-300">Deemed to be University | Vadlamudi, Guntur — 522 213</div>
            </div>
          </div>
          {onClose && (
            <button onClick={onClose} className="text-white/60 hover:text-white transition-colors">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
        <div className="mt-3 text-center">
          <div className="text-lg font-black tracking-[0.2em] uppercase">CIRCULAR</div>
          {c.is_ai_generated && (
            <div className="mt-1 inline-block px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-400/50 text-amber-300 text-[9px] font-bold tracking-wider">
              ⚠ AI-GENERATED DRAFT — PENDING APPROVAL
            </div>
          )}
        </div>
      </div>

      {/* Metadata Strip */}
      <div className="grid grid-cols-3 divide-x divide-slate-200 bg-blue-50 border-b border-slate-200">
        {[
          { label: 'Ref No.', val: c.reference },
          { label: 'Date', val: c.date },
          { label: 'Priority', val: c.priority },
        ].map(({ label, val }) => (
          <div key={label} className="px-4 py-2.5">
            <div className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">{label}</div>
            <div className="text-xs font-semibold text-slate-800 mt-0.5">{val}</div>
          </div>
        ))}
      </div>

      {/* Body */}
      <div className="px-6 py-5 space-y-4">
        <div className="flex gap-2 text-xs">
          <span className="font-bold text-slate-700 w-20 shrink-0">To:</span>
          <span className="text-slate-800">{c.audience}</span>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="font-bold text-slate-700 w-20 shrink-0">Department:</span>
          <span className="text-slate-800">{c.department}</span>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="font-bold text-slate-700 w-20 shrink-0">Subject:</span>
          <span className="font-bold text-slate-900">{c.subject}</span>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="font-bold text-slate-700 w-20 shrink-0">Effective:</span>
          <span className="font-semibold text-blue-700">{c.effective_date}</span>
        </div>

        <hr className="border-slate-200 my-2" />

        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Matter</div>
          <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">{c.body}</div>
        </div>

        {c.instructions && (
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">Compliance Instructions</div>
            <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">{c.instructions}</div>
          </div>
        )}

        {c.contact_information && (
          <div>
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">For Queries</div>
            <div className="text-xs text-slate-600 whitespace-pre-wrap">{c.contact_information}</div>
          </div>
        )}

        <div className="mt-6 text-right">
          <div className="text-xs font-bold text-slate-900">{c.signatory_name}</div>
          <div className="text-xs text-slate-500">{c.signatory_designation}</div>
          <div className="text-[10px] text-slate-400 mt-0.5">Vignan's Foundation for Science, Technology & Research</div>
        </div>

        {c.is_ai_generated && (
          <div className="mt-2 p-2 rounded-lg bg-amber-50 border border-amber-200 text-[10px] text-amber-700">
            This document is an AI-generated draft for review only. It has not been officially approved or published.
          </div>
        )}
      </div>
    </div>
  );
}

// ── Editable Form (shared by both modes after generation) ─────────────────────

interface EditFormProps {
  content: GeneratedCircularContent;
  onChange: (updated: GeneratedCircularContent) => void;
}
function EditableCircularForm({ content: c, onChange }: EditFormProps) {
  const update = (key: keyof GeneratedCircularContent, val: string | boolean) =>
    onChange({ ...c, [key]: val });

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Circular Title" required>
          <input className={inputCls()} value={c.title} onChange={e => update('title', e.target.value)} placeholder="Official circular title" />
        </Field>
        <Field label="Subject">
          <input className={inputCls()} value={c.subject} onChange={e => update('subject', e.target.value)} placeholder="Subject line" />
        </Field>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Field label="Reference No.">
          <input className={inputCls('font-mono')} value={c.reference} onChange={e => update('reference', e.target.value)} />
        </Field>
        <Field label="Date of Issue">
          <input className={inputCls()} value={c.date} onChange={e => update('date', e.target.value)} placeholder="DD Month YYYY" />
        </Field>
        <Field label="Effective Date">
          <input className={inputCls()} value={c.effective_date} onChange={e => update('effective_date', e.target.value)} placeholder="DD Month YYYY or YYYY-MM-DD" />
        </Field>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Issuing Department">
          <select className={selectCls()} value={c.department} onChange={e => update('department', e.target.value)}>
            {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </Field>
        <Field label="Target Audience / To">
          <input className={inputCls()} value={c.audience} onChange={e => update('audience', e.target.value)} placeholder="e.g. All CSE Students and Faculty" />
        </Field>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Priority">
          <select className={selectCls()} value={c.priority} onChange={e => update('priority', e.target.value)}>
            {PRIORITIES.map(p => <option key={p}>{p}</option>)}
          </select>
        </Field>
        <Field label="Category">
          <select className={selectCls()} value={c.category} onChange={e => update('category', e.target.value)}>
            {CATEGORIES.map(cat => <option key={cat}>{cat}</option>)}
          </select>
        </Field>
      </div>

      <Field label="Main Matter / Body" required>
        <textarea
          rows={8}
          className={inputCls('font-mono resize-y leading-relaxed')}
          value={c.body}
          onChange={e => update('body', e.target.value)}
          placeholder="Write the main body of the circular..."
        />
      </Field>

      <Field label="Compliance Instructions">
        <textarea
          rows={4}
          className={inputCls('resize-y leading-relaxed')}
          value={c.instructions}
          onChange={e => update('instructions', e.target.value)}
          placeholder="1. Numbered compliance steps..."
        />
      </Field>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Contact Information">
          <textarea
            rows={3}
            className={inputCls('resize-y')}
            value={c.contact_information}
            onChange={e => update('contact_information', e.target.value)}
            placeholder="Name, designation, email, phone"
          />
        </Field>
        <div className="space-y-4">
          <Field label="Signatory Name">
            <input className={inputCls()} value={c.signatory_name} onChange={e => update('signatory_name', e.target.value)} placeholder="Full name of signing authority" />
          </Field>
          <Field label="Signatory Designation">
            <input className={inputCls()} value={c.signatory_designation} onChange={e => update('signatory_designation', e.target.value)} placeholder="e.g. University Registrar" />
          </Field>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export const NewCircular: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser, openLoginModal, token } = useAuth();
  const { isDark } = useTheme();

  // ── RBAC guard ──────────────────────────────────────────────────────────────
  if (!currentUser.canUploadDocuments) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4 animate-in fade-in duration-300">
        <div className="glass-card rounded-3xl p-8 border border-amber-500/30 bg-slate-950/80 backdrop-blur-xl shadow-2xl text-center space-y-6">
          <div className="w-20 h-20 rounded-3xl bg-amber-500/10 border border-amber-500/30 mx-auto flex items-center justify-center text-amber-400 shadow-inner">
            <Lock className="w-10 h-10" />
          </div>
          <div className="space-y-2">
            <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-xs font-bold uppercase tracking-wider border border-amber-500/40">
              Access Restricted • Role: {currentUser.role.toUpperCase()}
            </span>
            <h1 className="text-2xl font-extrabold text-white mt-2">Issuance & Upload Authority Required</h1>
            <p className="text-sm text-slate-300 max-w-md mx-auto leading-relaxed">
              Students have read-only rights. Creating circulars requires{' '}
              <span className="text-indigo-400 font-semibold">Registrar</span> or{' '}
              <span className="text-purple-400 font-semibold">Faculty / HOD</span> credentials.
            </p>
          </div>
          <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-left flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-400 space-y-1">
              <p className="text-slate-200 font-medium">Logged in as: <span className="text-white font-bold">{currentUser.name}</span> ({currentUser.department})</p>
              <p>Switch to an authorized account to draft and issue circulars.</p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button onClick={openLoginModal} className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:scale-105">
              <UserCheck className="w-4 h-4" /> Switch to Registrar / Faculty
            </button>
            <button onClick={() => navigate('/circulars')} className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs transition-colors">
              View Active Directives
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── State ───────────────────────────────────────────────────────────────────
  const [mode, setMode] = useState<CreationMode>(null);
  const [view, setView] = useState<'form' | 'edit' | 'preview'>('form');
  const { addCircular } = useDatabase();

  // AI mode form
  const [aiTopic, setAiTopic] = useState('');
  const [aiDept, setAiDept] = useState('');
  const [aiAudience, setAiAudience] = useState('');
  const [aiEffDate, setAiEffDate] = useState('');
  const [aiPriority, setAiPriority] = useState('High');
  const [aiCategory, setAiCategory] = useState('Policy & Compliance');
  const [aiInstructions, setAiInstructions] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Shared circular content (populated by AI or manual)
  const [circularContent, setCircularContent] = useState<GeneratedCircularContent | null>(null);

  // PDF state
  const [isDownloading, setIsDownloading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [pdfSuccess, setPdfSuccess] = useState(false);

  // Save / Persistence state
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  // ── Save Circular Draft ─────────────────────────────────────────────────────
  const handleSave = async () => {
    if (!circularContent) return;
    if (!circularContent.title.trim()) {
      setSaveError('Please enter a title for the circular.');
      return;
    }
    if (!circularContent.body.trim()) {
      setSaveError('Circular body matter cannot be empty.');
      return;
    }

    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(null);

    const res = await saveCircular(circularContent, token);
    setIsSaving(false);

    if (res.success && res.data) {
      const saved = res.data;
      setSaveSuccess(`Circular ${saved.ref_no} saved successfully as Draft! Redirecting to Approvals...`);

      const validCategories: CircularCategory[] = [
        'Policy & Compliance',
        'Safety & Security',
        'Financial & Delegation',
        'Operations & Logistics',
        'IT & Data Governance',
        'HR & Workforce',
      ];
      const category: CircularCategory = validCategories.includes(saved.category as any)
        ? (saved.category as CircularCategory)
        : 'Policy & Compliance';

      const validPriorities: PriorityLevel[] = ['Critical', 'High', 'Medium', 'Low'];
      const priority: PriorityLevel = validPriorities.includes(saved.priority as any)
        ? (saved.priority as PriorityLevel)
        : 'High';

      // Add to local DatabaseContext so it appears immediately in Approvals
      addCircular({
        id: saved.id,
        refNo: saved.ref_no,
        title: saved.title,
        summary: saved.summary || circularContent.subject || circularContent.title,
        aiExecutiveSummary: saved.summary || circularContent.subject || circularContent.title,
        category,
        status: 'Draft',
        priority,
        issuingAuthority: saved.department || circularContent.department || 'Executive Office',
        signatoryName: saved.signatory || circularContent.signatory_name || currentUser.name,
        signatoryTitle: circularContent.signatory_designation || 'Authorized Signatory',
        effectiveDate: saved.effective_date,
        version: '1.0',
        tags: Array.isArray(saved.tags) && saved.tags.length > 0 ? saved.tags : ['New Directive', saved.department || 'General'],
        affectedAudience: {
          departments: ['All Departments'],
          totalCount: 1200,
          ackCount: 0,
          ackPercentage: 0,
        },
        actionItems: [],
        approvalChain: [
          {
            stage: 1,
            title: 'Originator / HOD Submission',
            approverRole: 'Originator',
            approverName: currentUser.name,
            status: 'Approved',
            timestamp: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            comments: 'Draft authored and submitted for executive authorization.',
          },
          {
            stage: 2,
            title: 'Dean / Registrar Authorization',
            approverRole: 'Registrar',
            approverName: 'Pending Registrar Signature',
            status: 'Pending',
          },
        ],
        departmentBreakdown: [],
        conflictCheckStatus: 'No Conflicts',
        contentMarkdown: saved.body || circularContent.body || '',
        documentUrl: saved.file_attachment || undefined,
      });

      setTimeout(() => {
        navigate('/approvals');
      }, 1500);
    } else {
      setSaveError(res.error || 'Failed to save circular to database.');
    }
  };

  // ── AI Generation ───────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    if (!aiTopic.trim()) { setGenError('Please enter a topic for the circular.'); return; }
    setIsGenerating(true);
    setGenError(null);
    const res = await generateCircularWithAI({
      topic: aiTopic,
      department: aiDept || undefined,
      audience: aiAudience || undefined,
      effective_date: aiEffDate || undefined,
      priority: aiPriority,
      additional_instructions: aiInstructions || undefined,
      category: aiCategory,
    }, token);
    setIsGenerating(false);
    if (res.success && res.data) {
      setCircularContent(res.data);
      setView('edit');
    } else {
      setGenError(res.error || 'Generation failed. Please try again.');
    }
  };

  // Manual mode: start with blank template
  const startManual = () => {
    setCircularContent({
      title: '',
      subject: '',
      department: currentUser.department || 'Office of the Registrar',
      audience: '',
      reference: generateRefNo(),
      date: todayStr(),
      effective_date: '',
      body: '',
      instructions: '',
      contact_information: `${currentUser.name}\n${currentUser.designation}\n${currentUser.email}`,
      signatory_name: currentUser.name,
      signatory_designation: currentUser.designation,
      priority: 'High',
      category: 'Policy & Compliance',
      is_ai_generated: false,
    });
    setMode('manual');
    setView('edit');
  };

  // ── PDF Download ────────────────────────────────────────────────────────────
  const handleDownloadPDF = async () => {
    if (!circularContent) return;
    setIsDownloading(true);
    setPdfError(null);
    setPdfSuccess(false);
    const res = await downloadCircularPDF({ content: circularContent }, token);
    setIsDownloading(false);
    if (res.success) {
      setPdfSuccess(true);
      setTimeout(() => setPdfSuccess(false), 4000);
    } else {
      setPdfError(res.error || 'PDF generation failed.');
    }
  };

  // ── Theme tokens ────────────────────────────────────────────────────────────
  const card = `rounded-2xl border ${isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200 shadow-sm'}`;
  const innerCard = `rounded-xl border ${isDark ? 'bg-slate-800/60 border-slate-700' : 'bg-slate-50 border-slate-200'}`;
  const heading = isDark ? 'text-slate-100' : 'text-slate-900';
  const sub = isDark ? 'text-slate-400' : 'text-slate-500';

  // ── Mode Selector ────────────────────────────────────────────────────────────
  if (mode === null) {
    return (
      <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
        <div>
          <h1 className={`text-2xl font-extrabold tracking-tight ${heading}`}>New Institutional Circular</h1>
          <p className={`text-xs mt-1 ${sub}`}>Author an official circular — use AI assistance or write your own matter.</p>
        </div>

        <div className={`${card} p-8`}>
          <div className="text-center mb-8">
            <div className={`text-sm font-semibold mb-1 ${heading}`}>How would you like to create this circular?</div>
            <div className={`text-xs ${sub}`}>Both modes produce the same professional PDF format.</div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {/* AI Mode Card */}
            <button
              id="btn-ai-mode"
              onClick={() => setMode('ai')}
              className={`group relative p-6 rounded-2xl border-2 text-left transition-all hover:scale-[1.02] ${
                isDark
                  ? 'border-indigo-500/40 bg-indigo-950/30 hover:border-indigo-400 hover:bg-indigo-950/50'
                  : 'border-indigo-200 bg-indigo-50 hover:border-indigo-400 hover:bg-indigo-100'
              }`}
            >
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-4">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div className={`text-base font-bold mb-1.5 ${heading}`}>✨ Generate with AI</div>
              <div className={`text-xs leading-relaxed ${sub}`}>
                Describe the topic and let Cira AI draft a professional circular. You can review, edit, and modify the result before generating the PDF.
              </div>
              <div className="mt-4 flex items-center gap-2">
                <div className="flex items-center gap-1 text-[11px] font-medium text-indigo-400">
                  <Zap className="w-3 h-3" /> AI-assisted
                </div>
                <div className="flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                  <FileCheck className="w-3 h-3" /> Always editable
                </div>
              </div>
              <ChevronRight className={`absolute top-1/2 -translate-y-1/2 right-4 w-5 h-5 transition-transform group-hover:translate-x-1 ${isDark ? 'text-slate-600' : 'text-slate-300'}`} />
            </button>

            {/* Manual Mode Card */}
            <button
              id="btn-manual-mode"
              onClick={startManual}
              className={`group relative p-6 rounded-2xl border-2 text-left transition-all hover:scale-[1.02] ${
                isDark
                  ? 'border-slate-700 bg-slate-800/40 hover:border-slate-500 hover:bg-slate-800/70'
                  : 'border-slate-200 bg-slate-50 hover:border-slate-400 hover:bg-slate-100'
              }`}
            >
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-slate-500 to-slate-700 flex items-center justify-center shadow-lg mb-4">
                <PenLine className="w-6 h-6 text-white" />
              </div>
              <div className={`text-base font-bold mb-1.5 ${heading}`}>✍️ Write Your Own Matter</div>
              <div className={`text-xs leading-relaxed ${sub}`}>
                Directly compose all sections of the circular — title, body, instructions, signatory — with full manual control over every word.
              </div>
              <div className="mt-4 flex items-center gap-2">
                <div className="flex items-center gap-1 text-[11px] font-medium text-slate-400">
                  <PenLine className="w-3 h-3" /> Full control
                </div>
                <div className="flex items-center gap-1 text-[11px] font-medium text-sky-400">
                  <FileText className="w-3 h-3" /> Your exact words
                </div>
              </div>
              <ChevronRight className={`absolute top-1/2 -translate-y-1/2 right-4 w-5 h-5 transition-transform group-hover:translate-x-1 ${isDark ? 'text-slate-600' : 'text-slate-300'}`} />
            </button>
          </div>

          <div className={`mt-6 p-3 rounded-xl flex items-start gap-2.5 ${innerCard}`}>
            <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <p className={`text-[11px] leading-relaxed ${sub}`}>
              AI-generated circulars are always marked as <strong>DRAFT</strong> and require official review and approval before issuance.
              The LLM never invents official policies — it generates professional structure that you must verify.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── AI Mode: Generation Form ─────────────────────────────────────────────────
  if (mode === 'ai' && view === 'form') {
    return (
      <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-300">
        <div className="flex items-center gap-3">
          <button onClick={() => setMode(null)} className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-600'}`}>
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className={`text-xl font-extrabold tracking-tight ${heading}`}>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">✨ AI Circular Generation</span>
            </h1>
            <p className={`text-xs mt-0.5 ${sub}`}>Describe the topic and Cira AI will draft a structured circular for you to review.</p>
          </div>
        </div>

        <div className={`${card} p-6 space-y-6`}>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl overflow-hidden border border-indigo-400/40 shrink-0">
              <img src="/cira-agent.jpg" alt="Cira" className="w-full h-full object-cover" />
            </div>
            <div>
              <div className={`text-sm font-bold ${heading}`}>Cira AI Document Assistant</div>
              <div className={`text-[11px] ${sub}`}>Fill in the details below — Cira will generate a professional draft.</div>
            </div>
          </div>

          <Field label="Topic / Circular Purpose" required hint="Be specific. e.g. 'Revised Attendance Policy for B.Tech CSE Students'">
            <input
              id="ai-topic"
              className={inputCls()}
              value={aiTopic}
              onChange={e => { setAiTopic(e.target.value); setGenError(null); }}
              placeholder="What is this circular about?"
              disabled={isGenerating}
            />
          </Field>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <Field label="Issuing Department">
              <select className={selectCls()} value={aiDept} onChange={e => setAiDept(e.target.value)} disabled={isGenerating}>
                <option value="">— Select Department —</option>
                {DEPARTMENTS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </Field>
            <Field label="Target Audience / Recipients">
              <input
                className={inputCls()}
                value={aiAudience}
                onChange={e => setAiAudience(e.target.value)}
                placeholder="e.g. All B.Tech CSE Students and Faculty"
                disabled={isGenerating}
              />
            </Field>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <Field label="Effective Date">
              <input
                type="date"
                className={inputCls('font-mono')}
                value={aiEffDate}
                onChange={e => setAiEffDate(e.target.value)}
                disabled={isGenerating}
              />
            </Field>
            <Field label="Priority">
              <select className={selectCls()} value={aiPriority} onChange={e => setAiPriority(e.target.value)} disabled={isGenerating}>
                {PRIORITIES.map(p => <option key={p}>{p}</option>)}
              </select>
            </Field>
            <Field label="Category">
              <select className={selectCls()} value={aiCategory} onChange={e => setAiCategory(e.target.value)} disabled={isGenerating}>
                {CATEGORIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </Field>
          </div>

          <Field label="Additional Instructions (Optional)" hint="Mention specific details like minimum attendance %, contact details, or references to include.">
            <textarea
              rows={3}
              className={inputCls('resize-none')}
              value={aiInstructions}
              onChange={e => setAiInstructions(e.target.value)}
              placeholder="Any specific rules, references, or guidance for the AI..."
              disabled={isGenerating}
            />
          </Field>

          {genError && (
            <div className="flex items-start gap-2.5 p-3 rounded-xl bg-red-950/40 border border-red-500/40">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <p className="text-xs text-red-300">{genError}</p>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <button onClick={() => setMode(null)} className={`px-4 py-2.5 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-700'}`}>
              <ArrowLeft className="w-3.5 h-3.5" /> Back
            </button>
            <button
              id="btn-generate-ai"
              onClick={handleGenerate}
              disabled={isGenerating || !aiTopic.trim()}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:scale-105"
            >
              {isGenerating ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
              ) : (
                <><Sparkles className="w-4 h-4" /> Generate Circular</>
              )}
            </button>
          </div>
        </div>

        {/* Progress indicator during generation */}
        {isGenerating && (
          <div className={`${card} p-5`}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl overflow-hidden border border-indigo-400/40 shrink-0 animate-pulse">
                <img src="/cira-agent.jpg" alt="Cira" className="w-full h-full object-cover" />
              </div>
              <div className="flex-1">
                <div className={`text-sm font-semibold ${heading}`}>Cira AI is drafting your circular...</div>
                <div className={`text-xs mt-0.5 ${sub}`}>Generating structured, professional institutional content.</div>
              </div>
            </div>
            <div className="mt-4 space-y-1.5">
              {['Analyzing topic and context', 'Structuring circular format', 'Writing body and instructions', 'Finalizing signatory details'].map((step, i) => (
                <div key={step} className={`flex items-center gap-2 text-xs transition-all duration-500 ${i === 0 ? 'text-indigo-400' : isDark ? 'text-slate-600' : 'text-slate-400'}`}>
                  {i === 0 ? <Loader2 className="w-3 h-3 animate-spin" /> : <div className="w-3 h-3 rounded-full bg-slate-700 border border-slate-600" />}
                  {step}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Edit View (shared by both AI result and manual) ───────────────────────────
  if ((mode === 'ai' || mode === 'manual') && view === 'edit' && circularContent) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in duration-300">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => mode === 'ai' ? setView('form') : setMode(null)}
              className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-600'}`}
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className={`text-xl font-extrabold tracking-tight ${heading}`}>
                {mode === 'ai' ? (
                  <><span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-violet-400">AI-Generated Draft</span> — Review & Edit</>
                ) : '✍️ Write Circular Matter'}
              </h1>
              <p className={`text-xs mt-0.5 ${sub}`}>
                {mode === 'ai'
                  ? 'Review the AI-generated content below. Edit any field before previewing or downloading the PDF.'
                  : 'Fill in all sections of the circular. Preview and download when ready.'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {mode === 'ai' && (
              <button
                onClick={() => setView('form')}
                className={`px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700' : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-200'}`}
              >
                <RefreshCw className="w-3.5 h-3.5" /> Regenerate
              </button>
            )}
            <button
              onClick={() => setView('preview')}
              className={`px-3 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700' : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-200'}`}
            >
              <Eye className="w-3.5 h-3.5" /> Preview
            </button>
          </div>
        </div>

        {/* AI draft badge */}
        {mode === 'ai' && circularContent.is_ai_generated && (
          <div className={`flex items-start gap-2.5 p-3.5 rounded-xl ${isDark ? 'bg-amber-950/30 border border-amber-500/30' : 'bg-amber-50 border border-amber-200'}`}>
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <p className="text-xs text-amber-300">
              <strong>AI-Generated Draft:</strong> This content was generated by Cira AI. Review all sections carefully.
              The AI does not invent official policies — verify all factual claims before issuance.
              This circular will remain a <strong>DRAFT</strong> until officially approved.
            </p>
          </div>
        )}

        {/* Editable Form */}
        <div className={`${card} p-6`}>
          <EditableCircularForm content={circularContent} onChange={setCircularContent} />
        </div>

        {/* PDF errors/success */}
        {pdfError && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-red-950/40 border border-red-500/40">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-xs text-red-300">{pdfError}</p>
          </div>
        )}
        {pdfSuccess && (
          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <p className="text-xs text-emerald-300 font-semibold">PDF downloaded successfully!</p>
          </div>
        )}

        {/* Save errors/success */}
        {saveError && (
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-950/40 border border-red-500/40">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-xs text-red-300">{saveError}</p>
          </div>
        )}
        {saveSuccess && (
          <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 animate-pulse">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <p className="text-xs text-emerald-300 font-semibold">{saveSuccess}</p>
          </div>
        )}

        {/* Action Bar */}
        <div className={`${card} p-4 flex flex-wrap items-center justify-between gap-3`}>
          <div className={`text-xs ${sub}`}>
            {mode === 'ai' ? 'Edit the content above, then save as draft or download PDF.' : 'Complete all fields, then save as draft or download PDF.'}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setView('preview')}
              className={`px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${isDark ? 'bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600' : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-200'}`}
            >
              <Eye className="w-4 h-4" /> Preview Circular
            </button>
            <button
              id="btn-generate-pdf"
              onClick={handleDownloadPDF}
              disabled={isDownloading || !circularContent.title.trim() || !circularContent.body.trim()}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold flex items-center gap-2 transition-colors"
            >
              {isDownloading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> PDF...</>
              ) : (
                <><Download className="w-4 h-4" /> Download PDF</>
              )}
            </button>
            <button
              id="btn-save-circular"
              onClick={handleSave}
              disabled={isSaving || !circularContent.title.trim() || !circularContent.body.trim()}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:scale-105"
            >
              {isSaving ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Saving Draft...</>
              ) : (
                <><Save className="w-4 h-4" /> Save as Draft &amp; Submit</>
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Preview View ─────────────────────────────────────────────────────────────
  if (view === 'preview' && circularContent) {
    return (
      <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in duration-300">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => setView('edit')} className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-600'}`}>
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <h1 className={`text-xl font-extrabold tracking-tight ${heading}`}>Circular Preview</h1>
              <p className={`text-xs mt-0.5 ${sub}`}>This is how the circular will appear in the official PDF.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setView('edit')} className={`px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700' : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-200'}`}>
              <PenLine className="w-3.5 h-3.5" /> Edit
            </button>
            <button
              id="btn-download-pdf"
              onClick={handleDownloadPDF}
              disabled={isDownloading}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-semibold flex items-center gap-2 transition-colors"
            >
              {isDownloading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> PDF...</>
              ) : (
                <><Download className="w-4 h-4" /> Download PDF</>
              )}
            </button>
            <button
              id="btn-save-preview"
              onClick={handleSave}
              disabled={isSaving || !circularContent.title.trim() || !circularContent.body.trim()}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:scale-105"
            >
              {isSaving ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Saving Draft...</>
              ) : (
                <><Save className="w-4 h-4" /> Save as Draft &amp; Submit</>
              )}
            </button>
          </div>
        </div>

        {saveError && (
          <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-950/40 border border-red-500/40">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-xs text-red-300">{saveError}</p>
          </div>
        )}
        {saveSuccess && (
          <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 animate-pulse">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <p className="text-xs text-emerald-300 font-semibold">{saveSuccess}</p>
          </div>
        )}

        {pdfError && (
          <div className="flex items-start gap-2.5 p-3 rounded-xl bg-red-950/40 border border-red-500/40">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <p className="text-xs text-red-300">{pdfError}</p>
          </div>
        )}
        {pdfSuccess && (
          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <p className="text-xs text-emerald-300 font-semibold">PDF downloaded successfully!</p>
          </div>
        )}

        <CircularPreview c={circularContent} />
      </div>
    );
  }

  return null;
};

export default NewCircular;
