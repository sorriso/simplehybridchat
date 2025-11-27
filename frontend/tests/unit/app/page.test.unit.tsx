// path: tests/unit/app/page.test.unit.tsx
// version: 2

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Home from '@/app/page';
import { useAuth } from '@/lib/hooks/useAuth';
import { useConversations } from '@/lib/hooks/useConversations';

// Mock all components
jest.mock('@/components/sidebar/Sidebar', () => ({
  Sidebar: ({ onSettingsClick, onUploadClick }: any) => (
    <div data-testid="sidebar">
      <button onClick={onSettingsClick}>Settings</button>
      <button onClick={onUploadClick}>Upload</button>
    </div>
  ),
}));

jest.mock('@/components/chat/ChatContainer', () => ({
  ChatContainer: ({ currentConversationId }: any) => (
    <div data-testid="chat-container">
      Conversation: {currentConversationId || 'none'}
    </div>
  ),
}));

jest.mock('@/components/upload/FileUploadPanel', () => ({
  FileUploadPanel: ({ isOpen, onClose }: any) => (
    isOpen ? (
      <div data-testid="upload-panel">
        <button onClick={onClose}>Close Upload</button>
      </div>
    ) : null
  ),
}));

jest.mock('@/components/settings/SettingsPanel', () => ({
  SettingsPanel: ({ isOpen, onClose }: any) => (
    isOpen ? (
      <div data-testid="settings-panel">
        <button onClick={onClose}>Close Settings</button>
      </div>
    ) : null
  ),
}));

jest.mock('@/components/auth/LoginForm', () => ({
  LoginForm: ({ onLogin, loading, error }: any) => (
    <div data-testid="login-form">
      <button onClick={() => onLogin('user', 'pass')}>Login</button>
      {loading && <span>Logging in...</span>}
      {error && <span>Error: {error}</span>}
    </div>
  ),
}));

// Mock hooks
jest.mock('@/lib/hooks/useAuth');
jest.mock('@/lib/hooks/useConversations');

