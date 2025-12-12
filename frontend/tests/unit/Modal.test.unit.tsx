// path: tests/unit/components/Modal.test.unit.tsx
// version: 3

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Modal } from '@/components/ui/Modal'

describe('Modal Component', () => {
  const onClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <Modal isOpen={false} onClose={onClose} title="Test Modal">
          Content
        </Modal>
      )
      
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render when isOpen is true', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="Test Modal">
          Content
        </Modal>
      )
      
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should render title', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="Test Modal">
          Content
        </Modal>
      )
      
      expect(screen.getByText('Test Modal')).toBeInTheDocument()
    })

    it('should render children content', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="Test Modal">
          <p>Modal content here</p>
        </Modal>
      )
      
      expect(screen.getByText('Modal content here')).toBeInTheDocument()
    })

    it('should render close button', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="Test Modal">
          Content
        </Modal>
      )
      
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })
  })

  describe('Close Functionality', () => {
    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <Modal isOpen={true} onClose={onClose} title="Test Modal">
          Content
        </Modal>
      )
      
      await user.click(screen.getByRole('button', { name: /close/i }))
      
      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when overlay is clicked', async () => {
      const user = userEvent.setup()
      
      const { container } = render(
        <Modal isOpen={true} onClose={onClose} title="Test Modal">
          Content
        </Modal>
      )
      
      const overlay = container.querySelector('[data-overlay="true"]')
      if (overlay) {
        await user.click(overlay)
        expect(onClose).toHaveBeenCalledTimes(1)
      }
    })

    it('should call onClose when Escape key is pressed', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="Test Modal">
          Content
        </Modal>
      )
      
      fireEvent.keyDown(document, { key: 'Escape' })
      
      expect(onClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Sizes', () => {
    it('should apply small size class', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={onClose} title="Test" size="sm">
          Content
        </Modal>
      )
      
      const dialog = container.querySelector('[role="dialog"]')
      // Small size uses max-w-md
      expect(dialog?.className).toContain('max-w-md')
    })

    it('should apply medium size class', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={onClose} title="Test" size="md">
          Content
        </Modal>
      )
      
      const dialog = container.querySelector('[role="dialog"]')
      // Medium size uses max-w-lg
      expect(dialog?.className).toContain('max-w-lg')
    })

    it('should apply large size class', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={onClose} title="Test" size="lg">
          Content
        </Modal>
      )
      
      const dialog = container.querySelector('[role="dialog"]')
      // Large size uses max-w-2xl
      expect(dialog?.className).toContain('max-w-2xl')
    })
  })

  describe('Accessibility', () => {
    it('should have dialog role', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="Test">
          Content
        </Modal>
      )
      
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should have aria-modal attribute', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="Test">
          Content
        </Modal>
      )
      
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
    })

    it('should be labelled by title', () => {
      render(
        <Modal isOpen={true} onClose={onClose} title="My Modal Title">
          Content
        </Modal>
      )
      
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-labelledby')
    })
  })

  describe('Overlay', () => {
    it('should render overlay backdrop', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={onClose} title="Test">
          Content
        </Modal>
      )
      
      const overlay = container.querySelector('[data-overlay="true"]')
      expect(overlay).toBeInTheDocument()
    })

    it('should have semi-transparent background', () => {
      const { container } = render(
        <Modal isOpen={true} onClose={onClose} title="Test">
          Content
        </Modal>
      )
      
      const overlay = container.querySelector('[data-overlay="true"]')
      expect(overlay?.className).toContain('bg-black')
      expect(overlay?.className).toContain('bg-opacity')
    })
  })
})
