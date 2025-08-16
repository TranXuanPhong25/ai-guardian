'use client';

import { useChat } from 'ai/react';
import ChatMessages from './Messages';
import MessageInput from './MessageInput';
import { useAuth } from '@/context/AuthContext';
import { useEffect, useState } from 'react';
import { fetchMessagesForSession } from '@/utils/api';
import { Message } from 'ai';
import { v4 as uuidv4 } from 'uuid';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, AlertCircle } from 'lucide-react';
import { useChatSession } from '@/context/ChatSessionContext';
import { ILLMModel } from '@/types/chat.interface';

type ChatSectionProps = {
  sessionId?: string;
};

export default function ChatSection({ sessionId }: ChatSectionProps) {
  const { getToken } = useAuth();
  const [jwtToken, setJwtToken] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>(
    sessionId || uuidv4() // Generate a new sessionId if not provided
  );
  const [fetchLoading, setFetchLoading] = useState(!!sessionId);
  const [fetchError, setFetchError] = useState('');

  const defaultModel: ILLMModel = {
    id: 'gemini-pro',
    name: 'Gemini Pro',
  };
  const [model, setModel] = useState<ILLMModel>(defaultModel);

  const { refreshChatSessions } = useChatSession();

  useEffect(() => {
    async function fetchToken() {
      const token = await getToken();
      setJwtToken(token);
    }

    fetchToken();
  }, [getToken]);

  useEffect(() => {
    async function loadMessages() {
      if (sessionId && jwtToken) {
        setFetchLoading(true);
        setFetchError('');
        try {
          const messages = await fetchMessagesForSession(sessionId, jwtToken);
          setInitialMessages(messages);
        } catch (error) {
          setFetchError(
            `Failed to fetch messages for conversation ${sessionId}`
          );
        } finally {
          setFetchLoading(false);
        }
      }
    }
    loadMessages();
  }, [sessionId, jwtToken]);

  const headers: Record<string, string> = {};

  if (jwtToken) {
    // console.log(jwtToken);
    headers['Authorization'] = `Bearer ${jwtToken}`;
  }

  const {
    input,
    isLoading,
    messages,
    handleInputChange,
    setInput,
    handleSubmit: AIChatSubmit,
    stop,
  } = useChat({
    api: `${process.env.NEXT_PUBLIC_CHAT_API}/api/sessions/${currentSessionId}`,
    headers,
    initialMessages: initialMessages,
    streamProtocol: 'data',
    body: { sessionId: currentSessionId, model: model.id },
    onFinish: () => {
      // Route to the new session page only after the first message is sent
      if (!sessionId) {
        setCurrentSessionId(currentSessionId);
        window.history.replaceState(null, '', `/chat/${currentSessionId}`);
        refreshChatSessions(); // trigger refresh in sidebar
      }
    },
  });
  // Custom submit handler for files
  const handleSubmit = (
    e: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>,
    options?: { data?: FormData; hasFiles?: boolean }
  ) => {
    if (options?.hasFiles && options?.data) {
      // Handle file upload with fetch API
      fetch(`${process.env.NEXT_PUBLIC_CHAT_API}/api/sessions/${currentSessionId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
        },
        body: options.data,
      })
        .then(response => {
          if (!response.ok) throw new Error('Upload failed');
          // Handle response or refresh messages
          return response.json();
        })
        .catch(error => {
          console.error('File upload error:', error);
        });
    } else {
      // Regular text message
      AIChatSubmit(e);
    }
  }; return (
    <div className="h-full flex flex-col overflow-y-auto">
      <div className=" w-full h-full flex flex-col justify-center ">
        {fetchLoading && (
          <div className="flex justify-center items-center pt-10">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
          </div>
        )}
        {!fetchLoading && !fetchError && (
          <>
            {
              messages.length !== 0 &&
              <ChatMessages messages={messages} isLoading={isLoading} sessionId={currentSessionId} />

            }
            <MessageInput
              isLoading={isLoading}
              input={input}
              handleSubmit={handleSubmit}
              handleInputChange={handleInputChange}
              setInput={setInput}
              model={model}
              setModel={setModel}
              stop={stop}
              sessionId={currentSessionId}
            />
          </>
        )}
        {fetchError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{fetchError}</AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}
