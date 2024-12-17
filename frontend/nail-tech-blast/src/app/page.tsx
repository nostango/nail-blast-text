'use client';
import { useEffect, useState } from 'react';
import { Auth } from 'aws-amplify';
import { useRouter } from 'next/navigation';
import { GroupMessageFormComponent } from '@/components/group-message-form';

export default function Home() {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const checkUser = async () => {
      try {
        const authUser = await Auth.currentAuthenticatedUser();
        setUser(authUser);
      } catch {
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };

    checkUser();
  }, [router]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-4 bg-white rounded shadow-lg">
        <h1 className="text-2xl font-bold text-center mb-4">Send a Text Blast</h1>

        {/* Group Message Form component */}
        <GroupMessageFormComponent />
      </div>
    </div>
  );
}
