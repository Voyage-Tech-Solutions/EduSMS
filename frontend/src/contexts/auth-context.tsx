'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getUserProfile, getSession } from '@/lib/supabase';

interface UserProfile {
    id: string;
    email: string;
    role: string;
    first_name: string;
    last_name: string;
    school_id?: string;
}

interface AuthContextType {
    session: any | null;
    profile: UserProfile | null;
    isLoading: boolean;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const [session, setSession] = useState<any | null>(null);
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const initAuth = async () => {
            try {
                const currentSession = await getSession();
                setSession(currentSession);

                if (currentSession) {
                    const userProfile = await getUserProfile();
                    setProfile(userProfile);
                }
            } catch (error) {
                console.error('Auth initialization error:', error);
            } finally {
                setIsLoading(false);
            }
        };

        initAuth();
    }, []);

    const signOut = async () => {
        const { auth } = await import('@/lib/supabase');
        await auth.signOut();
        setSession(null);
        setProfile(null);
        router.push('/login');
    };

    return (
        <AuthContext.Provider value={{ session, profile, isLoading, signOut }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
