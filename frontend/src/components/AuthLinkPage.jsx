import { useState, useEffect } from 'react';
import { Mail, Lock, CheckCircle, AlertCircle, Loader2, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import { confirmEmailVerification, confirmPasswordReset } from '../api/client';

export default function AuthLinkPage({ path, onGoHome, onOpenAuth }) {
  const isVerify = path === '/verify-email';
  const queryParams = new URLSearchParams(window.location.search);
  const token = queryParams.get('token') || '';

  // Verification state
  const [verifyStatus, setVerifyStatus] = useState('loading'); // 'loading' | 'success' | 'error'
  const [verifyError, setVerifyError] = useState('');

  // Password reset state
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState('');
  const [resetSuccess, setResetSuccess] = useState(false);

  useEffect(() => {
    if (isVerify) {
      if (!token) {
        setVerifyStatus('error');
        setVerifyError('Verification link is missing the token parameter.');
        return;
      }
      confirmEmailVerification(token)
        .then(() => {
          setVerifyStatus('success');
        })
        .catch((err) => {
          setVerifyStatus('error');
          setVerifyError(err.message || 'Verification link is invalid or has expired.');
        });
    }
  }, [isVerify, token]);

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    setResetError('');
    if (!token) {
      setResetError('Reset token is missing.');
      return;
    }
    if (password.length < 8) {
      setResetError('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setResetError('Passwords do not match.');
      return;
    }

    setResetLoading(true);
    try {
      await confirmPasswordReset(token, password);
      setResetSuccess(true);
    } catch (err) {
      setResetError(err.message || 'Failed to reset password. The link may have expired.');
    } finally {
      setResetLoading(false);
    }
  };

  const handleNavigateHome = () => {
    window.history.pushState({}, '', '/');
    if (onGoHome) onGoHome();
  };

  const handleOpenLogin = () => {
    window.history.pushState({}, '', '/');
    if (onGoHome) onGoHome();
    if (onOpenAuth) onOpenAuth('login');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 p-8 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
          <button
            onClick={handleNavigateHome}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to JobHelperGuru
          </button>
        </div>

        {isVerify ? (
          <div className="text-center space-y-4 py-4">
            {verifyStatus === 'loading' && (
              <>
                <div className="flex justify-center">
                  <Loader2 className="w-12 h-12 text-primary-600 animate-spin" />
                </div>
                <h2 className="text-xl font-bold">Verifying your email...</h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Please hold on while we confirm your email address.
                </p>
              </>
            )}

            {verifyStatus === 'success' && (
              <>
                <div className="flex justify-center">
                  <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                    <CheckCircle className="w-8 h-8" />
                  </div>
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Email Verified!</h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Your email address has been verified successfully. You can now sign in to your account.
                </p>
                <div className="pt-2">
                  <button
                    onClick={handleOpenLogin}
                    className="w-full py-2.5 px-4 rounded-xl font-medium bg-primary-600 hover:bg-primary-700 text-white shadow-md shadow-primary-500/20 transition-colors"
                  >
                    Sign In
                  </button>
                </div>
              </>
            )}

            {verifyStatus === 'error' && (
              <>
                <div className="flex justify-center">
                  <div className="w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 flex items-center justify-center">
                    <AlertCircle className="w-8 h-8" />
                  </div>
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Verification Failed</h2>
                <p className="text-sm text-red-600 dark:text-red-400">
                  {verifyError}
                </p>
                <div className="pt-2">
                  <button
                    onClick={handleNavigateHome}
                    className="w-full py-2.5 px-4 rounded-xl font-medium bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 transition-colors"
                  >
                    Return Home
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-center space-y-1">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Reset Your Password</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Enter your new account password below.
              </p>
            </div>

            {resetSuccess ? (
              <div className="text-center space-y-4 py-4">
                <div className="flex justify-center">
                  <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                    <CheckCircle className="w-8 h-8" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Password Updated!</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Your password has been reset successfully. You can now sign in with your new credentials.
                </p>
                <button
                  onClick={handleOpenLogin}
                  className="w-full py-2.5 px-4 rounded-xl font-medium bg-primary-600 hover:bg-primary-700 text-white shadow-md shadow-primary-500/20 transition-colors"
                >
                  Sign In
                </button>
              </div>
            ) : (
              <form onSubmit={handleResetSubmit} className="space-y-4">
                {resetError && (
                  <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl text-xs text-red-600 dark:text-red-400 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    <span>{resetError}</span>
                  </div>
                )}

                <div className="space-y-1.5">
                  <label htmlFor="new-password" className="block text-xs font-semibold text-slate-700 dark:text-slate-300">New Password</label>
                  <div className="relative">
                    <input
                      id="new-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      placeholder="At least 8 characters"
                      className="w-full pl-10 pr-10 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="confirm-password" className="block text-xs font-semibold text-slate-700 dark:text-slate-300">Confirm New Password</label>
                  <div className="relative">
                    <input
                      id="confirm-password"
                      type={showPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      placeholder="Re-enter your new password"
                      className="w-full pl-10 pr-10 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  </div>
                </div>


                <button
                  type="submit"
                  disabled={resetLoading}
                  className="w-full py-2.5 px-4 rounded-xl font-medium bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white shadow-md shadow-primary-500/20 flex items-center justify-center gap-2 transition-colors"
                >
                  {resetLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Set New Password'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
