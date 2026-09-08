import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import ThemeToggle from '../components/ThemeToggle'

describe('ThemeToggle', () => {
  it('renders and invokes the toggle action without network access', () => {
    const onToggle = vi.fn()
    render(<ThemeToggle theme="light" onToggle={onToggle} />)
    fireEvent.click(screen.getByRole('button', { name: 'Switch to dark mode' }))
    expect(onToggle).toHaveBeenCalledOnce()
    expect(fetch).not.toHaveBeenCalled()
  })
})
