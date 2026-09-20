/**
 * circularGen.ts — Frontend API helpers for Phase 18
 * AI Circular Generation + PDF Download
 * Never exposes LLM_API_KEY — all calls go through the authenticated FastAPI backend.
 */

import { API_BASE_URL } from './api';

// ── Types matching backend schemas ────────────────────────────────────────────

export interface CircularGenerateRequest {
  topic: string;
  department?: string;
  audience?: string;
  effective_date?: string;
  priority?: string;
  additional_instructions?: string;
  category?: string;
}

export interface GeneratedCircularContent {
  title: string;
  subject: string;
  department: string;
  audience: string;
  reference: string;
  date: string;
  effective_date: string;
  body: string;
  instructions: string;
  contact_information: string;
  signatory_name: string;
  signatory_designation: string;
  priority: string;
  category: string;
  is_ai_generated: boolean;
}

export interface CircularPDFRequest {
  content: GeneratedCircularContent;
  institution_name?: string;
}

export interface GenApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// ── AI Generation ─────────────────────────────────────────────────────────────

export async function generateCircularWithAI(
  payload: CircularGenerateRequest,
  token: string | null
): Promise<GenApiResponse<GeneratedCircularContent>> {
  if (!token) {
    return { success: false, error: 'Authentication required. Please log in.' };
  }
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/circulars/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      return { success: false, error: err.detail || `Server error: ${res.status}` };
    }
    const data: GeneratedCircularContent = await res.json();
    return { success: true, data };
  } catch (e: any) {
    return {
      success: false,
      error: e?.message || 'Cannot reach the backend. Please ensure the server is running.',
    };
  }
}

// ── PDF Download ──────────────────────────────────────────────────────────────

export async function downloadCircularPDF(
  payload: CircularPDFRequest,
  token: string | null
): Promise<GenApiResponse<null>> {
  if (!token) {
    return { success: false, error: 'Authentication required. Please log in.' };
  }
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/circulars/generate-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      return { success: false, error: err.detail || `PDF generation failed: ${res.status}` };
    }
    // Trigger browser file download
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const disposition = res.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
    const filename = filenameMatch ? filenameMatch[1] : 'circular.pdf';
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    return { success: true, data: null };
  } catch (e: any) {
    return {
      success: false,
      error: e?.message || 'PDF download failed. Please try again.',
    };
  }
}

// ── Save / Persist Circular Draft ─────────────────────────────────────────────

export interface SaveCircularPayload {
  title: string;
  subject?: string;
  department: string;
  category?: string;
  priority?: string;
  effective_date?: string;
  reference?: string;
  body: string;
  instructions?: string;
  contact_information?: string;
  signatory_name?: string;
  signatory_designation?: string;
  audience?: string;
  target_audience?: string[];
  tags?: string[];
  required_actions?: string[];
  status?: string;
}

export interface SavedCircularResponse {
  id: string;
  ref_no: string;
  title: string;
  department: string;
  category: string;
  status: string;
  priority: string;
  published_date: string;
  effective_date: string;
  version: string;
  author: string;
  signatory: string;
  summary: string;
  body: string;
  target_audience: string[];
  tags: string[];
  required_actions: string[];
  file_attachment?: string;
}

export async function saveCircular(
  payload: SaveCircularPayload | GeneratedCircularContent,
  token: string | null,
): Promise<GenApiResponse<SavedCircularResponse>> {
  if (!token) {
    return { success: false, error: 'Authentication required. Please log in.' };
  }
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/circulars`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      return { success: false, error: err.detail || `Server error: ${res.status}` };
    }
    const data: SavedCircularResponse = await res.json();
    return { success: true, data };
  } catch (e: any) {
    return {
      success: false,
      error: e?.message || 'Cannot reach the backend. Please ensure the server is running.',
    };
  }
}

