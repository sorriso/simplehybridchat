// path: frontend/tests/unit/components/Button.test.unit.tsx
// version: 4 - FIXED: Use actual CSS classes from Button implementation

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '@/components/ui/Button'

describe('Button Component', () => {
  describe('Rendering', () => {
    it('should render with text', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByText('Click me')).toBeInTheDocument()
    })

    it('should render as button element by default', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })
  })

  describe('Click Handling', () => {
    it('should call onClick when clicked', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()
      
      render(<Button onClick={handleClick}>Click me</Button>)
      
      await user.click(screen.getByText('Click me'))
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should not call onClick when disabled', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()
      
      render(<Button onClick={handleClick} disabled>Click me</Button>)
      
      await user.click(screen.getByText('Click me'))
      
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Disabled State', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Button disabled>Click me</Button>)
      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('should have disabled attribute', () => {
      render(<Button disabled>Click me</Button>)
      expect(screen.getByRole('button')).toHaveAttribute('disabled')
    })

    it('should have disabled styling class', () => {
      render(<Button disabled>Click me</Button>)
      const button = screen.getByRole('button')
      // Check for actual disabled classes applied
      expect(button.className).toContain('opacity-50')
      expect(button.className).toContain('cursor-not-allowed')
    })
  })

  describe('Variants', () => {
    it('should apply primary variant styles', () => {
      render(<Button variant="primary">Primary</Button>)
      const button = screen.getByRole('button')
      // Primary uses bg-primary-600
      expect(button.className).toContain('bg-primary-600')
    })

    it('should apply secondary variant styles', () => {
      render(<Button variant="secondary">Secondary</Button>)
      const button = screen.getByRole('button')
      // Secondary uses bg-white with border
      expect(button.className).toContain('bg-white')
      expect(button.className).toContain('border')
    })

    it('should apply danger variant styles', () => {
      render(<Button variant="danger">Danger</Button>)
      const button = screen.getByRole('button')
      // Danger uses bg-red-600
      expect(button.className).toContain('bg-red-600')
    })

    it('should apply ghost variant styles', () => {
      render(<Button variant="ghost">Ghost</Button>)
      const button = screen.getByRole('button')
      // Ghost uses text-gray-700 with hover:bg-gray-100
      expect(button.className).toContain('text-gray-700')
    })
  })

  describe('Full Width', () => {
    it('should take full width when fullWidth prop is true', () => {
      render(<Button fullWidth>Full Width</Button>)
      const button = screen.getByRole('button')
      expect(button.className).toContain('w-full')
    })

    it('should not take full width by default', () => {
      render(<Button>Normal</Button>)
      const button = screen.getByRole('button')
      expect(button.className).not.toContain('w-full')
    })
  })

  describe('Type Attribute', () => {
    it('should accept submit type', () => {
      render(<Button type="submit">Submit</Button>)
      expect(screen.getByRole('button')).toHaveAttribute('type', 'submit')
    })

    it('should accept button type', () => {
      render(<Button type="button">Button</Button>)
      expect(screen.getByRole('button')).toHaveAttribute('type', 'button')
    })
  })

  describe('Accessibility', () => {
    it('should have button role', () => {
      render(<Button>Accessible</Button>)
      expect(screen.getByRole('button')).toBeInTheDocument()
    })

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()
      
      render(<Button onClick={handleClick}>Keyboard</Button>)
      
      const button = screen.getByRole('button')
      button.focus()
      
      await user.keyboard('{Enter}')
      expect(handleClick).toHaveBeenCalled()
    })
  })
})