// path: tests/helpers/render.tsx
// version: 1

import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'

/**
 * Custom render function that wraps components with necessary providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  // For now, we don't have global providers (Context API)
  // When we add AuthContext, ConversationsContext, etc., they'll go here
  
  return render(ui, options)
}

/**
 * Re-export everything from testing library
 */
export * from '@testing-library/react'
export { renderWithProviders as render }