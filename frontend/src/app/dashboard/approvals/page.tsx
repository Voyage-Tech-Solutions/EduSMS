'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function ApprovalsPage() {
    const [approvals, setApprovals] = useState<any[]>([]);

    useEffect(() => {
        fetchApprovals();
    }, []);

    const fetchApprovals = async () => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/principal/approvals`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) setApprovals(await res.json());
        } catch (error) {
            console.error('Failed to fetch approvals:', error);
        }
    };

    return (
        <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">Approvals Required</h1>
                    <p className="text-slate-500 mt-1">Review and approve pending requests</p>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle>Pending Approvals</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Count</TableHead>
                                    <TableHead>Priority</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {approvals.map((approval, idx) => (
                                    <TableRow key={idx}>
                                        <TableCell className="font-medium">{approval.type}</TableCell>
                                        <TableCell>
                                            <Badge variant="secondary">{approval.count}</Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge className={approval.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}>
                                                {approval.priority}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-right space-x-2">
                                            <Button size="sm" variant="outline">
                                                <CheckCircle className="h-4 w-4 mr-1" />
                                                Review
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
        </div>
    );
}
