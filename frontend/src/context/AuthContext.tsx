'use client';

import {
  createContext,
  useContext,
  useEffect,
  ReactNode,
} from 'react';
import { createClient } from '@/utils/supabase/client';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { useUser, useAuthSession, useLogout } from '@/hooks/useQueries';

type User = {
  email: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  logout: () => Promise<void>;
  getToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const queryClient = useQueryClient();
  const router = useRouter();
  
  const { data: user, isLoading: userLoading } = useUser();
  const { data: session, isLoading: sessionLoading } = useAuthSession();
  const { mutateAsync: logoutMutation } = useLogout();

  // Listen for auth state changes
  useEffect(() => {
    const supabase = createClient();

    const { data: authListener } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === 'SIGNED_OUT') {
          queryClient.clear();
        } else {
          // Refetch user and session data
          queryClient.invalidateQueries({ queryKey: ['user'] });
          queryClient.invalidateQueries({ queryKey: ['auth-session'] });
        }
      }
    );

    return () => {
      authListener?.subscription.unsubscribe();
    };
  }, [queryClient]);

  const logout = async () => {
    await logoutMutation();
    router.push('/');
  };

  const getToken = async () => {
    return session?.access_token || null;
  };

  return (
    <AuthContext.Provider value={{ 
      user: user || null,
      loading: userLoading || sessionLoading,
      logout,
      getToken
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
