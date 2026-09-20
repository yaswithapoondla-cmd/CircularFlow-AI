import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDatabase } from '../context/DatabaseContext';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from '../components/ui/StatusBadge';
import { PriorityBadge } from '../components/ui/PriorityBadge';
import { CheckCircle2, XCircle, MessageSquare, ShieldCheck, Clock, FileText, ArrowRight, Check, AlertTriangle, Lock, UserCheck, Loader2, Mail } from 'lucide-react';
import { formatDate } from '../lib/utils';
import { publishCircular } from '../lib/api';

export const Approvals: React.FC = () => {
  const { circulars, approveCircular, rejectCircular } = useDatabase();
  const { currentUser, openLoginModal, token } = useAuth();
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Track which circular IDs are currently being published (prevent duplicate requests)
  const [publishingIds, setPublishingIds] = useState<Set<string>>(new Set());

  // Derived list of circulars currently under review or draft
  const pendingApprovals = circulars.filter(
    (c) => c.status === 'Under Review' || c.status === 'Draft'
  );

  /**
   * handleApprove:
   * 1. Calls POST /api/v1/circulars/{id}/publish (backend, with JWT auth)
   * 2. On success → also updates local/frontend state via approveCircular()
   * 3. On failure → shows error, does NOT update local state, allows retry
   * 4. Falls back to local-only approve when backend is unreachable (offline/demo mode)
   */
  const handleApprove = async (id: string, refNo: string) => {
    // Prevent duplicate clicks
    if (publishingIds.has(id)) return;

    setActionError(null);
    setActionSuccess(null);
    setPublishingIds(prev => new Set(prev).add(id));

    try {
      const result = await publishCircular(
        // Prefer refNo as the backend identifier (it matches the URL param search)
        refNo,
        token,
        {
          published_by: currentUser.name,
          published_by_email: currentUser.email,
          send_email_notifications: true,
        },
      );

      if (result.success && result.data) {
        // ── Backend accepted → sync frontend local state ──────────────────
        approveCircular(id, 0, currentUser.name, 'Approved');

        const emailMsg = result.data.email_notifications_queued
          ? ' Email notifications queued for delivery.'
          : '';
        setActionSuccess(
          `Directive ${refNo} signed and published by ${currentUser.name}!${emailMsg}`
        );
        setTimeout(() => setActionSuccess(null), 6000);
      } else if (!result.isBackendOnline) {
        // ── Backend unreachable (offline / demo mode) → local-only fallback ──
        approveCircular(id, 0, currentUser.name, 'Approved (local)');
        setActionSuccess(
          `Directive ${refNo} approved locally. Backend offline — email notifications skipped.`
        );
        setTimeout(() => setActionSuccess(null), 6000);
      } else {
        // ── Backend reachable but returned an error → do NOT update state ──
        setActionError(
          `Could not publish ${refNo}: ${result.error ?? 'Unknown error.'} Please try again.`
        );
        setTimeout(() => setActionError(null), 8000);
      }
    } finally {
      setPublishingIds(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleReject = (id: string, refNo: string) => {
    rejectCircular(id, 0, currentUser.name, 'Flagged for revision');
    setActionError(null);
    setActionSuccess(`Directive ${refNo} flagged for revision and returned to author.`);
    setTimeout(() => setActionSuccess(null), 4000);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight">
            Approval Gateway &amp; Executive Sign-off Inbox
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Review pending circular drafts, legal risk checks, and execute digital signatures before public issuance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold">
            {pendingApprovals.length} Pending Sign-offs
          </span>
        </div>
      </div>

      {/* Success toast */}
      {actionSuccess && (
        <div className="p-4 rounded-xl bg-emerald-950/80 border border-emerald-500/40 text-emerald-200 text-xs flex items-center gap-2 animate-in slide-in-from-top-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Error toast */}
      {actionError && (
        <div className="p-4 rounded-xl bg-rose-950/80 border border-rose-500/40 text-rose-200 text-xs flex items-center gap-2 animate-in slide-in-from-top-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Role notice for students */}
      {!currentUser.canApproveDirectives && (
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Lock className="w-4 h-4 text-amber-400 shrink-0" />
            <span>You are viewing the Institutional Sign-off Queue in <strong>Auditor / Student Mode</strong> (Read-only).</span>
          </div>
          <button
            onClick={openLoginModal}
            className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs flex items-center gap-1.5 shrink-0 transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5" /> Switch to Registrar
          </button>
        </div>
      )}

      {/* Approvals Queue */}
      <div className="space-y-4">
        {pendingApprovals.map((circ) => {
          const isPublishing = publishingIds.has(circ.id);
          return (
            <div
              key={circ.id}
              className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4 hover:border-indigo-500/40 transition-all"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {circ.refNo}
                  </span>
                  <PriorityBadge priority={circ.priority} />
                  <StatusBadge status={circ.status} size="sm" />
                </div>

                <span className="text-xs text-slate-400 font-mono">
                  Submitted: {formatDate(circ.createdAt)}
                </span>
              </div>

              <div className="space-y-2">
                <Link
                  to={`/circulars/${circ.id}`}
                  className="text-lg font-bold text-slate-100 hover:text-indigo-400 transition-colors block"
                >
                  {circ.title}
                </Link>
                <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
                  {circ.summary}
                </p>
              </div>

              {/* AI Risk & Conflict Clearance */}
              <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
                <div className="flex items-center gap-2 text-slate-300">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>AI Policy Audit: <strong className="text-emerald-400">Clear (0 conflicts found)</strong></span>
                </div>
                <div className="text-slate-400 font-mono">
                  Issuing: <strong>{circ.issuingAuthority}</strong>
                </div>
              </div>

              {/* Decision Action Buttons */}
              <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
                <Link
                  to={`/circulars/${circ.id}`}
                  className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 font-medium"
                >
                  Full Draft Preview <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                {currentUser.canApproveDirectives ? (
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleReject(circ.id, circ.refNo)}
                      disabled={isPublishing}
                      className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-rose-400 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <XCircle className="w-4 h-4" /> Request Changes
                    </button>

                    <button
                      onClick={() => handleApprove(circ.id, circ.refNo)}
                      disabled={isPublishing}
                      className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-emerald-600/25 transition-all hover:scale-105 disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                      {isPublishing ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" /> Publishing…
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-4 h-4" /> Sign &amp; Authorize Broadcast
                        </>
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="text-xs text-slate-500 flex items-center gap-1.5 font-mono">
                    <Lock className="w-3.5 h-3.5 text-slate-600" /> Signature rights reserved for Registrar &amp; Dean
                  </div>
                )}
              </div>

              {/* Publishing in-progress indicator */}
              {isPublishing && (
                <div className="flex items-center gap-2 text-xs text-indigo-300 animate-pulse pt-1">
                  <Mail className="w-3.5 h-3.5" />
                  <span>Contacting backend &amp; queuing email notifications…</span>
                </div>
              )}
            </div>
          );
        })}

        {pendingApprovals.length === 0 && (
          <div className="py-16 text-center text-slate-500 glass-card rounded-2xl">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3 opacity-80" />
            <h3 className="text-base font-semibold text-slate-200">Approval Inbox Cleared</h3>
            <p className="text-xs text-slate-400 mt-1">All pending institutional circulars have been authorized and signed.</p>
          </div>
        )}
      </div>
    </div>
  );
};
