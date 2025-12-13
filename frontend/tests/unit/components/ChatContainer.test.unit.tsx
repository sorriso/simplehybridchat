// path: frontend/tests/unit/components/ChatContainer.test.unit.tsx
// version: 4 - FIXED: Import React before mocks, proper mock structure

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock ChatInterface AFTER React import
jest.mock('@/components/chat/ChatInterface', () => ({
  ChatInterface: ({ conversationId, promptCustomization, onMessageSent }: any) => (
    <div data-testid="chat-interface">
      <div data-testid="conversation-id">{conversationId ?? 'null'}</div>
      <div data-testid="prompt-customization">{promptCustomization ?? 'none'}</div>
      {onMessageSent && <button onClick={onMessageSent} data-testid="send-button">Send</button>}
    </div>
  ),
}));

// Mock useSettings hook
jest.mock('@/lib/hooks/useSettings');

import { ChatContainer } from '@/components/chat/ChatContainer';
import { useSettings } from '@/lib/hooks/useSettings';

describe('ChatContainer', () => {
  const mockUseSettings = useSettings as jest.MockedFunction<typeof useSettings>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders ChatInterface with conversationId', () => {
    mockUseSettings.mockReturnValue({
      settings: null,
      updateSettings: jest.fn(),
      loading: false,
    });

    render(<ChatContainer currentConversationId="conv-123" />);

    expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    expect(screen.getByTestId('conversation-id')).toHaveTextContent('conv-123');
  });

  it('renders ChatInterface with null conversationId', () => {
    mockUseSettings.mockReturnValue({
      settings: null,
      updateSettings: jest.fn(),
      loading: false,
    });

    render(<ChatContainer currentConversationId={null} />);

    expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    expect(screen.getByTestId('conversation-id')).toHaveTextContent('null');
  });

  it('passes promptCustomization from settings', () => {
    mockUseSettings.mockReturnValue({
      settings: {
        promptCustomization: 'Be concise and helpful',
      },
      updateSettings: jest.fn(),
      loading: false,
    });

    render(<ChatContainer currentConversationId="conv-123" />);

    expect(screen.getByTestId('prompt-customization')).toHaveTextContent('Be concise and helpful');
  });

  it('passes undefined promptCustomization when settings is null', () => {
    mockUseSettings.mockReturnValue({
      settings: null,
      updateSettings: jest.fn(),
      loading: false,
    });

    render(<ChatContainer currentConversationId="conv-123" />);

    expect(screen.getByTestId('prompt-customization')).toHaveTextContent('none');
  });

  it('passes undefined promptCustomization when promptCustomization is not set', () => {
    mockUseSettings.mockReturnValue({
      settings: {},
      updateSettings: jest.fn(),
      loading: false,
    });

    render(<ChatContainer currentConversationId="conv-123" />);

    expect(screen.getByTestId('prompt-customization')).toHaveTextContent('none');
  });

  it('updates ChatInterface when conversationId changes', () => {
    mockUseSettings.mockReturnValue({
      settings: null,
      updateSettings: jest.fn(),
      loading: false,
    });

    const { rerender } = render(<ChatContainer currentConversationId="conv-1" />);

    expect(screen.getByTestId('conversation-id')).toHaveTextContent('conv-1');

    rerender(<ChatContainer currentConversationId="conv-2" />);

    expect(screen.getByTestId('conversation-id')).toHaveTextContent('conv-2');
  });

  it('passes onMessageSent callback to ChatInterface', () => {
    mockUseSettings.mockReturnValue({
      settings: null,
      updateSettings: jest.fn(),
      loading: false,
    });

    const mockOnMessageSent = jest.fn();
    render(
      <ChatContainer 
        currentConversationId="conv-123" 
        onMessageSent={mockOnMessageSent}
      />
    );

    const sendButton = screen.getByTestId('send-button');
    sendButton.click();

    expect(mockOnMessageSent).toHaveBeenCalledTimes(1);
  });
});