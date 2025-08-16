import { Button } from '@/components/ui/button';
import { ArrowUp, X, Paperclip } from 'lucide-react';
import { ChatHandler, ILLMModel } from '@/types/chat.interface';
import { AttachedFile } from '@/types/file.interface';
import ModelsDropdown from './ModelsDropdown';
import FilePreview from './FilePreview';
import { useState, useRef } from 'react';

interface MessageInputProps
  extends Pick<
    ChatHandler,
    | 'isLoading'
    | 'input'
    | 'handleInputChange'
    | 'setInput'
    | 'stop'
    | 'onFileUpload'
    | 'onFileError'
  > {
  handleSubmit: (
    e: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>,
    options?: { data: FormData; hasFiles?: boolean }
  ) => void;
  // Model selection
  model: ILLMModel;
  setModel: React.Dispatch<React.SetStateAction<ILLMModel>>;
}

export default function MessageInput({
  isLoading,
  input,
  handleSubmit,
  handleInputChange,
  setInput,
  stop,
  model,
  setModel,
  onFileUpload,
  onFileError,
}: MessageInputProps) {
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);

  // Remove attached file
  const removeFile = (fileId: string) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Add file to attachments
  const addFileToAttachments = async (file: File) => {
    const fileId = Date.now().toString();
    let preview: string | undefined;

    // Create preview for images
    if (file.type.startsWith('image/')) {
      preview = URL.createObjectURL(file);
    }

    const attachedFile: AttachedFile = {
      file,
      id: fileId,
      preview
    };

    setAttachedFiles(prev => [...prev, attachedFile]);

    // Call the onFileUpload prop if provided
    if (onFileUpload) {
      try {
        await onFileUpload(file);
      } catch (error) {
        // Remove file from attachments if upload fails
        setAttachedFiles(prev => prev.filter(f => f.id !== fileId));
        throw error;
      }
    }
  };
  const onSubmit = (
    e: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    e.preventDefault();
    if (!input.trim() && attachedFiles.length === 0) return;

    // Create FormData for file uploads
    const formData = new FormData();
    formData.append('message', input);
    formData.append('model', model.id);

    // Add files to FormData
    attachedFiles.forEach((attachedFile) => {
      formData.append('files', attachedFile.file);
    });

    // Clear the input field and attachments
    setInput!('');
    setAttachedFiles([]);

    // Call handleSubmit with FormData
    handleSubmit(e, {
      data: formData,
      hasFiles: attachedFiles.length > 0
    });
  };

  // allows to submit chat with Cmd / Ctrl + Enter
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Prevent default newline behavior
      onSubmit(e);
    }
  };

  // Handle paste events to allow file attachments
  const handlePaste = async (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];

      // Check if the item is a file
      if (item.kind === 'file') {
        e.preventDefault(); // Prevent default paste behavior
        const file = item.getAsFile();

        if (file) {
          try {
            // Add file to attachments instead of direct upload
            await addFileToAttachments(file);
          } catch (error) {
            console.error('Error handling pasted file:', error);
            const errorMsg = `Error processing the pasted file: ${error}`;
            if (onFileError) {
              onFileError(errorMsg);
            } else {
              alert(errorMsg);
            }
          }
        }
      }
    }
  };

  return (
    <form onSubmit={onSubmit}>
      <div className="bg-neutral-50 dark:bg-neutral-800 p-3 rounded-xl max-w-4xl mb-4 mx-4 md:mx-8 lg:mx-auto space-y-2">
        <FilePreview
          attachedFiles={attachedFiles}
          onRemoveFile={removeFile}
        />
        {/* Textarea for message input */}
        <textarea
          value={input}
          onChange={handleInputChange}
          onPaste={handlePaste}
          placeholder="Ask anything..."
          className="w-full bg-transparent p-2 outline-none resize-none"
          rows={Math.min(input.split('\n').length, 8)}
          disabled={isLoading}
          onKeyDown={handleKeyDown}
        />

        {/* Bottom section with options and submit */}
        <div className="flex items-center justify-between">
          {/* Model Dropdown */}
          <ModelsDropdown model={model} setModel={setModel} />

          {/* Submit or stop button */}
          {!isLoading ? (
            <Button
              variant="default"
              size="icon"
              disabled={!input.trim()}
              type="submit"
              className="rounded-full"
            >
              <ArrowUp />
            </Button>
          ) : (
            <Button
              variant="default"
              size="icon"
              type="button"
              className="rounded-full"
              onClick={stop}
            >
              <X />
            </Button>
          )}
        </div>
      </div>
    </form>
  );
}
