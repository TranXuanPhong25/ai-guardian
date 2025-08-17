import { Download, FileText, Image as ImageIcon, FileSpreadsheet, File, Eye, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Image from 'next/image';
import { useState } from 'react';

interface MessageFile {
   file_id: number;
   filename: string;
   file_path: string;
}

interface FilePreviewInMessageProps {
   files: MessageFile[];
}

export default function FilePreviewInMessage({ files }: FilePreviewInMessageProps) {
   const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

   // Get appropriate icon for file type
   const getFileIcon = (filename: string) => {
      // Handle encoded filenames and extract clean extension
      let cleanFilename = filename;
      try {
         // Try to decode if it's URL encoded
         cleanFilename = decodeURIComponent(filename);
      } catch (e) {
         // If decoding fails, use original
      }

      // Remove UUID prefix if exists (format: uuid_filename)
      cleanFilename = cleanFilename.replace(/^[a-f0-9]{32}_/, '');

      const extension = cleanFilename.split('.').pop()?.toLowerCase();

      if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(extension || '')) {
         return <ImageIcon className="w-4 h-4 text-blue-500" />;
      } else if (extension === 'pdf') {
         return <FileText className="w-4 h-4 text-red-500" />;
      } else if (['xlsx', 'xls', 'csv'].includes(extension || '')) {
         return <FileSpreadsheet className="w-4 h-4 text-green-500" />;
      } else if (['docx', 'doc'].includes(extension || '')) {
         return <FileText className="w-4 h-4 text-blue-500" />;
      } else {
         return <File className="w-4 h-4 text-gray-500" />;
      }
   };

   // Check if file is an image
   const isImage = (filename: string) => {
      let cleanFilename = filename;
      try {
         cleanFilename = decodeURIComponent(filename);
      } catch (e) {
         // If decoding fails, use original
      }

      // Remove UUID prefix if exists
      cleanFilename = cleanFilename.replace(/^[a-f0-9]{32}_/, '');

      const extension = cleanFilename.split('.').pop()?.toLowerCase();
      return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension || '');
   };

   // Get clean filename for display
   const getCleanFilename = (filename: string) => {
      let cleanFilename = filename;
      try {
         cleanFilename = decodeURIComponent(filename);
      } catch (e) {
         // If decoding fails, use original
      }

      // Remove UUID prefix if exists
      return cleanFilename.replace(/^[a-f0-9]{32}_/, '');
   };

   // Get file size display (if available in URL)
   const getFileSize = (filename: string) => {
      // This is a placeholder - you might want to add file size to your backend response
      return null;
   };

   // Handle image load error
   const handleImageError = (fileId: string) => {
      setImageErrors(prev => {
         const newSet = new Set(prev);
         newSet.add(fileId);
         return newSet;
      });
   };

   if (!files || files.length === 0) {
      return null;
   }

   return (
      <div className="mt-3 space-y-3">
         <div className="flex justify-end gap-3">
            {files.map((file) => {
               const isImg = isImage(file.filename);
               const hasImageError = imageErrors.has(file.file_id.toString());
               const cleanFilename = getCleanFilename(file.filename);

               return (
                  <div
                     key={file.file_id}
                     className="relative group bg-background border rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                  >
                     {/* Image Preview */}
                     {isImg && !hasImageError ? (
                        <div className="relative">
                           <div className="aspect-video w-full bg-muted flex items-center justify-center overflow-hidden">
                              <Image
                                 src={file.file_path}
                                 alt={cleanFilename}
                                 fill
                                 className="object-cover"
                                 onError={() => handleImageError(file.file_id.toString())}
                                 sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                              />
                           </div>
                           {/* Overlay for image actions */}
                           <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                              <div className="flex gap-2">
                                 <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => window.open(file.file_path, '_blank')}
                                    className="bg-white/90 hover:bg-white text-black"
                                 >
                                    <Eye className="h-4 w-4 mr-1" />
                                    View
                                 </Button>
                                 <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => {
                                       const link = document.createElement('a');
                                       link.href = file.file_path;
                                       link.download = cleanFilename;
                                       link.click();
                                    }}
                                    className="bg-white/90 hover:bg-white text-black"
                                 >
                                    <Download className="h-4 w-4 mr-1" />
                                    Download
                                 </Button>
                              </div>
                           </div>
                        </div>
                     ) : (
                        /* Non-image file preview */
                        <div className="p-4 min-h-[80px] flex items-center justify-center bg-muted/30">
                           <div className="text-center">
                              {getFileIcon(file.filename)}
                              <div className="text-sm text-muted-foreground mt-2">
                                 {cleanFilename.split('.').pop()?.toUpperCase()} file
                              </div>
                           </div>
                        </div>
                     )}

                     {/* File info footer */}
                     <div className="p-3 border-t bg-muted/20">
                        <div className="flex items-center justify-between">
                           <div className="flex items-center gap-2 min-w-0 flex-1">
                              {!isImg && getFileIcon(file.filename)}
                              <div className="min-w-0 flex-1">
                                 <div className="text-sm font-medium truncate" title={cleanFilename}>
                                    {cleanFilename}
                                 </div>
                                 {getFileSize(file.filename) && (
                                    <div className="text-xs text-muted-foreground">
                                       {getFileSize(file.filename)}
                                    </div>
                                 )}
                              </div>
                           </div>

                           <div className="flex items-center gap-1 ml-2">
                              {isImg && (
                                 <Badge variant="secondary" className="text-xs">
                                    Image
                                 </Badge>
                              )}
                              <Button
                                 variant="ghost"
                                 size="sm"
                                 onClick={() => window.open(file.file_path, '_blank')}
                                 className="h-8 w-8 p-0 hover:bg-muted"
                              >
                                 <ExternalLink className="h-4 w-4" />
                              </Button>
                              <Button
                                 variant="ghost"
                                 size="sm"
                                 onClick={() => {
                                    const link = document.createElement('a');
                                    link.href = file.file_path;
                                    link.download = cleanFilename;
                                    link.click();
                                 }}
                                 className="h-8 w-8 p-0 hover:bg-muted"
                              >
                                 <Download className="h-4 w-4" />
                              </Button>
                           </div>
                        </div>
                     </div>
                  </div>
               );
            })}
         </div>
      </div>
   );
}
