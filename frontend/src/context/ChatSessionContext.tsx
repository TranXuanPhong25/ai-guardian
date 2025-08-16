'use client';

import React, { createContext, useContext } from 'react';
import { IChatSession } from '@/types/chat.interface';
import { useQueryClient } from '@tanstack/react-query';
import { useChatSessions } from '@/hooks/useQueries';

interface ChatSessionContextProps {
  loading: boolean;
  error: string | null;
  chatSessions: IChatSession[];
  setChatSessions: (sessions: IChatSession[]) => void;
  refreshChatSessions: () => Promise<void>;
}

const ChatSessionContext = createContext<ChatSessionContextProps | undefined>(
  undefined
);

export const ChatSessionProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = useQueryClient();
  const { 
    data: chatSessions = [], 
    isLoading: loading, 
    error,
    refetch 
  } = useChatSessions();

  const setChatSessions = (sessions: IChatSession[]) => {
    queryClient.setQueryData(['chat-sessions'], sessions);
  };

  const refreshChatSessions = async () => {
    await refetch();
  };

  return (
    <ChatSessionContext.Provider
      value={{
        loading,
        error: error ? error.message : null,
        chatSessions,
        setChatSessions,
        refreshChatSessions,
      }}
    >
      {children}
    </ChatSessionContext.Provider>
  );
};

export const useChatSession = () => {
  const context = useContext(ChatSessionContext);
  if (context === undefined) {
    throw new Error('useChatSession must be used within a ChatSessionProvider');
  }
  return context;
};
