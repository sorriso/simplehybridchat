// path: tests/unit/components/PromptCustomization.test.unit.tsx
// version: 1

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { PromptCustomization } from '@/components/settings/PromptCustomization';

// Mock Button component
jest.mock('@/components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, variant }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant}>
      {children}
    </button>
  ),
}));

describe('PromptCustomization', () => {
  const defaultProps = {
    initialValue: 'Initial prompt',
    onSave: jest.fn().mockResolvedValue(undefined),
    isSaving: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render with initial value', () => {
      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('Initial prompt');
      expect(screen.getByText('14 characters')).toBeInTheDocument();
    });

    it('should render all labels and descriptions', () => {
      render(<PromptCustomization {...defaultProps} />);

      expect(screen.getByText('Prompt Customization')).toBeInTheDocument();
      expect(
        screen.getByText(/Add custom instructions to personalize/)
      ).toBeInTheDocument();
    });

    it('should show Save Changes button', () => {
      render(<PromptCustomization {...defaultProps} />);

      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });

    it('should show Saving... when isSaving is true', () => {
      render(<PromptCustomization {...defaultProps} isSaving={true} />);

      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });
  });

  describe('Value changes', () => {
    it('should update value when typing', async () => {
      const user = userEvent.setup();
      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await user.clear(textarea);
      await user.type(textarea, 'New prompt value');

      expect(textarea).toHaveValue('New prompt value');
    });

    it('should update character count when typing', async () => {
      const user = userEvent.setup();
      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await user.clear(textarea);
      await user.type(textarea, 'Test');

      expect(screen.getByText('4 characters')).toBeInTheDocument();
    });

    it('should show "Unsaved changes" when value differs from initial', async () => {
      const user = userEvent.setup();
      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, ' modified');

      await waitFor(() => {
        expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
      });
    });

    it('should not show "Unsaved changes" initially', () => {
      render(<PromptCustomization {...defaultProps} />);

      expect(screen.queryByText('Unsaved changes')).not.toBeInTheDocument();
    });

    it('should enable save button when there are changes', async () => {
      const user = userEvent.setup();
      render(<PromptCustomization {...defaultProps} />);

      const saveButton = screen.getByText('Save Changes');
      expect(saveButton).toBeDisabled();

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, ' modified');

      await waitFor(() => {
        expect(saveButton).not.toBeDisabled();
      });
    });

    it('should update local state when initialValue changes', () => {
      const { rerender } = render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('Initial prompt');

      rerender(
        <PromptCustomization
          {...defaultProps}
          initialValue="Updated initial value"
        />
      );

      expect(textarea).toHaveValue('Updated initial value');
      expect(screen.queryByText('Unsaved changes')).not.toBeInTheDocument();
    });
  });

  describe('Save functionality', () => {
    it('should call onSave with current value when save is clicked', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn().mockResolvedValue(undefined);

      render(<PromptCustomization {...defaultProps} onSave={onSave} />);

      const textarea = screen.getByRole('textbox');
      await user.clear(textarea);
      await user.type(textarea, 'New value');

      const saveButton = screen.getByText('Save Changes');
      await user.click(saveButton);

      await waitFor(() => {
        expect(onSave).toHaveBeenCalledWith('New value');
      });
    });

    it('should not call onSave when there are no changes', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn();

      render(<PromptCustomization {...defaultProps} onSave={onSave} />);

      const saveButton = screen.getByText('Save Changes');
      await user.click(saveButton);

      expect(onSave).not.toHaveBeenCalled();
    });

    it('should clear hasChanges after successful save', async () => {
      const user = userEvent.setup();
      const onSave = jest.fn().mockResolvedValue(undefined);

      render(<PromptCustomization {...defaultProps} onSave={onSave} />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, ' modified');

      await waitFor(() => {
        expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
      });

      const saveButton = screen.getByText('Save Changes');
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.queryByText('Unsaved changes')).not.toBeInTheDocument();
      });
    });

    it('should handle save errors gracefully', async () => {
      const user = userEvent.setup();
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const onSave = jest.fn().mockRejectedValue(new Error('Save failed'));

      render(<PromptCustomization {...defaultProps} onSave={onSave} />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, ' modified');

      const saveButton = screen.getByText('Save Changes');
      await user.click(saveButton);

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith(
          'Failed to save prompt customization:',
          expect.any(Error)
        );
      });

      // Should still show unsaved changes after error
      expect(screen.getByText('Unsaved changes')).toBeInTheDocument();

      consoleError.mockRestore();
    });

    it('should disable save button when isSaving is true', () => {
      render(<PromptCustomization {...defaultProps} isSaving={true} />);

      const saveButton = screen.getByText('Saving...');
      expect(saveButton).toBeDisabled();
    });

    it('should disable save button when no changes and isSaving', async () => {
      const user = userEvent.setup();
      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, ' modified');

      const saveButton = screen.getByText('Save Changes');
      expect(saveButton).not.toBeDisabled();

      // Clear changes to match initial
      await user.clear(textarea);
      await user.type(textarea, 'Initial prompt');

      await waitFor(() => {
        expect(saveButton).toBeDisabled();
      });
    });
  });

  describe('Edge cases', () => {
    it('should handle empty initial value', () => {
      render(<PromptCustomization {...defaultProps} initialValue="" />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('');
      expect(screen.getByText('0 characters')).toBeInTheDocument();
    });

    it('should handle long text values', async () => {
      const user = userEvent.setup();
      const longText = 'a'.repeat(1000);

      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await user.clear(textarea);
      await user.type(textarea, longText);

      expect(screen.getByText('1000 characters')).toBeInTheDocument();
    });

    it('should handle rapid typing', async () => {
      const user = userEvent.setup();
      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      
      // Type multiple characters rapidly
      await user.type(textarea, 'abcdefghij');

      expect(textarea).toHaveValue('Initial promptabcdefghij');
    });

    it('should track changes correctly after multiple edits', async () => {
      const user = userEvent.setup();
      render(<PromptCustomization {...defaultProps} />);

      const textarea = screen.getByRole('textbox');

      // First edit
      await user.type(textarea, ' edit1');
      await waitFor(() => {
        expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
      });

      // Revert to original
      await user.clear(textarea);
      await user.type(textarea, 'Initial prompt');
      await waitFor(() => {
        expect(screen.queryByText('Unsaved changes')).not.toBeInTheDocument();
      });

      // Edit again
      await user.type(textarea, ' edit2');
      await waitFor(() => {
        expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
      });
    });
  });
});