"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CheckCircle, XCircle, Clock, AlertCircle, CalendarCheck } from "lucide-react";

export default function ParentAttendancePage() {
  const [attendance, setAttendance] = useState<any>({ attendance: [], stats: {} });
  const [children, setChildren] = useState<any[]>([]);
  const [selectedChild, setSelectedChild] = useState("");
  const [selectedDate, setSelectedDate] = useState<Date>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/parent/children")
      .then(res => res.json())
      .then(data => {
        setChildren(data.children || []);
        if (data.children?.length > 0) setSelectedChild(data.children[0].student_id);
      });
  }, []);

  useEffect(() => {
    if (selectedChild) fetchAttendance();
  }, [selectedChild]);

  const fetchAttendance = async () => {
    setLoading(true);
    const response = await fetch(`/api/v1/parent/attendance?student_id=${selectedChild}`);
    const data = await response.json();
    setAttendance(data);
    setLoading(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "present": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "absent": return <XCircle className="w-4 h-4 text-red-500" />;
      case "late": return <Clock className="w-4 h-4 text-orange-500" />;
      case "excused": return <AlertCircle className="w-4 h-4 text-blue-500" />;
      default: return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "present": return "bg-green-100 text-green-800";
      case "absent": return "bg-red-100 text-red-800";
      case "late": return "bg-orange-100 text-orange-800";
      case "excused": return "bg-blue-100 text-blue-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <CalendarCheck className="w-8 h-8" />
            Attendance
          </h1>
          <p className="text-muted-foreground">Track your child's attendance</p>
        </div>
        <div className="flex gap-2">
          {children.length > 1 && (
            <Select value={selectedChild} onValueChange={setSelectedChild}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select Child" />
              </SelectTrigger>
              <SelectContent>
                {children.map((child) => (
                  <SelectItem key={child.student_id} value={child.student_id}>
                    {child.student_name} - {child.grade_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <ReportAbsenceDialog studentId={selectedChild} onSuccess={fetchAttendance} />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Days</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{attendance.stats.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Present</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{attendance.stats.present || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Absent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{attendance.stats.absent || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Late</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{attendance.stats.late || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Attendance Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{attendance.stats.percentage || 0}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Calendar View */}
      <Card>
        <CardHeader>
          <CardTitle>Attendance Calendar</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span className="text-sm">Present</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span className="text-sm">Absent</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-500 rounded"></div>
              <span className="text-sm">Late</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              <span className="text-sm">Excused</span>
            </div>
          </div>
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={setSelectedDate}
            className="rounded-md border"
          />
        </CardContent>
      </Card>

      {/* Attendance History */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Attendance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {loading ? (
              <p className="text-center text-muted-foreground">Loading...</p>
            ) : attendance.attendance.length === 0 ? (
              <p className="text-center text-muted-foreground">No attendance records</p>
            ) : (
              attendance.attendance.slice(0, 10).map((record: any) => (
                <div key={record.id} className="flex justify-between items-center p-3 border rounded">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(record.status)}
                    <div>
                      <p className="font-medium">{new Date(record.date).toLocaleDateString()}</p>
                      {record.notes && <p className="text-sm text-muted-foreground">{record.notes}</p>}
                    </div>
                  </div>
                  <Badge className={getStatusColor(record.status)}>{record.status}</Badge>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ReportAbsenceDialog({ studentId, onSuccess }: any) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ absence_date: '', reason: "" });

  useEffect(() => {
    setData(prev => ({ ...prev, absence_date: new Date().toISOString().split('T')[0] }));
  }, []);

  const handleSubmit = async () => {
    await fetch("/api/v1/parent/attendance/report-absence", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: studentId, ...data }),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Report Absence</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Report Absence</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Date</Label>
            <Input type="date" value={data.absence_date} onChange={(e) => setData({ ...data, absence_date: e.target.value })} />
          </div>
          <div>
            <Label>Reason</Label>
            <Textarea value={data.reason} onChange={(e) => setData({ ...data, reason: e.target.value })} placeholder="Explain the reason for absence..." />
          </div>
          <div>
            <Label>Supporting Document (Optional)</Label>
            <Input type="file" />
          </div>
          <Button onClick={handleSubmit} className="w-full">Submit Report</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
