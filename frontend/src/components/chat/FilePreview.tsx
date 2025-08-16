import { FileText, Image as ImageIcon, FileSpreadsheet, File, Trash2, X } from 'lucide-react';
import Image from 'next/image';
import { AttachedFile } from '@/types/file.interface';
import { Button } from '../ui/button';

interface FilePreviewProps {
  attachedFiles: AttachedFile[];
  onRemoveFile: (fileId: string) => void;
}

export default function FilePreview({ attachedFiles, onRemoveFile }: FilePreviewProps) {
  // Get appropriate icon for file type
  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) {
      return <ImageIcon className="w-4 h-4" />;
    } else if (fileType.includes('pdf')) {
      return <FileText className="w-4 h-4 text-red-500" />;
    } else if (fileType.includes('spreadsheet') || fileType.includes('excel') || fileType.includes('csv')) {
      return <FileSpreadsheet className="w-4 h-4 text-green-500" />;
    } else if (fileType.includes('document') || fileType.includes('word')) {
      return <FileText className="w-4 h-4 text-blue-500" />;
    } else {
      return <File className="w-4 h-4" />;
    }
  };

  if (attachedFiles.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2 p-2 bg-neutral-100 dark:bg-neutral-700 rounded-lg">
      {attachedFiles.map((attachedFile) => (
        <div
          key={attachedFile.id}
          className="flex items-center gap-2 bg-white dark:bg-neutral-600 p-2 rounded-md border group hover:bg-gray-50 dark:hover:bg-neutral-500 transition-colors"
        >
          {/* File Icon or Image Preview */}
          <div className="flex-shrink-0">
            {attachedFile.preview ? (
              <Image
                src={attachedFile.preview}
                alt={attachedFile.file.name}
                width={32}
                height={32}
                className="w-8 h-8 object-cover rounded"
              />
            ) : (
              getFileIcon(attachedFile.file.type)
            )}
          </div>
          
          {/* File Info */}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {attachedFile.file.name}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {(attachedFile.file.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          
          {/* Remove Button */}
          <Button
            variant="ghost" 
            type="button"
            onClick={() => onRemoveFile(attachedFile.id)}
            className="flex-shrink-0 px-3 rounded-full hover:bg-red-100 dark:hover:bg-red-900 transition-colors"
            aria-label={`Remove ${attachedFile.file.name}`}
          >
            <X className="size-4 text-red-500" />
          </Button>
        </div>
      ))}
    </div>
  );
}
