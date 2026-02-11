'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, AlertCircle, Mail, Lock } from 'lucide-react';
import { auth, getUserProfile } from '@/lib/supabase';

const loginSchema = z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
    const router = useRouter();
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
    });

    const onSubmit = async (data: LoginFormData) => {
        setIsLoading(true);
        setError('');

        try {
            const { user } = await auth.signIn(data.email, data.password);

            if (user) {
                const profile = await getUserProfile();

                if (profile) {
                    router.push('/dashboard');
                } else {
                    router.push('/dashboard');
                }
            }
        } catch (err: any) {
            setError(err.message || 'Failed to sign in');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {error && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2 animate-in fade-in duration-200">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    {error}
                </div>
            )}

            <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-700 font-medium">
                    Email
                </Label>
                <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                        id="email"
                        type="email"
                        placeholder="you@school.edu"
                        {...register('email')}
                        className={`pl-10 h-11 transition-all duration-200 focus:ring-2 focus:ring-emerald-500/20 ${errors.email ? 'border-red-500' : 'border-slate-200 hover:border-slate-300'}`}
                    />
                </div>
                {errors.email && (
                    <p className="text-xs text-red-500">{errors.email.message}</p>
                )}
            </div>

            <div className="space-y-2">
                <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-slate-700 font-medium">
                        Password
                    </Label>
                    <a
                        href="/forgot-password"
                        className="text-sm text-emerald-600 hover:text-emerald-700 font-medium transition-colors"
                    >
                        Forgot password?
                    </a>
                </div>
                <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                        id="password"
                        type="password"
                        placeholder="Enter your password"
                        {...register('password')}
                        className={`pl-10 h-11 transition-all duration-200 focus:ring-2 focus:ring-emerald-500/20 ${errors.password ? 'border-red-500' : 'border-slate-200 hover:border-slate-300'}`}
                    />
                </div>
                {errors.password && (
                    <p className="text-xs text-red-500">{errors.password.message}</p>
                )}
            </div>

            <Button
                type="submit"
                className="w-full h-11 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white font-semibold shadow-md shadow-emerald-600/20 hover:shadow-lg hover:shadow-emerald-600/30 transition-all duration-200"
                disabled={isLoading}
            >
                {isLoading ? (
                    <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Signing in...
                    </>
                ) : (
                    'Sign In'
                )}
            </Button>
        </form>
    );
}
