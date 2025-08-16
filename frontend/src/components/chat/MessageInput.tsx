import { Button } from '@/components/ui/button';
import { ArrowUp, X, Paperclip, Eye, EyeOff, AlertTriangle, Loader2, Square, Check } from 'lucide-react';
import { ChatHandler, ILLMModel } from '@/types/chat.interface';
import { AttachedFile } from '@/types/file.interface';
import ModelsDropdown from './ModelsDropdown';
import FilePreview from './FilePreview';
import SafetyWarning from '@/components/SafetyWarning';
import { useState, useRef, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { useSensitiveValidation, useMaskingOperations } from '@/hooks/useQueries';

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
  sessionId: string;
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
  sessionId,
}: MessageInputProps) {
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [messageAnalysis, setMessageAnalysis] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [isMasked, setIsMasked] = useState(false);
  const [maskedContent, setMaskedContent] = useState<string>('');
  const [isFetchingMask, setIsFetchingMask] = useState(false);
  const [maskMapping, setMaskMapping] = useState<Record<string, string>>({});

  // Use React Query for sensitive validation  
  const { data: validationResult } = useSensitiveValidation(input || '', !!input?.trim());
  const sensitiveFound = validationResult?.alert !== null;

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

    // Analyze file safety

    // Call the onFileUpload prop if provided
    if (onFileUpload) {
      try {
        await onFileUpload(file);
      } catch (error) {
        // Remove file from attachments if upload fails
        setAttachedFiles(prev => prev.filter(f => f.id !== fileId));
      }
    }
  };

  // Auto-analyze with React Query - no manual useEffect needed
  useEffect(() => {
    // Just update UI states based on React Query results
    setShowWarning(sensitiveFound);
  }, [sensitiveFound]);

  const onSubmit = async (
    e: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    e.preventDefault();
    if (!input.trim() && attachedFiles.length === 0) return;

    // Create FormData for file uploads
    const formData = new FormData();
    
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
    
    formData.append('message', messageToSend);
    formData.append('model', model.id);

    // Add files to FormData
    attachedFiles.forEach((attachedFile) => {
      formData.append('files', attachedFile.file);
    });

    // Clear the input field and attachments
    setInput!('');
    setAttachedFiles([]);
    setMaskedContent('');
    setMaskMapping({});
    setIsMasked(false);
    // Remove setSensitiveFound since it's computed from React Query

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
    <div className="w-full relative">
      {/* Safety Warnings */}
      {showWarning && messageAnalysis  && (
        <SafetyWarning
          alertContent={messageAnalysis}
          type="message"
          onDismiss={() => setShowWarning(false)}
          onProceed={() => setShowWarning(false)}
        />
      )}
      

      <form onSubmit={onSubmit}>
        <div className="bg-neutral-50 dark:bg-neutral-800 p-3 rounded-xl space-y-2 max-w-4xl mx-4 md:mx-8 lg:mx-auto">
        <FilePreview
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
            className={`w-full bg-transparent p-2 outline-none resize-none ${isMasked && sensitiveFound ? 'bg-yellow-50/20 dark:bg-yellow-900/10' : ''}`}
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
              <Badge variant="outline" className="bg-green-50 text-green-800 border-green-300 flex items-center gap-1">
                <Check className="h-3 w-3" />
                <span className="text-xs">Content masked</span>
              </Badge>
            </div>
          )}
        </div>

        {/* Bottom section with options and submit */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* Model Dropdown */}
            <ModelsDropdown model={model} setModel={setModel} />
            
            {/* Mask/Unmask toggle button */}
            <Button
              type="button"
              variant={sensitiveFound ? "outline" : "ghost"}
              size="icon"
              onClick={() => toggleMask()}
              title={isMasked ? 'Show original content' : 'Mask sensitive content'}
              className={`rounded-full h-8 w-8 flex items-center justify-center ${sensitiveFound ? 'border-yellow-300 hover:bg-yellow-50' : ''}`}
              disabled={isFetchingMask || !input.trim()}
            >
              {isFetchingMask ? (
                <Loader2 className="h-4 w-4 animate-spin" />
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
                (!input.trim() && !isMasked) || 
                (isMasked && !maskedContent.trim()) || 
                isMasked ||
                isAnalyzing
              }
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
              <Square />
            </Button>
          )}
        </div>
      </div>
    </form>
    </div>
  );
}
