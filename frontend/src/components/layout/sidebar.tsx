'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/auth-context';
import {
    LayoutDashboard,
    Users,
    GraduationCap,
    CreditCard,
    CalendarCheck,
    FileText,
    Settings,
    LogOut,
    School,
    UserPlus,
    BookOpen,
    Bell,
    ChevronLeft,
    ChevronRight,
    Building2,
    Shield,
    Activity,
    Flag,
    AlertTriangle,
    TrendingUp,
    Briefcase,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';

interface NavItem {
    title: string;
    href: string;
    icon: React.ElementType;
    roles?: string[];
}

const systemAdminNavItems: NavItem[] = [
    { title: 'Overview', href: '/dashboard/sysadmin', icon: LayoutDashboard },
    { title: 'Tenants', href: '/dashboard/sysadmin/tenants', icon: Building2 },
    { title: 'Billing', href: '/dashboard/sysadmin/billing', icon: CreditCard },
    { title: 'Features', href: '/dashboard/sysadmin/features', icon: Flag },
    { title: 'Security', href: '/dashboard/sysadmin/security', icon: Shield },
    { title: 'Monitoring', href: '/dashboard/sysadmin/monitoring', icon: Activity },
    { title: 'Support', href: '/dashboard/sysadmin/support', icon: Bell },
    { title: 'Settings', href: '/dashboard/sysadmin/settings', icon: Settings },
];

const teacherNavItems: NavItem[] = [
    { title: 'Dashboard', href: '/dashboard/teacher', icon: LayoutDashboard },
    { title: 'My Timetable', href: '/dashboard/teacher/timetable', icon: CalendarCheck },
    { title: 'My Classes', href: '/dashboard/teacher/classes', icon: BookOpen },
    { title: 'Attendance', href: '/dashboard/teacher/attendance', icon: CalendarCheck },
    { title: 'Gradebook', href: '/dashboard/teacher/gradebook', icon: GraduationCap },
    { title: 'Assignments', href: '/dashboard/teacher/assignments', icon: FileText },
    { title: 'Planning', href: '/dashboard/teacher/planning', icon: BookOpen },
    { title: 'Messages', href: '/dashboard/teacher/messages', icon: Bell },
    { title: 'Reports', href: '/dashboard/teacher/reports', icon: FileText },
];

const parentNavItems: NavItem[] = [
    { title: 'Home', href: '/dashboard/parent-portal', icon: LayoutDashboard },
    { title: 'My Children', href: '/dashboard/parent-portal/children', icon: Users },
    { title: 'Attendance', href: '/dashboard/parent-portal/attendance', icon: CalendarCheck },
    { title: 'Academics', href: '/dashboard/parent-portal/academics', icon: GraduationCap },
    { title: 'Assignments', href: '/dashboard/parent-portal/assignments', icon: BookOpen },
    { title: 'Fees & Payments', href: '/dashboard/parent-portal/fees', icon: CreditCard },
    { title: 'Documents', href: '/dashboard/parent-portal/documents', icon: FileText },
    { title: 'Messages', href: '/dashboard/parent-portal/messages', icon: Bell },
    { title: 'School Notices', href: '/dashboard/parent-portal/notices', icon: Bell },
    { title: 'Profile', href: '/dashboard/parent-portal/profile', icon: Settings },
];


const officeAdminNavItems: NavItem[] = [
    { title: 'Dashboard', href: '/dashboard/office-admin', icon: LayoutDashboard },
    { title: 'Students', href: '/dashboard/office-admin/students', icon: Users },
    { title: 'Admissions', href: '/dashboard/office-admin/admissions', icon: UserPlus },
    { title: 'Attendance', href: '/dashboard/office-admin/attendance', icon: CalendarCheck },
    { title: 'Fees & Billing', href: '/dashboard/office-admin/fees', icon: CreditCard },
    { title: 'Documents', href: '/dashboard/office-admin/documents', icon: FileText },
    { title: 'Reports', href: '/dashboard/office-admin/reports', icon: FileText },
    { title: 'Settings', href: '/dashboard/office-admin/settings', icon: Settings },
];

const principalNavItems: NavItem[] = [
    { title: 'Dashboard', href: '/dashboard/principal', icon: LayoutDashboard },
    { title: 'Approvals & Decisions', href: '/dashboard/principal/approvals', icon: Shield },
    { title: 'Students', href: '/dashboard/principal/students', icon: Users },
    { title: 'At Risk Students', href: '/dashboard/principal/risk', icon: AlertTriangle },
    { title: 'Academics', href: '/dashboard/principal/academic', icon: BookOpen },
    { title: 'Attendance', href: '/dashboard/principal/attendance', icon: CalendarCheck },
    { title: 'Finance', href: '/dashboard/principal/finance', icon: CreditCard },
    { title: 'Staff', href: '/dashboard/principal/staff', icon: Briefcase },
    { title: 'Reports & Analytics', href: '/dashboard/principal/reports', icon: TrendingUp },
    { title: 'Settings', href: '/dashboard/principal/settings', icon: Settings },
];

const navItems: NavItem[] = [
    { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { title: 'Students', href: '/dashboard/students', icon: Users },
    { title: 'Admissions', href: '/dashboard/admissions', icon: UserPlus, roles: ['office_admin'] },
    { title: 'Attendance', href: '/dashboard/attendance', icon: CalendarCheck },
    { title: 'Fees & Billing', href: '/dashboard/fees', icon: CreditCard, roles: ['office_admin', 'parent'] },
    { title: 'Academics', href: '/dashboard/academics', icon: BookOpen, roles: ['office_admin', 'teacher'] },
    { title: 'Reports', href: '/dashboard/reports', icon: FileText },
    { title: 'Settings', href: '/dashboard/settings', icon: Settings, roles: ['office_admin'] },
];

interface SidebarProps {
    collapsed?: boolean;
    onToggle?: () => void;
}

export function Sidebar({ collapsed = false, onToggle }: SidebarProps) {
    const pathname = usePathname();
    const { profile, signOut } = useAuth();

    // Use role-specific navigation
    const items = profile?.role === 'system_admin' ? systemAdminNavItems : 
                  profile?.role === 'principal' ? principalNavItems :
                  profile?.role === 'office_admin' ? officeAdminNavItems :
                  profile?.role === 'teacher' ? teacherNavItems :
                  profile?.role === 'parent' ? parentNavItems : navItems;

    const filteredNavItems = items.filter((item) => {
        if (!item.roles) return true;
        return profile && item.roles.includes(profile.role);
    });

    const getInitials = () => {
        if (!profile) return 'U';
        return `${profile.first_name?.[0] || ''}${profile.last_name?.[0] || ''}`.toUpperCase();
    };

    return (
        <TooltipProvider delayDuration={0}>
            <aside
                className={cn(
                    'flex flex-col h-screen bg-slate-900 text-white transition-all duration-300',
                    collapsed ? 'w-16' : 'w-64'
                )}
            >
                {/* Logo */}
                <div className="flex items-center justify-between h-16 px-4 border-b border-slate-700">
                    {!collapsed && (
                        <Link href="/dashboard" className="flex items-center gap-2">
                            <School className="h-8 w-8 text-emerald-400" />
                            <span className="font-bold text-xl">EduCore</span>
                        </Link>
                    )}
                    {collapsed && (
                        <School className="h-8 w-8 text-emerald-400 mx-auto" />
                    )}
                </div>

                {/* Nav Items */}
                <nav className="flex-1 py-4 overflow-y-auto">
                    <ul className="space-y-1 px-2">
                        {filteredNavItems.map((item) => {
                            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                            const Icon = item.icon;

                            const linkContent = (
                                <Link
                                    href={item.href}
                                    className={cn(
                                        'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                                        isActive
                                            ? 'bg-emerald-600 text-white'
                                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                                    )}
                                >
                                    <Icon className="h-5 w-5 flex-shrink-0" />
                                    {!collapsed && <span>{item.title}</span>}
                                </Link>
                            );

                            if (collapsed) {
                                return (
                                    <li key={item.href}>
                                        <Tooltip>
                                            <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                                            <TooltipContent side="right">
                                                <p>{item.title}</p>
                                            </TooltipContent>
                                        </Tooltip>
                                    </li>
                                );
                            }

                            return <li key={item.href}>{linkContent}</li>;
                        })}
                    </ul>
                </nav>

                {/* User Profile & Logout */}
                <div className="border-t border-slate-700 p-4">
                    <div className={cn('flex items-center', collapsed ? 'justify-center' : 'gap-3')}>
                        <Avatar className="h-10 w-10 bg-emerald-600">
                            <AvatarFallback className="bg-emerald-600 text-white">
                                {getInitials()}
                            </AvatarFallback>
                        </Avatar>
                        {!collapsed && (
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">
                                    {profile?.first_name} {profile?.last_name}
                                </p>
                                <p className="text-xs text-slate-400 capitalize truncate">
                                    {profile?.role?.replace('_', ' ')}
                                </p>
                            </div>
                        )}
                    </div>

                    <Button
                        variant="ghost"
                        className={cn(
                            'mt-3 text-slate-300 hover:text-white hover:bg-slate-800',
                            collapsed ? 'w-full justify-center px-2' : 'w-full justify-start'
                        )}
                        onClick={signOut}
                    >
                        <LogOut className="h-4 w-4" />
                        {!collapsed && <span className="ml-2">Sign Out</span>}
                    </Button>
                </div>

                {/* Toggle Button */}
                <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-20 -right-3 h-6 w-6 rounded-full bg-slate-700 text-white hover:bg-slate-600"
                    onClick={onToggle}
                >
                    {collapsed ? (
                        <ChevronRight className="h-4 w-4" />
                    ) : (
                        <ChevronLeft className="h-4 w-4" />
                    )}
                </Button>
            </aside>
        </TooltipProvider>
    );
}
