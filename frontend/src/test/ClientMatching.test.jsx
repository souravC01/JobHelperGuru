import { describe, expect, it, vi } from 'vitest'
import * as api from '../api/client'

const success = (data) => ({ ok: true, status: 200, json: async () => data })

describe('overall fit client', () => {
  it('forwards raw job, selected IDs, fresh and abort signal with authentication', async () => {
    localStorage.setItem('jh_token', 'test-token')
    const controller = new AbortController()
    const result = { comparison_complete: true, evaluations: [] }
    fetch.mockResolvedValue(success(result))
    expect(await api.evaluateResumes('  Raw JD\n', ['r1'], { fresh: true, signal: controller.signal })).toEqual(result)
    expect(fetch).toHaveBeenCalledWith('/api/resumes/evaluate', expect.objectContaining({
      method: 'POST', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer test-token' },
      body: JSON.stringify({ job_text: '  Raw JD\n', resume_ids: ['r1'], fresh: true }),
    }))
  })
  it('loads the authenticated rollout flag and prepares a stored profile without uploading text', async () => {
    fetch.mockResolvedValueOnce(success({ matching_v2_enabled: false })).mockResolvedValueOnce(success({ status: 'complete' }))
    expect(await api.getFeatures()).toEqual({ matching_v2_enabled: false })
    const signal = new AbortController().signal
    expect(await api.prepareResumeProfile('r /?', { signal })).toEqual({ status: 'complete' })
    expect(fetch).toHaveBeenLastCalledWith('/api/resumes/r%20%2F%3F/profile', expect.objectContaining({ method: 'POST', signal }))
    expect(fetch.mock.calls[1][1].body).toBeUndefined()
  })
  it('preserves structured failure status without silently switching offline or retrying', async () => {
    fetch.mockResolvedValue({ ok: false, status: 502, json: async () => ({ detail: { message: 'Assessment failed.', can_switch_offline: false } }) })
    await expect(api.evaluateResumes('JD', ['r'])).rejects.toMatchObject({ status: 502, canSwitchOffline: false, message: 'Assessment failed.' })
    expect(fetch).toHaveBeenCalledTimes(1)
  })
  it('propagates cancellation without retrying', async () => {
    const error = new DOMException('Cancelled', 'AbortError')
    fetch.mockRejectedValue(error)
    await expect(api.evaluateResumes('JD', ['r'])).rejects.toBe(error)
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
