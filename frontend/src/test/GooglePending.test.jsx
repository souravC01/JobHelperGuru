import { it, expect, vi, afterEach } from 'vitest';
import { googleAuthUser } from '../api/client';

afterEach(() => { vi.unstubAllGlobals(); localStorage.clear(); });

it('does not cache an unverified Google identity as a signed-in user', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({
    token: null, requires_verification: true, user: { email: 'pending@example.test' },
  }) }));
  const result = await googleAuthUser('synthetic');
  expect(result.requires_verification).toBe(true);
  expect(localStorage.getItem('jh_user')).toBeNull();
  expect(localStorage.getItem('jh_token')).toBeNull();
});
