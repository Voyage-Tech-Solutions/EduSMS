'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Globe, Shield, Mail, Database, Save } from 'lucide-react';

export default function SettingsPage() {
    const { profile } = useAuth();
    const isSystemAdmin = profile?.role === 'system_admin';
    const [settings, setSettings] = useState({
        platform_name: 'EduCore SaaS',
        support_email: 'support@educore.com',
        default_timezone: 'UTC',
        default_currency: 'USD',
        session_timeout: '60',
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isSystemAdmin) {
            loadSettings();
        }
    }, [isSystemAdmin]);

    const loadSettings = async () => {
        try {
            const response = await fetch('/api/v1/system/settings');
            const data = await response.json();
            setSettings(data);
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    };

    const saveSettings = async () => {
        setLoading(true);
        try {
            await fetch('/api/v1/system/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
            });
        } catch (error) {
            console.error('Failed to save settings:', error);
        } finally {
            setLoading(false);
        }
    };

    if (isSystemAdmin) {
        return (
            <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold">Platform Settings</h1>
                            <p className="text-slate-500 mt-1">Configure global system behavior</p>
                        </div>
                        <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={saveSettings} disabled={loading}>
                            <Save className="mr-2 h-4 w-4" />
                            {loading ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </div>

                    <Tabs defaultValue="general" className="space-y-6">
                        <TabsList>
                            <TabsTrigger value="general">General</TabsTrigger>
                            <TabsTrigger value="security">Security</TabsTrigger>
                            <TabsTrigger value="notifications">Notifications</TabsTrigger>
                            <TabsTrigger value="backup">Backup & Data</TabsTrigger>
                        </TabsList>

                        <TabsContent value="general">
                            <div className="grid gap-6">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2">
                                            <Globe className="h-5 w-5" />
                                            Platform Configuration
                                        </CardTitle>
                                        <CardDescription>Global platform settings</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <Label>Platform Name</Label>
                                                <Input value={settings.platform_name} onChange={(e) => setSettings({...settings, platform_name: e.target.value})} />
                                            </div>
                                            <div className="space-y-2">
                                                <Label>Support Email</Label>
                                                <Input value={settings.support_email} onChange={(e) => setSettings({...settings, support_email: e.target.value})} />
                                            </div>
                                            <div className="space-y-2">
                                                <Label>Default Timezone</Label>
                                                <Select value={settings.default_timezone} onValueChange={(value) => setSettings({...settings, default_timezone: value})}>
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="UTC">UTC</SelectItem>
                                                        <SelectItem value="America/New_York">Eastern Time</SelectItem>
                                                        <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="space-y-2">
                                                <Label>Default Currency</Label>
                                                <Select value={settings.default_currency} onValueChange={(value) => setSettings({...settings, default_currency: value})}>
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="USD">USD ($)</SelectItem>
                                                        <SelectItem value="EUR">EUR (€)</SelectItem>
                                                        <SelectItem value="GBP">GBP (£)</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        </TabsContent>

                        <TabsContent value="security">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Shield className="h-5 w-5" />
                                        Security Policies
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="flex items-center justify-between p-4 rounded-lg border">
                                        <div>
                                            <p className="font-medium">Global 2FA Enforcement</p>
                                            <p className="text-sm text-slate-500">Require 2FA for all admin users</p>
                                        </div>
                                        <Button variant="outline">Enable</Button>
                                    </div>
                                    <div className="flex items-center justify-between p-4 rounded-lg border">
                                        <div>
                                            <p className="font-medium">Session Timeout</p>
                                            <p className="text-sm text-slate-500">Global session timeout limit</p>
                                        </div>
                                        <Select value={settings.session_timeout} onValueChange={(value) => setSettings({...settings, session_timeout: value})}>
                                            <SelectTrigger className="w-32">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="30">30 min</SelectItem>
                                                <SelectItem value="60">1 hour</SelectItem>
                                                <SelectItem value="120">2 hours</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="flex items-center justify-between p-4 rounded-lg border">
                                        <div>
                                            <p className="font-medium">Password Requirements</p>
                                            <p className="text-sm text-slate-500">Minimum 8 characters, 1 uppercase, 1 number</p>
                                        </div>
                                        <Button variant="outline">Configure</Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="notifications">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Mail className="h-5 w-5" />
                                        Notification Services
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="space-y-2">
                                        <Label>Email Provider</Label>
                                        <Select defaultValue="sendgrid">
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="sendgrid">SendGrid</SelectItem>
                                                <SelectItem value="ses">AWS SES</SelectItem>
                                                <SelectItem value="mailgun">Mailgun</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>API Key</Label>
                                        <Input type="password" placeholder="••••••••••••••••" />
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="backup">
                            <Card>
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Database className="h-5 w-5" />
                                        Backup & Data Management
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="flex items-center justify-between p-4 rounded-lg border">
                                        <div>
                                            <p className="font-medium">Automatic Backups</p>
                                            <p className="text-sm text-slate-500">Daily at 2:00 AM UTC</p>
                                        </div>
                                        <Button variant="outline">Configure</Button>
                                    </div>
                                    <div className="flex items-center justify-between p-4 rounded-lg border">
                                        <div>
                                            <p className="font-medium">Backup Retention</p>
                                            <p className="text-sm text-slate-500">Keep backups for 30 days</p>
                                        </div>
                                        <Select defaultValue="30">
                                            <SelectTrigger className="w-32">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="7">7 days</SelectItem>
                                                <SelectItem value="30">30 days</SelectItem>
                                                <SelectItem value="90">90 days</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="flex items-center justify-between p-4 rounded-lg border">
                                        <div>
                                            <p className="font-medium">Manual Backup</p>
                                            <p className="text-sm text-slate-500">Trigger immediate backup</p>
                                        </div>
                                        <Button>Backup Now</Button>
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>
        );
    }

    // School admin settings (existing code)
    return (
        <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">School Settings</h1>
                    <p className="text-slate-500 mt-1">Manage your school configuration</p>
                </div>
                <Card>
                    <CardHeader>
                        <CardTitle>School Information</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-slate-500">School-level settings coming soon...</p>
                    </CardContent>
                </Card>
            </div>
    );
}