describe('Home Page', () => {
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
  const mockUseConversations = useConversations as jest.MockedFunction<typeof useConversations>;

  const mockConversationsReturn = {
    conversations: [],
    groups: [],
    currentConversationId: null,
    createConversation: jest.fn(),
    deleteConversation: jest.fn(),
    updateConversation: jest.fn(),
    createGroup: jest.fn(),
    deleteGroup: jest.fn(),
    setCurrentConversationId: jest.fn(),
    loading: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseConversations.mockReturnValue(mockConversationsReturn);
  });

  describe('Loading state', () => {
    it('shows loading spinner when auth is loading', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: true,
        login: jest.fn(),
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: null,
      });

      const { container } = render(<Home />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('border-b-2', 'border-primary-600');
    });
  });

  describe('Login state', () => {
    it('shows login form when user is not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: jest.fn(),
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: null,
      });

      render(<Home />);

      expect(screen.getByTestId('login-form')).toBeInTheDocument();
    });

    it('calls login when login button is clicked', () => {
      const mockLogin = jest.fn();
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: mockLogin,
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: null,
      });

      render(<Home />);

      fireEvent.click(screen.getByText('Login'));

      expect(mockLogin).toHaveBeenCalledWith('user', 'pass');
    });

    it('displays login error when present', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: jest.fn(),
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: 'Invalid credentials',
      });

      render(<Home />);

      expect(screen.getByText('Error: Invalid credentials')).toBeInTheDocument();
    });
  });

  describe('Authenticated state', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', username: 'testuser', role: 'user', disabled: false },
        loading: false,
        login: jest.fn(),
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: null,
      });
    });

    it('renders main application when authenticated', () => {
      render(<Home />);

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('chat-container')).toBeInTheDocument();
      expect(screen.getByText('AI Assistant')).toBeInTheDocument();
    });

    it('passes currentConversationId to ChatContainer', () => {
      mockUseConversations.mockReturnValue({
        ...mockConversationsReturn,
        currentConversationId: 'conv-123',
      });

      render(<Home />);

      expect(screen.getByText('Conversation: conv-123')).toBeInTheDocument();
    });

    it('passes conversations data to Sidebar', () => {
      const conversations = [
        { id: 'c1', title: 'Chat 1', createdAt: new Date(), userId: '1' },
      ];
      const groups = [
        { id: 'g1', name: 'Group 1', conversationIds: [] },
      ];

      mockUseConversations.mockReturnValue({
        ...mockConversationsReturn,
        conversations,
        groups,
      });

      render(<Home />);

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    });
  });

  describe('Upload panel', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', username: 'testuser', role: 'user', disabled: false },
        loading: false,
        login: jest.fn(),
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: null,
      });
    });

    it('opens upload panel when upload button is clicked', () => {
      render(<Home />);

      expect(screen.queryByTestId('upload-panel')).not.toBeInTheDocument();

      fireEvent.click(screen.getByText('Upload'));

      expect(screen.getByTestId('upload-panel')).toBeInTheDocument();
    });

    it('closes upload panel when close button is clicked', () => {
      render(<Home />);

      fireEvent.click(screen.getByText('Upload'));
      expect(screen.getByTestId('upload-panel')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Close Upload'));
      expect(screen.queryByTestId('upload-panel')).not.toBeInTheDocument();
    });

    it('shows overlay when upload panel is open', () => {
      const { container } = render(<Home />);

      fireEvent.click(screen.getByText('Upload'));

      const overlay = container.querySelector('.fixed.inset-0.bg-black.bg-opacity-30');
      expect(overlay).toBeInTheDocument();
    });

    it('closes upload panel when clicking overlay', () => {
      const { container } = render(<Home />);

      fireEvent.click(screen.getByText('Upload'));
      expect(screen.getByTestId('upload-panel')).toBeInTheDocument();

      const overlay = container.querySelector('.fixed.inset-0.bg-black.bg-opacity-30');
      fireEvent.click(overlay!);

      expect(screen.queryByTestId('upload-panel')).not.toBeInTheDocument();
    });
  });

  describe('Settings panel', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', username: 'testuser', role: 'user', disabled: false },
        loading: false,
        login: jest.fn(),
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: null,
      });
    });

    it('opens settings panel when settings button is clicked', () => {
      render(<Home />);

      expect(screen.queryByTestId('settings-panel')).not.toBeInTheDocument();

      fireEvent.click(screen.getByText('Settings'));

      expect(screen.getByTestId('settings-panel')).toBeInTheDocument();
    });

    it('closes settings panel when close button is clicked', () => {
      render(<Home />);

      fireEvent.click(screen.getByText('Settings'));
      expect(screen.getByTestId('settings-panel')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Close Settings'));
      expect(screen.queryByTestId('settings-panel')).not.toBeInTheDocument();
    });

    it('shows overlay when settings panel is open', () => {
      const { container } = render(<Home />);

      fireEvent.click(screen.getByText('Settings'));

      const overlay = container.querySelector('.fixed.inset-0.bg-black.bg-opacity-30');
      expect(overlay).toBeInTheDocument();
    });

    it('closes settings panel when clicking overlay', () => {
      const { container } = render(<Home />);

      fireEvent.click(screen.getByText('Settings'));
      expect(screen.getByTestId('settings-panel')).toBeInTheDocument();

      const overlay = container.querySelector('.fixed.inset-0.bg-black.bg-opacity-30');
      fireEvent.click(overlay!);

      expect(screen.queryByTestId('settings-panel')).not.toBeInTheDocument();
    });
  });

  describe('Both panels', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: { id: '1', username: 'testuser', role: 'user', disabled: false },
        loading: false,
        login: jest.fn(),
        logout: jest.fn(),
        forceLogout: jest.fn(),
        error: null,
      });
    });

    it('can open both panels and overlay closes both', () => {
      const { container } = render(<Home />);

      fireEvent.click(screen.getByText('Upload'));
      fireEvent.click(screen.getByText('Settings'));

      expect(screen.getByTestId('upload-panel')).toBeInTheDocument();
      expect(screen.getByTestId('settings-panel')).toBeInTheDocument();

      const overlay = container.querySelector('.fixed.inset-0.bg-black.bg-opacity-30');
      fireEvent.click(overlay!);

      expect(screen.queryByTestId('upload-panel')).not.toBeInTheDocument();
      expect(screen.queryByTestId('settings-panel')).not.toBeInTheDocument();
    });
  });
});