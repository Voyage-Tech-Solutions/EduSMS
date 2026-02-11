'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { StatCard } from '@/components/dashboard';
import {
    Search,
    Plus,
    MoreHorizontal,
    Eye,
    CheckCircle,
    XCircle,
    Clock,
    UserPlus,
    FileText,
    Download,
    Mail,
} from 'lucide-react';

// Mock data for admissions
const mockApplications = [
    {
        id: '1',
        application_number: 'APP-2024-001',
        student_name: 'Alex Thompson',
        parent_name: 'Robert Thompson',
        email: 'robert.t@email.com',
        phone: '+1234567890',
        grade_applied: 'Grade 5',
        application_date: '2024-02-01',
        status: 'pending',
        documents_complete: true,
    },
    {
        id: '2',
        application_number: 'APP-2024-002',
        student_name: 'Sophie Martinez',
        parent_name: 'Maria Martinez',
        email: 'maria.m@email.com',
        phone: '+1234567891',
        grade_applied: 'Grade 6',
        application_date: '2024-02-03',
        status: 'review',
        documents_complete: true,
    },
    {
        id: '3',
        application_number: 'APP-2024-003',
        student_name: 'Daniel Lee',
        parent_name: 'Jennifer Lee',
        email: 'jennifer.l@email.com',
        phone: '+1234567892',
        grade_applied: 'Grade 5',
        application_date: '2024-02-05',
        status: 'approved',
        documents_complete: true,
    },
    {
        id: '4',
        application_number: 'APP-2024-004',
        student_name: 'Emma Wilson',
        parent_name: 'David Wilson',
        email: 'david.w@email.com',
        phone: '+1234567893',
        grade_applied: 'Grade 7',
        application_date: '2024-02-07',
        status: 'incomplete',
        documents_complete: false,
    },
    {
        id: '5',
        application_number: 'APP-2024-005',
        student_name: 'Lucas Garcia',
        parent_name: 'Carlos Garcia',
        email: 'carlos.g@email.com',
        phone: '+1234567894',
        grade_applied: 'Grade 6',
        application_date: '2024-02-08',
        status: 'rejected',
        documents_complete: true,
    },
];

const statusConfig = {
    pending: { color: 'bg-amber-100 text-amber-800', label: 'Pending' },
    review: { color: 'bg-blue-100 text-blue-800', label: 'Under Review' },
    approved: { color: 'bg-emerald-100 text-emerald-800', label: 'Approved' },
    rejected: { color: 'bg-red-100 text-red-800', label: 'Rejected' },
    incomplete: { color: 'bg-slate-100 text-slate-800', label: 'Incomplete' },
};

