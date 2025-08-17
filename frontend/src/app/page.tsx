'use client';

import ChatSection from '@/components/chat/Section';
import { useAuth } from '@/context/AuthContext';
import LandingPage from '@/app/LandingPage';
import { useEffect } from 'react';
import Head from 'next/head';

export default function Home() {
  const { user } = useAuth();

  useEffect(() => {
    // Update document title based on user status
    document.title = user ? 'AI Guardian - Chat' : 'AI Guardian - Welcome';
  }, [user]);

  return (
    <>
      <Head>
        <title>{user ? 'AI Guardian - Chat' : 'AI Guardian - Welcome'}</title>
        <meta name="description" content="AI Guardian - Your intelligent assistant with privacy protection" />
      </Head>
      {user ? <ChatSection /> : <LandingPage />}
    </>
  );
}
