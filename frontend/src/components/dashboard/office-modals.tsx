'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';

// Save Attendance Modal
export function SaveAttendanceModal({ open, onClose, onSuccess }: any) {
    const [date, setDate] = useState('');

    useEffect(() => {
        setDate(new Date().toISOString().split('T')[0]);
    }, []);
    const [classId, setClassId] = useState('');
    const [students, setStudents] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/office-admin/attendance/save`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session?.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date,
                    class_id: classId,
                    records: students.map(s => ({
                        student_id: s.id,
                        status: s.status || 'present',
                        notes: s.notes || ''
                    }))
                })
            });
            if (response.ok) {
                onSuccess();
                onClose();
            }
        } catch (error) {
            console.error('Failed to save attendance:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Save Attendance</DialogTitle>
                    <DialogDescription>Record attendance for students in the selected class.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div>
                        <Label>Date</Label>
                        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                    </div>
                    <div>
                        <Label>Class</Label>
                        <Select value={classId} onValueChange={setClassId}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select class" />
                            </SelectTrigger>
                            <SelectContent>
                                {/* Dynamic class list will be loaded */}
                            </SelectContent>
                        </Select>
                    </div>
                    {students.map((student, idx) => (
                        <div key={idx} className="flex items-center gap-4 p-3 border rounded">
                            <span className="flex-1">{student.name}</span>
                            <RadioGroup value={student.status} onValueChange={(val) => {
                                const updated = [...students];
                                updated[idx].status = val;
                                setStudents(updated);
                            }}>
                                <div className="flex gap-4">
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value="present" id={`present-${idx}`} />
                                        <Label htmlFor={`present-${idx}`}>Present</Label>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value="absent" id={`absent-${idx}`} />
                                        <Label htmlFor={`absent-${idx}`}>Absent</Label>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value="late" id={`late-${idx}`} />
                                        <Label htmlFor={`late-${idx}`}>Late</Label>
                                    </div>
                                </div>
                            </RadioGroup>
                        </div>
                    ))}
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSubmit} disabled={loading}>
                        {loading ? 'Saving...' : 'Save Attendance'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// Create Invoice Modal
export function CreateInvoiceModal({ open, onClose, onSuccess }: any) {
    const [formData, setFormData] = useState({
        student_id: '',
        fee_type: '',
        description: '',
        amount: '',
        due_date: '',
        allow_payment_plan: false,
        notes: ''
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/office-admin/invoice/create`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session?.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            if (response.ok) {
                onSuccess();
                onClose();
            }
        } catch (error) {
            console.error('Failed to create invoice:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Create Invoice</DialogTitle>
                    <DialogDescription>Generate a new fee invoice for a student.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div>
                        <Label>Student</Label>
                        <Select value={formData.student_id} onValueChange={(val) => setFormData({...formData, student_id: val})}>
                            <SelectTrigger>
                                <SelectValue placeholder="Search student" />
                            </SelectTrigger>
                            <SelectContent>
                                {/* Dynamic student list will be loaded */}
                            </SelectContent>
                        </Select>
                    </div>
                    <div>
                        <Label>Fee Type</Label>
                        <Select value={formData.fee_type} onValueChange={(val) => setFormData({...formData, fee_type: val})}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select fee type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="tuition">Tuition</SelectItem>
                                <SelectItem value="transport">Transport</SelectItem>
                                <SelectItem value="books">Books</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div>
                        <Label>Description</Label>
                        <Input value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} />
                    </div>
                    <div>
                        <Label>Amount</Label>
                        <Input type="number" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} />
                    </div>
                    <div>
                        <Label>Due Date</Label>
                        <Input type="date" value={formData.due_date} onChange={(e) => setFormData({...formData, due_date: e.target.value})} />
                    </div>
                    <div className="flex items-center gap-2">
                        <input type="checkbox" checked={formData.allow_payment_plan} onChange={(e) => setFormData({...formData, allow_payment_plan: e.target.checked})} />
                        <Label>Allow Payment Plan</Label>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSubmit} disabled={loading}>
                        {loading ? 'Creating...' : 'Create Invoice'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// Add Student Modal
export function AddStudentModal({ open, onClose, onSuccess }: any) {
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        admission_date: '',
        grade_id: '',
        class_id: '',
        parent_name: '',
        parent_id_number: '',
        parent_phone: '',
        parent_email: '',
        parent_address: '',
        medical_conditions: '',
        allergies: '',
        emergency_contact: ''
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setFormData(prev => ({ ...prev, admission_date: new Date().toISOString().split('T')[0] }));
    }, []);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/office-admin/student/add`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session?.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            if (response.ok) {
                onSuccess();
                onClose();
            }
        } catch (error) {
            console.error('Failed to add student:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Add Student</DialogTitle>
                    <DialogDescription>Register a new student with their details and parent information.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div className="font-semibold">Basic Information</div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>First Name *</Label>
                            <Input value={formData.first_name} onChange={(e) => setFormData({...formData, first_name: e.target.value})} />
                        </div>
                        <div>
                            <Label>Last Name *</Label>
                            <Input value={formData.last_name} onChange={(e) => setFormData({...formData, last_name: e.target.value})} />
                        </div>
                        <div>
                            <Label>Date of Birth *</Label>
                            <Input type="date" value={formData.date_of_birth} onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})} />
                        </div>
                        <div>
                            <Label>Gender *</Label>
                            <Select value={formData.gender} onValueChange={(val) => setFormData({...formData, gender: val})}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select gender" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="male">Male</SelectItem>
                                    <SelectItem value="female">Female</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <Label>Admission Date *</Label>
                            <Input type="date" value={formData.admission_date} onChange={(e) => setFormData({...formData, admission_date: e.target.value})} />
                        </div>
                        <div>
                            <Label>Grade *</Label>
                            <Select value={formData.grade_id} onValueChange={(val) => setFormData({...formData, grade_id: val})}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select grade" />
                                </SelectTrigger>
                                <SelectContent>
                                    {/* Dynamic grade list will be loaded */}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    
                    <div className="font-semibold mt-4">Parent Information</div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <Label>Parent Full Name *</Label>
                            <Input value={formData.parent_name} onChange={(e) => setFormData({...formData, parent_name: e.target.value})} />
                        </div>
                        <div>
                            <Label>ID Number *</Label>
                            <Input value={formData.parent_id_number} onChange={(e) => setFormData({...formData, parent_id_number: e.target.value})} />
                        </div>
                        <div>
                            <Label>Phone *</Label>
                            <Input value={formData.parent_phone} onChange={(e) => setFormData({...formData, parent_phone: e.target.value})} />
                        </div>
                        <div>
                            <Label>Email</Label>
                            <Input type="email" value={formData.parent_email} onChange={(e) => setFormData({...formData, parent_email: e.target.value})} />
                        </div>
                    </div>
                    
                    <div className="font-semibold mt-4">Medical Information</div>
                    <div>
                        <Label>Medical Conditions</Label>
                        <Textarea value={formData.medical_conditions} onChange={(e) => setFormData({...formData, medical_conditions: e.target.value})} />
                    </div>
                    <div>
                        <Label>Emergency Contact *</Label>
                        <Input value={formData.emergency_contact} onChange={(e) => setFormData({...formData, emergency_contact: e.target.value})} />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSubmit} disabled={loading}>
                        {loading ? 'Adding...' : 'Add Student'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// Add Staff Modal
export function AddStaffModal({ open, onClose, onSuccess }: any) {
    const [formData, setFormData] = useState({
        full_name: '',
        role: '',
        department: '',
        email: '',
        phone: '',
        employment_type: ''
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/office-admin/staff/add`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session?.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            if (response.ok) {
                onSuccess();
                onClose();
            }
        } catch (error) {
            console.error('Failed to add staff:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Add Staff</DialogTitle>
                    <DialogDescription>Send an invitation to a new staff member.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div>
                        <Label>Full Name *</Label>
                        <Input value={formData.full_name} onChange={(e) => setFormData({...formData, full_name: e.target.value})} />
                    </div>
                    <div>
                        <Label>Role *</Label>
                        <Select value={formData.role} onValueChange={(val) => setFormData({...formData, role: val})}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select role" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="teacher">Teacher</SelectItem>
                                <SelectItem value="office_admin">Office Admin</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div>
                        <Label>Department *</Label>
                        <Input value={formData.department} onChange={(e) => setFormData({...formData, department: e.target.value})} />
                    </div>
                    <div>
                        <Label>Email *</Label>
                        <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} />
                    </div>
                    <div>
                        <Label>Phone *</Label>
                        <Input value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} />
                    </div>
                    <div>
                        <Label>Employment Type *</Label>
                        <Select value={formData.employment_type} onValueChange={(val) => setFormData({...formData, employment_type: val})}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="full_time">Full Time</SelectItem>
                                <SelectItem value="part_time">Part Time</SelectItem>
                                <SelectItem value="contract">Contract</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSubmit} disabled={loading}>
                        {loading ? 'Sending Invitation...' : 'Send Invitation'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// Bulk Reminder Modal
export function BulkReminderModal({ open, onClose, onSuccess }: any) {
    const [targetType, setTargetType] = useState('');
    const [deliveryMethod, setDeliveryMethod] = useState('email');
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const { getSession } = await import('@/lib/supabase');
            const session = await getSession();
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/office-admin/notifications/bulk`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session?.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target_type: targetType,
                    delivery_method: deliveryMethod,
                    message
                })
            });
            if (response.ok) {
                onSuccess();
                onClose();
            }
        } catch (error) {
            console.error('Failed to send reminders:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Send Bulk Reminder</DialogTitle>
                    <DialogDescription>Send reminders to multiple parents about missing documents or fees.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div>
                        <Label>Target Group</Label>
                        <Select value={targetType} onValueChange={setTargetType}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select target" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="missing_birth_certificates">Missing Birth Certificates</SelectItem>
                                <SelectItem value="missing_parent_ids">Missing Parent IDs</SelectItem>
                                <SelectItem value="missing_medical_forms">Missing Medical Forms</SelectItem>
                                <SelectItem value="overdue_fees">Overdue Fees</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div>
                        <Label>Delivery Method</Label>
                        <Select value={deliveryMethod} onValueChange={setDeliveryMethod}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="email">Email</SelectItem>
                                <SelectItem value="sms">SMS</SelectItem>
                                <SelectItem value="both">Both</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div>
                        <Label>Message</Label>
                        <Textarea 
                            value={message} 
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Dear Parent, Our records show missing documentation for [Student Name]. Please upload within 5 working days."
                            rows={5}
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSubmit} disabled={loading}>
                        {loading ? 'Sending...' : 'Send Reminders'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
