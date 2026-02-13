'use client';

import React, { useState, useEffect } from 'react';
import { authFetch } from "@/lib/authFetch";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Flag, ToggleLeft, ToggleRight, Eye } from 'lucide-react';

export default function FeaturesPage() {
    const [features, setFeatures] = useState<any[]>([]);

    useEffect(() => {
        loadFeatures();
    }, []);

    const loadFeatures = async () => {
        try {
            const response = await authFetch('/api/v1/system/features');
            const data = await response.json();
            setFeatures(data);
        } catch (error) {
            console.error('Failed to load features:', error);
            setFeatures([]);
        }
    };

    const toggleFeature = async (featureId: string, currentStatus: string) => {
        try {
            await authFetch(`/api/v1/system/features/${featureId}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: currentStatus !== 'enabled' }),
            });
            loadFeatures();
        } catch (error) {
            console.error('Failed to toggle feature:', error);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'enabled': return 'bg-emerald-100 text-emerald-800';
            case 'beta': return 'bg-blue-100 text-blue-800';
            case 'pilot': return 'bg-amber-100 text-amber-800';
            default: return 'bg-slate-100 text-slate-800';
        }
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'stable': return 'bg-emerald-100 text-emerald-800';
            case 'beta': return 'bg-blue-100 text-blue-800';
            default: return 'bg-amber-100 text-amber-800';
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Feature Flags</h1>
                <p className="text-slate-500 mt-1">Control platform feature rollout</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Total Features</p>
                                <p className="text-3xl font-bold text-slate-900">{features.length}</p>
                            </div>
                            <Flag className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">Enabled</p>
                                <p className="text-3xl font-bold text-slate-900">{features.filter(f => f.status === 'enabled').length}</p>
                            </div>
                            <ToggleRight className="h-8 w-8 text-emerald-500" />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-500">In Beta</p>
                                <p className="text-3xl font-bold text-slate-900">{features.filter(f => f.type === 'beta').length}</p>
                            </div>
                            <Flag className="h-8 w-8 text-blue-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>All Features</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Feature Name</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead>Rollout</TableHead>
                                <TableHead>Last Modified</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {features.length > 0 ? features.map((feature) => (
                                <TableRow key={feature.id}>
                                    <TableCell className="font-medium">{feature.name}</TableCell>
                                    <TableCell>
                                        <Badge className={getStatusColor(feature.status)}>
                                            {feature.status}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge className={getTypeColor(feature.type)}>
                                            {feature.type}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 bg-slate-200 rounded-full h-2">
                                                <div 
                                                    className="bg-emerald-500 h-2 rounded-full" 
                                                    style={{width: `${(feature.enabled_schools / feature.total_schools) * 100}%`}}
                                                />
                                            </div>
                                            <span className="text-sm text-slate-600">
                                                {feature.enabled_schools}/{feature.total_schools}
                                            </span>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-sm text-slate-500">{feature.last_modified}</TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            <Button variant="ghost" size="sm" onClick={() => toggleFeature(feature.id, feature.status)}>
                                                {feature.status === 'enabled' ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}
                                            </Button>
                                            <Button variant="ghost" size="sm">
                                                <Eye className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )) : (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center text-slate-500">
                                        No features available
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
