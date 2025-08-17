import { useChat } from 'ai/react';
import ChatMessages from './Messages';
import MessageInput from './MessageInput';
import { useAuth } from '@/context/AuthContext';
import { useEffect, useState } from 'react';
import { fetchMessagesForSession } from '@/utils/api';
import { MessageWithFiles } from '@/types/chat.interface';
import { v4 as uuidv4 } from 'uuid';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, AlertCircle } from 'lucide-react';
import { useChatSession } from '@/context/ChatSessionContext';
import { ILLMModel } from '@/types/chat.interface';
import { fileService } from '@/services/fileService';

type ChatSectionProps = {
  sessionId?: string;
};

export default function ChatSection({ sessionId }: ChatSectionProps) {
  const { getToken ,user} = useAuth();
  const [jwtToken, setJwtToken] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<MessageWithFiles[]>([]);
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
          const backendMessages = await fetchMessagesForSession(sessionId, jwtToken);
          // Convert backend messages to frontend format
          const messages: MessageWithFiles[] = backendMessages.map((msg: any) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            createdAt: new Date(msg.created_at),
            attached_files: msg.attached_files || []
          }));
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

  // State for attached files - store both fileId and URL
  const [attachedFiles, setAttachedFiles] = useState<{fileId: number, url: string}[]>([]);

  const {
    input,
    isLoading,
    messages,
    handleInputChange,
    handleSubmit,
    setInput,
    stop,
  } = useChat({
    api: `${process.env.NEXT_PUBLIC_CHAT_API}/api/sessions/${currentSessionId}`,
    headers,
    initialMessages: initialMessages,
    streamProtocol: 'data',
    body: { 
      sessionId: currentSessionId, 
      model: model.id,
      fileUrls: attachedFiles.map(file => file.url)
    },
    onFinish: () => {
      // Clear attached files after sending
      setAttachedFiles([]);
      // Refresh chat sessions when message is finished
      refreshChatSessions();
      // Route to the new session page only after the first message is sent
      if (!sessionId) {
        window.history.replaceState(null, '', `/chat/${currentSessionId}`);
      }
    }
  });

  

  // Function to handle file removal
  const handleFileRemove = async (index: number) => {
    const fileInfo = attachedFiles[index];
    if (!fileInfo) return;

    try {
      // Delete from server using fileId
      await fileService.deleteFile(fileInfo.fileId);
      
      // Then remove from local state
      setAttachedFiles(prev => prev.filter((_, i) => i !== index));
    } catch (error) {
      console.error('File deletion error:', error);
      // Still remove from local state even if server deletion fails
      setAttachedFiles(prev => prev.filter((_, i) => i !== index));
      setFetchError('Failed to delete file from server, but removed from chat');
    }
  };

  // Function to handle file attachment (called from MessageInput)
  const handleFileAttach = async (files: File[]) => {
    if(!user) return;
    try {
      const uploadPromises = files.map(file => fileService.uploadFile(file, user?.id));
      const fileInfos = await Promise.all(uploadPromises);
      const newFiles = fileInfos.map(info => ({
        fileId: info.file_id,
        url: info.url
      }));
      setAttachedFiles(prev => [...prev, ...newFiles]);
    } catch (error) {
      console.error('File upload error:', error);
      setFetchError('Failed to upload files');
    }
  };  return (
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
            <div>
              {
                messages.length === 0 && !isLoading && (
                  <div className="flex flex-col items-center justify-center h-full -mt-10">
                    <p className="font-bold text-3xl ">Welcome to AI Guardian</p>
                  </div>
                )
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
                attachedFiles={attachedFiles.map(file => file.url)}
                onFileAttach={handleFileAttach}
                onRemoveFile={handleFileRemove}
              />
            </div>
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
