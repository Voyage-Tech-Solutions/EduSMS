'use client';

import React from 'react';
import { useAuth } from '@/contexts/auth-context';
import {
    AdminDashboard,
    TeacherDashboard,
    ParentDashboard,
    SystemAdminDashboard,
} from '@/components/dashboard';
import { OfficeAdminDashboard } from '@/components/dashboard/office-admin-dashboard';
import { Loader2, AlertCircle } from 'lucide-react';

export default function DashboardPage() {
    const { profile, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-[calc(100vh-100px)]">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            </div>
        );
    }

    // Redirect to role-specific dashboard
    React.useEffect(() => {
        if (!isLoading && profile?.role) {
            const roleRoutes: Record<string, string> = {
                'system_admin': '/dashboard/system-admin',
                'principal': '/dashboard/principal',
                'office_admin': '/dashboard/office-admin',
                'teacher': '/dashboard/teacher',
                'parent': '/dashboard/parent-portal',
            };
            
            const route = roleRoutes[profile.role];
            if (route && window.location.pathname === '/dashboard') {
                window.location.href = route;
            }
        }
    }, [profile, isLoading]);

    const renderDashboard = () => {
        switch (profile?.role) {
            case 'system_admin':
                return <SystemAdminDashboard />;
            case 'principal':
                return <AdminDashboard />;
            case 'office_admin':
                return <OfficeAdminDashboard />;
            case 'teacher':
                return <TeacherDashboard />;
            case 'parent':
                return <ParentDashboard />;
            default:
                return (
                    <div className="flex items-center justify-center h-[calc(100vh-100px)]">
                        <div className="text-center">
                            <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
                            <h2 className="mt-4 text-xl font-semibold text-slate-900">Access Error</h2>
                            <p className="mt-2 text-slate-500">Your role is not recognized. Please contact your administrator.</p>
                        </div>
                    </div>
                );
        }
    };

    return (
        <>
            {renderDashboard()}
        </>
    );
}
