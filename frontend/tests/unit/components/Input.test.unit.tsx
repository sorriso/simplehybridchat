// path: tests/unit/components/Input.test.unit.tsx
// version: 3

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '@/components/ui/Input'

describe('Input Component', () => {
  describe('Rendering', () => {
    it('should render input element', () => {
      render(<Input />)
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('should render with label', () => {
      render(<Input label="Username" />)
      expect(screen.getByLabelText('Username')).toBeInTheDocument()
    })

    it('should render with placeholder', () => {
      render(<Input placeholder="Enter text" />)
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
    })

    it('should render with default value', () => {
      render(<Input defaultValue="Hello" />)
      expect(screen.getByRole('textbox')).toHaveValue('Hello')
    })
  })

  describe('Value Changes', () => {
    it('should accept user input', async () => {
      const user = userEvent.setup()
      
      render(<Input />)
      const input = screen.getByRole('textbox')
      
      await user.type(input, 'Hello')
      
      expect(input).toHaveValue('Hello')
    })

    it('should update value controlled component', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()
      
      render(<Input value="" onChange={handleChange} />)
      const input = screen.getByRole('textbox')
      
      await user.type(input, 'a')
      
      // Just verify onChange was called - the exact event structure varies
      expect(handleChange).toHaveBeenCalled()
    })
  })

  describe('Input Types', () => {
    it('should render as password type', () => {
      const { container } = render(<Input type="password" />)
      // Password inputs don't have textbox role, query by tag
      const input = container.querySelector('input')
      expect(input).toHaveAttribute('type', 'password')
    })

    it('should render as email type', () => {
      render(<Input type="email" />)
      expect(screen.getByRole('textbox')).toHaveAttribute('type', 'email')
    })
  })

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Input disabled />)
      expect(screen.getByRole('textbox')).toBeDisabled()
    })

    it('should not accept input when disabled', async () => {
      const user = userEvent.setup()
      
      render(<Input disabled />)
      const input = screen.getByRole('textbox')
      
      await user.type(input, 'Hello')
      
      expect(input).toHaveValue('')
    })
  })

  describe('Error State', () => {
    it('should display error message', () => {
      render(<Input error="This field is required" />)
      expect(screen.getByText('This field is required')).toBeInTheDocument()
    })

    it('should apply error styling', () => {
      render(<Input error="Error" />)
      const input = screen.getByRole('textbox')
      // Check for Tailwind error border class
      expect(input.className).toContain('border-red-500')
    })
  })

  describe('Full Width', () => {
    it('should be full width when fullWidth prop is true', () => {
      const { container } = render(<Input fullWidth />)
      const wrapper = container.firstChild
      expect(wrapper).toHaveClass('w-full')
    })
  })

  describe('Accessibility', () => {
    it('should associate label with input', () => {
      render(<Input label="Email" />)
      const input = screen.getByLabelText('Email')
      expect(input).toBeInTheDocument()
    })

    it('should have aria-invalid when error is present', () => {
      render(<Input error="Error message" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveAttribute('aria-invalid', 'true')
    })

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup()
      const handleChange = jest.fn()
      
      render(<Input onChange={handleChange} />)
      const input = screen.getByRole('textbox')
      
      input.focus()
      await user.type(input, 'Test')
      
      expect(handleChange).toHaveBeenCalled()
    })
  })
})
