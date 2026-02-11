'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { School, UserPlus, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';

// Mock schools data - in production, fetch from API
const mockSchools = [
    { id: '11111111-1111-1111-1111-111111111111', name: 'Demo School', code: 'DEMO001' },
    { id: '22222222-2222-2222-2222-222222222222', name: 'Greenwood Academy', code: 'GWA001' },
    { id: '33333333-3333-3333-3333-333333333333', name: 'Sunrise High School', code: 'SHS001' },
];

export default function RegisterPage() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [schools, setSchools] = useState(mockSchools);

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        firstName: '',
        lastName: '',
        phone: '',
        role: '',
        schoolId: '',
        schoolCode: '',
    });

    // In production, fetch schools from Supabase
    useEffect(() => {
        // fetchSchools();
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError('');
    };

    const handleRoleChange = (value: string) => {
        setFormData({ ...formData, role: value });
        setError('');
    };

    const handleSchoolChange = (value: string) => {
        setFormData({ ...formData, schoolId: value });
        setError('');
    };

    const validateForm = () => {
        if (!formData.email || !formData.password || !formData.firstName || !formData.lastName) {
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

        if (!formData.role) {
            setError('Please select your role');
            return false;
        }

        if (!formData.schoolId && !formData.schoolCode) {
            setError('Please select a school or enter a school code');
            return false;
        }

        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!validateForm()) return;

        setIsLoading(true);
        setError('');

        try {
            // In production, this would call Supabase auth
            // 1. Create user in Supabase auth
            // const { data: authData, error: authError } = await supabase.auth.signUp({
            //   email: formData.email,
            //   password: formData.password,
            // });
            // 
            // 2. Create user profile in user_profiles table
            // const { error: profileError } = await supabase.from('user_profiles').insert({
            //   id: authData.user.id,
            //   email: formData.email,
            //   first_name: formData.firstName,
            //   last_name: formData.lastName,
            //   phone: formData.phone,
            //   role: formData.role,
            //   school_id: formData.schoolId,
            //   is_approved: false, // Needs admin approval
            // });

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1500));

            setSuccess(true);
        } catch (err) {
            setError('Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 flex items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardContent className="pt-6">
                        <div className="text-center">
                            <div className="mx-auto w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                                <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                            </div>
                            <h2 className="text-2xl font-bold text-slate-900 mb-2">Registration Submitted!</h2>
                            <p className="text-slate-600 mb-6">
                                Your account has been created. Please check your email to verify your account.
                                A school administrator will review and approve your access.
                            </p>
                            <Link href="/login">
                                <Button className="bg-emerald-600 hover:bg-emerald-700 w-full">
                                    Go to Login
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 flex items-center justify-center p-4">
            <Card className="w-full max-w-lg">
                <CardHeader className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <School className="h-8 w-8 text-emerald-600" />
                        <span className="text-2xl font-bold text-slate-900">EduCore</span>
                    </div>
                    <CardTitle className="text-2xl">Create an Account</CardTitle>
                    <CardDescription>
                        Parents and students can register here.
                        <br />
                        <span className="text-amber-600">Teachers and staff are invited by the school principal.</span>
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
                                    disabled={isLoading}
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
                                    disabled={isLoading}
                                />
                            </div>
                        </div>

                        {/* Email */}
                        <div className="space-y-2">
                            <Label htmlFor="email">Email Address *</Label>
                            <Input
                                id="email"
                                name="email"
                                type="email"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="john.doe@example.com"
                                disabled={isLoading}
                            />
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
                                disabled={isLoading}
                            />
                        </div>

                        {/* Role Selection */}
                        <div className="space-y-2">
                            <Label>I am a *</Label>
                            <Select value={formData.role} onValueChange={handleRoleChange} disabled={isLoading}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select your role" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="parent">
                                        <div className="flex items-center gap-2">
                                            <span>👨‍👩‍👧</span>
                                            <span>Parent / Guardian</span>
                                        </div>
                                    </SelectItem>
                                    <SelectItem value="student">
                                        <div className="flex items-center gap-2">
                                            <span>🎓</span>
                                            <span>Student</span>
                                        </div>
                                    </SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* School Selection */}
                        <div className="space-y-2">
                            <Label>School *</Label>
                            <Select value={formData.schoolId} onValueChange={handleSchoolChange} disabled={isLoading}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select your school" />
                                </SelectTrigger>
                                <SelectContent>
                                    {schools.map((school) => (
                                        <SelectItem key={school.id} value={school.id}>
                                            {school.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-slate-500">
                                Or enter school code:
                                <Input
                                    name="schoolCode"
                                    value={formData.schoolCode}
                                    onChange={handleChange}
                                    placeholder="e.g. DEMO001"
                                    className="mt-1 h-8 text-sm"
                                    disabled={isLoading || !!formData.schoolId}
                                />
                            </p>
                        </div>

                        {/* Password */}
                        <div className="space-y-2">
                            <Label htmlFor="password">Password *</Label>
                            <Input
                                id="password"
                                name="password"
                                type="password"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="At least 8 characters"
                                disabled={isLoading}
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
                                disabled={isLoading}
                            />
                        </div>

                        {/* Submit Button */}
                        <Button
                            type="submit"
                            className="w-full bg-emerald-600 hover:bg-emerald-700"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Creating Account...
                                </>
                            ) : (
                                <>
                                    <UserPlus className="mr-2 h-4 w-4" />
                                    Create Account
                                </>
                            )}
                        </Button>

                        {/* Login Link */}
                        <p className="text-center text-sm text-slate-600">
                            Already have an account?{' '}
                            <Link href="/login" className="text-emerald-600 hover:underline font-medium">
                                Sign in
                            </Link>
                        </p>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
