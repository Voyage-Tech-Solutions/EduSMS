'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatCard } from '@/components/dashboard';
import { Users, CalendarCheck, DollarSign, GraduationCap, Download, FileText } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function ReportsPage() {
    const [period, setPeriod] = useState('month');
    const [stats, setStats] = useState<any>({});

    useEffect(() => {
        loadReportStats();
    }, [period]);

    const loadReportStats = async () => {
        try {
            const response = await fetch(`/api/v1/reports/overview?period=${period}`);
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Failed to load report stats:', error);
            setStats({});
        }
    };

    return (
        <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Reports</h1>
                        <p className="text-slate-500 mt-1">Analytics and insights for your school</p>
                    </div>
                    <div className="flex gap-3">
                        <Select value={period} onValueChange={setPeriod}>
                            <SelectTrigger className="w-48">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="week">This Week</SelectItem>
                                <SelectItem value="month">This Month</SelectItem>
                                <SelectItem value="term">This Term</SelectItem>
                                <SelectItem value="year">This Year</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button variant="outline">
                            <Download className="mr-2 h-4 w-4" />
                            Export All
                        </Button>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <StatCard
                        title="Total Enrollment"
                        value={stats.total_students || 0}
                        description="active students"
                        icon={Users}
                    />
                    <StatCard
                        title="Avg Attendance"
                        value={`${stats.avg_attendance || 0}%`}
                        description="this period"
                        icon={CalendarCheck}
                    />
                    <StatCard
                        title="Fee Collection"
                        value={`$${(stats.total_collected || 0).toLocaleString()}`}
                        description={`${stats.collection_rate || 0}% of target`}
                        icon={DollarSign}
                    />
                    <StatCard
                        title="Academic Avg"
                        value={`${stats.academic_avg || 0}%`}
                        description="all classes"
                        icon={GraduationCap}
                    />
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Quick Reports</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <Button variant="outline" className="h-24 flex-col">
                                <FileText className="h-6 w-6 mb-2" />
                                <span>Student Directory</span>
                            </Button>
                            <Button variant="outline" className="h-24 flex-col">
                                <FileText className="h-6 w-6 mb-2" />
                                <span>Fee Statement</span>
                            </Button>
                            <Button variant="outline" className="h-24 flex-col">
                                <FileText className="h-6 w-6 mb-2" />
                                <span>Attendance Summary</span>
                            </Button>
                            <Button variant="outline" className="h-24 flex-col">
                                <FileText className="h-6 w-6 mb-2" />
                                <span>Grade Report</span>
                            </Button>
                        </div>
                    </CardContent>
                </Card>
        </div>
    );
}
