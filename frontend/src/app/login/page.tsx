'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import SignIn from './SignIn';
import Head from 'next/head';

const SignInPage = () => {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Update document title
    document.title = 'Login - AI Guardian';
  }, []);

  useEffect(() => {
    if (user) {
      router.push('/');
    }
  }, [user, router]);

  return (
    <>
      <Head>
        <title>Login - AI Guardian</title>
        <meta name="description" content="Login to AI Guardian" />
      </Head>
      <div className="flex items-center justify-center h-full">
        <SignIn />
      </div>
    </>
  );
};

export default SignInPage;
