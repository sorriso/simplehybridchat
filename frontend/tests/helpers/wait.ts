// path: tests/helpers/wait.ts
// version: 1

import { waitFor } from '@testing-library/react'

/**
 * Wait for element to appear
 */
export async function waitForElement(
  callback: () => HTMLElement | null,
  options?: { timeout?: number }
): Promise<HTMLElement> {
  let element: HTMLElement | null = null
  
  await waitFor(
    () => {
      element = callback()
      if (!element) throw new Error('Element not found')
    },
    { timeout: options?.timeout || 3000 }
  )
  
  return element!
}

/**
 * Wait for loading to complete (no loading spinner)
 */
export async function waitForLoadingComplete(
  getByTestId: (id: string) => HTMLElement,
  options?: { timeout?: number }
) {
  await waitFor(
    () => {
      expect(() => getByTestId('loading-spinner')).toThrow()
    },
    { timeout: options?.timeout || 3000 }
  )
}

/**
 * Wait for specific time (use sparingly, prefer waitFor)
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Wait for mock function to be called
 */
export async function waitForMockCall(
  mockFn: jest.Mock,
  options?: { timeout?: number; times?: number }
): Promise<void> {
  const times = options?.times || 1
  
  await waitFor(
    () => {
      expect(mockFn).toHaveBeenCalledTimes(times)
    },
    { timeout: options?.timeout || 3000 }
  )
}

/**
 * Wait for API request to complete (checks MSW handlers)
 */
export async function waitForApiCall(
  endpoint: string,
  options?: { timeout?: number }
): Promise<void> {
  // This is a placeholder - in real implementation, 
  // we'd track MSW handler calls
  await sleep(100)
}