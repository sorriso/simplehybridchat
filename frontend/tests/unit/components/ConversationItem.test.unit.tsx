// path: tests/unit/components/ConversationItem.test.unit.tsx
// version: 2

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ConversationItem } from '@/components/sidebar/ConversationItem';
import type { Conversation } from '@/types/conversation';

// Mock ContextMenu
jest.mock('@/components/ui/ContextMenu', () => ({
  ContextMenu: ({ children, items }: any) => (
    <div data-testid="context-menu">
      {children}
      {items.map((item: any, idx: number) => (
        <button key={idx} onClick={item.onClick} data-variant={item.variant}>
          {item.label}
        </button>
      ))}
    </div>
  ),
}));

describe('ConversationItem', () => {
  const mockConversation: Conversation = {
    id: 'conv-123',
    title: 'Test Conversation',
    userId: 'user-1',
    messageCount: 5,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  const defaultProps = {
    conversation: mockConversation,
    isActive: false,
    onClick: jest.fn(),
    onDelete: jest.fn(),
    onRename: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    console.log = jest.fn();
  });

  describe('Rendering', () => {
    it('should render conversation title and message count', () => {
      render(<ConversationItem {...defaultProps} />);

      expect(screen.getByText('Test Conversation')).toBeInTheDocument();
      expect(screen.getByText('5 messages')).toBeInTheDocument();
    });

    it('should render "New Conversation" when title is empty', () => {
      const conv = { ...mockConversation, title: '' };
      render(<ConversationItem {...defaultProps} conversation={conv} />);

      expect(screen.getByText('New Conversation')).toBeInTheDocument();
    });

    it('should apply active styles when isActive is true', () => {
      const { container } = render(
        <ConversationItem {...defaultProps} isActive={true} />
      );

      const button = container.querySelector('button');
      expect(button).toHaveClass('bg-primary-100', 'border-primary-600');
    });

    it('should apply inactive styles when isActive is false', () => {
      const { container } = render(
        <ConversationItem {...defaultProps} isActive={false} />
      );

      const button = container.querySelector('button');
      expect(button).toHaveClass('border-transparent', 'text-gray-700');
    });

    it('should apply dragging opacity when isDragging is true', () => {
      const { container } = render(
        <ConversationItem {...defaultProps} isDragging={true} />
      );

      const draggableDiv = container.querySelector('[draggable="true"]');
      expect(draggableDiv).toHaveClass('opacity-50');
    });

    it('should not apply dragging opacity when isDragging is false', () => {
      const { container } = render(
        <ConversationItem {...defaultProps} isDragging={false} />
      );

      const draggableDiv = container.querySelector('[draggable="true"]');
      expect(draggableDiv).not.toHaveClass('opacity-50');
    });
  });

  describe('Click handling', () => {
    it('should call onClick when conversation is clicked', () => {
      render(<ConversationItem {...defaultProps} />);

      fireEvent.click(screen.getByText('Test Conversation'));

      expect(defaultProps.onClick).toHaveBeenCalledTimes(1);
    });

    it('should log conversation id when clicked', () => {
      render(<ConversationItem {...defaultProps} />);

      fireEvent.click(screen.getByText('Test Conversation'));

      expect(console.log).toHaveBeenCalledWith(
        '[ConversationItem] Clicked:',
        'conv-123'
      );
    });
  });

  describe('Context menu', () => {
    it('should render rename and delete options', () => {
      render(<ConversationItem {...defaultProps} />);

      expect(screen.getByText('Rename')).toBeInTheDocument();
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });

    it('should call onRename when rename is clicked', () => {
      render(<ConversationItem {...defaultProps} />);

      fireEvent.click(screen.getByText('Rename'));

      expect(defaultProps.onRename).toHaveBeenCalledTimes(1);
    });

    it('should call onDelete when delete is clicked', () => {
      render(<ConversationItem {...defaultProps} />);

      fireEvent.click(screen.getByText('Delete'));

      expect(defaultProps.onDelete).toHaveBeenCalledTimes(1);
    });

    it('should mark delete option as danger variant', () => {
      render(<ConversationItem {...defaultProps} />);

      const deleteButton = screen.getByText('Delete');
      expect(deleteButton).toHaveAttribute('data-variant', 'danger');
    });
  });

  describe('Drag and drop', () => {
    it('should be draggable', () => {
      const { container } = render(<ConversationItem {...defaultProps} />);

      const draggableDiv = container.querySelector('[draggable="true"]');
      expect(draggableDiv).toBeInTheDocument();
    });

    it('should call onDragStart with conversation id', () => {
      const onDragStart = jest.fn();
      const { container } = render(
        <ConversationItem {...defaultProps} onDragStart={onDragStart} />
      );

      const draggableDiv = container.querySelector('[draggable="true"]')!;
      
      const mockDataTransfer = {
        effectAllowed: '',
        setData: jest.fn(),
      };

      fireEvent.dragStart(draggableDiv, {
        dataTransfer: mockDataTransfer,
      });

      expect(mockDataTransfer.effectAllowed).toBe('move');
      expect(mockDataTransfer.setData).toHaveBeenCalledWith(
        'conversationId',
        'conv-123'
      );
      expect(onDragStart).toHaveBeenCalledWith('conv-123');
    });

    it('should not call onDragStart if not provided', () => {
      const { container } = render(<ConversationItem {...defaultProps} />);

      const draggableDiv = container.querySelector('[draggable="true"]')!;
      
      const mockDataTransfer = {
        effectAllowed: '',
        setData: jest.fn(),
      };

      // Should not throw
      expect(() => {
        fireEvent.dragStart(draggableDiv, {
          dataTransfer: mockDataTransfer,
        });
      }).not.toThrow();

      expect(mockDataTransfer.setData).toHaveBeenCalled();
    });

    it('should call onDragEnd when drag ends', () => {
      const onDragEnd = jest.fn();
      const { container } = render(
        <ConversationItem {...defaultProps} onDragEnd={onDragEnd} />
      );

      const draggableDiv = container.querySelector('[draggable="true"]')!;
      fireEvent.dragEnd(draggableDiv);

      expect(onDragEnd).toHaveBeenCalledTimes(1);
    });

    it('should not call onDragEnd if not provided', () => {
      const { container } = render(<ConversationItem {...defaultProps} />);

      const draggableDiv = container.querySelector('[draggable="true"]')!;

      // Should not throw
      expect(() => {
        fireEvent.dragEnd(draggableDiv);
      }).not.toThrow();
    });
  });

  describe('Icon rendering', () => {
    it('should render MessageSquare icon', () => {
      const { container } = render(<ConversationItem {...defaultProps} />);

      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should render GripVertical drag handle', () => {
      const { container } = render(<ConversationItem {...defaultProps} />);

      const gripIcon = container.querySelector('.cursor-grab');
      expect(gripIcon).toBeInTheDocument();
    });

    it('should change icon color when active', () => {
      const { container } = render(
        <ConversationItem {...defaultProps} isActive={true} />
      );

      const messageIcon = container.querySelector('.text-primary-600');
      expect(messageIcon).toBeInTheDocument();
    });
  });

  describe('Edge cases', () => {
    it('should handle undefined messageCount', () => {
      const conv = { ...mockConversation, messageCount: undefined };
      render(<ConversationItem {...defaultProps} conversation={conv as any} />);

      // When messageCount is undefined, it displays as empty string + " messages"
      expect(screen.getByText(/messages$/)).toBeInTheDocument();
    });

    it('should handle zero messageCount', () => {
      const conv = { ...mockConversation, messageCount: 0 };
      render(<ConversationItem {...defaultProps} conversation={conv} />);

      expect(screen.getByText('0 messages')).toBeInTheDocument();
    });

    it('should handle large messageCount', () => {
      const conv = { ...mockConversation, messageCount: 9999 };
      render(<ConversationItem {...defaultProps} conversation={conv} />);

      expect(screen.getByText('9999 messages')).toBeInTheDocument();
    });
  });
});