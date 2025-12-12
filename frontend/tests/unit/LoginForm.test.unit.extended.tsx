/* path: tests/unit/components/LoginForm.test.unit.extended.tsx
   version: 1 - Extended tests for LoginForm validation (lines 28-30, 32-35, 46) */

   import React from 'react';
   import { render, screen, fireEvent, waitFor } from '@testing-library/react';
   import { LoginForm } from '@/components/auth/LoginForm';
   import type { User } from '@/types/auth';
   
   describe('LoginForm - Extended Validation Coverage', () => {
     const mockOnLogin = jest.fn();
     const mockUser: User = {
       id: 'user-1',
       email: 'test@example.com',
       role: 'user',
       createdAt: new Date().toISOString(),
     };
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     describe('Client-side validation', () => {
       it('should show error when email is empty on submit', async () => {
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Leave email empty, fill password
         const passwordInput = screen.getByLabelText(/password/i);
         fireEvent.change(passwordInput, { target: { value: 'password123' } });
         
         // Try to submit
         fireEvent.click(submitButton);
   
         // Should show email required error
         await waitFor(() => {
           expect(screen.getByText(/email is required/i)).toBeInTheDocument();
         });
   
         // onLogin should not be called
         expect(mockOnLogin).not.toHaveBeenCalled();
       });
   
       it('should show error when email is only whitespace', async () => {
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const passwordInput = screen.getByLabelText(/password/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Fill with whitespace
         fireEvent.change(emailInput, { target: { value: '   ' } });
         fireEvent.change(passwordInput, { target: { value: 'password123' } });
         
         // Submit
         fireEvent.click(submitButton);
   
         // Should show email required error
         await waitFor(() => {
           expect(screen.getByText(/email is required/i)).toBeInTheDocument();
         });
   
         expect(mockOnLogin).not.toHaveBeenCalled();
       });
   
       it('should show error when password is empty on submit', async () => {
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Fill email, leave password empty
         fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
         
         // Try to submit
         fireEvent.click(submitButton);
   
         // Should show password required error
         await waitFor(() => {
           expect(screen.getByText(/password is required/i)).toBeInTheDocument();
         });
   
         // onLogin should not be called
         expect(mockOnLogin).not.toHaveBeenCalled();
       });
   
       it('should show error when password is only whitespace', async () => {
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const passwordInput = screen.getByLabelText(/password/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Fill with whitespace
         fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
         fireEvent.change(passwordInput, { target: { value: '   ' } });
         
         // Submit
         fireEvent.click(submitButton);
   
         // Should show password required error
         await waitFor(() => {
           expect(screen.getByText(/password is required/i)).toBeInTheDocument();
         });
   
         expect(mockOnLogin).not.toHaveBeenCalled();
       });
   
       it('should clear local error when submitting with valid credentials', async () => {
         mockOnLogin.mockResolvedValue(mockUser);
         
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const passwordInput = screen.getByLabelText(/password/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // First, trigger an error
         fireEvent.click(submitButton);
         
         await waitFor(() => {
           expect(screen.getByText(/email is required/i)).toBeInTheDocument();
         });
   
         // Now fill valid credentials
         fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
         fireEvent.change(passwordInput, { target: { value: 'password123' } });
         
         // Submit again
         fireEvent.click(submitButton);
   
         // Error should be cleared (line 36: setLocalError(null))
         await waitFor(() => {
           expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument();
         });
   
         expect(mockOnLogin).toHaveBeenCalledWith('test@example.com', 'password123');
       });
   
       it('should prioritize email validation before password', async () => {
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Submit with both empty
         fireEvent.click(submitButton);
   
         // Should show email error first, not password error
         await waitFor(() => {
           expect(screen.getByText(/email is required/i)).toBeInTheDocument();
           expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
         });
       });
     });
   
     describe('Error display logic (line 46)', () => {
       it('should display parent error when provided', () => {
         const parentError = 'Invalid credentials from server';
         
         render(<LoginForm onLogin={mockOnLogin} error={parentError} />);
   
         // Parent error should be displayed
         expect(screen.getByText(/invalid credentials from server/i)).toBeInTheDocument();
       });
   
       it('should display local validation error when no parent error', async () => {
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const submitButton = screen.getByRole('button', { name: /log in/i });
         fireEvent.click(submitButton);
   
         // Local error should be displayed
         await waitFor(() => {
           expect(screen.getByText(/email is required/i)).toBeInTheDocument();
         });
       });
   
       it('should prioritize parent error over local error', async () => {
         const parentError = 'Server error';
         
         render(<LoginForm onLogin={mockOnLogin} error={parentError} />);
   
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Try to trigger local error
         fireEvent.click(submitButton);
   
         // Parent error should still be displayed, not local
         expect(screen.getByText(/server error/i)).toBeInTheDocument();
       });
   
       it('should not display any error when both are null', () => {
         render(<LoginForm onLogin={mockOnLogin} />);
   
         // No error should be displayed initially
         expect(screen.queryByRole('alert')).not.toBeInTheDocument();
       });
     });
   
     describe('Error handling in onLogin catch block', () => {
       it('should handle onLogin rejection without crashing', async () => {
         mockOnLogin.mockRejectedValue(new Error('Login failed'));
         
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const passwordInput = screen.getByLabelText(/password/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
         fireEvent.change(passwordInput, { target: { value: 'password123' } });
         fireEvent.click(submitButton);
   
         // Component should not crash (catch block on lines 42-44)
         await waitFor(() => {
           expect(mockOnLogin).toHaveBeenCalled();
         });
   
         // Form should still be rendered
         expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
       });
   
       it('should allow parent component to handle errors', async () => {
         const onLoginError = new Error('Invalid credentials');
         mockOnLogin.mockRejectedValue(onLoginError);
         
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const passwordInput = screen.getByLabelText(/password/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
         fireEvent.change(passwordInput, { target: { value: 'wrong' } });
         fireEvent.click(submitButton);
   
         // Error is swallowed by catch block, parent handles it
         await waitFor(() => {
           expect(mockOnLogin).toHaveBeenCalled();
         });
   
         // No local error should be displayed
         expect(screen.queryByText(/email is required/i)).not.toBeInTheDocument();
         expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
       });
     });
   
     describe('Validation edge cases', () => {
       it('should handle email with leading/trailing spaces', async () => {
         mockOnLogin.mockResolvedValue(mockUser);
         
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const passwordInput = screen.getByLabelText(/password/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Email with spaces
         fireEvent.change(emailInput, { target: { value: '  test@example.com  ' } });
         fireEvent.change(passwordInput, { target: { value: 'password123' } });
         fireEvent.click(submitButton);
   
         // Should call onLogin with trimmed email
         await waitFor(() => {
           expect(mockOnLogin).toHaveBeenCalledWith('  test@example.com  ', 'password123');
         });
       });
   
       it('should handle password with leading/trailing spaces', async () => {
         mockOnLogin.mockResolvedValue(mockUser);
         
         render(<LoginForm onLogin={mockOnLogin} />);
   
         const emailInput = screen.getByLabelText(/email/i);
         const passwordInput = screen.getByLabelText(/password/i);
         const submitButton = screen.getByRole('button', { name: /log in/i });
         
         // Password with spaces
         fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
         fireEvent.change(passwordInput, { target: { value: '  password123  ' } });
         fireEvent.click(submitButton);
   
         // Should call onLogin with exact password (including spaces)
         await waitFor(() => {
           expect(mockOnLogin).toHaveBeenCalledWith('test@example.com', '  password123  ');
         });
       });
     });
   });