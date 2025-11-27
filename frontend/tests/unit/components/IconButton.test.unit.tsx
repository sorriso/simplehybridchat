// path: tests/unit/components/IconButton.test.unit.tsx
// version: 1

import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { IconButton } from '@/components/ui/IconButton'
import { Settings, Trash2 } from 'lucide-react'

describe('IconButton', () => {
  describe('Rendering', () => {
    it('renders with icon', () => {
      render(<IconButton icon={Settings} aria-label="Settings" />)
      
      const button = screen.getByRole('button', { name: /settings/i })
      expect(button).toBeInTheDocument()
      expect(button.querySelector('svg')).toBeInTheDocument()
    })

    it('renders with default size (md)', () => {
      render(<IconButton icon={Settings} aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('p-2') // md size
    })

    it('renders with small size', () => {
      render(<IconButton icon={Settings} size="sm" aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('p-1') // sm size
    })

    it('renders with large size', () => {
      render(<IconButton icon={Settings} size="lg" aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('p-3') // lg size
    })

    it('renders with default variant (ghost)', () => {
      render(<IconButton icon={Settings} aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('text-gray-600')
    })

    it('renders with danger variant', () => {
      render(<IconButton icon={Trash2} variant="danger" aria-label="Delete" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('text-red-600')
    })

    it('applies custom className', () => {
      render(<IconButton icon={Settings} className="custom-class" aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })
  })

  describe('Click handling', () => {
    it('calls onClick when clicked', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()
      
      render(<IconButton icon={Settings} onClick={handleClick} aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when disabled', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()
      
      render(<IconButton icon={Settings} onClick={handleClick} disabled aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Disabled state', () => {
    it('applies disabled styles', () => {
      render(<IconButton icon={Settings} disabled aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(button).toHaveClass('disabled:opacity-50')
    })

    it('is not clickable when disabled', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()
      
      render(<IconButton icon={Settings} onClick={handleClick} disabled aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('has accessible role', () => {
      render(<IconButton icon={Settings} aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })

    it('supports aria-label', () => {
      render(<IconButton icon={Settings} aria-label="Open settings" />)
      
      const button = screen.getByRole('button', { name: /open settings/i })
      expect(button).toBeInTheDocument()
    })

    it('has focus styles', () => {
      render(<IconButton icon={Settings} aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2')
    })

    it('can receive focus', async () => {
      const user = userEvent.setup()
      render(<IconButton icon={Settings} aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      await user.tab()
      
      expect(button).toHaveFocus()
    })

    it('cannot receive focus when disabled', () => {
      render(<IconButton icon={Settings} disabled aria-label="Settings" />)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })
  })

  describe('Icon size variants', () => {
    it('renders small icon for sm size', () => {
      const { container } = render(<IconButton icon={Settings} size="sm" aria-label="Settings" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('width', '16')
      expect(svg).toHaveAttribute('height', '16')
    })

    it('renders medium icon for md size', () => {
      const { container } = render(<IconButton icon={Settings} size="md" aria-label="Settings" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('width', '20')
      expect(svg).toHaveAttribute('height', '20')
    })

    it('renders large icon for lg size', () => {
      const { container } = render(<IconButton icon={Settings} size="lg" aria-label="Settings" />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveAttribute('width', '24')
      expect(svg).toHaveAttribute('height', '24')
    })
  })

  describe('HTML attributes', () => {
    it('forwards ref', () => {
      const ref = React.createRef<HTMLButtonElement>()
      render(<IconButton icon={Settings} ref={ref} aria-label="Settings" />)
      
      expect(ref.current).toBeInstanceOf(HTMLButtonElement)
    })

    it('supports additional props', () => {
      render(
        <IconButton 
          icon={Settings} 
          aria-label="Settings" 
          data-testid="custom-button"
          title="Settings button"
        />
      )
      
      const button = screen.getByTestId('custom-button')
      expect(button).toHaveAttribute('title', 'Settings button')
    })
  })
})