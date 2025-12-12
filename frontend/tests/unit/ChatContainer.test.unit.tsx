// path: tests/unit/components/ChatContainer.test.unit.tsx
// version: 1

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { useSettings } from '@/lib/hooks/useSettings';

// Mock ChatInterface
jest.mock('@/components/chat/ChatInterface', () => ({
  ChatInterface: ({ conversationId, promptCustomization }: any) => (
    <div data-testid="chat-interface">
      <div data-testid="conversation-id">{conversationId || 'null'}</div>
      <div data-testid="prompt-customization">{promptCustomization || 'none'}</div>
    </div>
  ),
}));

// Mock useSettings hook
jest.mock('@/lib/hooks/useSettings');

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

  it('renders container with correct structure', () => {
    mockUseSettings.mockReturnValue({
      settings: null,
      updateSettings: jest.fn(),
      loading: false,
    });

    const { container } = render(<ChatContainer currentConversationId="conv-123" />);

    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('h-full', 'flex', 'flex-col');
  });
});