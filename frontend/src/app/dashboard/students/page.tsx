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
import {
    Search,
    Plus,
    MoreHorizontal,
    Eye,
    Edit,
    Trash2,
    Download,
    Filter,
} from 'lucide-react';

// Mock data for students
const mockStudents = [
    {
        id: '1',
        admission_number: 'STU-2024-001',
        first_name: 'Emily',
        last_name: 'Johnson',
        grade: 'Grade 5',
        class: '5A',
        gender: 'female',
        status: 'active',
    },
    {
        id: '2',
        admission_number: 'STU-2024-002',
        first_name: 'Michael',
        last_name: 'Brown',
        grade: 'Grade 6',
        class: '6B',
        gender: 'male',
        status: 'active',
    },
    {
        id: '3',
        admission_number: 'STU-2024-003',
        first_name: 'Sarah',
        last_name: 'Williams',
        grade: 'Grade 5',
        class: '5A',
        gender: 'female',
        status: 'active',
    },
    {
        id: '4',
        admission_number: 'STU-2024-004',
        first_name: 'James',
        last_name: 'Davis',
        grade: 'Grade 7',
        class: '7A',
        gender: 'male',
        status: 'inactive',
    },
    {
        id: '5',
        admission_number: 'STU-2024-005',
        first_name: 'Emma',
        last_name: 'Miller',
        grade: 'Grade 6',
        class: '6A',
        gender: 'female',
        status: 'active',
    },
];

const statusColors = {
    active: 'bg-emerald-100 text-emerald-800',
    inactive: 'bg-slate-100 text-slate-800',
    transferred: 'bg-blue-100 text-blue-800',
    graduated: 'bg-purple-100 text-purple-800',
};

export default function StudentsPage() {
    const [students, setStudents] = useState<any[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedGrade, setSelectedGrade] = useState('all');

    useEffect(() => {
        loadStudents();
    }, []);

    const loadStudents = async () => {
        try {
            const response = await fetch('/api/v1/students');
            const data = await response.json();
            setStudents(data);
        } catch (error) {
            console.error('Failed to load students:', error);
            setStudents([]);
        }
    };

    const filteredStudents = students.filter((student) => {
        const fullName = `${student.first_name} ${student.last_name}`.toLowerCase();
        const matchesSearch =
            fullName.includes(searchQuery.toLowerCase()) ||
            student.admission_number?.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesGrade = selectedGrade === 'all' || student.grade_level === selectedGrade;

        return matchesSearch && matchesGrade;
    });

    return (
        <div className="space-y-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Students</h1>
                        <p className="text-slate-500 mt-1">Manage your student records</p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="outline">
                            <Download className="mr-2 h-4 w-4" />
                            Export
                        </Button>
                        <Button className="bg-emerald-600 hover:bg-emerald-700">
                            <Plus className="mr-2 h-4 w-4" />
                            Add Student
                        </Button>
                    </div>
                </div>

                {/* Filters */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="relative flex-1">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                                <Input
                                    placeholder="Search by name or admission number..."
                                    className="pl-10"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <Select value={selectedGrade} onValueChange={setSelectedGrade}>
                                <SelectTrigger className="w-full md:w-48">
                                    <SelectValue placeholder="Filter by grade" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Grades</SelectItem>
                                    <SelectItem value="Grade 5">Grade 5</SelectItem>
                                    <SelectItem value="Grade 6">Grade 6</SelectItem>
                                    <SelectItem value="Grade 7">Grade 7</SelectItem>
                                </SelectContent>
                            </Select>
                            <Button variant="outline">
                                <Filter className="mr-2 h-4 w-4" />
                                More Filters
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Students Table */}
                <Card>
                    <CardHeader>
                        <CardTitle>
                            Student List
                            <Badge variant="secondary" className="ml-2">
                                {filteredStudents.length} students
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Admission #</TableHead>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Grade</TableHead>
                                    <TableHead>Class</TableHead>
                                    <TableHead>Gender</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredStudents.map((student) => (
                                    <TableRow key={student.id}>
                                        <TableCell className="font-mono text-sm">
                                            {student.admission_number}
                                        </TableCell>
                                        <TableCell>
                                            <div className="font-medium">
                                                {student.first_name} {student.last_name}
                                            </div>
                                            <div className="text-sm text-slate-500">{student.grade_level}</div>
                                        </TableCell>
                                        <TableCell>{student.grade_level}</TableCell>
                                        <TableCell>{student.class_name || 'N/A'}</TableCell>
                                        <TableCell className="capitalize">{student.gender}</TableCell>
                                        <TableCell>
                                            <Badge
                                                variant="secondary"
                                                className={statusColors[student.status as keyof typeof statusColors]}
                                            >
                                                {student.status}
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
                                                        View Details
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem>
                                                        <Edit className="mr-2 h-4 w-4" />
                                                        Edit
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem className="text-red-600">
                                                        <Trash2 className="mr-2 h-4 w-4" />
                                                        Delete
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>

                        {filteredStudents.length === 0 && (
                            <div className="text-center py-12 text-slate-500">
                                No students found matching your criteria.
                            </div>
                        )}
                    </CardContent>
                </Card>
        </div>
    );
}
