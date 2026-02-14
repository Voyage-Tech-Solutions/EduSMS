'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authFetch } from '@/lib/authFetch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Eye, Ban, CheckCircle, Plus, Search } from 'lucide-react';

export default function TenantsPage() {
    const router = useRouter();
    const [tenants, setTenants] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        status: '',
        plan: '',
        search: '',
    });

    useEffect(() => {
        loadTenants();
    }, [filters]);

    const loadTenants = async () => {
        try {
            const params = new URLSearchParams();
            if (filters.status) params.append('status', filters.status);
            if (filters.plan) params.append('plan', filters.plan);
            if (filters.search) params.append('search', filters.search);

            const data = await authFetch(`/api/v1/sysadmin/tenants?${params}`).then(r => r.json());
            setTenants(data);
        } catch (error) {
            console.error('Failed to load tenants:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSuspend = async (tenantId: string) => {
        if (!confirm('Are you sure you want to suspend this tenant?')) return;

        const reason = prompt('Reason for suspension:');
        if (!reason) return;

        try {
            await authFetch(`/api/v1/sysadmin/tenants/${tenantId}/suspend`, {
                method: 'POST',
                body: JSON.stringify({ reason }),
            });
            loadTenants();
        } catch (error) {
            console.error('Failed to suspend tenant:', error);
        }
    };

    const handleActivate = async (tenantId: string) => {
        try {
            await authFetch(`/api/v1/sysadmin/tenants/${tenantId}/activate`, {
                method: 'POST',
            });
            loadTenants();
        } catch (error) {
            console.error('Failed to activate tenant:', error);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Tenants</h1>
                    <p className="text-slate-500 mt-1">Manage all schools on the platform</p>
                </div>
                <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Tenant
                </Button>
            </div>

            {/* Filters */}
            <Card>
                <CardContent className="pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                            <Input
                                placeholder="Search tenants..."
                                className="pl-10"
                                value={filters.search}
                                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                            />
                        </div>
                        <Select value={filters.status} onValueChange={(v) => setFilters({ ...filters, status: v })}>
                            <SelectTrigger>
                                <SelectValue placeholder="All Status" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="">All Status</SelectItem>
                                <SelectItem value="active">Active</SelectItem>
                                <SelectItem value="suspended">Suspended</SelectItem>
                                <SelectItem value="trial">Trial</SelectItem>
                            </SelectContent>
                        </Select>
                        <Select value={filters.plan} onValueChange={(v) => setFilters({ ...filters, plan: v })}>
                            <SelectTrigger>
                                <SelectValue placeholder="All Plans" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="">All Plans</SelectItem>
                                <SelectItem value="free">Free</SelectItem>
                                <SelectItem value="basic">Basic</SelectItem>
                                <SelectItem value="pro">Pro</SelectItem>
                                <SelectItem value="enterprise">Enterprise</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button variant="outline" onClick={loadTenants}>
                            Refresh
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Tenants Table */}
            <Card>
                <CardHeader>
                    <CardTitle>All Tenants ({tenants.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Tenant</TableHead>
                                <TableHead>Code</TableHead>
                                <TableHead>Plan</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Subscription</TableHead>
                                <TableHead>Users</TableHead>
                                <TableHead>Students</TableHead>
                                <TableHead>Created</TableHead>
                                <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={9} className="text-center">Loading...</TableCell>
                                </TableRow>
                            ) : tenants.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={9} className="text-center text-slate-500">
                                        No tenants found
                                    </TableCell>
                                </TableRow>
                            ) : (
                                tenants.map((tenant) => (
                                    <TableRow key={tenant.id}>
                                        <TableCell className="font-medium">{tenant.name}</TableCell>
                                        <TableCell className="font-mono text-sm">{tenant.code}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className="capitalize">
                                                {tenant.plan}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={tenant.status === 'Active' ? 'default' : 'secondary'}>
                                                {tenant.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={tenant.subscription_status === 'active' ? 'default' : 'secondary'}>
                                                {tenant.subscription_status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>{tenant.users}</TableCell>
                                        <TableCell>
                                            {tenant.students} / {tenant.max_students}
                                        </TableCell>
                                        <TableCell className="text-sm text-slate-500">
                                            {new Date(tenant.created_at).toLocaleDateString()}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex justify-end gap-2">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => router.push(`/dashboard/sysadmin/tenants/${tenant.id}`)}
                                                >
                                                    <Eye className="h-4 w-4" />
                                                </Button>
                                                {tenant.status === 'Active' ? (
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleSuspend(tenant.id)}
                                                    >
                                                        <Ban className="h-4 w-4 text-red-500" />
                                                    </Button>
                                                ) : (
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleActivate(tenant.id)}
                                                    >
                                                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                                                    </Button>
                                                )}
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
}
