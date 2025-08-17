import { Button } from '@/components/ui/button';
import { ArrowUp, X, Paperclip, Eye, EyeOff, AlertTriangle, Loader2, Square, Check } from 'lucide-react';
import { ChatHandler, ILLMModel } from '@/types/chat.interface';
import ModelsDropdown from './ModelsDropdown';
import SafetyWarning from '@/components/SafetyWarning';
import { useState, useRef, useEffect, useMemo } from 'react';
import { Badge } from '@/components/ui/badge';
import { useSensitiveValidation, useMaskingOperations } from '@/hooks/useQueries';
import FileUrlPreview from './FileUrlPreview';

interface MessageInputProps
  extends Pick<
    ChatHandler,
    | 'isLoading'
    | 'input'
    | 'handleInputChange'
    | 'handleSubmit'
    | 'setInput'
    | 'stop'
  > {
  // Model selection
  model: ILLMModel;
  setModel: React.Dispatch<React.SetStateAction<ILLMModel>>;
  sessionId: string;
  // File handling with URLs
  attachedFiles: string[];
  onFileAttach: (files: File[]) => Promise<void>;
  onRemoveFile: (index: number) => void;
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
  sessionId,
  attachedFiles,
  onFileAttach,
  onRemoveFile,
}: MessageInputProps) {
  const [isMasked, setIsMasked] = useState(false);
  const [maskedContent, setMaskedContent] = useState<string>('');
  const [isFetchingMask, setIsFetchingMask] = useState(false);
  const [maskMapping, setMaskMapping] = useState<Record<string, string>>({});
  
  // File input reference
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Use React Query for sensitive validation with debouncing
  const { data: validationResult, isLoading: isValidating } = useSensitiveValidation(input || '', !!input?.trim(), 300);
  const alertContent = !!input.trim() ? validationResult?.alert : null;
  const sensitiveFound = alertContent !== null;
  // Use mutations for masking operations
  const { maskText: maskTextMutation, unmaskText: unmaskTextMutation } = useMaskingOperations();

  // Toggle mask and fetch masked content
  const toggleMask = async () => {
    // If already fetching, don't do anything
    if (isFetchingMask || maskTextMutation.isPending) return;
    
    if (!isMasked && input.trim()) {
      setIsFetchingMask(true);
      try {
        // setSensitiveFound is no longer needed since sensitiveFound is computed from React Query
        
        if (sensitiveFound) {
          // Use mutation to mask text
          const maskResult = await maskTextMutation.mutateAsync({
            sessionId: sessionId,
            content: input
          });
          setMaskedContent(maskResult.masked_text);
          setMaskMapping(maskResult.mapping);
          setIsMasked(true);
        } else {
          // No sensitive content found - show a temporary message
          setMaskedContent("No sensitive content detected.");
          setTimeout(() => {
            if (setInput) setInput(input); // Keep the original input
            setIsMasked(false);
            setMaskedContent("");
          }, 1500);
        }
      } catch (error) {
        console.error('Error fetching masked content:', error);
        // Fallback to simple masking if service fails
        setMaskedContent(input.replace(/\S/g, '•'));
        setIsMasked(true);
      } finally {
        setIsFetchingMask(false);
      }
    } else if (isMasked && Object.keys(maskMapping).length > 0) {
      // When unmasking, restore original content if needed
      setIsFetchingMask(true);
      try {
        // If we have mask mappings, use the unmask mutation
        const unmaskResult = await unmaskTextMutation.mutateAsync({
          maskedText: maskedContent,
          mapping: maskMapping
        });
        if (unmaskResult && unmaskResult.text && setInput) {
          setInput(unmaskResult.text);
        }
      } catch (error) {
        console.error('Error unmasking content:', error);
      } finally {
        setIsFetchingMask(false);
        setIsMasked(false);
      }
    } else {
      // Simple toggle when no mapping exists
      setIsMasked(!isMasked);
    }
  };
  // Remove attached file by index
  const removeFile = (index: number) => {
    onRemoveFile(index);
  };

  // Add file to attachments (upload immediately)
  const addFileToAttachments = async (file: File) => {
    try {
      await onFileAttach([file]);
    } catch (error) {
      console.error('File upload failed:', error);
      // Show error to user if needed
    }
  };

  const onSubmit = async (
    e: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    e.preventDefault();
    if (!input.trim() && attachedFiles.length ===0) return;
    
    // If content is masked, we need to unmask it before sending
    let messageToSend = input;
    if (isMasked && Object.keys(maskMapping).length > 0) {
      try {
        const unmaskResult = await unmaskTextMutation.mutateAsync({
          maskedText: maskedContent,
          mapping: maskMapping
        });
        if (unmaskResult && unmaskResult.text) {
          messageToSend = unmaskResult.text;
        }
      } catch (error) {
        console.error('Error unmasking content for submission:', error);
      }
    }
    
    // Clear the input field and attachments
    setInput!(messageToSend); // Set the unmasked content temporarily
    setMaskedContent('');
    setMaskMapping({});
    setIsMasked(false);

    // Call handleSubmit - useChat will handle the rest
    handleSubmit(e);
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

    const filesToUpload: File[] = [];

    // Collect all files from paste
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          filesToUpload.push(file);
        }
      }
    }

    // If we have files, prevent default paste and upload them
    if (filesToUpload.length > 0) {
      e.preventDefault();
      try {
        // Upload all files at once
        await onFileAttach(filesToUpload);
      } catch (error) {
        console.error('Error handling pasted files:', error);
        const errorMsg = `Error processing ${filesToUpload.length} pasted file(s): ${error}`;
        alert(errorMsg);
      }
    }
  };

  // Handle file input change (support multiple files)
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Convert FileList to Array and upload all at once
      const fileArray = Array.from(files);
      onFileAttach(fileArray);
    }
    // Reset input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  // Trigger file input
  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full relative">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInput}
        multiple
        accept="image/*,.pdf,.doc,.docx,.txt,.csv,.xlsx,.xls"
        className="hidden"
      />
      
      {/* Safety Warnings */}
      {alertContent  && (
        <SafetyWarning
          alertContent={alertContent}
          type="message"
        />
      )}
      

      <form onSubmit={onSubmit}>
        <div className="bg-neutral-50 dark:bg-neutral-800 p-3 rounded-xl space-y-2 max-w-4xl mx-4 md:mx-8 lg:mx-auto">
        <FileUrlPreview
          attachedFiles={attachedFiles}
          onRemoveFile={removeFile}
        />
        
        <div className="relative">
          {/* Textarea for message input */}
          <textarea
            value={isMasked ? maskedContent : input}
            onChange={handleInputChange}
            onPaste={handlePaste}
            placeholder={isFetchingMask ? "Masking content..." : "Ask anything..."}
            className={`w-full bg-transparent p-2 outline-none resize-none rounded-md ${isMasked && sensitiveFound ? 'bg-yellow-50/20 dark:bg-yellow-300/30 ' : ''}`}
            rows={Math.min((isMasked ? maskedContent : input).split('\n').length, 8)}
            disabled={isLoading || isFetchingMask}
            onKeyDown={handleKeyDown}
          />
          
          {/* Loading indicator while masking */}
          {isFetchingMask && (
            <div className="absolute right-2 top-2">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          )}
          
          {/* Sensitive content indicator */}
          {isMasked && !isFetchingMask && (
            <div className="absolute right-2 top-2">
              <Badge variant="outline" className="!bg-green-50 !text-green-800 !300 flex items-center gap-1">
                <Check className="h-3 w-3" />
                <span className="text-xs">Content masked</span>
              </Badge>
            </div>
          )}
          
          {/* Validation in progress indicator */}
          {isValidating && input?.trim() && (
            <div className="absolute right-2 top-2">
              <Badge variant="outline" className="bg-blue-50 text-blue-800 border-blue-300 flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span className="text-xs">Checking content...</span>
              </Badge>
            </div>
          )}
        </div>

        {/* Bottom section with options and submit */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* Model Dropdown */}
            <ModelsDropdown model={model} setModel={setModel} />
            
            {/* File attachment button */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={triggerFileInput}
              title="Attach files"
              className="rounded-full h-8 w-8 flex items-center justify-center"
              disabled={isLoading}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            
            {/* Mask/Unmask toggle button */}
            <Button
              type="button"
              variant={sensitiveFound ? "outline" : "ghost"}
              size="icon"
              onClick={() => toggleMask()}
              title={
                isValidating 
                  ? 'Checking for sensitive content...' 
                  : isMasked 
                    ? 'Show original content' 
                    : 'Mask sensitive content'
              }
              className={`rounded-full h-8 w-8 flex items-center justify-center ${
                sensitiveFound ? 'border-yellow-300 hover:bg-yellow-50' : ''
              } ${isValidating ? 'border-blue-300 hover:bg-blue-50' : ''}`}
              disabled={isFetchingMask || !input.trim()}
            >
              {isFetchingMask ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : isValidating ? (
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              ) : isMasked ? (
                <Eye className={`h-4 w-4 ${sensitiveFound ? 'text-yellow-600' : ''}`} />
              ) : (
                <EyeOff className={`h-4 w-4 ${sensitiveFound ? 'text-yellow-600' : ''}`} />
              )}
            </Button>
          </div>

          {/* Submit or stop button */}
          {!isLoading ? (
            <Button
              variant="default"
              size="icon"
              disabled={
                ((!input.trim() && attachedFiles.length === 0) && !isMasked) || 
                (isMasked && !maskedContent.trim()) || 
                isMasked 
              }
              type="submit"
              className="rounded-full "
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
              <Square />
            </Button>
          )}
        </div>
      </div>
    </form>
    </div>
  );
}
