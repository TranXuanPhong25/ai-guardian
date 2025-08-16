import { useCopyToClipboard } from './hooks/useCopyToClipboard';
import { Check, Copy, Eye, EyeOff } from 'lucide-react';
import ChatAvatar from './Avatar';
import Markdown from './Markdown';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Message } from 'ai';
import { cn } from '@/lib/utils';
import { useState, useEffect } from 'react';
import { maskingService } from '@/services/maskingService';
import { Badge } from '@/components/ui/badge';

export default function ChatMessage({ chatMessage }: { chatMessage: Message }) {
  const { isCopied, copyToClipboard } = useCopyToClipboard({ timeout: 2000 });
  const [isMasked, setIsMasked] = useState(false);
  const [maskedContent, setMaskedContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasSensitive, setHasSensitive] = useState(false);
  const [mapping, setMapping] = useState<Record<string, string>>({});

  // Check for sensitive content and prepare masked version
  useEffect(() => {
    const checkAndMaskContent = async () => {
      if (!chatMessage.content) return;
      
      try {
        // Check if the message contains sensitive information
        const validationResult = await maskingService.validateSensitive(chatMessage.content);
        setHasSensitive(validationResult.sensitive);

        // If it contains sensitive data, prepare masked version
        if (validationResult.sensitive) {
          const maskedResult = await maskingService.maskText(chatMessage.content);
          setMaskedContent(maskedResult.masked_text);
          setMapping(maskedResult.mapping);
        }
      } catch (error) {
        console.error('Error checking for sensitive content:', error);
      }
    };

    checkAndMaskContent();
  }, [chatMessage.content]);

  // Toggle between masked and unmasked content
  const toggleMask = () => {
    setIsMasked(!isMasked);
  };

  // Get the current content to display
  const displayContent = isMasked && hasSensitive ? maskedContent : chatMessage.content;

  return (
    <Card className={cn(
      "flex items-start gap-4 px-2 md:px-4 !border-0 shadow-none dark:bg-transparent",
    )}>
      <CardContent className="group flex flex-col flex-1 gap-2 relative p-0">
        <ChatAvatar role={chatMessage.role} />
        <div className="flex-1 pt-1 break-words overflow-hidden">
          <Markdown content={displayContent} role={chatMessage.role} />
        </div>
        <div className="flex items-center gap-1 mt-1">
          {/* Copy button */}
          <div className={
            chatMessage.role === 'user' ? 'ml-auto': ""
          }/>
            <Button
              onClick={() => copyToClipboard(chatMessage.content)}
            variant="outline"
            size="icon"
            className={cn(
              "h-8 w-8 min-w-[32px] flex items-center justify-center",
              //  
            )}
          >
            {isCopied ? (
              <Check className="h-4 w-4 text-foreground" />
            ) : (
              <Copy className="h-4 w-4 text-foreground" />
            )}
          </Button>
          
          {/* Mask/Unmask toggle button - only show if content has sensitive information */}
          {hasSensitive && (
            <Button
              onClick={toggleMask}
              variant="outline"
              size="icon"
              className={cn(
                "h-8 w-8 min-w-[32px] flex items-center justify-center",
                // chatMessage.role === 'user' ? 'ml-0' : 'mr-0',
                !isMasked ? "bg-yellow-50 dark:bg-yellow-900/20" : ""
              )}
              title={!isMasked ? "Show original content" : "Mask sensitive content"}
            >
              {!isMasked ? (
                <Eye className="h-4 w-4 text-foreground" />
              ) : (
                <EyeOff className="h-4 w-4 text-foreground" />
              )}
            </Button>
          )}
          {hasSensitive && (
            <div className="flex  items-center">
              <Badge 
                variant="outline" 
                className={cn(
                  "text-xs bg-yellow-50/50 text-yellow-800 border-yellow-300 ",
                  isMasked ? "bg-yellow-100/50" : ""
                )}
              >
                {isMasked ? "Masked content" : "Contains sensitive data"}
              </Badge>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
