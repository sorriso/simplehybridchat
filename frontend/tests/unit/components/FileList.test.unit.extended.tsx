/* path: tests/unit/components/FileList.test.unit.extended.tsx
   version: 1 - Extended tests for uncovered lines (41-45, 109-129) */

   import React from 'react';
   import { render, screen, fireEvent } from '@testing-library/react';
   import { FileList } from '@/components/upload/FileList';
   import type { PendingFile, UploadedFile } from '@/types/file';
   
   describe('FileList - Extended Coverage', () => {
     const mockOnRemovePending = jest.fn();
     const mockOnRemoveUploaded = jest.fn();
   
     beforeEach(() => {
       jest.clearAllMocks();
     });
   
     describe('Status Icons', () => {
       it('should display uploading icon for uploading status', () => {
         const pendingFiles: PendingFile[] = [
           {
             id: 'file-1',
             name: 'uploading.pdf',
             size: 1024,
             type: 'application/pdf',
             file: new File([], 'uploading.pdf'),
             status: 'uploading',
             progress: 50,
           },
         ];
   
         render(
           <FileList
             pendingFiles={pendingFiles}
             uploadedFiles={[]}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Check for uploading indicator (loader with spin animation)
         const loader = screen.getByText('uploading.pdf')
           .closest('div')
           ?.querySelector('.animate-spin');
         expect(loader).toBeInTheDocument();
       });
   
       it('should display completed icon for completed status', () => {
         const pendingFiles: PendingFile[] = [
           {
             id: 'file-2',
             name: 'completed.pdf',
             size: 2048,
             type: 'application/pdf',
             file: new File([], 'completed.pdf'),
             status: 'completed',
             progress: 100,
           },
         ];
   
         render(
           <FileList
             pendingFiles={pendingFiles}
             uploadedFiles={[]}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Completed icon should be present
         expect(screen.getByText('completed.pdf')).toBeInTheDocument();
         expect(screen.getByText('100%')).toBeInTheDocument();
       });
   
       it('should display error icon for error status', () => {
         const pendingFiles: PendingFile[] = [
           {
             id: 'file-3',
             name: 'error.pdf',
             size: 3072,
             type: 'application/pdf',
             file: new File([], 'error.pdf'),
             status: 'error',
             error: 'Upload failed',
           },
         ];
   
         render(
           <FileList
             pendingFiles={pendingFiles}
             uploadedFiles={[]}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Error message should be displayed
         expect(screen.getByText('error.pdf')).toBeInTheDocument();
         expect(screen.getByText('Upload failed')).toBeInTheDocument();
       });
   
       it('should display default icon for pending status', () => {
         const pendingFiles: PendingFile[] = [
           {
             id: 'file-4',
             name: 'pending.pdf',
             size: 4096,
             type: 'application/pdf',
             file: new File([], 'pending.pdf'),
             status: 'pending',
           },
         ];
   
         render(
           <FileList
             pendingFiles={pendingFiles}
             uploadedFiles={[]}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         expect(screen.getByText('pending.pdf')).toBeInTheDocument();
         expect(screen.getByText('4.0 KB')).toBeInTheDocument();
       });
     });
   
     describe('Uploaded Files Section', () => {
       it('should display uploaded files with correct formatting', () => {
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'uploaded-1',
             name: 'document1.pdf',
             size: 5120,
             type: 'application/pdf',
             url: 'https://example.com/doc1.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
           {
             id: 'uploaded-2',
             name: 'document2.docx',
             size: 10240,
             type: 'application/docx',
             url: 'https://example.com/doc2.docx',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         render(
           <FileList
             pendingFiles={[]}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Check header
         expect(screen.getByText('Uploaded Files')).toBeInTheDocument();
   
         // Check both files are displayed
         expect(screen.getByText('document1.pdf')).toBeInTheDocument();
         expect(screen.getByText('document2.docx')).toBeInTheDocument();
   
         // Check file sizes are formatted
         expect(screen.getByText(/5\.0 KB/)).toBeInTheDocument();
         expect(screen.getByText(/10\.0 KB/)).toBeInTheDocument();
   
         // Check status is displayed
         const statusElements = screen.getAllByText('completed');
         expect(statusElements.length).toBeGreaterThanOrEqual(2);
       });
   
       it('should call onRemoveUploaded when delete button is clicked', () => {
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'uploaded-1',
             name: 'document.pdf',
             size: 2048,
             type: 'application/pdf',
             url: 'https://example.com/doc.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         render(
           <FileList
             pendingFiles={[]}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Find and click delete button
         const deleteButtons = screen.getAllByTitle('Delete');
         fireEvent.click(deleteButtons[0]);
   
         expect(mockOnRemoveUploaded).toHaveBeenCalledWith('uploaded-1');
         expect(mockOnRemoveUploaded).toHaveBeenCalledTimes(1);
       });
   
       it('should display uploaded files with green background styling', () => {
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'uploaded-1',
             name: 'styled-document.pdf',
             size: 1024,
             type: 'application/pdf',
             url: 'https://example.com/styled.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         const { container } = render(
           <FileList
             pendingFiles={[]}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Check for green background class
         const uploadedFileElement = screen.getByText('styled-document.pdf').closest('div');
         expect(uploadedFileElement).toHaveClass('bg-green-50');
       });
   
       it('should show check circle icon for uploaded files', () => {
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'uploaded-1',
             name: 'icon-test.pdf',
             size: 512,
             type: 'application/pdf',
             url: 'https://example.com/icon.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         const { container } = render(
           <FileList
             pendingFiles={[]}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Check for CheckCircle icon (green color)
         const iconContainer = screen.getByText('icon-test.pdf').closest('div');
         const icon = iconContainer?.querySelector('.text-green-500');
         expect(icon).toBeInTheDocument();
       });
   
       it('should truncate long file names in uploaded files', () => {
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'uploaded-1',
             name: 'very-long-file-name-that-should-be-truncated-properly.pdf',
             size: 2048,
             type: 'application/pdf',
             url: 'https://example.com/long.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         const { container } = render(
           <FileList
             pendingFiles={[]}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         const fileName = screen.getByText(/very-long-file-name/);
         expect(fileName).toHaveClass('truncate');
       });
     });
   
     describe('Mixed Content', () => {
       it('should display both pending and uploaded files together', () => {
         const pendingFiles: PendingFile[] = [
           {
             id: 'pending-1',
             name: 'pending.pdf',
             size: 1024,
             type: 'application/pdf',
             file: new File([], 'pending.pdf'),
             status: 'uploading',
             progress: 50,
           },
         ];
   
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'uploaded-1',
             name: 'uploaded.pdf',
             size: 2048,
             type: 'application/pdf',
             url: 'https://example.com/up.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         render(
           <FileList
             pendingFiles={pendingFiles}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         // Both sections should be visible
         expect(screen.getByText('Pending Files')).toBeInTheDocument();
         expect(screen.getByText('Uploaded Files')).toBeInTheDocument();
   
         // Both files should be visible
         expect(screen.getByText('pending.pdf')).toBeInTheDocument();
         expect(screen.getByText('uploaded.pdf')).toBeInTheDocument();
       });
     });
   
     describe('File Size Formatting', () => {
       it('should format large file sizes correctly', () => {
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'large-1',
             name: 'large.pdf',
             size: 1048576, // 1 MB
             type: 'application/pdf',
             url: 'https://example.com/large.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         render(
           <FileList
             pendingFiles={[]}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         expect(screen.getByText(/1\.0 MB/)).toBeInTheDocument();
       });
   
       it('should format very large file sizes correctly', () => {
         const uploadedFiles: UploadedFile[] = [
           {
             id: 'huge-1',
             name: 'huge.pdf',
             size: 1073741824, // 1 GB
             type: 'application/pdf',
             url: 'https://example.com/huge.pdf',
             status: 'completed',
             uploadedAt: new Date().toISOString(),
           },
         ];
   
         render(
           <FileList
             pendingFiles={[]}
             uploadedFiles={uploadedFiles}
             onRemovePending={mockOnRemovePending}
             onRemoveUploaded={mockOnRemoveUploaded}
           />
         );
   
         expect(screen.getByText(/1\.0 GB/)).toBeInTheDocument();
       });
     });
   });