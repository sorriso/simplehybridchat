// path: tests/unit/components/ContextMenu.test.unit.tsx
// version: 3

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ContextMenu } from '@/components/ui/ContextMenu'

describe('ContextMenu', () => {
  const mockItems = [
    { label: 'Edit', onClick: jest.fn() },
    { label: 'Delete', onClick: jest.fn(), variant: 'danger' as const },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders children', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      expect(screen.getByTestId('trigger')).toBeInTheDocument()
    })

    it('does not show menu initially', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  describe('Context Menu Opening', () => {
    it('shows menu on right click', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      expect(screen.getByRole('menu')).toBeInTheDocument()
    })

    it('shows all menu items', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      expect(screen.getByText('Edit')).toBeInTheDocument()
      expect(screen.getByText('Delete')).toBeInTheDocument()
    })

    it('positions menu at click location', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger, { clientX: 100, clientY: 200 })
      
      const menu = screen.getByRole('menu')
      expect(menu.style.left).toBe('100px')
      expect(menu.style.top).toBe('200px')
    })
  })

  describe('Menu Items', () => {
    it('calls onClick when item is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      // Find the button that contains the text
      const editButton = screen.getByRole('menuitem', { name: /edit/i })
      await user.click(editButton)
      
      expect(mockItems[0].onClick).toHaveBeenCalledTimes(1)
    })

    it('closes menu after item click', async () => {
      const user = userEvent.setup()
      
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      const editButton = screen.getByRole('menuitem', { name: /edit/i })
      await user.click(editButton)
      
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })

    it('applies danger variant styling', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      // Find the Delete button (danger variant)
      const deleteButton = screen.getByRole('menuitem', { name: /delete/i })
      expect(deleteButton).toHaveClass('text-red-600')
    })
  })

  describe('Menu Closing', () => {
    it('closes menu on outside click', async () => {
      const user = userEvent.setup()
      
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      expect(screen.getByRole('menu')).toBeInTheDocument()
      
      await user.click(document.body)
      
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })

    it('closes menu on Escape key', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      expect(screen.getByRole('menu')).toBeInTheDocument()
      
      fireEvent.keyDown(document, { key: 'Escape' })
      
      expect(screen.queryByRole('menu')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has menu role for container', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      expect(screen.getByRole('menu')).toBeInTheDocument()
    })

    it('has menuitem role for menu items', () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      const menuItems = screen.getAllByRole('menuitem')
      expect(menuItems).toHaveLength(2)
    })

    it('is keyboard accessible', async () => {
      render(
        <ContextMenu items={mockItems}>
          <div data-testid="trigger">Right click me</div>
        </ContextMenu>
      )
      
      const trigger = screen.getByTestId('trigger')
      fireEvent.contextMenu(trigger)
      
      // First item should be focused
      const firstItem = screen.getByRole('menuitem', { name: /edit/i })
      
      // Press Enter to activate
      fireEvent.keyDown(document, { key: 'Enter' })
      
      expect(mockItems[0].onClick).toHaveBeenCalled()
    })
  })
})
