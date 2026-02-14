'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Settings, Mail, Database, Shield, Bell } from 'lucide-react';

export default function SettingsPage() {
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        // Save settings logic
        setTimeout(() => setSaving(false), 1000);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">Platform Settings</h1>
                <p className="text-slate-500 mt-1">Configure global platform settings</p>
            </div>

            <Tabs defaultValue="general" className="space-y-6">
                <TabsList>
                    <TabsTrigger value="general">
                        <Settings className="h-4 w-4 mr-2" />
                        General
                    </TabsTrigger>
                    <TabsTrigger value="email">
                        <Mail className="h-4 w-4 mr-2" />
                        Email/SMS
                    </TabsTrigger>
                    <TabsTrigger value="storage">
                        <Database className="h-4 w-4 mr-2" />
                        Storage
                    </TabsTrigger>
                    <TabsTrigger value="security">
                        <Shield className="h-4 w-4 mr-2" />
                        Security
                    </TabsTrigger>
                    <TabsTrigger value="notifications">
                        <Bell className="h-4 w-4 mr-2" />
                        Notifications
                    </TabsTrigger>
                </TabsList>

                {/* General Settings */}
                <TabsContent value="general">
                    <Card>
                        <CardHeader>
                            <CardTitle>General Platform Settings</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Platform Name</Label>
                                <Input defaultValue="EduCore" />
                            </div>
                            <div className="space-y-2">
                                <Label>Support Email</Label>
                                <Input type="email" defaultValue="support@educore.com" />
                            </div>
                            <div className="space-y-2">
                                <Label>Default Currency</Label>
                                <Input defaultValue="USD" />
                            </div>
                            <div className="space-y-2">
                                <Label>Default Timezone</Label>
                                <Input defaultValue="UTC" />
                            </div>
                            <Button onClick={handleSave} disabled={saving}>
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Email/SMS Settings */}
                <TabsContent value="email">
                    <Card>
                        <CardHeader>
                            <CardTitle>Email & SMS Providers</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="space-y-4">
                                <h3 className="font-medium">Email Provider</h3>
                                <div className="space-y-2">
                                    <Label>Provider</Label>
                                    <Input defaultValue="SendGrid" />
                                </div>
                                <div className="space-y-2">
                                    <Label>API Key</Label>
                                    <Input type="password" placeholder="••••••••••••" />
                                </div>
                                <div className="space-y-2">
                                    <Label>From Email</Label>
                                    <Input type="email" defaultValue="noreply@educore.com" />
                                </div>
                            </div>

                            <div className="space-y-4 pt-6 border-t">
                                <h3 className="font-medium">SMS Provider</h3>
                                <div className="space-y-2">
                                    <Label>Provider</Label>
                                    <Input defaultValue="Twilio" />
                                </div>
                                <div className="space-y-2">
                                    <Label>Account SID</Label>
                                    <Input type="password" placeholder="••••••••••••" />
                                </div>
                                <div className="space-y-2">
                                    <Label>Auth Token</Label>
                                    <Input type="password" placeholder="••••••••••••" />
                                </div>
                            </div>

                            <Button onClick={handleSave} disabled={saving}>
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Storage Settings */}
                <TabsContent value="storage">
                    <Card>
                        <CardHeader>
                            <CardTitle>Storage Configuration</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Storage Provider</Label>
                                <Input defaultValue="Supabase Storage" />
                            </div>
                            <div className="space-y-2">
                                <Label>Default Storage Limit (GB)</Label>
                                <Input type="number" defaultValue="5" />
                            </div>
                            <div className="space-y-2">
                                <Label>Max File Size (MB)</Label>
                                <Input type="number" defaultValue="10" />
                            </div>
                            <div className="space-y-2">
                                <Label>Allowed File Types</Label>
                                <Input defaultValue="pdf,doc,docx,jpg,png" />
                            </div>
                            <Button onClick={handleSave} disabled={saving}>
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Security Settings */}
                <TabsContent value="security">
                    <Card>
                        <CardHeader>
                            <CardTitle>Security Policies</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Password Min Length</Label>
                                <Input type="number" defaultValue="8" />
                            </div>
                            <div className="space-y-2">
                                <Label>Session Timeout (minutes)</Label>
                                <Input type="number" defaultValue="60" />
                            </div>
                            <div className="space-y-2">
                                <Label>Max Login Attempts</Label>
                                <Input type="number" defaultValue="5" />
                            </div>
                            <div className="space-y-2">
                                <Label>Account Lockout Duration (minutes)</Label>
                                <Input type="number" defaultValue="30" />
                            </div>
                            <div className="space-y-2">
                                <Label>MFA Required Roles</Label>
                                <Input defaultValue="system_admin,principal" />
                            </div>
                            <Button onClick={handleSave} disabled={saving}>
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Notification Settings */}
                <TabsContent value="notifications">
                    <Card>
                        <CardHeader>
                            <CardTitle>Notification Settings</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Admin Alert Email</Label>
                                <Input type="email" defaultValue="admin@educore.com" />
                            </div>
                            <div className="space-y-2">
                                <Label>Incident Notification Threshold</Label>
                                <Input defaultValue="high" />
                            </div>
                            <div className="space-y-2">
                                <Label>Payment Failure Notification</Label>
                                <Input type="email" defaultValue="billing@educore.com" />
                            </div>
                            <div className="space-y-2">
                                <Label>System Health Alert Threshold</Label>
                                <Input defaultValue="95%" />
                            </div>
                            <Button onClick={handleSave} disabled={saving}>
                                {saving ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Data Retention */}
            <Card>
                <CardHeader>
                    <CardTitle>Data Retention Policies</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Audit Log Retention (days)</Label>
                            <Input type="number" defaultValue="365" />
                        </div>
                        <div className="space-y-2">
                            <Label>Deleted Tenant Retention (days)</Label>
                            <Input type="number" defaultValue="30" />
                        </div>
                        <div className="space-y-2">
                            <Label>Backup Retention (days)</Label>
                            <Input type="number" defaultValue="90" />
                        </div>
                        <div className="space-y-2">
                            <Label>Log File Retention (days)</Label>
                            <Input type="number" defaultValue="30" />
                        </div>
                    </div>
                    <Button onClick={handleSave} disabled={saving}>
                        {saving ? 'Saving...' : 'Save Changes'}
                    </Button>
                </CardContent>
            </Card>

            {/* Backup Settings */}
            <Card>
                <CardHeader>
                    <CardTitle>Backup Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Backup Schedule</Label>
                        <Input defaultValue="Daily at 2:00 AM UTC" />
                    </div>
                    <div className="space-y-2">
                        <Label>Backup Location</Label>
                        <Input defaultValue="s3://educore-backups/" />
                    </div>
                    <div className="space-y-2">
                        <Label>Last Backup</Label>
                        <Input disabled defaultValue="2024-03-20 02:00:00 UTC" />
                    </div>
                    <div className="flex gap-2">
                        <Button onClick={handleSave} disabled={saving}>
                            {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                        <Button variant="outline">
                            Run Backup Now
                        </Button>
                        <Button variant="outline">
                            Test Restore
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
