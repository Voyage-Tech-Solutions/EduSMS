'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface ActivityItem {
    id: string;
    title: string;
    description: string;
    time: string;
    type: 'student' | 'payment' | 'attendance' | 'report';
}

const mockActivities: ActivityItem[] = [
    {
        id: '1',
        title: 'New Student Enrolled',
        description: 'Emily Johnson enrolled in Grade 5A',
        time: '2 hours ago',
        type: 'student',
    },
    {
        id: '2',
        title: 'Fee Payment Received',
        description: '$1,200 received from Michael Brown',
        time: '3 hours ago',
        type: 'payment',
    },
    {
        id: '3',
        title: 'Attendance Alert',
        description: '3 students marked absent in Grade 7B',
        time: '4 hours ago',
        type: 'attendance',
    },
    {
        id: '4',
        title: 'Report Approved',
        description: 'Term 1 reports approved for Grade 8',
        time: '5 hours ago',
        type: 'report',
    },
];

const typeColors = {
    student: 'bg-blue-100 text-blue-800',
    payment: 'bg-emerald-100 text-emerald-800',
    attendance: 'bg-amber-100 text-amber-800',
    report: 'bg-purple-100 text-purple-800',
};

export function RecentActivity() {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-4">
                    {mockActivities.map((activity) => (
                        <div
                            key={activity.id}
                            className="flex items-start gap-4 p-3 rounded-lg hover:bg-slate-50 transition-colors"
                        >
                            <Badge
                                variant="secondary"
                                className={typeColors[activity.type]}
                            >
                                {activity.type}
                            </Badge>
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-slate-900">{activity.title}</p>
                                <p className="text-sm text-slate-500 truncate">
                                    {activity.description}
                                </p>
                            </div>
                            <span className="text-xs text-slate-400 whitespace-nowrap">
                                {activity.time}
                            </span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
