"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Settings, Target, Bell, FileText, Save } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function PrincipalSettingsPage() {
  const [targets, setTargets] = useState({ attendance: 95, passRate: 75, collection: 90 });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Settings className="w-8 h-8" />
          Principal Settings
        </h1>
        <p className="text-muted-foreground">Configure school targets and approval rules</p>
      </div>

      <Tabs defaultValue="targets">
        <TabsList>
          <TabsTrigger value="targets">School Targets</TabsTrigger>
          <TabsTrigger value="approvals">Approval Rules</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="targets">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                Institutional Goals
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Attendance Target (%)</Label>
                <Input type="number" value={targets.attendance} onChange={(e) => setTargets({...targets, attendance: +e.target.value})} />
              </div>
              <div>
                <Label>Pass Rate Target (%)</Label>
                <Input type="number" value={targets.passRate} onChange={(e) => setTargets({...targets, passRate: +e.target.value})} />
              </div>
              <div>
                <Label>Fee Collection Target (%)</Label>
                <Input type="number" value={targets.collection} onChange={(e) => setTargets({...targets, collection: +e.target.value})} />
              </div>
              <Button><Save className="w-4 h-4 mr-2" />Save Targets</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="approvals">
          <Card>
            <CardHeader>
              <CardTitle>Approval Workflows</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Configure what requires principal approval</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Alert Thresholds
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Set notification triggers</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Audit Trail
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">View system activity logs</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
