"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, XCircle, Clock, AlertTriangle, DollarSign, BookOpen, FileText, MessageSquare, Calendar } from "lucide-react";
import Link from "next/link";

export default function ParentDashboardPage() {
  const [dashboard, setDashboard] = useState<any>({});
  const [selectedChild, setSelectedChild] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, [selectedChild]);

  const fetchDashboard = async () => {
    setLoading(true);
    const url = selectedChild ? `/api/v1/parent/dashboard?student_id=${selectedChild}` : "/api/v1/parent/dashboard";
    const response = await fetch(url);
    const data = await response.json();
    setDashboard(data);
    if (!selectedChild && data.selected_student) {
      setSelectedChild(data.selected_student);
    }
    setLoading(false);
  };

  const getAttendanceIcon = (status: string) => {
    switch (status) {
      case "present": return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "absent": return <XCircle className="w-5 h-5 text-red-500" />;
      case "late": return <Clock className="w-5 h-5 text-orange-500" />;
      default: return <AlertTriangle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "good": return "text-green-600";
      case "at_risk": return "text-orange-600";
      case "failing": return "text-red-600";
      default: return "text-gray-600";
    }
  };

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      {/* Header with Child Selector */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Parent Dashboard</h1>
          <p className="text-muted-foreground">Monitor your child's progress</p>
        </div>
        {dashboard.children && dashboard.children.length > 1 && (
          <Select value={selectedChild} onValueChange={setSelectedChild}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select Child" />
            </SelectTrigger>
            <SelectContent>
              {dashboard.children.map((child: any) => (
                <SelectItem key={child.student_id} value={child.student_id}>
                  {child.student_name} - {child.grade_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Daily Status Card */}
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getAttendanceIcon(dashboard.daily_status?.attendance_status)}
            Today's Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Attendance</p>
              <p className="text-lg font-semibold capitalize">{dashboard.daily_status?.attendance_status || "Not Recorded"}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Next Class</p>
              <p className="text-lg font-semibold">{dashboard.daily_status?.next_class || "No class scheduled"}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Active Alerts</p>
              <p className="text-lg font-semibold text-red-600">{dashboard.daily_status?.alerts_count || 0}</p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Link href="/dashboard/parent-portal/attendance">
              <Button variant="outline" size="sm">View Attendance</Button>
            </Link>
            <Button variant="outline" size="sm">Notify School</Button>
          </div>
        </CardContent>
      </Card>

      {/* Academic Snapshot */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Academic Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Current Average</p>
              <p className={`text-2xl font-bold ${getStatusColor(dashboard.academic_snapshot?.status)}`}>
                {dashboard.academic_snapshot?.current_average || 0}%
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <Badge variant={dashboard.academic_snapshot?.status === "good" ? "default" : "destructive"}>
                {dashboard.academic_snapshot?.status || "N/A"}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Latest Score</p>
              <p className="text-lg font-semibold">{dashboard.academic_snapshot?.latest_score || "N/A"}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Missing Assignments</p>
              <p className="text-lg font-semibold text-red-600">{dashboard.academic_snapshot?.missing_assignments || 0}</p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Link href="/dashboard/parent-portal/academics">
              <Button variant="outline" size="sm">View Full Report</Button>
            </Link>
            <Link href="/dashboard/parent-portal/assignments">
              <Button variant="outline" size="sm">View Assignments</Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Financial Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Fees & Payments
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Outstanding Balance</p>
              <p className="text-2xl font-bold text-red-600">${dashboard.financial_summary?.outstanding_balance || 0}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <Badge variant={dashboard.financial_summary?.overdue ? "destructive" : "default"}>
                {dashboard.financial_summary?.overdue ? "Overdue" : "Current"}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Next Due Date</p>
              <p className="text-lg font-semibold">{dashboard.financial_summary?.next_due_date || "N/A"}</p>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <Link href="/dashboard/parent-portal/fees">
              <Button size="sm">Pay Now</Button>
            </Link>
            <Link href="/dashboard/parent-portal/fees">
              <Button variant="outline" size="sm">View Statement</Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Alerts & Notifications */}
      {dashboard.alerts && dashboard.alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Alerts & Notifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboard.alerts.map((alert: any, index: number) => (
              <Alert key={index} variant={alert.severity === "high" ? "destructive" : "default"}>
                <AlertDescription className="flex justify-between items-center">
                  <span>{alert.alert_message}</span>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline">View Details</Button>
                    <Button size="sm" variant="outline">Contact Teacher</Button>
                  </div>
                </AlertDescription>
              </Alert>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Link href="/dashboard/parent-portal/fees">
              <Button variant="outline" className="h-20 flex flex-col gap-2">
                <DollarSign className="w-6 h-6" />
                Pay Fees
              </Button>
            </Link>
            <Link href="/dashboard/parent-portal/messages">
              <Button variant="outline" className="h-20 flex flex-col gap-2 relative">
                <MessageSquare className="w-6 h-6" />
                Message Teacher
                {dashboard.unread_messages > 0 && (
                  <Badge variant="destructive" className="absolute top-2 right-2">{dashboard.unread_messages}</Badge>
                )}
              </Button>
            </Link>
            <Link href="/dashboard/parent-portal/documents">
              <Button variant="outline" className="h-20 flex flex-col gap-2">
                <FileText className="w-6 h-6" />
                Upload Document
              </Button>
            </Link>
            <Link href="/dashboard/parent-portal/academics">
              <Button variant="outline" className="h-20 flex flex-col gap-2">
                <BookOpen className="w-6 h-6" />
                View Report Card
              </Button>
            </Link>
            <Button variant="outline" className="h-20 flex flex-col gap-2">
              <Calendar className="w-6 h-6" />
              Download Timetable
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
