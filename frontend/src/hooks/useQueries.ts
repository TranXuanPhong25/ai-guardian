'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createClient } from '@/utils/supabase/client';
import { getAllChatSessions } from '@/utils/api';
import { IChatSession } from '@/types/chat.interface';

// Auth queries
export const useUser = () => {
  return useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();
      if (data.user && data.user.email) {
        return { email: data.user.email };
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
