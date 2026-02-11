'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { GraduationCap, TrendingUp, TrendingDown, Award } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function AcademicsPage() {
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        fetchAcademicData();
    }, []);

    const fetchAcademicData = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/principal/academic/performance`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) setData(await res.json());
        } catch (error) {
            console.error('Failed to fetch academic data:', error);
        }
    };

    return (
        <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">Academic Performance</h1>
                    <p className="text-slate-500 mt-1">School-wide academic insights and trends</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Award className="h-5 w-5 text-emerald-500" />
                                Pass Rate
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-3xl font-bold">{data?.pass_rate || 0}%</p>
                            <p className="text-sm text-slate-500 mt-1">Overall school performance</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <GraduationCap className="h-5 w-5 text-blue-500" />
                                Assessment Completion
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-3xl font-bold">{data?.completion_rate || 0}%</p>
                            <p className="text-sm text-slate-500 mt-1">Students assessed</p>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Reports Submitted</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-3xl font-bold">{data?.reports_submitted || 0}/{data?.total_teachers || 0}</p>
                            <p className="text-sm text-slate-500 mt-1">Teachers completed</p>
                        </CardContent>
                    </Card>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Grade-Level Performance</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-slate-500">Detailed grade analysis coming soon</p>
                        <Button variant="outline" className="mt-4">View Full Report</Button>
                    </CardContent>
                </Card>
        </div>
    );
}
