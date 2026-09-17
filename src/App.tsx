import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { DatabaseProvider } from './context/DatabaseContext';
import { LoginModal } from './components/auth/LoginModal';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Layout } from './components/layout/Layout';
import { AgenticHome } from './pages/AgenticHome';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { CircularsList } from './pages/CircularsList';
import { CircularDetail } from './pages/CircularDetail';
import { NewCircular } from './pages/NewCircular';
import { Approvals } from './pages/Approvals';
import { Distribution } from './pages/Distribution';
import { ActionItems } from './pages/ActionItems';
import { Archive } from './pages/Archive';
import { Analytics } from './pages/Analytics';
import { Assistant } from './pages/Assistant';

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <DatabaseProvider>
          <BrowserRouter>
            <LoginModal />
            <Routes>
              {/* ── Original Branded Home / Showcase Page ──────────────── */}
              <Route path="/" element={<AgenticHome />} />

              {/* ── Public Authentication Page ─────────────────────────── */}
              <Route path="/login" element={<Login />} />

              {/* ── Protected Governance OS Routes ─────────────────────── */}
              <Route
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                {/* Main Governance OS Dashboard */}
                <Route path="dashboard" element={<Dashboard />} />

                {/* AI Assistant (Cira) */}
                <Route path="assistant" element={<Assistant />} />

                {/* Governance Records & Circular Workflow */}
                <Route path="circulars" element={<CircularsList />} />
                <Route path="circulars/new" element={<NewCircular />} />
                <Route path="circulars/:id" element={<CircularDetail />} />

                {/* Approvals & Verification */}
                <Route path="approvals" element={<Approvals />} />
                <Route path="verification" element={<Approvals />} />

                {/* Distribution & Institutional Services */}
                <Route path="distribution" element={<Distribution />} />
                <Route path="services" element={<Distribution />} />

                {/* Action Items & Application Tracking */}
                <Route path="actions" element={<ActionItems />} />
                <Route path="application-tracking" element={<ActionItems />} />

                {/* Archive, Lineage, Audit Logs & Flow Visualizer */}
                <Route path="archive" element={<Archive />} />
                <Route path="audit-logs" element={<Archive />} />
                <Route path="flow-visualizer" element={<Archive />} />

                {/* Compliance Analytics & Schema Mapping */}
                <Route path="analytics" element={<Analytics />} />
                <Route path="schema-mapping" element={<Analytics />} />

                {/* Knowledge Base */}
                <Route path="knowledge-base" element={<CircularsList />} />

                {/* Agentic Showcase view */}
                <Route path="showcase" element={<AgenticHome />} />
              </Route>

              {/* Fallback to Home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </DatabaseProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
