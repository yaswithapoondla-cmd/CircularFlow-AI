import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth, type UserRole, AUTH_CREDENTIALS } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
  ShieldCheck,
  GraduationCap,
  BookOpen,
  Lock,
  Mail,
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  AlertCircle,
  Sun,
  Moon,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export const Login: React.FC = () => {
  const { login, isAuthenticated, isLoading: authLoading, currentUser, currentRole } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const [identifier, setIdentifier] = useState<string>('registrar@vignan.ac.in');
  const [password, setPassword] = useState<string>('registrar@123');
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedDemoRole, setSelectedDemoRole] = useState<UserRole>('Registrar');

  // Redirection destination: redirect to authenticated Landing/Home page (/)
  const destination = '/';

  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, authLoading, destination, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !password.trim()) {
      setErrorMessage('Please enter your institutional email/username and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    const result = await login(identifier, password);
    setIsLoading(false);

    if (result.success) {
      navigate(destination, { replace: true });
    } else {
      setErrorMessage(result.error || 'Invalid credentials. Please verify your email and password.');
    }
  };

  const handleSelectDemoUser = (role: UserRole) => {
    setSelectedDemoRole(role);
    const creds = AUTH_CREDENTIALS[role];
    setIdentifier(creds.email);
    setPassword(creds.password);
    setErrorMessage(null);
  };

  return (
    <div
      className={`min-h-screen flex flex-col justify-between transition-colors duration-300 relative overflow-x-hidden ${
        isDark ? 'bg-slate-950 text-slate-100' : 'bg-[#f4f7fc] text-slate-900'
      }`}
    >
      {/* Background Decorative Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-indigo-500/10 via-blue-500/5 to-transparent blur-3xl pointer-events-none -z-10" />

      {/* Header with Vignan Branding & Theme Toggle */}
      <header className={`w-full max-w-6xl mx-auto px-6 py-5 flex items-center justify-between`}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-400 p-0.5 shadow-lg shadow-indigo-500/20 shrink-0">
            <div className={`w-full h-full rounded-[10px] flex items-center justify-center p-0.5 ${
              isDark ? 'bg-slate-950' : 'bg-white'
            }`}>
              <img
                src="/cse-shield-logo.jpg"
                alt="Vignan CSE"
                className="w-full h-full object-contain rounded-md"
              />
            </div>
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-sm tracking-tight flex items-center gap-1.5 leading-tight">
              CircularFlow <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-500 border border-indigo-500/30">AI</span>
            </span>
            <span className={`text-[10px] font-semibold tracking-wider uppercase font-mono ${
              isDark ? 'text-blue-400' : 'text-blue-600'
            }`}>
              Vignan's University
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className={`p-2 rounded-xl border transition-all ${
              isDark ? 'bg-slate-900 border-slate-800 text-slate-300 hover:text-white' : 'bg-white border-slate-200 text-slate-700 hover:text-slate-900 shadow-xs'
            }`}
            title="Toggle theme"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
          </button>
        </div>
      </header>

      {/* Main Login Card Section */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md">
          {/* Card Container */}
          <div
            className={`rounded-2xl border shadow-xl p-6 sm:p-8 backdrop-blur-xl transition-all ${
              isDark
                ? 'bg-slate-900/90 border-slate-800 shadow-indigo-950/40'
                : 'bg-white border-slate-200 shadow-indigo-100/50'
            }`}
          >
            {/* Institution Badge & Title */}
            <div className="text-center mb-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium border mb-3 bg-indigo-500/10 text-indigo-500 border-indigo-500/20">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Institutional Governance OS</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight">Sign In to CircularFlow</h1>
              <p className={`text-xs mt-1.5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                Enter your Vignan university credentials to access directives and AI governance tools.
              </p>
            </div>

            {/* Currently Logged In Session Notice */}
            {isAuthenticated && (
              <div className="mb-5 p-3.5 rounded-xl border flex items-center justify-between gap-3 bg-indigo-500/10 border-indigo-500/30 text-indigo-400 text-xs animate-in fade-in duration-200">
                <div className="flex items-center gap-2 overflow-hidden">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="truncate">Active: <strong>{currentUser.name}</strong> ({currentRole})</span>
                </div>
                <Link
                  to="/dashboard"
                  className="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[11px] shrink-0 transition-all"
                >
                  Dashboard →
                </Link>
              </div>
            )}

            {/* Error Message Alert */}
            {errorMessage && (
              <div className="mb-5 p-3.5 rounded-xl border flex items-start gap-3 bg-rose-500/10 border-rose-500/30 text-rose-500 text-xs animate-in fade-in duration-200">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <span className="font-semibold block">Authentication Failed</span>
                  <span>{errorMessage}</span>
                </div>
              </div>
            )}

            {/* Quick Demo Role Selector */}
            <div className="mb-6">
              <label className={`block text-[11px] font-mono uppercase tracking-wider mb-2 font-semibold ${
                isDark ? 'text-slate-400' : 'text-slate-600'
              }`}>
                Quick Demo Accounts (1-Click Fill)
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { role: 'Registrar' as UserRole, label: 'Registrar', icon: ShieldCheck, color: 'text-emerald-500' },
                  { role: 'Faculty' as UserRole, label: 'Faculty', icon: BookOpen, color: 'text-indigo-500' },
                  { role: 'Student' as UserRole, label: 'Student', icon: GraduationCap, color: 'text-amber-500' },
                ].map((item) => {
                  const Icon = item.icon;
                  const isSelected = selectedDemoRole === item.role;
                  return (
                    <button
                      key={item.role}
                      type="button"
                      onClick={() => handleSelectDemoUser(item.role)}
                      className={`py-2 px-2.5 rounded-xl border text-xs font-medium flex flex-col items-center gap-1 transition-all ${
                        isSelected
                          ? (isDark
                              ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-sm'
                              : 'bg-indigo-50 border-indigo-400 text-indigo-900 shadow-xs')
                          : (isDark
                              ? 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                              : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100 hover:border-slate-300')
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${item.color}`} />
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email / Identifier Field */}
              <div>
                <label
                  htmlFor="identifier"
                  className={`block text-xs font-medium mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}
                >
                  Institutional Email or Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    id="identifier"
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="name@vignan.ac.in or role alias"
                    className={`w-full pl-9 pr-3 py-2.5 rounded-xl text-xs border transition-colors outline-none focus:ring-2 focus:ring-indigo-500/30 ${
                      isDark
                        ? 'bg-slate-950 border-slate-800 text-slate-100 placeholder-slate-500 focus:border-indigo-500'
                        : 'bg-slate-50 border-slate-200 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:bg-white'
                    }`}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="password"
                    className={`block text-xs font-medium ${isDark ? 'text-slate-300' : 'text-slate-700'}`}
                  >
                    Password
                  </label>
                  <span className={`text-[10px] font-mono ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                    Hint: {AUTH_CREDENTIALS[selectedDemoRole].hint}
                  </span>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter account password"
                    className={`w-full pl-9 pr-10 py-2.5 rounded-xl text-xs border transition-colors outline-none focus:ring-2 focus:ring-indigo-500/30 ${
                      isDark
                        ? 'bg-slate-950 border-slate-800 text-slate-100 placeholder-slate-500 focus:border-indigo-500'
                        : 'bg-slate-50 border-slate-200 text-slate-900 placeholder-slate-400 focus:border-indigo-500 focus:bg-white'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 px-4 rounded-xl font-medium text-xs text-white bg-gradient-to-r from-blue-600 via-indigo-600 to-indigo-700 hover:from-blue-500 hover:to-indigo-600 active:scale-[0.99] transition-all shadow-md shadow-indigo-500/25 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Authenticating with PostgreSQL...</span>
                  </>
                ) : (
                  <>
                    <span>Authenticate & Access OS</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Role Permissions Preview Box */}
            <div className={`mt-6 pt-5 border-t text-[11px] ${
              isDark ? 'border-slate-800 text-slate-400' : 'border-slate-100 text-slate-600'
            }`}>
              <div className="flex items-center gap-2 mb-2 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-500" />
                <span>Selected Role Scope: <strong className={isDark ? 'text-slate-200' : 'text-slate-800'}>{selectedDemoRole}</strong></span>
              </div>
              <ul className="space-y-1 text-[10px] font-mono">
                {selectedDemoRole === 'Registrar' && (
                  <>
                    <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3 text-emerald-500" /> Full registry authorship & publishing</li>
                    <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3 text-emerald-500" /> Executive 3-stage approvals & broadcast nudges</li>
                  </>
                )}
                {selectedDemoRole === 'Faculty' && (
                  <>
                    <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3 text-indigo-500" /> Departmental review & action assignment</li>
                    <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3 text-indigo-500" /> Policy acknowledgements & Cira Copilot</li>
                  </>
                )}
                {selectedDemoRole === 'Student' && (
                  <>
                    <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3 text-amber-500" /> Policy view & digital signature receipt</li>
                    <li className="flex items-center gap-1.5"><CheckCircle2 className="w-3 h-3 text-amber-500" /> Cira AI inquiries & personal deadlines</li>
                  </>
                )}
              </ul>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className={`py-4 text-center text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
        <p>Vignan's Foundation for Science, Technology & Research · CircularFlow AI Governance OS v2.4</p>
      </footer>
    </div>
  );
};
