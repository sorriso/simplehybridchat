// path: tests/unit/components/FileUploadPanel.test.unit.tsx
// version: 1

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { FileUploadPanel } from '@/components/upload/FileUploadPanel';
import { useFileUpload } from '@/lib/hooks/useFileUpload';

// Mock child components
jest.mock('@/components/upload/FileDropzone', () => ({
  FileDropzone: ({ onFilesSelected, disabled }: any) => (
    <div data-testid="dropzone" data-disabled={disabled}>
      <button onClick={() => onFilesSelected([{ name: 'test.txt' }])}>
        Select Files
      </button>
    </div>
  ),
}));

jest.mock('@/components/upload/FileList', () => ({
  FileList: ({ pendingFiles, uploadedFiles, onRemovePending, onRemoveUploaded }: any) => (
    <div data-testid="file-list">
      {pendingFiles.map((file: any) => (
        <div key={file.name}>
          Pending: {file.name}
          <button onClick={() => onRemovePending(file.name)}>Remove Pending</button>
        </div>
      ))}
      {uploadedFiles.map((file: any) => (
        <div key={file.id}>
          Uploaded: {file.filename}
          <button onClick={() => onRemoveUploaded(file.id)}>Remove Uploaded</button>
        </div>
      ))}
    </div>
  ),
}));

jest.mock('@/components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, variant }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant}>
      {children}
    </button>
  ),
}));

jest.mock('@/components/ui/IconButton', () => ({
  IconButton: ({ icon: Icon, onClick, title }: any) => (
    <button onClick={onClick} title={title}>
      Close
    </button>
  ),
}));

// Mock useFileUpload hook
jest.mock('@/lib/hooks/useFileUpload');

// Mock window.confirm
global.confirm = jest.fn();

