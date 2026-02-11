'use client';

import React from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Bell, Search, Settings, User, LogOut, School } from 'lucide-react';

export function Header() {
    const { profile, signOut } = useAuth();

    const getInitials = () => {
        if (!profile) return 'U';
        return `${profile.first_name?.[0] || ''}${profile.last_name?.[0] || ''}`.toUpperCase();
    };

    return (
        <header className="sticky top-0 z-40 h-16 bg-white border-b border-slate-200 px-6">
            <div className="flex items-center justify-between h-full">
                {/* Search */}
                <div className="flex-1 max-w-md">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                        <Input
                            type="search"
                            placeholder="Search students, invoices..."
                            className="pl-10 bg-slate-50 border-slate-200"
                        />
                    </div>
                </div>

                {/* Right Side */}
                <div className="flex items-center gap-4">
                    {/* School Indicator */}
                    <div className="hidden md:flex items-center gap-2 text-sm text-slate-600">
                        <School className="h-4 w-4" />
                        <span>{(profile as any)?.schools?.name || 'EduCore'}</span>
                    </div>

                    {/* Notifications */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="relative">
                                <Bell className="h-5 w-5 text-slate-600" />
                                <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs bg-red-500">
                                    3
                                </Badge>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-80">
                            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="flex flex-col items-start py-3">
                                <span className="font-medium">New admission request</span>
                                <span className="text-sm text-slate-500">John Smith applied for Grade 5</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem className="flex flex-col items-start py-3">
                                <span className="font-medium">Fee payment received</span>
                                <span className="text-sm text-slate-500">$500 received from Jane Doe</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem className="flex flex-col items-start py-3">
                                <span className="font-medium">Report pending approval</span>
                                <span className="text-sm text-slate-500">Grade 8 Term 1 reports ready</span>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-center text-emerald-600">
                                View all notifications
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* User Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="flex items-center gap-2 px-2">
                                <Avatar className="h-8 w-8 bg-emerald-600">
                                    <AvatarFallback className="bg-emerald-600 text-white text-sm">
                                        {getInitials()}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="hidden md:block text-left">
                                    <p className="text-sm font-medium">
                                        {profile?.first_name} {profile?.last_name}
                                    </p>
                                    <p className="text-xs text-slate-500 capitalize">
                                        {profile?.role?.replace('_', ' ')}
                                    </p>
                                </div>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                            <DropdownMenuLabel>My Account</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem>
                                <User className="mr-2 h-4 w-4" />
                                Profile
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                                <Settings className="mr-2 h-4 w-4" />
                                Settings
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={signOut} className="text-red-600">
                                <LogOut className="mr-2 h-4 w-4" />
                                Sign Out
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>
        </header>
    );
}
