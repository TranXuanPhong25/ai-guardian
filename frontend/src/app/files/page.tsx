'use client';

import { FileManager } from "@/components/file-manager"
import { FileManagerIntegrated } from "@/components/file-manager-integrated"
import { useEffect } from "react"
import Head from 'next/head'

export default function FilesPage() {
  useEffect(() => {
    // Update document title
    document.title = 'Files - AI Guardian';
  }, []);

  return (
    <>
      <Head>
        <title>Files - AI Guardian</title>
        <meta name="description" content="Manage your files in AI Guardian" />
      </Head>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">File Management</h1>
        <FileManagerIntegrated />
      </div>
    </>
  )
}