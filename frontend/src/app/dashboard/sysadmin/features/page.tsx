'use client';

import { useEffect, useState } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Flag, Plus, TrendingUp } from 'lucide-react';

export default function FeaturesPage() {
    const [flags, setFlags] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadFlags();
    }, []);

    const loadFlags = async () => {
        try {
            const data = await authFetch('/api/v1/sysadmin/features/flags').then(r => r.json());
            setFlags(data);
        } catch (error) {
            console.error('Failed to load feature flags:', error);
        } finally {
            setLoading(false);
        }
    };

    const toggleFlag = async (flagId: string, enabled: boolean) => {
        try {
            await authFetch(`/api/v1/sysadmin/features/flags/${flagId}/toggle`, {
                method: 'PATCH',
                body: JSON.stringify({ enabled }),
            });
            loadFlags();
        } catch (error) {
            console.error('Failed to toggle flag:', error);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Feature Flags</h1>
                    <p className="text-slate-500 mt-1">Control feature rollouts across the platform</p>
                </div>
                <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    New Feature Flag
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>All Feature Flags</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Feature Name</TableHead>
                                <TableHead>Description</TableHead>
                                <TableHead>Global Status</TableHead>
                                <TableHead>Staging</TableHead>
                                <TableHead>Rollout %</TableHead>
                                <TableHead>Tenants Enabled</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center">Loading...</TableCell>
                                </TableRow>
                            ) : flags.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center text-slate-500">
                                        No feature flags found
                                    </TableCell>
                                </TableRow>
                            ) : (
                                flags.map((flag) => (
                                    <TableRow key={flag.id}>
                                        <TableCell className="font-medium">
                                            <div className="flex items-center gap-2">
                                                <Flag className="h-4 w-4 text-blue-500" />
                                                {flag.name}
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-sm text-slate-500">
                                            {flag.description || 'No description'}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Switch
                                                    checked={flag.enabled_globally}
                                                    onCheckedChange={(checked) => toggleFlag(flag.id, checked)}
                                                />
                                                <Badge variant={flag.enabled_globally ? 'default' : 'secondary'}>
                                                    {flag.enabled_globally ? 'Enabled' : 'Disabled'}
                                                </Badge>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={flag.enabled_in_staging ? 'default' : 'secondary'}>
                                                {flag.enabled_in_staging ? 'Yes' : 'No'}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <TrendingUp className="h-4 w-4 text-emerald-500" />
                                                {flag.rollout_percentage}%
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="outline">
                                                {flag.tenants_enabled || 0} tenants
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button variant="ghost" size="sm">
                                                Configure
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Feature Flag Guidelines */}
            <Card>
                <CardHeader>
                    <CardTitle>Feature Flag Best Practices</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3 text-sm text-slate-600">
                        <div className="flex items-start gap-2">
                            <div className="h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-blue-600 text-xs font-bold">1</span>
                            </div>
                            <p>Test in staging before enabling globally</p>
                        </div>
                        <div className="flex items-start gap-2">
                            <div className="h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-blue-600 text-xs font-bold">2</span>
                            </div>
                            <p>Use gradual rollout (10% → 50% → 100%) for risky features</p>
                        </div>
                        <div className="flex items-start gap-2">
                            <div className="h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-blue-600 text-xs font-bold">3</span>
                            </div>
                            <p>Monitor error rates after enabling new features</p>
                        </div>
                        <div className="flex items-start gap-2">
                            <div className="h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                                <span className="text-blue-600 text-xs font-bold">4</span>
                            </div>
                            <p>Keep flags temporary - remove after full rollout</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
