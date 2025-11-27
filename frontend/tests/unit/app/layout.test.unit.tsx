// path: tests/unit/app/layout.test.unit.tsx
// version: 1

import { render, screen } from '@testing-library/react';
import RootLayout, { metadata } from '@/app/layout';

// Mock MSWProvider to avoid MSW initialization in tests
jest.mock('@/components/MSWProvider', () => ({
  MSWProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock next/font/google
jest.mock('next/font/google', () => ({
  Inter: () => ({
    className: 'inter-font-class',
  }),
}));

describe('RootLayout', () => {
  describe('Metadata', () => {
    it('exports correct metadata', () => {
      expect(metadata).toEqual({
        title: 'AI Chatbot',
        description: 'Modern AI chatbot interface',
      });
    });
  });

  describe('Component rendering', () => {
    it('renders html with lang attribute', () => {
      const { container } = render(
        <RootLayout>
          <div>Test content</div>
        </RootLayout>
      );

      const html = container.querySelector('html');
      expect(html).toBeInTheDocument();
      expect(html).toHaveAttribute('lang', 'en');
    });

    it('renders body with Inter font className', () => {
      const { container } = render(
        <RootLayout>
          <div>Test content</div>
        </RootLayout>
      );

      const body = container.querySelector('body');
      expect(body).toBeInTheDocument();
      expect(body).toHaveClass('inter-font-class');
    });

    it('wraps children in MSWProvider', () => {
      render(
        <RootLayout>
          <div data-testid="child-content">Test content</div>
        </RootLayout>
      );

      expect(screen.getByTestId('child-content')).toBeInTheDocument();
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    it('renders multiple children correctly', () => {
      render(
        <RootLayout>
          <div>First child</div>
          <div>Second child</div>
        </RootLayout>
      );

      expect(screen.getByText('First child')).toBeInTheDocument();
      expect(screen.getByText('Second child')).toBeInTheDocument();
    });

    it('renders nested structure correctly', () => {
      const { container } = render(
        <RootLayout>
          <div>Content</div>
        </RootLayout>
      );

      const html = container.querySelector('html');
      const body = html?.querySelector('body');
      
      expect(html).toBeInTheDocument();
      expect(body).toBeInTheDocument();
      expect(body?.textContent).toContain('Content');
    });
  });

  describe('Edge cases', () => {
    it('renders with empty children', () => {
      const { container } = render(
        <RootLayout>
          <></>
        </RootLayout>
      );

      const body = container.querySelector('body');
      expect(body).toBeInTheDocument();
    });

    it('renders with null children', () => {
      const { container } = render(
        <RootLayout>
          {null}
        </RootLayout>
      );

      const body = container.querySelector('body');
      expect(body).toBeInTheDocument();
    });

    it('renders with complex nested children', () => {
      render(
        <RootLayout>
          <div>
            <header>Header</header>
            <main>Main content</main>
            <footer>Footer</footer>
          </div>
        </RootLayout>
      );

      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Main content')).toBeInTheDocument();
      expect(screen.getByText('Footer')).toBeInTheDocument();
    });
  });
});