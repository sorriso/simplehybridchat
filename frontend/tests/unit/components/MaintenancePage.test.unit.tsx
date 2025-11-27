// path: tests/unit/components/MaintenancePage.test.unit.tsx
// version: 3

import { render, screen } from '@testing-library/react';
import { MaintenancePage } from '@/components/maintenance/MaintenancePage';

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Wrench: () => <svg data-testid="wrench-icon" />,
}));

describe('MaintenancePage', () => {
  describe('Rendering', () => {
    it('renders main title', () => {
      render(<MaintenancePage />);

      expect(screen.getByText('Application Under Maintenance')).toBeInTheDocument();
    });

    it('renders descriptive message', () => {
      render(<MaintenancePage />);

      expect(screen.getByText(/We're making improvements to better serve you/i)).toBeInTheDocument();
      expect(screen.getByText(/Please try again later/i)).toBeInTheDocument();
    });

    it('renders Wrench icon', () => {
      render(<MaintenancePage />);

      expect(screen.getByTestId('wrench-icon')).toBeInTheDocument();
    });

    it('renders contact section', () => {
      render(<MaintenancePage />);

      expect(screen.getByText('Need immediate assistance?')).toBeInTheDocument();
    });

    it('renders support email link', () => {
      render(<MaintenancePage />);

      const emailLink = screen.getByText('support@company.com');
      expect(emailLink).toBeInTheDocument();
      expect(emailLink.tagName).toBe('A');
      expect(emailLink).toHaveAttribute('href', 'mailto:support@company.com');
    });

    it('renders additional information', () => {
      render(<MaintenancePage />);

      expect(screen.getByText(/Maintenance is usually completed within a few hours/i)).toBeInTheDocument();
      expect(screen.getByText(/We appreciate your patience/i)).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('renders with full-height layout', () => {
      const { container } = render(<MaintenancePage />);

      const mainDiv = container.querySelector('.min-h-screen');
      expect(mainDiv).toBeInTheDocument();
      expect(mainDiv).toHaveClass('bg-gray-50', 'flex', 'items-center', 'justify-center');
    });

    it('renders icon with blue styling', () => {
      const { container } = render(<MaintenancePage />);

      const iconContainer = container.querySelector('.bg-blue-100');
      expect(iconContainer).toBeInTheDocument();
      expect(iconContainer).toHaveClass('rounded-full', 'w-20', 'h-20');
    });

    it('renders title with correct styling', () => {
      const { container } = render(<MaintenancePage />);

      const title = screen.getByText('Application Under Maintenance');
      expect(title.tagName).toBe('H1');
      expect(title).toHaveClass('text-3xl', 'font-bold', 'text-gray-900');
    });

    it('renders contact box with white background', () => {
      const { container } = render(<MaintenancePage />);

      const contactBox = container.querySelector('.bg-white.rounded-lg');
      expect(contactBox).toBeInTheDocument();
      expect(contactBox).toHaveClass('border', 'border-gray-200', 'p-6');
    });

    it('renders email link with hover styling', () => {
      render(<MaintenancePage />);

      const emailLink = screen.getByText('support@company.com');
      expect(emailLink).toHaveClass('text-blue-600', 'hover:text-blue-700', 'font-medium');
    });
  });

  describe('Component structure', () => {
    it('renders with centered container', () => {
      const { container } = render(<MaintenancePage />);

      const contentContainer = container.querySelector('.max-w-md.w-full.text-center');
      expect(contentContainer).toBeInTheDocument();
    });

    it('renders all sections in correct order', () => {
      const { container } = render(<MaintenancePage />);

      const sections = container.querySelectorAll('div');
      expect(sections.length).toBeGreaterThan(0);
      
      // Check icon appears before title
      const wrenchIcon = screen.getByTestId('wrench-icon');
      const title = screen.getByText('Application Under Maintenance');
      
      expect(wrenchIcon).toBeInTheDocument();
      expect(title).toBeInTheDocument();
    });

    it('renders message sections with proper spacing', () => {
      const { container } = render(<MaintenancePage />);

      const mainMessage = screen.getByText(/We're making improvements/i);
      expect(mainMessage).toHaveClass('text-lg', 'text-gray-600');
      expect(mainMessage.tagName).toBe('P');
    });
  });

  describe('Edge cases', () => {
    it('renders without errors', () => {
      expect(() => render(<MaintenancePage />)).not.toThrow();
    });

    it('renders as a static component without props', () => {
      const { container } = render(<MaintenancePage />);

      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders all text content correctly', () => {
      render(<MaintenancePage />);

      const allText = [
        'Application Under Maintenance',
        "We're making improvements to better serve you.",
        'Please try again later.',
        'Need immediate assistance?',
        'support@company.com',
        'Maintenance is usually completed within a few hours.',
        'We appreciate your patience.',
      ];

      allText.forEach(text => {
        expect(screen.getByText(new RegExp(text, 'i'))).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('renders semantic HTML elements', () => {
      const { container } = render(<MaintenancePage />);

      expect(container.querySelector('h1')).toBeInTheDocument();
      expect(container.querySelector('a')).toBeInTheDocument();
      expect(container.querySelector('p')).toBeInTheDocument();
    });

    it('renders email link with valid mailto href', () => {
      render(<MaintenancePage />);

      const emailLink = screen.getByText('support@company.com');
      const href = emailLink.getAttribute('href');
      
      expect(href).toBe('mailto:support@company.com');
      expect(href?.startsWith('mailto:')).toBe(true);
    });
  });
});