import { FileManager } from "@/components/file-manager"
import { FileManagerIntegrated } from "@/components/file-manager-integrated"

export default function FilesPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">File Management</h1>
      <FileManagerIntegrated />
    </div>
  )
}