describe('FileUploadPanel', () => {
  const mockUseFileUpload = useFileUpload as jest.MockedFunction<typeof useFileUpload>;

  const defaultHookReturn = {
    pendingFiles: [],
    uploadedFiles: [],
    isUploading: false,
    addFiles: jest.fn(),
    removePendingFile: jest.fn(),
    clearPendingFiles: jest.fn(),
    uploadFiles: jest.fn().mockResolvedValue(undefined),
    deleteUploadedFile: jest.fn().mockResolvedValue(undefined),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseFileUpload.mockReturnValue(defaultHookReturn);
    (global.confirm as jest.Mock).mockReturnValue(true);
  });

  describe('Rendering', () => {
    it('should render null when isOpen is false', () => {
      const { container } = render(
        <FileUploadPanel isOpen={false} onClose={jest.fn()} />
      );

      expect(container.firstChild).toBeNull();
    });

    it('should render panel when isOpen is true', () => {
      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      expect(screen.getByText('Upload Files')).toBeInTheDocument();
      expect(screen.getByTestId('dropzone')).toBeInTheDocument();
      expect(screen.getByTestId('file-list')).toBeInTheDocument();
    });

    it('should render close button', () => {
      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      expect(screen.getByTitle('Close')).toBeInTheDocument();
    });

    it('should not show footer when no pending files', () => {
      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      expect(screen.queryByText(/Upload.*file\(s\)/)).not.toBeInTheDocument();
      expect(screen.queryByText('Clear All')).not.toBeInTheDocument();
    });

    it('should show footer when there are pending files', () => {
      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      expect(screen.getByText('Upload 1 file(s)')).toBeInTheDocument();
      expect(screen.getByText('Clear All')).toBeInTheDocument();
    });

    it('should show correct count for multiple pending files', () => {
      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [
          { name: 'test1.txt', size: 100 },
          { name: 'test2.txt', size: 200 },
          { name: 'test3.txt', size: 300 },
        ],
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      expect(screen.getByText('Upload 3 file(s)')).toBeInTheDocument();
    });

    it('should show "Uploading..." when isUploading is true', () => {
      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
        isUploading: true,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      expect(screen.getByText('Uploading...')).toBeInTheDocument();
    });
  });

  describe('Close functionality', () => {
    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();

      render(<FileUploadPanel isOpen={true} onClose={onClose} />);

      await user.click(screen.getByTitle('Close'));

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('File selection', () => {
    it('should call addFiles when files are selected', async () => {
      const user = userEvent.setup();
      const addFiles = jest.fn();

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        addFiles,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Select Files'));

      expect(addFiles).toHaveBeenCalledWith([{ name: 'test.txt' }]);
    });

    it('should disable dropzone when uploading', () => {
      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        isUploading: true,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      const dropzone = screen.getByTestId('dropzone');
      expect(dropzone).toHaveAttribute('data-disabled', 'true');
    });
  });

  describe('Upload functionality', () => {
    it('should call uploadFiles when upload button is clicked', async () => {
      const user = userEvent.setup();
      const uploadFiles = jest.fn().mockResolvedValue(undefined);

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
        uploadFiles,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Upload 1 file(s)'));

      await waitFor(() => {
        expect(uploadFiles).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle upload errors gracefully', async () => {
      const user = userEvent.setup();
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const uploadFiles = jest.fn().mockRejectedValue(new Error('Upload failed'));

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
        uploadFiles,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Upload 1 file(s)'));

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith(
          'Upload failed:',
          expect.any(Error)
        );
      });

      consoleError.mockRestore();
    });

    it('should disable upload button when uploading', () => {
      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
        isUploading: true,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      const uploadButton = screen.getByText('Uploading...');
      expect(uploadButton).toBeDisabled();
    });
  });

  describe('Clear functionality', () => {
    it('should call clearPendingFiles when clear button is clicked', async () => {
      const user = userEvent.setup();
      const clearPendingFiles = jest.fn();

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
        clearPendingFiles,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Clear All'));

      expect(clearPendingFiles).toHaveBeenCalledTimes(1);
    });

    it('should disable clear button when uploading', () => {
      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
        isUploading: true,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      const clearButton = screen.getByText('Clear All');
      expect(clearButton).toBeDisabled();
    });
  });

  describe('File removal', () => {
    it('should call removePendingFile when pending file is removed', async () => {
      const user = userEvent.setup();
      const removePendingFile = jest.fn();

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        pendingFiles: [{ name: 'test.txt', size: 100 }],
        removePendingFile,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Remove Pending'));

      expect(removePendingFile).toHaveBeenCalledWith('test.txt');
    });

    it('should call deleteUploadedFile when uploaded file is removed with confirmation', async () => {
      const user = userEvent.setup();
      (global.confirm as jest.Mock).mockReturnValue(true);
      const deleteUploadedFile = jest.fn().mockResolvedValue(undefined);

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        uploadedFiles: [
          {
            id: 'file-1',
            filename: 'uploaded.txt',
            size: 100,
            mimeType: 'text/plain',
            uploadedAt: new Date().toISOString(),
          },
        ],
        deleteUploadedFile,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Remove Uploaded'));

      await waitFor(() => {
        expect(global.confirm).toHaveBeenCalledWith(
          'Are you sure you want to delete this file?'
        );
        expect(deleteUploadedFile).toHaveBeenCalledWith('file-1');
      });
    });

    it('should not delete uploaded file when confirmation is cancelled', async () => {
      const user = userEvent.setup();
      (global.confirm as jest.Mock).mockReturnValue(false);
      const deleteUploadedFile = jest.fn();

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        uploadedFiles: [
          {
            id: 'file-1',
            filename: 'uploaded.txt',
            size: 100,
            mimeType: 'text/plain',
            uploadedAt: new Date().toISOString(),
          },
        ],
        deleteUploadedFile,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Remove Uploaded'));

      await waitFor(() => {
        expect(global.confirm).toHaveBeenCalled();
      });

      expect(deleteUploadedFile).not.toHaveBeenCalled();
    });

    it('should handle delete errors gracefully', async () => {
      const user = userEvent.setup();
      (global.confirm as jest.Mock).mockReturnValue(true);
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const deleteUploadedFile = jest.fn().mockRejectedValue(new Error('Delete failed'));

      mockUseFileUpload.mockReturnValue({
        ...defaultHookReturn,
        uploadedFiles: [
          {
            id: 'file-1',
            filename: 'uploaded.txt',
            size: 100,
            mimeType: 'text/plain',
            uploadedAt: new Date().toISOString(),
          },
        ],
        deleteUploadedFile,
      });

      render(<FileUploadPanel isOpen={true} onClose={jest.fn()} />);

      await user.click(screen.getByText('Remove Uploaded'));

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith(
          'Delete failed:',
          expect.any(Error)
        );
      });

      consoleError.mockRestore();
    });
  });
});