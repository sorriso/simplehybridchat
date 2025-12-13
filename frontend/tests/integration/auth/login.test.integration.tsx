// path: tests/integration/auth/login.test.integration.tsx
// version: 6 - FIXED: Updated button text to match actual component ("Sign In" not "Log In")

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { rest } from 'msw'
import { server } from '@/tests/mocks/server'
import { renderWithProviders } from '@/tests/helpers/render'
import { LoginForm } from '@/components/auth/LoginForm'

describe('Login Integration', () => {
  // Mock onLogin function
  const mockOnLogin = jest.fn()

  beforeEach(() => {
    mockOnLogin.mockClear()
    localStorage.clear()
  })

  it('does not call onLogin with empty fields', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<LoginForm onLogin={mockOnLogin} />)
    
    // Try to submit with empty fields - validation should prevent submission
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)
    
    // onLogin should not be called because validation prevents submission
    expect(mockOnLogin).not.toHaveBeenCalled()
  })

  it('calls onLogin with email and password', async () => {
    const user = userEvent.setup()
    
    // Mock successful login - returns a User object
    const mockUser = {
      id: 'user-1',
      email: 'john.doe@example.com',
      role: 'user' as const,
      createdAt: new Date().toISOString(),
    }
    mockOnLogin.mockResolvedValue(mockUser)
    
    renderWithProviders(<LoginForm onLogin={mockOnLogin} />)
    
    // Fill form
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    
    await user.type(emailInput, 'john.doe@example.com')
    await user.type(passwordInput, 'password123')
    
    // Submit
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)
    
    // Verify onLogin was called with email and password
    await waitFor(() => {
      expect(mockOnLogin).toHaveBeenCalledWith('john.doe@example.com', 'password123')
    })
  })

  it('displays error from parent component', async () => {
    const user = userEvent.setup()
    
    const errorMessage = 'Invalid credentials'
    
    renderWithProviders(<LoginForm onLogin={mockOnLogin} error={errorMessage} />)
    
    // Error should be displayed
    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
  })

  it('shows loading state', async () => {
    renderWithProviders(<LoginForm onLogin={mockOnLogin} loading={true} />)
    
    // Button text changes to "Signing in..." when loading
    const submitButton = screen.getByRole('button', { name: /signing in/i })
    
    // Button should be disabled when loading
    expect(submitButton).toBeDisabled()
  })
})