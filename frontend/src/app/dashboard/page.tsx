'use client';

import React from 'react';
import { useAuth } from '@/contexts/auth-context';
import {
    AdminDashboard,
    TeacherDashboard,
    ParentDashboard,
    StudentDashboard,
    SystemAdminDashboard,
} from '@/components/dashboard';
import { OfficeAdminDashboard } from '@/components/dashboard/office-admin-dashboard';
import { Loader2 } from 'lucide-react';

export default function DashboardPage() {
    const { profile, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-[calc(100vh-100px)]">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-600" />
            </div>
        );
    }

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
            case 'student':
                return <StudentDashboard />;
            default:
                return <AdminDashboard />;
        }
    };

    return (
        <>
            {renderDashboard()}
        </>
    );
}
