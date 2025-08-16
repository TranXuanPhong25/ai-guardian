import { useRouter } from 'next/navigation';
import ThemeModeToggle from '@/components/ThemeModeToggle';
import Particles from '@/components/ui/particles-bg';
import { Button } from '@/components/ui/button';
import { Shield, Lock, AlertCircle } from 'lucide-react';

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="bg-gradient-to-b from-neutral-100 to-neutral-300 dark:from-neutral-900 dark:to-neutral-800 text-neutral-900 dark:text-neutral-100 overflow-y-none">
      <header className="w-full py-4 px-4 md:px-6 bg-transparent fixed z-[100]">
        <div className="container mx-auto px-4 md:px-6 flex justify-between items-center">
          <h1 className="text-xl md:text-3xl font-bold">AI Guardian</h1>
          <ThemeModeToggle />
        </div>
      </header>

      <div className="h-screen relative">
        <Particles
          particleColors={['#ffffff', '#ffffff']}
          particleCount={200}
          particleSpread={10}
          speed={0.1}
          particleBaseSize={100}
          moveParticlesOnHover={true}
          alphaParticles={false}
          disableRotation={false}
        />
        
        {/* Hero Section */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="container mx-auto px-4 text-center z-10">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-500 to-teal-400">
              Secure AI Conversations
            </h1>
            <p className="text-xl md:text-2xl mb-8 max-w-2xl mx-auto text-neutral-700 dark:text-neutral-300">
              Ai Guardian protects your sensitive information while chatting with AI. 
              Automatic detection and masking of personal data.
            </p>
            
            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12 max-w-4xl mx-auto">
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg">
                <Shield className="w-12 h-12 mb-4 mx-auto text-blue-500" />
                <h3 className="text-xl font-semibold mb-2">Privacy First</h3>
                <p className="text-neutral-600 dark:text-neutral-400">
                  Automatic detection and masking of sensitive information
                </p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg">
                <Lock className="w-12 h-12 mb-4 mx-auto text-blue-500" />
                <h3 className="text-xl font-semibold mb-2">Secure Chat</h3>
                <p className="text-neutral-600 dark:text-neutral-400">
                  End-to-end encryption for all your conversations
                </p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm p-6 rounded-lg">
                <AlertCircle className="w-12 h-12 mb-4 mx-auto text-blue-500" />
                <h3 className="text-xl font-semibold mb-2">Smart Detection</h3>
                <p className="text-neutral-600 dark:text-neutral-400">
                  AI-powered detection of potentially sensitive content
                </p>
              </div>
            </div>
            
            {/* CTA Button */}
            <Button
              onClick={() => router.push('/login')}
              size="lg"
              className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-full text-lg"
            >
              Try AI Guardian Now
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}