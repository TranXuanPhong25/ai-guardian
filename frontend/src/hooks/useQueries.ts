'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createClient } from '@/utils/supabase/client';
import { getAllChatSessions } from '@/utils/api';
import { IChatSession } from '@/types/chat.interface';
import { maskingService } from '@/services/maskingService';
import { fileService } from '@/services/fileService';

// Auth queries
export const useUser = () => {
  return useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();
      if (data.user && data.user.email) {
        return { email: data.user.email, id: data.user.id };
      }
      return null;
    },
    staleTime: Infinity,
  });
};

export const useAuthSession = () => {
  return useQuery({
    queryKey: ['auth-session'],
    queryFn: async () => {
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      return data.session;
    },
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
};

// Chat sessions queries
export const useChatSessions = () => {
  const { data: session } = useAuthSession();
  
  return useQuery({
    queryKey: ['chat-sessions'],
    queryFn: async () => {
      if (!session?.access_token) {
        throw new Error('No access token available');
      }
      return getAllChatSessions(session.access_token);
    },
    enabled: !!session?.access_token,
  });
};

// Masking queries
export const useSensitiveValidation = (content: string, enabled = true) => {
  return useQuery({
    queryKey: ['sensitive-validation', content],
    queryFn: async () => {
      if (!content?.trim()) return { alert: null };
      return maskingService.validateSensitive(content);
    },
    enabled: enabled && !!content?.trim(),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    retry: 1,
  });
};

export const useMaskingOperations = () => {
  const queryClient = useQueryClient();
  
  const maskText = useMutation({
    mutationFn: async ({ sessionId, content }: { sessionId: string; content: string }) => {
      return maskingService.maskText(sessionId, content);
    },
  });
  
  const unmaskText = useMutation({
    mutationFn: async ({ maskedText, mapping }: { maskedText: string; mapping: Record<string, string> }) => {
      return maskingService.unmaskText(maskedText, mapping);
    },
  });
  
  return { maskText, unmaskText };
};

// File management hooks
export const useFiles = (userId:string) => {
  return useQuery({
    queryKey: ['files', userId],
    queryFn: () => fileService.getFiles(userId),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes cache for file list
  });
};

export const useFileUpload = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, userId }: { file: File; userId: string }) => 
      fileService.uploadFile(file, userId),
    onSuccess: (_, variables) => {
      // Invalidate files list to refresh after upload
      queryClient.invalidateQueries({ queryKey: ['files', variables.userId] });
    },
  });
};


export const useFileDelete = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (fileId: number) => fileService.deleteFile(fileId),
    onSuccess: (deletedFile) => {
      // Remove deleted file from all user file lists
      queryClient.invalidateQueries({ queryKey: ['files'] });
      
      // Optionally update cache directly for better UX
      queryClient.setQueriesData(
        { queryKey: ['files'] },
        (oldData: any) => oldData?.filter((file: any) => file.file_id !== deletedFile.file_id)
      );
    },
  });
};

export const useFileExtract = () => {
  return useMutation({
    mutationFn: (fileId: number) => fileService.extractText(fileId),
  });
};

// Mutations
export const useLogout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      const supabase = createClient();
      await supabase.auth.signOut();
    },
    onSuccess: () => {
      // Clear all queries from the cache on logout
      queryClient.clear();
    },
  });
};
