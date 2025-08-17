import { FileText, Image as ImageIcon, FileSpreadsheet, File, X, Eye } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import Image from 'next/image';
import { useState } from 'react';

interface FileUrlPreviewProps {
   attachedFiles: string[];
   onRemoveFile: (index: number) => void;
}

export default function FileUrlPreview({ attachedFiles, onRemoveFile }: FileUrlPreviewProps) {
   const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

   // Get appropriate icon for file type based on URL
   const getFileIcon = (url: string) => {
      const extension = getFileExtension(url);
      
      if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(extension)) {
         return <ImageIcon className="w-4 h-4 text-blue-500" />;
      } else if (extension === 'pdf') {
         return <FileText className="w-4 h-4 text-red-500" />;
      } else if (['xlsx', 'xls', 'csv'].includes(extension)) {
         return <FileSpreadsheet className="w-4 h-4 text-green-500" />;
      } else if (['docx', 'doc'].includes(extension)) {
         return <FileText className="w-4 h-4 text-blue-500" />;
      } else {
         return <File className="w-4 h-4 text-gray-500" />;
      }
   };

   // Check if file is an image
   const isImage = (url: string) => {
      const extension = getFileExtension(url);
      return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension);
   };   // Get filename from URL (handle encoded URLs)
   const getFileName = (url: string) => {
      try {
         // Decode the URL first
         let decodedUrl = decodeURIComponent(url);
         
         // Remove Next.js image optimization params
         const cleanUrl = decodedUrl.split('?')[0];
         
         // Extract filename from the clean URL
         const parts = cleanUrl.split('/');
         const filename = parts[parts.length - 1];
         
         // Remove UUID prefix if it exists (format: uuid_filename)
         const cleanFilename = filename.replace(/^[a-f0-9]{32}_/, '');
         
         return cleanFilename || 'Unknown file';
      } catch (error) {
         // Fallback if URL decoding fails
         return url.split('/').pop()?.split('?')[0] || 'Unknown file';
      }
   };

   // Get file extension from URL (handle encoded URLs)
   const getFileExtension = (url: string) => {
      const filename = getFileName(url);
      return filename.split('.').pop()?.toLowerCase() || '';
   };

   // Handle image load error
   const handleImageError = (url: string) => {
      setImageErrors(prev => {
         const newSet = new Set(prev);
         newSet.add(url);
         return newSet;
      });
   };

   if (attachedFiles.length === 0) {
      return null;
   }
   
   return (
      <div className="p-3 bg-muted/30 rounded-lg border border-dashed">
         <div className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Ready to send ({attachedFiles.length} files)
         </div>

         <div className="flex  gap-3">
            {attachedFiles.map((url, index) => {
               const isImg = isImage(url);
               const hasImageError = imageErrors.has(url);
               const fileName = getFileName(url);

               return (
                  <div
                     key={index}
                     className="relative group bg-background border rounded-lg overflow-hidden hover:shadow-sm transition-shadow"
                  >
                     {/* Remove button */}
                     <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        className="absolute top-2 right-2 h-6 w-6 p-0 z-10 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => onRemoveFile(index)}
                     >
                        <X className="w-3 h-3" />
                     </Button>

                     {/* Preview */}
                     {isImg && !hasImageError ? (
                        <div className="relative ">
                           <div className="aspect-square  bg-muted flex items-center justify-center overflow-hidden">
                              <Image
                                 src={url}
                                 alt={fileName}
                                 fill
                                 className="object-cover"
                                 onError={() => handleImageError(url)}
                              />
                           </div>
                           <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                     ) : (
                        <div className="aspect-video w-full bg-muted/50 flex items-center justify-center">
                           <div className="text-center">
                              {getFileIcon(url)}
                              <div className="text-xs text-muted-foreground mt-1">
                                 {getFileExtension(url).toUpperCase()}
                              </div>
                           </div>
                        </div>
                     )}

                     {/* File info */}
                     <div className="p-2 border-t bg-background/80">
                        <div className="flex items-center justify-between">
                           <div className="flex items-center gap-2 min-w-0 flex-1">
                              {!isImg && (
                                 <div className="flex-shrink-0">
                                    {getFileIcon(url)}
                                 </div>
                              )}
                              <span className="text-xs font-medium truncate" title={fileName}>
                                 {fileName}
                              </span>
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
