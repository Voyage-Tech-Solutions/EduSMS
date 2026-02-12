'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Save, Building, Calendar, Clock, DollarSign, Bell } from 'lucide-react';

export default function SettingsPage() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [schoolData, setSchoolData] = useState({ name: '', address: '', phone: '', email: '', website: '' });
    const [settingsData, setSettingsData] = useState({ timezone: 'UTC', currency: 'USD', country: '', primary_color: '#10b981' });
    const [attendanceSettings, setAttendanceSettings] = useState({ allow_future_attendance: false, late_cutoff_time: '08:30:00' });
    const [billingSettings, setBillingSettings] = useState({ invoice_prefix: 'INV', default_due_days: 30, allow_overpayment: false });
    const [notificationSettings, setNotificationSettings] = useState({ sms_enabled: false, email_enabled: true });

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    const getHeaders = useCallback(async () => {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return null;
        return { 'Authorization': `Bearer ${session.access_token}`, 'Content-Type': 'application/json' };
    }, []);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const headers = await getHeaders();
            if (!headers) { setLoading(false); return; }
            const [schoolRes, attendanceRes, billingRes, notificationRes] = await Promise.all([
                fetch(`${baseUrl}/settings/school`, { headers }),
                fetch(`${baseUrl}/settings/attendance`, { headers }),
                fetch(`${baseUrl}/settings/billing`, { headers }),
                fetch(`${baseUrl}/settings/notifications`, { headers }),
            ]);
            if (schoolRes.ok) {
                const data = await schoolRes.json();
                if (data.school) setSchoolData(data.school);
                if (data.settings) setSettingsData(data.settings);
            }
            if (attendanceRes.ok) setAttendanceSettings(await attendanceRes.json());
            if (billingRes.ok) setBillingSettings(await billingRes.json());
            if (notificationRes.ok) setNotificationSettings(await notificationRes.json());
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const saveSchoolSettings = async () => {
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/settings/school`, {
                method: 'PATCH',
                headers,
                body: JSON.stringify({ ...schoolData, ...settingsData })
            });
            if (res.ok) {
                setMessage({ type: 'success', text: 'School settings saved successfully.' });
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to save settings.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const saveAttendanceSettings = async () => {
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/settings/attendance`, {
                method: 'PATCH',
                headers,
                body: JSON.stringify(attendanceSettings)
            });
            if (res.ok) {
                setMessage({ type: 'success', text: 'Attendance settings saved successfully.' });
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to save settings.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const saveBillingSettings = async () => {
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/settings/billing`, {
                method: 'PATCH',
                headers,
                body: JSON.stringify(billingSettings)
            });
            if (res.ok) {
                setMessage({ type: 'success', text: 'Billing settings saved successfully.' });
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to save settings.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    const saveNotificationSettings = async () => {
        setSaving(true);
        try {
            const headers = await getHeaders();
            if (!headers) return;
            const res = await fetch(`${baseUrl}/settings/notifications`, {
                method: 'PATCH',
                headers,
                body: JSON.stringify(notificationSettings)
            });
            if (res.ok) {
                setMessage({ type: 'success', text: 'Notification settings saved successfully.' });
            } else {
                const err = await res.json().catch(() => ({}));
                setMessage({ type: 'error', text: err.detail || 'Failed to save settings.' });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error.' });
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(null), 4000);
        }
    };

    if (loading) {
        return <div className="flex items-center justify-center h-64"><Loader2 className="h-12 w-12 animate-spin text-emerald-600" /></div>;
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">School Settings</h1>
                <p className="text-slate-500 mt-1">Manage your school configuration</p>
            </div>

            {message && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {message.text}
                </div>
            )}

            <Tabs defaultValue="school" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="school"><Building className="mr-2 h-4 w-4" />School Info</TabsTrigger>
                    <TabsTrigger value="attendance"><Clock className="mr-2 h-4 w-4" />Attendance</TabsTrigger>
                    <TabsTrigger value="billing"><DollarSign className="mr-2 h-4 w-4" />Billing</TabsTrigger>
                    <TabsTrigger value="notifications"><Bell className="mr-2 h-4 w-4" />Notifications</TabsTrigger>
                </TabsList>

                <TabsContent value="school">
                    <Card>
                        <CardHeader><CardTitle>School Information</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>School Name</Label>
                                    <Input value={schoolData.name} onChange={e => setSchoolData({ ...schoolData, name: e.target.value })} />
                                </div>
                                <div className="space-y-2">
                                    <Label>Email</Label>
                                    <Input type="email" value={schoolData.email} onChange={e => setSchoolData({ ...schoolData, email: e.target.value })} />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Phone</Label>
                                    <Input value={schoolData.phone} onChange={e => setSchoolData({ ...schoolData, phone: e.target.value })} />
                                </div>
                                <div className="space-y-2">
                                    <Label>Website</Label>
                                    <Input value={schoolData.website} onChange={e => setSchoolData({ ...schoolData, website: e.target.value })} />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label>Address</Label>
                                <Input value={schoolData.address} onChange={e => setSchoolData({ ...schoolData, address: e.target.value })} />
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                                <div className="space-y-2">
                                    <Label>Timezone</Label>
                                    <Select value={settingsData.timezone} onValueChange={v => setSettingsData({ ...settingsData, timezone: v })}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="UTC">UTC</SelectItem>
                                            <SelectItem value="America/New_York">Eastern Time</SelectItem>
                                            <SelectItem value="America/Chicago">Central Time</SelectItem>
                                            <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Currency</Label>
                                    <Select value={settingsData.currency} onValueChange={v => setSettingsData({ ...settingsData, currency: v })}>
                                        <SelectTrigger><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="USD">USD</SelectItem>
                                            <SelectItem value="EUR">EUR</SelectItem>
                                            <SelectItem value="GBP">GBP</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Country</Label>
                                    <Input value={settingsData.country} onChange={e => setSettingsData({ ...settingsData, country: e.target.value })} />
                                </div>
                            </div>
                            <Button onClick={saveSchoolSettings} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="attendance">
                    <Card>
                        <CardHeader><CardTitle>Attendance Rules</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Late Cutoff Time</Label>
                                <Input type="time" value={attendanceSettings.late_cutoff_time} onChange={e => setAttendanceSettings({ ...attendanceSettings, late_cutoff_time: e.target.value })} />
                            </div>
                            <Button onClick={saveAttendanceSettings} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="billing">
                    <Card>
                        <CardHeader><CardTitle>Billing Settings</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Invoice Prefix</Label>
                                    <Input value={billingSettings.invoice_prefix} onChange={e => setBillingSettings({ ...billingSettings, invoice_prefix: e.target.value })} />
                                </div>
                                <div className="space-y-2">
                                    <Label>Default Due Days</Label>
                                    <Input type="number" value={billingSettings.default_due_days} onChange={e => setBillingSettings({ ...billingSettings, default_due_days: parseInt(e.target.value) })} />
                                </div>
                            </div>
                            <Button onClick={saveBillingSettings} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="notifications">
                    <Card>
                        <CardHeader><CardTitle>Notification Settings</CardTitle></CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <Label>Enable Email Notifications</Label>
                                <input type="checkbox" checked={notificationSettings.email_enabled} onChange={e => setNotificationSettings({ ...notificationSettings, email_enabled: e.target.checked })} className="h-4 w-4" />
                            </div>
                            <div className="flex items-center justify-between">
                                <Label>Enable SMS Notifications</Label>
                                <input type="checkbox" checked={notificationSettings.sms_enabled} onChange={e => setNotificationSettings({ ...notificationSettings, sms_enabled: e.target.checked })} className="h-4 w-4" />
                            </div>
                            <Button onClick={saveNotificationSettings} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                                {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
