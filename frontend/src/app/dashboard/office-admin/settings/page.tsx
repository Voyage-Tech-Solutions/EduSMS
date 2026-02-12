"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Settings, School, Calendar, DollarSign, FileText, Bell } from "lucide-react";

export default function SettingsPage() {
  const [schoolSettings, setSchoolSettings] = useState<any>({});
  const [attendanceSettings, setAttendanceSettings] = useState<any>({});
  const [billingSettings, setBillingSettings] = useState<any>({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    const [school, attendance, billing] = await Promise.all([
      fetch("/api/v1/settings/school").then(r => r.json()),
      fetch("/api/v1/settings/attendance").then(r => r.json()),
      fetch("/api/v1/settings/billing").then(r => r.json())
    ]);
    
    setSchoolSettings(school);
    setAttendanceSettings(attendance);
    setBillingSettings(billing);
  };

  const handleSaveSchool = async () => {
    await fetch("/api/v1/settings/school", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(schoolSettings)
    });
    setHasChanges(false);
  };

  const handleSaveAttendance = async () => {
    await fetch("/api/v1/settings/attendance", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(attendanceSettings)
    });
    setHasChanges(false);
  };

  const handleSaveBilling = async () => {
    await fetch("/api/v1/settings/billing", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(billingSettings)
    });
    setHasChanges(false);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">School Settings</h1>
          <p className="text-gray-600">Manage your school configuration</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" disabled={!hasChanges}>Cancel</Button>
          <Button disabled={!hasChanges}>Save Changes</Button>
        </div>
      </div>

      <Tabs defaultValue="school" className="space-y-4">
        <TabsList>
          <TabsTrigger value="school"><School className="w-4 h-4 mr-2" />School Info</TabsTrigger>
          <TabsTrigger value="academic"><Calendar className="w-4 h-4 mr-2" />Academic</TabsTrigger>
          <TabsTrigger value="attendance"><Settings className="w-4 h-4 mr-2" />Attendance</TabsTrigger>
          <TabsTrigger value="billing"><DollarSign className="w-4 h-4 mr-2" />Billing</TabsTrigger>
          <TabsTrigger value="documents"><FileText className="w-4 h-4 mr-2" />Documents</TabsTrigger>
          <TabsTrigger value="notifications"><Bell className="w-4 h-4 mr-2" />Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="school">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">School Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>School Name</Label>
                <Input value={schoolSettings.name || ""} onChange={(e) => { setSchoolSettings({...schoolSettings, name: e.target.value}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>School Code</Label>
                <Input value={schoolSettings.code || ""} onChange={(e) => { setSchoolSettings({...schoolSettings, code: e.target.value}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>Email</Label>
                <Input type="email" value={schoolSettings.email || ""} onChange={(e) => { setSchoolSettings({...schoolSettings, email: e.target.value}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>Phone</Label>
                <Input value={schoolSettings.phone || ""} onChange={(e) => { setSchoolSettings({...schoolSettings, phone: e.target.value}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>Address</Label>
                <Input value={schoolSettings.address || ""} onChange={(e) => { setSchoolSettings({...schoolSettings, address: e.target.value}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>Website</Label>
                <Input value={schoolSettings.website || ""} onChange={(e) => { setSchoolSettings({...schoolSettings, website: e.target.value}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>Timezone</Label>
                <Select value={schoolSettings.timezone} onValueChange={(v) => { setSchoolSettings({...schoolSettings, timezone: v}); setHasChanges(true); }}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="UTC">UTC</SelectItem>
                    <SelectItem value="America/New_York">Eastern Time</SelectItem>
                    <SelectItem value="America/Chicago">Central Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Currency</Label>
                <Select value={schoolSettings.currency} onValueChange={(v) => { setSchoolSettings({...schoolSettings, currency: v}); setHasChanges(true); }}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                    <SelectItem value="GBP">GBP</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={handleSaveSchool} className="mt-4">Save School Info</Button>
          </Card>
        </TabsContent>

        <TabsContent value="academic">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Academic Setup</h3>
            <p className="text-gray-600">Manage terms, grades, classes, and subjects</p>
            <div className="mt-4 space-y-4">
              <Button variant="outline">Manage Terms</Button>
              <Button variant="outline">Manage Grades</Button>
              <Button variant="outline">Manage Classes</Button>
              <Button variant="outline">Manage Subjects</Button>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="attendance">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Attendance Rules</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Allow Future Dates</Label>
                  <p className="text-sm text-gray-600">Allow marking attendance for future dates</p>
                </div>
                <Switch checked={attendanceSettings.allow_future_dates} onCheckedChange={(v) => { setAttendanceSettings({...attendanceSettings, allow_future_dates: v}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>Late Cutoff Time</Label>
                <Input type="time" value={attendanceSettings.late_cutoff_time || ""} onChange={(e) => { setAttendanceSettings({...attendanceSettings, late_cutoff_time: e.target.value}); setHasChanges(true); }} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Excused Requires Note</Label>
                  <p className="text-sm text-gray-600">Require note for excused absences</p>
                </div>
                <Switch checked={attendanceSettings.excused_requires_note} onCheckedChange={(v) => { setAttendanceSettings({...attendanceSettings, excused_requires_note: v}); setHasChanges(true); }} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-mark Absent</Label>
                  <p className="text-sm text-gray-600">Auto-mark unmarked students as absent</p>
                </div>
                <Switch checked={attendanceSettings.auto_mark_absent} onCheckedChange={(v) => { setAttendanceSettings({...attendanceSettings, auto_mark_absent: v}); setHasChanges(true); }} />
              </div>
            </div>
            <Button onClick={handleSaveAttendance} className="mt-4">Save Attendance Rules</Button>
          </Card>
        </TabsContent>

        <TabsContent value="billing">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Fees & Billing Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Invoice Prefix</Label>
                <Input value={billingSettings.invoice_prefix || ""} onChange={(e) => { setBillingSettings({...billingSettings, invoice_prefix: e.target.value}); setHasChanges(true); }} />
              </div>
              <div>
                <Label>Default Due Days</Label>
                <Input type="number" value={billingSettings.default_due_days || ""} onChange={(e) => { setBillingSettings({...billingSettings, default_due_days: parseInt(e.target.value)}); setHasChanges(true); }} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Allow Overpayment</Label>
                  <p className="text-sm text-gray-600">Allow payments exceeding invoice balance</p>
                </div>
                <Switch checked={billingSettings.allow_overpayment} onCheckedChange={(v) => { setBillingSettings({...billingSettings, allow_overpayment: v}); setHasChanges(true); }} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Require Payment Proof</Label>
                  <p className="text-sm text-gray-600">Require proof for bank transfers</p>
                </div>
                <Switch checked={billingSettings.require_payment_proof} onCheckedChange={(v) => { setBillingSettings({...billingSettings, require_payment_proof: v}); setHasChanges(true); }} />
              </div>
            </div>
            <Button onClick={handleSaveBilling} className="mt-4">Save Billing Settings</Button>
          </Card>
        </TabsContent>

        <TabsContent value="documents">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Document Requirements</h3>
            <p className="text-gray-600">Configure required documents for students, parents, and staff</p>
            <Button variant="outline" className="mt-4">Manage Requirements</Button>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Notification Settings</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Enable SMS</Label>
                <Switch />
              </div>
              <div className="flex items-center justify-between">
                <Label>Enable Email</Label>
                <Switch defaultChecked />
              </div>
              <div>
                <Label>Default Sender Name</Label>
                <Input placeholder="School Name" />
              </div>
            </div>
            <Button className="mt-4">Save Notification Settings</Button>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
