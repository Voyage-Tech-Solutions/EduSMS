'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Megaphone } from 'lucide-react';

interface Announcement {
    id: string;
    title: string;
    content: string;
    priority: string;
    date: string;
}

export default function AnnouncementsPage() {
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAnnouncements();
    }, []);

    const fetchAnnouncements = async () => {
        try {
            const token = localStorage.getItem('token');
            if (!token) { setLoading(false); return; }

            const headers = { 'Authorization': `Bearer ${token}` };
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

            const res = await fetch(`${baseUrl}/parent/announcements`, { headers }).catch(() => ({ ok: false } as Response));
            if (res.ok) setAnnouncements(await res.json());
        } catch (error) {
            console.error('Failed to fetch announcements:', error);
        } finally {
            setLoading(false);
        }
    };

    const getPriorityBadge = (priority: string) => {
        switch (priority) {
            case 'urgent':
                return <Badge variant="destructive">Urgent</Badge>;
            case 'high':
                return <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100">Important</Badge>;
            default:
                return null;
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
                    <p className="mt-4 text-slate-500">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">School Announcements</h1>
                <p className="text-slate-500 mt-1">Stay up to date with school news and events</p>
            </div>

            {announcements.length > 0 ? (
                <div className="space-y-4">
                    {announcements.map((ann) => (
                        <Card key={ann.id}>
                            <CardContent className="pt-6">
                                <div className="flex items-start justify-between mb-2">
                                    <h3 className="text-lg font-semibold text-slate-900">{ann.title}</h3>
                                    {getPriorityBadge(ann.priority)}
                                </div>
                                <p className="text-slate-600 whitespace-pre-wrap">{ann.content}</p>
                                {ann.date && (
                                    <p className="text-xs text-slate-400 mt-4">
                                        Posted {new Date(ann.date).toLocaleDateString('en-US', {
                                            weekday: 'long',
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric'
                                        })}
                                    </p>
                                )}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card>
                    <CardContent className="py-12 text-center text-slate-500">
                        <Megaphone className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                        <p className="font-medium">No announcements at this time.</p>
                        <p className="text-sm mt-1">Check back later for school updates.</p>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
