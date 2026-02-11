'use client';

import { LoginForm } from '@/components/auth/login-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { GraduationCap } from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 p-4 overflow-hidden relative">
            {/* Animated background shapes */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-emerald-500/10 blur-3xl animate-pulse" />
                <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-emerald-600/8 blur-3xl animate-pulse [animation-delay:2s]" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-slate-700/10 blur-3xl" />
                <div className="absolute top-20 left-20 h-2 w-2 rounded-full bg-emerald-400/40 animate-ping [animation-delay:1s]" />
                <div className="absolute bottom-32 right-32 h-1.5 w-1.5 rounded-full bg-emerald-300/30 animate-ping [animation-delay:3s]" />
                <div className="absolute top-1/3 right-1/4 h-1 w-1 rounded-full bg-emerald-400/50 animate-ping [animation-delay:2s]" />
            </div>

            {/* Grid pattern overlay */}
            <div
                className="absolute inset-0 opacity-[0.03]"
                style={{
                    backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)',
                    backgroundSize: '60px 60px',
                }}
            />

            <Card className="w-full max-w-md relative z-10 shadow-2xl shadow-emerald-950/50 border-slate-800/50 bg-white/[0.97] backdrop-blur-sm">
                <CardHeader className="text-center pb-2 pt-8">
                    {/* Logo */}
                    <div className="mx-auto mb-5 h-20 w-20 rounded-2xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center shadow-lg shadow-emerald-500/25 rotate-3 hover:rotate-0 transition-transform duration-300">
                        <GraduationCap className="h-10 w-10 text-white" />
                    </div>

                    <CardTitle className="text-3xl font-bold tracking-tight text-slate-900">
                        Welcome back
                    </CardTitle>
                    <CardDescription className="text-slate-500 mt-1.5 text-[15px]">
                        Sign in to your EduCore dashboard
                    </CardDescription>
                </CardHeader>

                <CardContent className="px-8 pb-8">
                    <LoginForm />

                    <div className="mt-6 text-center text-sm text-slate-500">
                        Are you a parent or student?{' '}
                        <Link
                            href="/register"
                            className="text-emerald-600 hover:text-emerald-700 font-semibold transition-colors"
                        >
                            Create an account
                        </Link>
                    </div>

                    {/* Footer */}
                    <div className="mt-8 pt-6 border-t border-slate-100 text-center">
                        <p className="text-xs text-slate-400 tracking-wide">
                            Powered by <span className="font-semibold text-slate-500">EduCore</span>
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
