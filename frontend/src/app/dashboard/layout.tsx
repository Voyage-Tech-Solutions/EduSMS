'use client';

import React from 'react';
import { AuthProvider } from '@/contexts/auth-context';
import { DashboardLayout } from '@/components/layout';

export default function DashboardRootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <AuthProvider>
            <DashboardLayout>
                {children}
            </DashboardLayout>
        </AuthProvider>
    );
}
