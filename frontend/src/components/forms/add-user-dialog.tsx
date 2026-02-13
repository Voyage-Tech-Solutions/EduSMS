'use client';

import React, { useState, useEffect } from 'react';
import { authFetch } from '@/lib/authFetch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus } from 'lucide-react';

interface AddUserDialogProps {
    onUserAdded?: () => void;
}

export function AddUserDialog({ onUserAdded }: AddUserDialogProps) {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [schools, setSchools] = useState<any[]>([]);
    const [formData, setFormData] = useState({
        email: '',
        full_name: '',
        role: '',
        school_id: '',
    });

    useEffect(() => {
        if (open) {
            loadSchools();
        }
    }, [open]);

    const loadSchools = async () => {
        try {
            const response = await authFetch('/api/v1/system/schools');
            const data = await response.json();
            setSchools(data);
        } catch (error) {
            console.error('Failed to load schools:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await authFetch('/api/v1/system/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                setOpen(false);
                setFormData({ email: '', full_name: '', role: '', school_id: '' });
                onUserAdded?.();
            }
        } catch (error) {
            console.error('Failed to add user:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button className="bg-emerald-600 hover:bg-emerald-700">
                    <Plus className="mr-2 h-4 w-4" />
                    Add User
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Add New User</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="full_name">Full Name *</Label>
                        <Input
                            id="full_name"
                            value={formData.full_name}
                            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="email">Email *</Label>
                        <Input
                            id="email"
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="role">Role *</Label>
                        <Select value={formData.role} onValueChange={(value) => setFormData({ ...formData, role: value })}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select role" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="principal">Principal</SelectItem>
                                <SelectItem value="office_admin">Office Admin</SelectItem>
                                <SelectItem value="teacher">Teacher</SelectItem>
                                <SelectItem value="parent">Parent</SelectItem>
                                <SelectItem value="student">Student</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="school_id">School *</Label>
                        <Select value={formData.school_id} onValueChange={(value) => setFormData({ ...formData, school_id: value })}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select school" />
                            </SelectTrigger>
                            <SelectContent>
                                {schools.map((school) => (
                                    <SelectItem key={school.id} value={school.id}>
                                        {school.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="flex justify-end gap-2">
                        <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={loading}>
                            {loading ? 'Adding...' : 'Add User'}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