export default function AdmissionsPage() {
    const [applications, setApplications] = useState<any[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    useEffect(() => {
        loadApplications();
    }, []);

    const loadApplications = async () => {
        try {
            const response = await fetch('/api/v1/admissions');
            const data = await response.json();
            setApplications(data);
        } catch (error) {
            console.error('Failed to load applications:', error);
            setApplications([]);
        }
    };

    const filteredApplications = applications.filter((app) => {
        const matchesSearch =
            app.student_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            app.application_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            app.parent_name?.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesStatus = statusFilter === 'all' || app.status === statusFilter;

        return matchesSearch && matchesStatus;
    });

    const stats = {
        total: applications.length,
        pending: applications.filter(a => a.status === 'pending').length,
        approved: applications.filter(a => a.status === 'approved').length,
        review: applications.filter(a => a.status === 'review').length,
    };

    return (
        <div className="space-y-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Admissions</h1>
                        <p className="text-slate-500 mt-1">Manage student applications and enrollments</p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="outline">
                            <Download className="mr-2 h-4 w-4" />
                            Export
                        </Button>
                        <Button className="bg-emerald-600 hover:bg-emerald-700">
                            <Plus className="mr-2 h-4 w-4" />
                            New Application
                        </Button>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <StatCard
                        title="Total Applications"
                        value={stats.total}
                        description="this term"
                        icon={FileText}
                    />
                    <StatCard
                        title="Pending Review"
                        value={stats.pending}
                        description="awaiting action"
                        icon={Clock}
                    />
                    <StatCard
                        title="Under Review"
                        value={stats.review}
                        description="in progress"
                        icon={Eye}
                    />
                    <StatCard
                        title="Approved"
                        value={stats.approved}
                        description="ready for enrollment"
                        icon={CheckCircle}
                    />
                </div>

                {/* Pipeline Overview */}
                <Card>
                    <CardHeader>
                        <CardTitle>Application Pipeline</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-between">
                            {[
                                { label: 'Incomplete', count: 1, color: 'bg-slate-200' },
                                { label: 'Pending', count: stats.pending, color: 'bg-amber-200' },
                                { label: 'Under Review', count: stats.review, color: 'bg-blue-200' },
                                { label: 'Approved', count: stats.approved, color: 'bg-emerald-200' },
                                { label: 'Enrolled', count: 0, color: 'bg-purple-200' },
                            ].map((stage, index) => (
                                <div key={stage.label} className="flex items-center">
                                    <div className="text-center">
                                        <div className={`w-16 h-16 rounded-full ${stage.color} flex items-center justify-center text-xl font-bold`}>
                                            {stage.count}
                                        </div>
                                        <p className="text-sm text-slate-600 mt-2">{stage.label}</p>
                                    </div>
                                    {index < 4 && (
                                        <div className="w-12 h-0.5 bg-slate-200 mx-2" />
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Filters */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search by student name, application number, or parent..."
                                    className="pl-10"
                                    value={searchQuery}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-full md:w-48">
                                    <SelectValue placeholder="Filter by status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="pending">Pending</SelectItem>
                                    <SelectItem value="review">Under Review</SelectItem>
                                    <SelectItem value="approved">Approved</SelectItem>
                                    <SelectItem value="rejected">Rejected</SelectItem>
                                    <SelectItem value="incomplete">Incomplete</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                {/* Applications Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>
                            Applications
                            <Badge variant="secondary" className="ml-2">
                                {filteredApplications.length} applications
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Application #</TableHead>
                                    <TableHead>Student</TableHead>
                                    <TableHead>Parent/Guardian</TableHead>
                                    <TableHead>Grade Applied</TableHead>
                                    <TableHead>Date</TableHead>
                                    <TableHead>Documents</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredApplications.map((app) => (
                                    <TableRow key={app.id}>
                                        <TableCell className="font-mono text-sm">
                                            {app.application_number}
                                        </TableCell>
                                        <TableCell className="font-medium">
                                            {app.student_name}
                                        </TableCell>
                                        <TableCell>
                                            <div>
                                                <div>{app.parent_name}</div>
                                                <div className="text-sm text-slate-500">{app.email}</div>
                                            </div>
                                        </TableCell>
                                        <TableCell>{app.grade_applied}</TableCell>
                                        <TableCell>{app.application_date}</TableCell>
                                        <TableCell>
                                            {app.documents_complete ? (
                                                <Badge variant="secondary" className="bg-emerald-100 text-emerald-800">
                                                    <CheckCircle className="h-3 w-3 mr-1" />
                                                    Complete
                                                </Badge>
                                            ) : (
                                                <Badge variant="secondary" className="bg-red-100 text-red-800">
                                                    <XCircle className="h-3 w-3 mr-1" />
                                                    Incomplete
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <Badge
                                                variant="secondary"
                                                className={statusConfig[app.status as keyof typeof statusConfig].color}
                                            >
                                                {statusConfig[app.status as keyof typeof statusConfig].label}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem>
                                                        <Eye className="mr-2 h-4 w-4" />
                                                        View Application
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem>
                                                        <Mail className="mr-2 h-4 w-4" />
                                                        Contact Parent
                                                    </DropdownMenuItem>
                                                    {app.status === 'approved' && (
                                                        <DropdownMenuItem>
                                                            <UserPlus className="mr-2 h-4 w-4" />
                                                            Enroll Student
                                                        </DropdownMenuItem>
                                                    )}
                                                    {app.status === 'pending' && (
                                                        <>
                                                            <DropdownMenuItem className="text-emerald-600">
                                                                <CheckCircle className="mr-2 h-4 w-4" />
                                                                Approve
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem className="text-red-600">
                                                                <XCircle className="mr-2 h-4 w-4" />
                                                                Reject
                                                            </DropdownMenuItem>
                                                        </>
                                                    )}
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>

                        {filteredApplications.length === 0 && (
                            <div className="text-center py-12 text-slate-500">
                                No applications found matching your criteria.
                            </div>
                        )}
                    </CardContent>
                </Card>
        </div>
    );
}
