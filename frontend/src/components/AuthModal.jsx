import { useState, useEffect, useRef } from 'react';
import { X, Mail, Lock, User as UserIcon, Eye, EyeOff, AlertCircle, CheckCircle, Loader2, Briefcase, ArrowLeft } from 'lucide-react';
import { loginUser, registerUser, googleAuthUser, requestEmailVerification, requestPasswordReset } from '../api/client';

export default function AuthModal({ isOpen, onClose, onSuccess, initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode); // 'login' | 'register' | 'verify_pending' | 'forgot_password' | 'reset_sent'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [infoMessage, setInfoMessage] = useState('');
  const [gsiButtonRendered, setGsiButtonRendered] = useState(false);

  const googleBtnRef = useRef(null);

  // Read Google Client ID with dynamic backend fallback
  const [googleClientId, setGoogleClientId] = useState(import.meta.env.VITE_GOOGLE_CLIENT_ID || '');

  useEffect(() => {
    if (!googleClientId) {
      fetch('/api/auth/config')
        .then((res) => res.json())
        .then((data) => {
          if (data?.google_client_id) {
            setGoogleClientId(data.google_client_id);
          }
        })
        .catch(() => {});
    }
  }, [googleClientId]);

  useEffect(() => {
    setMode(initialMode);
    setError('');
    setInfoMessage('');
  }, [initialMode, isOpen]);

  // Handle Google OAuth Credential
  const handleCredentialResponse = async (response) => {
    if (!response?.credential) return;
    setLoading(true);
    setError('');
    try {
      const data = await googleAuthUser(response.credential);
      if (onSuccess) onSuccess(data.user, Boolean(data.is_new_user));
      onClose();
    } catch (err) {
      setError(err.message || 'Google sign-in failed. Please try again or use email login.');
    } finally {
      setLoading(false);
    }
  };

  // Initialize Google Identity Services (GIS)
  useEffect(() => {
    if (!isOpen || !googleClientId || (mode !== 'login' && mode !== 'register')) return;

    let attempts = 0;
    const maxAttempts = 40; // 4 seconds polling

    const setupGoogleSignIn = () => {
      if (window.google?.accounts?.id && googleBtnRef.current) {
        try {
          window.google.accounts.id.initialize({
            client_id: googleClientId,
            callback: handleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true,
          });

          googleBtnRef.current.innerHTML = '';
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: 'outline',
            size: 'large',
            width: 320,
            text: mode === 'login' ? 'signin_with' : 'signup_with',
            shape: 'pill',
            logo_alignment: 'left',
          });
          setGsiButtonRendered(true);
          return true;
        } catch (err) {
          console.warn('Google GSI render error:', err);
        }
      }
      return false;
    };

    if (!setupGoogleSignIn()) {
      const interval = setInterval(() => {
        attempts++;
        if (setupGoogleSignIn() || attempts >= maxAttempts) {
          clearInterval(interval);
        }
      }, 100);
      return () => clearInterval(interval);
    }
  }, [isOpen, mode, googleClientId]);

  if (!isOpen) return null;

  const handleCustomGoogleClick = () => {
    setError('');
    if (!googleClientId) {
      setError(
        'Google OAuth Client ID is missing. Add VITE_GOOGLE_CLIENT_ID to your .env file or sign in with email.'
      );
      return;
    }

    if (window.google?.accounts?.id) {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: handleCredentialResponse,
      });
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          setError(
            'Google Sign-In popup could not be displayed. Make sure popups are allowed and http://localhost:5173 is added to Authorized JavaScript Origins in your Google Cloud Console.'
          );
        }
      });
    } else {
      setError(
        'Google Identity SDK is still loading. Please check your internet connection or use email and password.'
      );
    }
  };

  const handleResendVerification = async () => {
    if (!email) {
      setError('Please enter your email address to resend verification.');
      return;
    }
    setLoading(true);
    setError('');
    setInfoMessage('');
    try {
      await requestEmailVerification(email);
      setInfoMessage('A fresh verification link has been sent to your email.');
    } catch (err) {
      setError(err.message || 'Failed to resend verification link.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPasswordSubmit = async (e) => {
    e.preventDefault();
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }
    setLoading(true);
    setError('');
    setInfoMessage('');
    try {
      await requestPasswordReset(email);
      setMode('reset_sent');
    } catch (err) {
      setError(err.message || 'Failed to request password reset.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfoMessage('');

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    const byteLen = new TextEncoder().encode(password).length;
    if (byteLen > 72) {
      setError('Password must not exceed 72 bytes.');
      return;
    }

    if (mode === 'register') {
      if (!name.trim()) {
        setError('Please enter your full name.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
    }

    setLoading(true);
    try {
      let data;
      if (mode === 'login') {
        data = await loginUser({ email, password });
        if (onSuccess) onSuccess(data.user, false);
        onClose();
      } else {
        data = await registerUser({ email, password, name });
        if (data.token) {
          if (onSuccess) onSuccess(data.user, true);
          onClose();
        } else {
          setMode('verify_pending');
        }
      }
    } catch (err) {
      const msg = err.message || 'Authentication failed. Please try again.';
      setError(msg);
      if (msg.toLowerCase().includes('verified')) {
        setInfoMessage('Your email has not been verified yet. Check your inbox or request a new link.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-md bg-white border border-[#e0e0e0] rounded-xl shadow-xl overflow-hidden p-6 sm:p-8 text-[#000000] animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Accent Line */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-[#0a66c2]" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 text-[#666666] hover:text-[#000000] rounded-lg transition-colors"
        >
          <X size={18} />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-[#0a66c2]/10 text-[#0a66c2] mb-3 border border-[#0a66c2]/20">
            <Briefcase size={22} />
          </div>
          <h2 className="text-xl font-bold text-[#000000] tracking-tight">
            {mode === 'login' && 'Welcome to JobHelperGuru'}
            {mode === 'register' && 'Create Your JobHelperGuru Account'}
            {mode === 'verify_pending' && 'Check Your Email'}
            {mode === 'forgot_password' && 'Reset Password'}
            {mode === 'reset_sent' && 'Password Reset Link Sent'}
          </h2>
          <p className="text-xs text-[#666666] mt-1">
            {mode === 'login' && 'Access your isolated resume vault and personal job pipeline.'}
            {mode === 'register' && 'Start tracking jobs and matching resumes with secure cloud storage.'}
            {mode === 'verify_pending' && 'We sent a verification link to your email address.'}
            {mode === 'forgot_password' && 'Enter your email to receive a password reset link.'}
            {mode === 'reset_sent' && 'Check your inbox for instructions to reset your password.'}
          </p>
        </div>

        {/* Tab Toggle for login/register */}
        {(mode === 'login' || mode === 'register') && (
          <div className="flex p-1 bg-[#f3f6f8] border border-[#e0e0e0] rounded-full mb-5">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError('');
                setInfoMessage('');
              }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all ${
                mode === 'login'
                  ? 'bg-[#0a66c2] text-white shadow-sm'
                  : 'text-[#666666] hover:text-[#000000]'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register');
                setError('');
                setInfoMessage('');
              }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all ${
                mode === 'register'
                  ? 'bg-[#0a66c2] text-white shadow-sm'
                  : 'text-[#666666] hover:text-[#000000]'
              }`}
            >
              Create Account
            </button>
          </div>
        )}

        {/* Error Notification */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-[#b24020]/10 border border-[#b24020]/25 text-[#b24020] text-xs flex items-start gap-2 animate-shake">
            <AlertCircle size={15} className="text-[#b24020] mt-0.5 shrink-0" />
            <span className="leading-relaxed">{error}</span>
          </div>
        )}

        {/* Info Notification */}
        {infoMessage && (
          <div className="mb-4 p-3 rounded-lg bg-[#0a66c2]/10 border border-[#0a66c2]/25 text-[#0a66c2] text-xs flex items-start gap-2">
            <CheckCircle size={15} className="text-[#0a66c2] mt-0.5 shrink-0" />
            <span className="leading-relaxed">{infoMessage}</span>
          </div>
        )}

        {/* Verify Pending View */}
        {mode === 'verify_pending' && (
          <div className="space-y-4 text-center">
            <div className="p-4 bg-[#f3f6f8] rounded-lg border border-[#e0e0e0] text-xs text-[#666666] leading-relaxed">
              We sent a verification link to <strong className="text-[#000000]">{email}</strong>. Please click the link in the email to activate your account.
            </div>
            <button
              type="button"
              disabled={loading}
              onClick={handleResendVerification}
              className="btn-secondary-corporate w-full py-2.5 px-4 text-xs font-semibold"
            >
              {loading ? 'Resending...' : 'Resend Verification Email'}
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError('');
                setInfoMessage('');
              }}
              className="text-xs text-[#0a66c2] hover:underline font-semibold flex items-center justify-center gap-1 mx-auto"
            >
              <ArrowLeft size={14} /> Back to Sign In
            </button>
          </div>
        )}

        {/* Reset Sent View */}
        {mode === 'reset_sent' && (
          <div className="space-y-4 text-center">
            <div className="p-4 bg-[#f3f6f8] rounded-lg border border-[#e0e0e0] text-xs text-[#666666] leading-relaxed">
              If an account exists with <strong className="text-[#000000]">{email}</strong>, a password reset link has been dispatched. Please check your inbox and spam folders.
            </div>
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError('');
                setInfoMessage('');
              }}
              className="btn-primary-corporate w-full py-2.5 px-4 text-xs font-semibold"
            >
              Back to Sign In
            </button>
          </div>
        )}

        {/* Forgot Password View */}
        {mode === 'forgot_password' && (
          <form onSubmit={handleForgotPasswordSubmit} className="space-y-3.5">
            <div>
              <label className="block text-[11px] font-semibold text-[#000000] mb-1">Email Address</label>
              <div className="relative">
                <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="input-corporate w-full pl-9 pr-3 py-2 text-xs"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary-corporate w-full mt-2 py-2.5 px-4 text-xs font-semibold flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : 'Send Reset Link'}
            </button>
            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setError('');
                  setInfoMessage('');
                }}
                className="text-xs text-[#0a66c2] hover:underline font-semibold"
              >
                Back to Sign In
              </button>
            </div>
          </form>
        )}

        {/* Login or Register Form */}
        {(mode === 'login' || mode === 'register') && (
          <>
            {/* Google SSO Button Container */}
            <div className="mb-4">
              <div
                ref={googleBtnRef}
                className={`w-full flex justify-center min-h-[40px] ${
                  !gsiButtonRendered ? 'hidden' : ''
                }`}
              />

              {!gsiButtonRendered && (
                <button
                  type="button"
                  onClick={handleCustomGoogleClick}
                  className="btn-secondary-corporate w-full py-2.5 px-4 text-xs font-semibold flex items-center justify-center gap-2.5"
                >
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  <span>Continue with Google</span>
                </button>
              )}

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-[#e0e0e0]" />
                </div>
                <div className="relative flex justify-center text-[10px] uppercase">
                  <span className="bg-white px-2 text-[#666666] font-semibold tracking-wider">
                    or continue with email
                  </span>
                </div>
              </div>
            </div>

            {/* Email & Password Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {mode === 'register' && (
                <div>
                  <label className="block text-[11px] font-semibold text-[#000000] mb-1">Full Name</label>
                  <div className="relative">
                    <UserIcon size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Jane Doe"
                      className="input-corporate w-full pl-9 pr-3 py-2 text-xs"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[11px] font-semibold text-[#000000] mb-1">Email Address</label>
                <div className="relative">
                  <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="input-corporate w-full pl-9 pr-3 py-2 text-xs"
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="block text-[11px] font-semibold text-[#000000]">Password</label>
                  {mode === 'login' && (
                    <button
                      type="button"
                      onClick={() => {
                        setMode('forgot_password');
                        setError('');
                        setInfoMessage('');
                      }}
                      className="text-[11px] text-[#0a66c2] hover:underline"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="8-72 characters"
                    className="input-corporate w-full pl-9 pr-10 py-2 text-xs"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#666666] hover:text-[#000000]"
                  >
                    {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div>
                  <label className="block text-[11px] font-semibold text-[#000000] mb-1">Confirm Password</label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repeat your password"
                      className="input-corporate w-full pl-9 pr-3 py-2 text-xs"
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="btn-primary-corporate w-full mt-2 py-2.5 px-4 text-xs font-semibold flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    <span>{mode === 'login' ? 'Signing In...' : 'Creating Account...'}</span>
                  </>
                ) : (
                  <span>{mode === 'login' ? 'Sign In' : 'Create Free Account'}</span>
                )}
              </button>
            </form>

            {/* Footer switch */}
            <div className="mt-5 text-center text-xs text-[#666666]">
              {mode === 'login' ? (
                <span>
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('register');
                      setError('');
                      setInfoMessage('');
                    }}
                    className="text-[#0a66c2] hover:underline font-semibold ml-1"
                  >
                    Sign up
                  </button>
                </span>
              ) : (
                <span>
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setMode('login');
                      setError('');
                      setInfoMessage('');
                    }}
                    className="text-[#0a66c2] hover:underline font-semibold ml-1"
                  >
                    Log in
                  </button>
                </span>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
