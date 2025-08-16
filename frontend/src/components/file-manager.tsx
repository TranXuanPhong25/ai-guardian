"use client"

import type React from "react"

import { useState, useRef, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { useToast } from "@/components/ui/use-toast"
import { Upload, Download, Trash2, Eye, File, ImageIcon, FileText, Music, Video, Archive } from "lucide-react"
import Image from "next/image"
interface FileItem {
   id: string
   name: string
   size: number
   type: string
   url: string
   uploadedAt: Date
}

export function FileManager() {
   const [files, setFiles] = useState<FileItem[]>([])
   const [previewFile, setPreviewFile] = useState<FileItem | null>(null)
   const [isDragging, setIsDragging] = useState(false)
   const fileInputRef = useRef<HTMLInputElement>(null)
   const { toast } = useToast()

   const formatFileSize = (bytes: number) => {
      if (bytes === 0) return "0 Bytes"
      const k = 1024
      const sizes = ["Bytes", "KB", "MB", "GB"]
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
   }

   const getFileIcon = (type: string) => {
      if (type.startsWith("image/")) return <ImageIcon className="h-5 w-5" />
      if (type.startsWith("video/")) return <Video className="h-5 w-5" />
      if (type.startsWith("audio/")) return <Music className="h-5 w-5" />
      if (type.includes("pdf") || type.includes("document")) return <FileText className="h-5 w-5" />
      if (type.includes("zip") || type.includes("rar")) return <Archive className="h-5 w-5" />
      return <File className="h-5 w-5" />
   }

   const handleFileUpload = useCallback(
      (uploadedFiles: FileList) => {
         Array.from(uploadedFiles).forEach((file) => {
            const reader = new FileReader()
            reader.onload = (e) => {
               const newFile: FileItem = {
                  id: Math.random().toString(36).substr(2, 9),
                  name: file.name,
                  size: file.size,
                  type: file.type,
                  url: e.target?.result as string,
                  uploadedAt: new Date(),
               }
               setFiles((prev) => [...prev, newFile])
               toast({
                  title: "File uploaded",
                  description: `${file.name} has been uploaded successfully.`,
               })
            }
            reader.readAsDataURL(file)
         })
      },
      [toast],
   )

   const handleDrop = useCallback(
      (e: React.DragEvent) => {
         e.preventDefault()
         setIsDragging(false)
         const droppedFiles = e.dataTransfer.files
         if (droppedFiles.length > 0) {
            handleFileUpload(droppedFiles)
         }
      },
      [handleFileUpload],
   )

   const handleDragOver = useCallback((e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(true)
   }, [])

   const handleDragLeave = useCallback((e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
   }, [])

   const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFiles = e.target.files
      if (selectedFiles && selectedFiles.length > 0) {
         handleFileUpload(selectedFiles)
      }
   }

   const handleDownload = (file: FileItem) => {
      const link = document.createElement("a")
      link.href = file.url
      link.download = file.name
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast({
         title: "Download started",
         description: `${file.name} is being downloaded.`,
      })
   }

   const handleDelete = (fileId: string) => {
      const file = files.find((f) => f.id === fileId)
      setFiles((prev) => prev.filter((f) => f.id !== fileId))
      toast({
         title: "File deleted",
         description: `${file?.name} has been deleted.`,
         variant: "destructive",
      })
   }

   const handlePreview = (file: FileItem) => {
      setPreviewFile(file)
   }

   const renderPreview = (file: FileItem) => {
      if (file.type.startsWith("image/")) {
         return (
            <Image
               src={file.url || "/placeholder.svg"}
               alt={file.name}
               className="max-w-full max-h-96 object-contain rounded-lg"
            />
         )
      }

      if (file.type.startsWith("video/")) {
         return (
            <video src={file.url} controls className="max-w-full max-h-96 rounded-lg">
               Your browser does not support the video tag.
            </video>
         )
      }

      if (file.type.startsWith("audio/")) {
         return (
            <audio src={file.url} controls className="w-full">
               Your browser does not support the audio tag.
            </audio>
         )
      }

      if (file.type === "application/pdf") {
         return <iframe src={file.url} className="w-full h-96 rounded-lg" title={file.name} />
      }

      return (
         <div className="flex flex-col items-center justify-center p-8 text-center">
            {getFileIcon(file.type)}
            <p className="mt-4 text-sm text-muted-foreground">Preview not available for this file type</p>
            <Button onClick={() => handleDownload(file)} className="mt-4" variant="outline">
               <Download className="h-4 w-4 mr-2" />
               Download to view
            </Button>
         </div>
      )
   }

   return (
      <div className="space-y-6">
         {/* Upload Area */}
         <Card>
            <CardHeader>
               <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Upload Files
               </CardTitle>
            </CardHeader>
            <CardContent>
               <div
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragging ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
                     }`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
               >
                  <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">{isDragging ? "Drop files here" : "Drag & drop files here"}</p>
                  <p className="text-sm text-muted-foreground mb-4">or click to browse files</p>
                  <Button onClick={() => fileInputRef.current?.click()} variant="outline">
                     Browse Files
                  </Button>
                  <input ref={fileInputRef} type="file" multiple onChange={handleFileInputChange} className="hidden" />
               </div>
            </CardContent>
         </Card>

         {/* Files List */}
         <Card>
            <CardHeader>
               <CardTitle className="flex items-center justify-between">
                  <span>Files ({files.length})</span>
                  {files.length > 0 && (
                     <Badge variant="secondary">{formatFileSize(files.reduce((acc, file) => acc + file.size, 0))} total</Badge>
                  )}
               </CardTitle>
            </CardHeader>
            <CardContent>
               {files.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                     <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
                     <p>No files uploaded yet</p>
                  </div>
               ) : (
                  <div className="space-y-2">
                     {files.map((file) => (
                        <div
                           key={file.id}
                           className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                        >
                           <div className="flex items-center gap-3 flex-1 min-w-0">
                              {getFileIcon(file.type)}
                              <div className="flex-1 min-w-0">
                                 <p className="font-medium truncate">{file.name}</p>
                                 <p className="text-sm text-muted-foreground">
                                    {formatFileSize(file.size)} • {file.uploadedAt.toLocaleDateString()}
                                 </p>
                              </div>
                           </div>
                           <div className="flex items-center gap-2">
                              <Button size="sm" variant="ghost" onClick={() => handlePreview(file)}>
                                 <Eye className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleDownload(file)}>
                                 <Download className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleDelete(file.id)}>
                                 <Trash2 className="h-4 w-4" />
                              </Button>
                           </div>
                        </div>
                     ))}
                  </div>
               )}
            </CardContent>
         </Card>

         {/* Preview Dialog */}
         <Dialog open={!!previewFile} onOpenChange={() => setPreviewFile(null)}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
               <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                     {previewFile && getFileIcon(previewFile.type)}
                     {previewFile?.name}
                  </DialogTitle>
               </DialogHeader>
               <div className="mt-4">{previewFile && renderPreview(previewFile)}</div>
               <div className="flex justify-end gap-2 mt-4">
                  <Button variant="outline" onClick={() => previewFile && handleDownload(previewFile)}>
                     <Download className="h-4 w-4 mr-2" />
                     Download
                  </Button>
                  <Button
                     variant="destructive"
                     onClick={() => {
                        if (previewFile) {
                           handleDelete(previewFile.id)
                           setPreviewFile(null)
                        }
                     }}
                  >
                     <Trash2 className="h-4 w-4 mr-2" />
                     Delete
                  </Button>
               </div>
            </DialogContent>
         </Dialog>
      </div>
   )
}
