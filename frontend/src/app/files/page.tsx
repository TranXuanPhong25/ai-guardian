import { FileManager } from "@/components/file-manager"

export default function Home() {
   return (
      <main className="min-h-screen bg-background">
         <div className="container mx-auto py-8">
            <div className="mb-8">
               <h1 className="text-3xl font-bold text-foreground mb-2">File Manager</h1>
               <p className="text-muted-foreground">Upload, preview, download, and manage your files</p>
            </div>
            <FileManager />
         </div>
      </main>
   )
}
