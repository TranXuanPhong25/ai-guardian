"use client"

import type React from "react"
import { useState, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useToast } from "@/components/ui/use-toast"
import { Upload, Download, Trash2, Eye, File, ImageIcon, FileText, Music, Video, Archive, Loader2 } from "lucide-react"
import Image from "next/image"

// Import React Query hooks
import {
   useFiles,
   useFileUpload,
   useFileDelete,
   useFileExtract,
   useUser
} from "@/hooks/useQueries"

export function FileManagerIntegrated() {
   const [previewFile, setPreviewFile] = useState<any>(null)
   const [isDragging, setIsDragging] = useState(false)
   const fileInputRef = useRef<HTMLInputElement>(null)
   const { toast } = useToast()

   // Get current user
   const { data: user } = useUser()
   const userId = user?.id || '' // You may need to adjust this based on your user ID structure

   // React Query hooks for file operations
   const {
      data: files = [],
      isLoading: filesLoading,
      error: filesError,
      refetch: refetchFiles
   } = useFiles(userId)

   const uploadFileMutation = useFileUpload()
   const deleteFileMutation = useFileDelete()
   const extractTextMutation = useFileExtract()

   const formatFileSize = (bytes: number) => {
      if (bytes === 0) return "0 Bytes"
      const k = 1024
      const sizes = ["Bytes", "KB", "MB", "GB"]
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
   }

   const getFileIcon = (filename: string) => {
      const ext = filename.split('.').pop()?.toLowerCase()
      if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '')) return <ImageIcon className="h-5 w-5" />
      if (['mp4', 'avi', 'mov', 'wmv'].includes(ext || '')) return <Video className="h-5 w-5" />
      if (['mp3', 'wav', 'flac', 'aac'].includes(ext || '')) return <Music className="h-5 w-5" />
      if (['pdf', 'doc', 'docx', 'txt'].includes(ext || '')) return <FileText className="h-5 w-5" />
      if (['zip', 'rar', '7z', 'tar'].includes(ext || '')) return <Archive className="h-5 w-5" />
      return <File className="h-5 w-5" />
   }

   const handleFileUpload = useCallback(
      (uploadedFiles: FileList) => {
         if (!userId) {
            toast({
               title: "Error",
               description: "Please log in to upload files",
               variant: "destructive",
            })
            return
         }

         const fileArray = Array.from(uploadedFiles)

         if (fileArray.length === 1) {
            // Single file upload
            uploadFileMutation.mutate(
               { file: fileArray[0], userId },
               {
                  onSuccess: (response) => {
                     toast({
                        title: "Upload successful",
                        description: `File "${fileArray[0].name}" uploaded successfully`,
                     })
                  },
                  onError: (error) => {
                     toast({
                        title: "Upload failed",
                        description: error instanceof Error ? error.message : "Unknown error occurred",
                        variant: "destructive",
                     })
                  }
               }
            )
         }
      },
      [uploadFileMutation, userId, toast]
   )

   const handleDeleteFile = useCallback(
      (fileId: number) => {
         deleteFileMutation.mutate(fileId, {
            onSuccess: (deletedFile) => {
               toast({
                  title: "File deleted",
                  description: `File "${deletedFile.filename}" deleted successfully`,
               })
            },
            onError: (error) => {
               toast({
                  title: "Delete failed",
                  description: error instanceof Error ? error.message : "Unknown error occurred",
                  variant: "destructive",
               })
            }
         })
      },
      [deleteFileMutation, toast]
   )

   const handleExtractText = useCallback(
      (fileId: number) => {
         extractTextMutation.mutate(fileId, {
            onSuccess: (response) => {
               toast({
                  title: "Text extraction successful",
                  description: "Text extracted from file",
               })
               // You might want to do something with the extracted text here
               console.log('Extracted text:', response.extracted_text)
            },
            onError: (error) => {
               toast({
                  title: "Text extraction failed",
                  description: error instanceof Error ? error.message : "Unknown error occurred",
                  variant: "destructive",
               })
            }
         })
      },
      [extractTextMutation, toast]
   )

   const handleDragOver = useCallback((e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(true)
   }, [])

   const handleDragLeave = useCallback((e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
   }, [])

   const handleDrop = useCallback(
      (e: React.DragEvent) => {
         e.preventDefault()
         setIsDragging(false)
         const droppedFiles = e.dataTransfer.files
         if (droppedFiles.length > 0) {
            handleFileUpload(droppedFiles)
         }
      },
      [handleFileUpload]
   )

   const openFileInput = () => {
      fileInputRef.current?.click()
   }

   const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFiles = e.target.files
      if (selectedFiles && selectedFiles.length > 0) {
         handleFileUpload(selectedFiles)
      }
      // Reset input
      if (fileInputRef.current) {
         fileInputRef.current.value = ''
      }
   }

   // Loading state
   if (filesLoading) {
      return (
         <div className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin" />
            <span className="ml-2">Loading files...</span>
         </div>
      )
   }

   // Error state
   if (filesError) {
      return (
         <div className="p-4">
            <Card>
               <CardContent className="p-6">
                  <div className="text-center">
                     <p className="text-red-600 mb-4">Error loading files: {filesError.message}</p>
                     <Button onClick={() => refetchFiles()}>Retry</Button>
                  </div>
               </CardContent>
            </Card>
         </div>
      )
   }

   return (
      <div className="p-4">
         <Card>
            <CardHeader>
               <CardTitle>File Manager</CardTitle>
            </CardHeader>
            <CardContent>
               {/* Upload Area */}
               <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300"
                     }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
               >
                  <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium mb-2">
                     {isDragging ? "Drop files here" : "Upload Files"}
                  </p>
                  <p className="text-gray-500 mb-4">
                     Drag and drop files here, or click to select files
                  </p>
                  <Button
                     onClick={openFileInput}
                     disabled={uploadFileMutation.isPending}
                  >
                     {uploadFileMutation.isPending && (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                     )}
                     Select Files
                  </Button>
               </div>

               {/* Hidden file input */}
               <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileInputChange}
                  className="hidden"
               />

               {/* Files Grid */}
               {files.length > 0 && (
                  <div className="mt-8">
                     <h3 className="text-lg font-medium mb-4">Your Files ({files.length})</h3>
                     <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {files.map((file) => (
                           <Card key={file.file_id} className="hover:shadow-md transition-shadow">
                              <CardContent className="p-4">
                                 <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center space-x-2">
                                       {getFileIcon(file.filename)}
                                       <div className="flex-1 min-w-0">
                                          <p className="text-sm font-medium truncate" title={file.filename}>
                                             {file.filename}
                                          </p>

                                       </div>
                                    </div>
                                 </div>

                                 <div className="flex items-center justify-between">
                                    <Badge variant="secondary" className="text-xs">
                                       {new Date(file.created_at).toLocaleDateString()}
                                    </Badge>
                                    <div className="flex space-x-1">
                                       <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() => handleExtractText(file.file_id)}
                                          disabled={extractTextMutation.isPending}
                                          title="Extract text"
                                       >
                                          {extractTextMutation.isPending ? (
                                             <Loader2 className="h-3 w-3 animate-spin" />
                                          ) : (
                                             <Eye className="h-3 w-3" />
                                          )}
                                       </Button>
                                       <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() => handleDeleteFile(file.file_id)}
                                          disabled={deleteFileMutation.isPending}
                                          title="Delete file"
                                       >
                                          {deleteFileMutation.isPending ? (
                                             <Loader2 className="h-3 w-3 animate-spin" />
                                          ) : (
                                             <Trash2 className="h-3 w-3" />
                                          )}
                                       </Button>
                                    </div>
                                 </div>
                              </CardContent>
                           </Card>
                        ))}
                     </div>
                  </div>
               )}

               {files.length === 0 && (
                  <div className="mt-8 text-center text-gray-500">
                     <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
                     <p>No files uploaded yet</p>
                  </div>
               )}
            </CardContent>
         </Card>

         {/* Preview Dialog */}
         {previewFile && (
            <Dialog open={!!previewFile} onOpenChange={() => setPreviewFile(null)}>
               <DialogContent className="max-w-4xl">
                  <DialogHeader>
                     <DialogTitle>{previewFile.filename}</DialogTitle>
                  </DialogHeader>
                  <div className="mt-4">
                     <p>File preview functionality can be implemented here</p>
                  </div>
               </DialogContent>
            </Dialog>
         )}
      </div>
   )
}
