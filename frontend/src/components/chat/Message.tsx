import { useCopyToClipboard } from './hooks/useCopyToClipboard';
import { Check, Copy } from 'lucide-react';
import ChatAvatar from './Avatar';
import Markdown from './Markdown';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Message } from 'ai';
import { cn } from '@/lib/utils';

export default function ChatMessage({ chatMessage }: { chatMessage: Message }) {
  const { isCopied, copyToClipboard } = useCopyToClipboard({ timeout: 2000 });

  return (
    <Card className={cn(
      "flex items-start gap-4 px-2 md:px-4  !border-0 shadow-none dark:bg-transparent",

    )}>
      <CardContent className="group flex flex-col flex-1 gap-2 relative p-0">
        <ChatAvatar role={chatMessage.role} />
        <div className="flex-1 pt-1 break-words overflow-hidden">
          <Markdown content={chatMessage.content} role={chatMessage.role} />
        </div>
        <Button
          onClick={() => copyToClipboard(chatMessage.content)}
          variant="outline"
          size="icon"
          className={cn(
            "h-8 w-8 min-w-[32px] flex items-center justify-center",
            chatMessage.role === 'user' ? 'ml-auto' : 'mr-auto',
          )}
        >
          {isCopied ? (
            <Check className="h-4 w-4 text-foreground" />
          ) : (
            <Copy className="h-4 w-4 text-foreground" />
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
