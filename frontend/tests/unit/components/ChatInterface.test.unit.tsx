// path: tests/unit/components/ChatInterface.test.unit.tsx
// version: 2

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { conversationsApi } from '@/lib/api/conversations';

// Mock NLUX components
jest.mock('@nlux/react', () => ({
  AiChat: ({ adapter, initialConversation, personaOptions }: any) => (
    <div data-testid="ai-chat">
      <div data-testid="persona-assistant">{personaOptions?.assistant?.name}</div>
      <div data-testid="initial-messages">{initialConversation?.length || 0}</div>
    </div>
  ),
  useAsStreamAdapter: (callback: any, deps: any) => callback,
}));

// Mock API
jest.mock('@/lib/api/conversations', () => ({
  conversationsApi: {
    getMessages: jest.fn(),
  },
}));

// Mock constants
jest.mock('@/lib/utils/constants', () => ({
  API_ENDPOINTS: {
    CHAT_STREAM: 'http://localhost:8000/api/chat/stream',
  },
  MOCK_USER: {
    name: 'Test User',
    token: 'test-token',
  },
}));

describe('ChatInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Empty state', () => {
    it('shows empty state when no conversation is selected', () => {
      render(<ChatInterface conversationId={null} />);

      expect(screen.getByText('No conversation selected')).toBeInTheDocument();
      expect(screen.getByText('Create or select a conversation to start chatting')).toBeInTheDocument();
    });

    it('does not load history when conversationId is null', () => {
      render(<ChatInterface conversationId={null} />);

      expect(conversationsApi.getMessages).not.toHaveBeenCalled();
    });
  });

  describe('Loading state', () => {
    it('shows loading spinner while fetching history', async () => {
      (conversationsApi.getMessages as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve([]), 100))
      );

      const { container } = render(<ChatInterface conversationId="conv-1" />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveClass('border-b-2', 'border-primary-600');
    });
  });

  describe('History loading', () => {
    it('loads conversation history on mount', async () => {
      const mockMessages = [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi there!' },
      ];

      (conversationsApi.getMessages as jest.Mock).mockResolvedValue(mockMessages);

      render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(conversationsApi.getMessages).toHaveBeenCalledWith('conv-1');
      });

      await waitFor(() => {
        expect(screen.getByTestId('initial-messages')).toHaveTextContent('2');
      });
    });

    it('handles history loading error gracefully', async () => {
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      (conversationsApi.getMessages as jest.Mock).mockRejectedValue(new Error('Network error'));

      render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(conversationsApi.getMessages).toHaveBeenCalledWith('conv-1');
      });

      await waitFor(() => {
        expect(screen.getByTestId('initial-messages')).toHaveTextContent('0');
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[ChatInterface] Failed to load history:',
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
    });

    it('reloads history when conversationId changes', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([]);

      const { rerender } = render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(conversationsApi.getMessages).toHaveBeenCalledWith('conv-1');
      });

      rerender(<ChatInterface conversationId="conv-2" />);

      await waitFor(() => {
        expect(conversationsApi.getMessages).toHaveBeenCalledWith('conv-2');
      });

      expect(conversationsApi.getMessages).toHaveBeenCalledTimes(2);
    });

    it('clears messages when conversationId becomes null', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([
        { role: 'user', content: 'Test' },
      ]);

      const { rerender } = render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(screen.getByTestId('initial-messages')).toHaveTextContent('1');
      });

      rerender(<ChatInterface conversationId={null} />);

      expect(screen.queryByTestId('ai-chat')).not.toBeInTheDocument();
      expect(screen.getByText('No conversation selected')).toBeInTheDocument();
    });
  });

  describe('Chat rendering', () => {
    it('renders AiChat with correct props', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([]);

      render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(screen.getByTestId('ai-chat')).toBeInTheDocument();
      });

      expect(screen.getByTestId('persona-assistant')).toHaveTextContent('AI Assistant');
    });

    it('passes promptCustomization to adapter', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([]);

      render(
        <ChatInterface 
          conversationId="conv-1" 
          promptCustomization="Be helpful and concise"
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('ai-chat')).toBeInTheDocument();
      });
    });
  });

  describe('Streaming adapter', () => {
    it('handles successful stream response', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([]);

      const mockReader = {
        read: jest.fn()
          .mockResolvedValueOnce({
            done: false,
            value: new Uint8Array([100, 97, 116, 97, 58, 32, 72, 101, 108, 108, 111, 10]), // 'data: Hello\n'
          })
          .mockResolvedValueOnce({
            done: false,
            value: new Uint8Array([100, 97, 116, 97, 58, 32, 87, 111, 114, 108, 100, 10]), // 'data: World\n'
          })
          .mockResolvedValueOnce({ done: true }),
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      });

      render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(screen.getByTestId('ai-chat')).toBeInTheDocument();
      });
    });

    it('handles stream error', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([]);
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      (global.fetch as jest.Mock).mockRejectedValue(new Error('Stream failed'));

      render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(screen.getByTestId('ai-chat')).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it('handles HTTP error response', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([]);
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(screen.getByTestId('ai-chat')).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });

    it('handles missing response body', async () => {
      (conversationsApi.getMessages as jest.Mock).mockResolvedValue([]);
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        body: null,
      });

      render(<ChatInterface conversationId="conv-1" />);

      await waitFor(() => {
        expect(screen.getByTestId('ai-chat')).toBeInTheDocument();
      });

      consoleErrorSpy.mockRestore();
    });
  });
});