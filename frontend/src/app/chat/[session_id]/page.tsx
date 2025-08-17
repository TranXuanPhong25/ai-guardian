'use client';

import ChatSection from '@/components/chat/Section';
import { useAuth } from '@/context/AuthContext';
import { use, useEffect } from 'react';
import Head from 'next/head';

export default function Home({ params }: { params: Promise<{ session_id: string }> }) {
  const { user } = useAuth();

  const { session_id: sessionId } =  use(params);

  useEffect(() => {
    // Update document title
    document.title = `Chat Session - AI Guardian`;
  }, [sessionId]);

  return (
    <>
      <Head>
        <title>Chat Session - AI Guardian</title>
        <meta name="description" content="AI Guardian chat session" />
      </Head>
      {user ? (
        <ChatSection sessionId={sessionId} />
      ) : (
        <div className='w-full h-screen flex items-center justify-center'>Hello, World! No user logged in!</div>
      )}
    </>
  );
}

