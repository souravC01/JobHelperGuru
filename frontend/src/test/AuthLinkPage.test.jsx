import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import AuthLinkPage from '../components/AuthLinkPage';
import * as client from '../api/client';

describe('AuthLinkPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('verifies email with valid token and displays success state', async () => {
    delete window.location;
    window.location = new URL('https://jobhelper.guru/verify-email?token=valid-token-123');

    vi.spyOn(client, 'confirmEmailVerification').mockResolvedValue({ message: 'Verified' });

    render(<AuthLinkPage path="/verify-email" onGoHome={vi.fn()} onOpenAuth={vi.fn()} />);

    expect(screen.getByText(/Verifying your email/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Email Verified!/i)).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  it('displays error when email verification fails', async () => {
    delete window.location;
    window.location = new URL('https://jobhelper.guru/verify-email?token=expired-token');

    vi.spyOn(client, 'confirmEmailVerification').mockRejectedValue(new Error('Token expired'));

    render(<AuthLinkPage path="/verify-email" onGoHome={vi.fn()} onOpenAuth={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Verification Failed/i)).toBeInTheDocument();
      expect(screen.getByText(/Token expired/i)).toBeInTheDocument();
    });
  });

  it('renders password reset form and submits successfully', async () => {
    delete window.location;
    window.location = new URL('https://jobhelper.guru/reset-password?token=reset-token-456');

    const resetSpy = vi.spyOn(client, 'confirmPasswordReset').mockResolvedValue({ message: 'Password reset' });

    render(<AuthLinkPage path="/reset-password" onGoHome={vi.fn()} onOpenAuth={vi.fn()} />);

    expect(screen.getByText(/Reset Your Password/i)).toBeInTheDocument();

    const newPassInput = screen.getByLabelText(/^New Password/i);
    const confirmPassInput = screen.getByLabelText(/^Confirm New Password/i);
    fireEvent.change(newPassInput, { target: { value: 'NewSecurePassword123!' } });
    fireEvent.change(confirmPassInput, { target: { value: 'NewSecurePassword123!' } });

    fireEvent.click(screen.getByRole('button', { name: /Set New Password/i }));

    await waitFor(() => {
      expect(resetSpy).toHaveBeenCalledWith('reset-token-456', 'NewSecurePassword123!');
      expect(screen.getByText(/Password Updated!/i)).toBeInTheDocument();
    });
  });

  it('shows validation error when passwords do not match', async () => {
    delete window.location;
    window.location = new URL('https://jobhelper.guru/reset-password?token=reset-token-456');

    render(<AuthLinkPage path="/reset-password" onGoHome={vi.fn()} onOpenAuth={vi.fn()} />);

    const newPassInput = screen.getByLabelText(/^New Password/i);
    const confirmPassInput = screen.getByLabelText(/^Confirm New Password/i);
    fireEvent.change(newPassInput, { target: { value: 'NewSecurePassword123!' } });
    fireEvent.change(confirmPassInput, { target: { value: 'DifferentPassword456!' } });

    fireEvent.click(screen.getByRole('button', { name: /Set New Password/i }));


    expect(screen.getByText(/Passwords do not match/i)).toBeInTheDocument();
  });
});
