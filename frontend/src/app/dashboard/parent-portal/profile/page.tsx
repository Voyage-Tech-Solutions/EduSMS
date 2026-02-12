"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { User, Bell, Save } from "lucide-react";

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>({});
  const [notifications, setNotifications] = useState({ sms: true, email: true, push: true });

  useEffect(() => {
    fetch("/api/v1/parent/profile")
      .then(res => res.json())
      .then(data => setProfile(data));
  }, []);

  const handleSave = async () => {
    await fetch("/api/v1/parent/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...profile, notification_preferences: notifications })
    });
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <User className="w-8 h-8" />
          Profile & Settings
        </h1>
        <p className="text-muted-foreground">Manage your account information</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Contact Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>First Name</Label>
              <Input value={profile.first_name || ""} onChange={(e) => setProfile({...profile, first_name: e.target.value})} />
            </div>
            <div>
              <Label>Last Name</Label>
              <Input value={profile.last_name || ""} onChange={(e) => setProfile({...profile, last_name: e.target.value})} />
            </div>
          </div>
          <div>
            <Label>Email</Label>
            <Input type="email" value={profile.email || ""} onChange={(e) => setProfile({...profile, email: e.target.value})} />
          </div>
          <div>
            <Label>Phone</Label>
            <Input value={profile.phone || ""} onChange={(e) => setProfile({...profile, phone: e.target.value})} />
          </div>
          <div>
            <Label>Emergency Contact</Label>
            <Input value={profile.emergency_contact || ""} onChange={(e) => setProfile({...profile, emergency_contact: e.target.value})} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notification Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <Label>SMS Notifications</Label>
            <Switch checked={notifications.sms} onCheckedChange={(checked) => setNotifications({...notifications, sms: checked})} />
          </div>
          <div className="flex items-center justify-between">
            <Label>Email Notifications</Label>
            <Switch checked={notifications.email} onCheckedChange={(checked) => setNotifications({...notifications, email: checked})} />
          </div>
          <div className="flex items-center justify-between">
            <Label>App Push Notifications</Label>
            <Switch checked={notifications.push} onCheckedChange={(checked) => setNotifications({...notifications, push: checked})} />
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave}>
        <Save className="w-4 h-4 mr-2" />
        Save Changes
      </Button>
    </div>
  );
}
