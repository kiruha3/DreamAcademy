import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('API client DELETE handling', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'test-token'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('resolves null on 204 No Content', async () => {
    const { deleteCourse } = await import('./client.js')
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
      json: vi.fn(() => Promise.reject(new Error('Should not call json'))),
    })

    const result = await deleteCourse(1)
    expect(result).toBeNull()
  })

  it('parses json on non-204 status', async () => {
    const { deleteCourse } = await import('./client.js')
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: vi.fn(() => Promise.resolve({ deleted: true })),
    })

    const result = await deleteCourse(1)
    expect(result).toEqual({ deleted: true })
  })
})
