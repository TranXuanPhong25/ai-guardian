// File service để tích hợp với backend APIs
import { createClient } from '@/utils/supabase/client';

export interface FileItem {
  file_id: number;
  filename: string;
  file_path: string;
  created_at: string;
  size?: number;
  type?: string;
}

export interface FileUploadResponse {
  file_id: number;
  filename: string;
  created_at: string;
  url: string;
}

export interface FileExtractResponse {
  file_id: number;
  extracted_text: string | null;
}

class FileService {
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  private async getAuthToken(): Promise<string> {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error('Not authenticated');
    }

    return session.access_token;
  }

  /**
   * Upload một file lên server
   */
  async uploadFile(file: File, userId: string): Promise<FileUploadResponse> {
    const token = await this.getAuthToken();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/file/upload?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Upload nhiều files cùng lúc
   */
  async uploadFiles(userId: string, files: File[]): Promise<FileUploadResponse[]> {
    const uploadPromises = files.map(file => this.uploadFile(file, userId));
    return Promise.all(uploadPromises);
  }

  /**
   * Lấy danh sách files của user
   */
  async getFiles(userId: string): Promise<FileItem[]> {
    const token = await this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/file?user_id=${userId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch files: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Xóa một file
   */
  async deleteFile(fileId: number): Promise<FileItem> {
    const token = await this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/file/file/${fileId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to delete file: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Extract text từ file (OCR/text extraction)
   */
  async extractText(fileId: number): Promise<FileExtractResponse> {
    const token = await this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/file/extract`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ file_id: fileId }),
    });

    if (!response.ok) {
      throw new Error(`Failed to extract text: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Download file từ server
   */
  async downloadFile(fileItem: FileItem): Promise<void> {
    try {
      // Nếu file_path là URL đầy đủ (MinIO), dùng trực tiếp
      const fileUrl = fileItem.file_path;

      const response = await fetch(fileUrl);

      if (!response.ok) {
        throw new Error(`Failed to download file: ${response.statusText}`);
      }

      const blob = await response.blob();

      // Tạo download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileItem.filename;

      document.body.appendChild(link);
      link.click();

      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }

  /**
   * Get file size từ URL
   */
  async getFileSize(url: string): Promise<number> {
    try {
      const response = await fetch(url, { method: 'HEAD' });
      const contentLength = response.headers.get('Content-Length');
      return contentLength ? parseInt(contentLength, 10) : 0;
    } catch {
      return 0;
    }
  }

  /**
   * Validate file trước khi upload
   */
  validateFile(file: File, maxSizeInMB: number = 10): { valid: boolean; error?: string } {
    // Check file size
    const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
    if (file.size > maxSizeInBytes) {
      return {
        valid: false,
        error: `File size too large. Maximum allowed size is ${maxSizeInMB}MB.`
      };
    }

    // Check file type (add more types as needed)
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'application/pdf',
      'text/plain', 'text/csv',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`
      };
    }

    return { valid: true };
  }

  /**
   * Format file size cho display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  }

  /**
   * Get file type icon name
   */
  getFileTypeIcon(mimeType: string): string {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType.includes('pdf')) return 'pdf';
    if (mimeType.includes('document') || mimeType.includes('word')) return 'document';
    if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return 'spreadsheet';
    if (mimeType.includes('zip') || mimeType.includes('rar')) return 'archive';
    return 'file';
  }
}

export const fileService = new FileService();
