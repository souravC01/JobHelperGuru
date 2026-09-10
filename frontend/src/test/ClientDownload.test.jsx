import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { downloadResumeFile, exportCoverLetterDocx } from '../api/client'

describe('client download functions', () => {
  let originalFetch
  let alertSpy

  beforeEach(() => {
    originalFetch = global.fetch
    alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    window.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
    window.URL.revokeObjectURL = vi.fn()
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  })

  afterEach(() => {
    global.fetch = originalFetch
    alertSpy.mockRestore()
    vi.restoreAllMocks()
  })

  it('shows alert message when resume download triggers text-generated fallback', async () => {
    const mockHeaders = new Headers({
      'content-disposition': 'attachment; filename="Sample_Resume_generated.docx"',
      'x-fallback-generated': 'true',
    })

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: mockHeaders,
      blob: vi.fn().mockResolvedValue(new Blob(['test docx content'])),
    })

    await downloadResumeFile('res-fallback-1', 'Sample.pdf')

    expect(alertSpy).toHaveBeenCalledWith(
      'Original uploaded file was not found in storage, so the file was generated from the saved text.'
    )
  })

  it('does not show fallback alert on normal file downloads', async () => {
    const mockHeaders = new Headers({
      'content-disposition': 'attachment; filename="Original_Resume.pdf"',
    })

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: mockHeaders,
      blob: vi.fn().mockResolvedValue(new Blob(['test pdf content'])),
    })

    await downloadResumeFile('res-normal-1', 'Original_Resume.pdf')

    expect(alertSpy).not.toHaveBeenCalled()
  })
})
