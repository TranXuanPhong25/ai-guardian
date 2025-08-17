'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import SignUp from './SignUp';
import Head from 'next/head';

const SignUpPage = () => {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Update document title
    document.title = 'Sign Up - AI Guardian';
  }, []);

  useEffect(() => {
    if (user) {
      router.push('/');
    }
  }, [user, router]);

  return (
    <>
      <Head>
        <title>Sign Up - AI Guardian</title>
        <meta name="description" content="Create an account with AI Guardian" />
      </Head>
      <div className="flex items-center justify-center h-full">
        <SignUp />
      </div>
    </>
  );
};

export default SignUpPage;
