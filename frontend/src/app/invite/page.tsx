'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { School, UserPlus, Loader2, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface InvitationData {
    email: string;
    role: string;
    schoolName: string;
    invitedBy: string;
    expiresAt: string;
}

function AcceptInvitationContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');

    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [invitation, setInvitation] = useState<InvitationData | null>(null);

    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        phone: '',
        password: '',
        confirmPassword: '',
    });

    // Verify invitation token on mount
    useEffect(() => {
        if (!token) {
            setError('Invalid invitation link. No token provided.');
            setIsLoading(false);
            return;
        }

        const verifyInvitation = async () => {
            try {
                // Simulate API call
                await new Promise(resolve => setTimeout(resolve, 1000));

                // Mock invitation data for demo
                setInvitation({
                    email: 'teacher@demoschool.edu',
                    role: 'teacher',
                    schoolName: 'Demo School',
                    invitedBy: 'Principal Admin',
                    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
                });
            } catch (err) {
                setError('This invitation link is invalid or has expired.');
            } finally {
                setIsLoading(false);
            }
        };

        verifyInvitation();
    }, [token]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const validateForm = () => {
        if (!formData.firstName || !formData.lastName || !formData.password) {
            setError('Please fill in all required fields');
            return false;
        }

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return false;
        }

        if (formData.password.length < 8) {
            setError('Password must be at least 8 characters');
            return false;
        }

        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) return;

        setIsSubmitting(true);
        setError('');

        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1500));
            setSuccess(true);
        } catch (err) {
            setError('Failed to create account. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    // Loading state
    if (isLoading) {
        return (
            <Card className="w-full max-w-md">
                <CardContent className="pt-6">
                    <div className="text-center">
                        <Loader2 className="h-12 w-12 animate-spin text-emerald-600 mx-auto mb-4" />
                        <p className="text-slate-600">Verifying invitation...</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Invalid/expired invitation
    if (!invitation && error) {
        return (
            <Card className="w-full max-w-md">
                <CardContent className="pt-6">
                    <div className="text-center">
                        <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                            <XCircle className="h-8 w-8 text-red-600" />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900 mb-2">Invalid Invitation</h2>
                        <p className="text-slate-600 mb-6">{error}</p>
                        <Link href="/login">
                            <Button variant="outline">Go to Login</Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Success state
    if (success) {
        return (
            <Card className="w-full max-w-md">
                <CardContent className="pt-6">
                    <div className="text-center">
                        <div className="mx-auto w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                            <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                        </div>
                        <h2 className="text-2xl font-bold text-slate-900 mb-2">Account Created!</h2>
                        <p className="text-slate-600 mb-6">
                            Your account has been created successfully. Please check your email to verify your account,
                            then you can sign in.
                        </p>
                        <Link href="/login">
                            <Button className="bg-emerald-600 hover:bg-emerald-700 w-full">
                                Go to Login
                            </Button>
                        </Link>
                    </div>
                </CardContent>
            </Card>
        );
    }

    // Registration form
    return (
        <Card className="w-full max-w-lg">
            <CardHeader className="text-center">
                <div className="flex items-center justify-center gap-2 mb-4">
                    <School className="h-8 w-8 text-emerald-600" />
                    <span className="text-2xl font-bold text-slate-900">EduCore</span>
                </div>
                <CardTitle className="text-2xl">Accept Invitation</CardTitle>
                <CardDescription>
                    You have been invited to join <strong>{invitation?.schoolName}</strong> as a{' '}
                    <strong className="capitalize">{invitation?.role}</strong>.
                    <br />
                    <span className="text-sm text-slate-500">Invited by: {invitation?.invitedBy}</span>
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="p-3 rounded-lg bg-red-50 border border-red-200 flex items-center gap-2 text-red-700 text-sm">
                            <AlertCircle className="h-4 w-4" />
                            {error}
                        </div>
                    )}

                    {/* Email (read-only) */}
                    <div className="space-y-2">
                        <Label>Email Address</Label>
                        <Input
                            value={invitation?.email || ''}
                            disabled
                            className="bg-slate-50"
                        />
                    </div>

                    {/* Name Fields */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="firstName">First Name *</Label>
                            <Input
                                id="firstName"
                                name="firstName"
                                value={formData.firstName}
                                onChange={handleChange}
                                placeholder="John"
                                disabled={isSubmitting}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="lastName">Last Name *</Label>
                            <Input
                                id="lastName"
                                name="lastName"
                                value={formData.lastName}
                                onChange={handleChange}
                                placeholder="Doe"
                                disabled={isSubmitting}
                            />
                        </div>
                    </div>

                    {/* Phone */}
                    <div className="space-y-2">
                        <Label htmlFor="phone">Phone Number</Label>
                        <Input
                            id="phone"
                            name="phone"
                            type="tel"
                            value={formData.phone}
                            onChange={handleChange}
                            placeholder="+1 555-123-4567"
                            disabled={isSubmitting}
                        />
                    </div>

                    {/* Password */}
                    <div className="space-y-2">
                        <Label htmlFor="password">Create Password *</Label>
                        <Input
                            id="password"
                            name="password"
                            type="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="At least 8 characters"
                            disabled={isSubmitting}
                        />
                    </div>

                    {/* Confirm Password */}
                    <div className="space-y-2">
                        <Label htmlFor="confirmPassword">Confirm Password *</Label>
                        <Input
                            id="confirmPassword"
                            name="confirmPassword"
                            type="password"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder="Re-enter your password"
                            disabled={isSubmitting}
                        />
                    </div>

                    {/* Submit Button */}
                    <Button
                        type="submit"
                        className="w-full bg-emerald-600 hover:bg-emerald-700"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Creating Account...
                            </>
                        ) : (
                            <>
                                <UserPlus className="mr-2 h-4 w-4" />
                                Accept & Create Account
                            </>
                        )}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}

function LoadingFallback() {
    return (
        <Card className="w-full max-w-md">
            <CardContent className="pt-6">
                <div className="text-center">
                    <Loader2 className="h-12 w-12 animate-spin text-emerald-600 mx-auto mb-4" />
                    <p className="text-slate-600">Loading...</p>
                </div>
            </CardContent>
        </Card>
    );
}

export default function AcceptInvitationPage() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 flex items-center justify-center p-4">
            <Suspense fallback={<LoadingFallback />}>
                <AcceptInvitationContent />
            </Suspense>
        </div>
    );
}
