import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import PrivacyModal from '../components/PrivacyModal';

describe('PrivacyModal', () => {
  it('does not render when isOpen is false', () => {
    const { container } = render(<PrivacyModal isOpen={false} onClose={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders privacy information and handles closing', () => {
    const onClose = vi.fn();
    render(<PrivacyModal isOpen={true} onClose={onClose} />);

    expect(screen.getByText('Privacy & Data Policy')).toBeInTheDocument();
    expect(screen.getByText(/Zero Tracking/i)).toBeInTheDocument();
    expect(screen.getByText(/BYOK/i)).toBeInTheDocument();
    expect(screen.getByText(/10 stored resumes/i)).toBeInTheDocument();
    expect(screen.getByText(/50MB/i)).toBeInTheDocument();

    const closeBtn = screen.getByRole('button', { name: /understood/i });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledOnce();
  });
});
