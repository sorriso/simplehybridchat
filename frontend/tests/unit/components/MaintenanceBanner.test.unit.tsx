// path: frontend/tests/unit/components/MaintenanceBanner.test.unit.tsx
// version: 4 - FIXED: Import React BEFORE mocks that use JSX

import React from 'react';

// Mock dependencies AFTER React import (mocks use JSX)
jest.mock('@/components/ui/Button', () => ({
  Button: ({ children, onClick, variant, size, className }: any) => (
    <button 
      onClick={onClick}
      data-variant={variant}
      data-size={size}
      className={className}
    >
      {children}
    </button>
  ),
}));

jest.mock('@/components/ui/IconButton', () => ({
  IconButton: ({ icon: Icon, onClick, size, title }: any) => (
    <button 
      onClick={onClick}
      data-size={size}
      title={title}
      data-testid="icon-button"
    >
      <Icon />
    </button>
  ),
}));

jest.mock('lucide-react', () => ({
  AlertTriangle: () => <svg data-testid="alert-triangle-icon" />,
  X: () => <svg data-testid="x-icon" />,
}));

import { render, screen, fireEvent } from '@testing-library/react';
import { MaintenanceBanner } from '@/components/maintenance/MaintenanceBanner';

describe('MaintenanceBanner', () => {
  const mockOnDisable = jest.fn();
  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders maintenance warning message', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} />);

      expect(screen.getByText(/MAINTENANCE MODE ACTIVE/i)).toBeInTheDocument();
      expect(screen.getByText(/Only root users can access the application/i)).toBeInTheDocument();
    });

    it('renders AlertTriangle icon', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} />);

      expect(screen.getByTestId('alert-triangle-icon')).toBeInTheDocument();
    });

    it('renders disable button with correct props', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} />);

      const disableButton = screen.getByText('Disable Maintenance Mode');
      expect(disableButton).toBeInTheDocument();
      expect(disableButton).toHaveAttribute('data-variant', 'secondary');
      expect(disableButton).toHaveAttribute('data-size', 'sm');
      expect(disableButton).toHaveClass('whitespace-nowrap');
    });

    it('renders with yellow theme styling', () => {
      const { container } = render(<MaintenanceBanner onDisable={mockOnDisable} />);

      const banner = container.querySelector('.bg-yellow-50');
      expect(banner).toBeInTheDocument();
      expect(banner).toHaveClass('border-b', 'border-yellow-200');
    });
  });

  describe('Dismiss functionality', () => {
    it('renders dismiss button when onDismiss is provided', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByTestId('icon-button');
      expect(dismissButton).toBeInTheDocument();
      expect(dismissButton).toHaveAttribute('title', 'Dismiss banner');
      expect(dismissButton).toHaveAttribute('data-size', 'sm');
    });

    it('does not render dismiss button when onDismiss is not provided', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} />);

      expect(screen.queryByTestId('icon-button')).not.toBeInTheDocument();
    });

    it('calls onDismiss when dismiss button is clicked', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} onDismiss={mockOnDismiss} />);

      const dismissButton = screen.getByTestId('icon-button');
      fireEvent.click(dismissButton);

      expect(mockOnDismiss).toHaveBeenCalledTimes(1);
    });

    it('renders X icon in dismiss button', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} onDismiss={mockOnDismiss} />);

      expect(screen.getByTestId('x-icon')).toBeInTheDocument();
    });
  });

  describe('Disable functionality', () => {
    it('calls onDisable when disable button is clicked', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} />);

      const disableButton = screen.getByText('Disable Maintenance Mode');
      fireEvent.click(disableButton);

      expect(mockOnDisable).toHaveBeenCalledTimes(1);
    });

    it('calls onDisable multiple times when clicked multiple times', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} />);

      const disableButton = screen.getByText('Disable Maintenance Mode');
      fireEvent.click(disableButton);
      fireEvent.click(disableButton);
      fireEvent.click(disableButton);

      expect(mockOnDisable).toHaveBeenCalledTimes(3);
    });
  });

  describe('Component structure', () => {
    it('renders with correct container structure', () => {
      const { container } = render(<MaintenanceBanner onDisable={mockOnDisable} />);

      expect(container.querySelector('.max-w-7xl')).toBeInTheDocument();
      expect(container.querySelector('.mx-auto')).toBeInTheDocument();
      expect(container.querySelector('.px-4')).toBeInTheDocument();
      expect(container.querySelector('.py-3')).toBeInTheDocument();
    });

    it('renders warning message and actions in flex layout', () => {
      const { container } = render(<MaintenanceBanner onDisable={mockOnDisable} />);

      const flexContainer = container.querySelector('.flex.items-center.justify-between');
      expect(flexContainer).toBeInTheDocument();
    });

    it('renders with both callbacks', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} onDismiss={mockOnDismiss} />);

      expect(screen.getByText('Disable Maintenance Mode')).toBeInTheDocument();
      expect(screen.getByTestId('icon-button')).toBeInTheDocument();
    });
  });

  describe('Edge cases', () => {
    it('renders correctly when onDismiss is undefined', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} onDismiss={undefined} />);

      expect(screen.getByText('Disable Maintenance Mode')).toBeInTheDocument();
      expect(screen.queryByTestId('icon-button')).not.toBeInTheDocument();
    });

    it('does not call onDismiss when not provided', () => {
      render(<MaintenanceBanner onDisable={mockOnDisable} />);

      // Should not crash when trying to interact
      const disableButton = screen.getByText('Disable Maintenance Mode');
      fireEvent.click(disableButton);

      expect(mockOnDisable).toHaveBeenCalledTimes(1);
    });
  });
});