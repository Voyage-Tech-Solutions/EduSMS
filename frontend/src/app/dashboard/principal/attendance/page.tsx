"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Send } from "lucide-react";

export default function PrincipalAttendancePage() {
  const [summary, setSummary] = useState<any>({});
  const [classes, setClasses] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState('');

  useEffect(() => {
    setSelectedDate(new Date().toISOString().split('T')[0]);
  }, []);
  const [showMissingModal, setShowMissingModal] = useState(false);
  const [showReminderModal, setShowReminderModal] = useState(false);

  useEffect(() => { fetchData(); }, [selectedDate]);

  const fetchData = async () => {
    const res = await authFetch(`/api/v1/principal-dashboard/attendance/summary?date=${selectedDate}`);
    setSummary(await res.json());
    const classRes = await authFetch(`/api/v1/principal-dashboard/attendance/classes?date=${selectedDate}`);
    setClasses(await classRes.json());
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Attendance Oversight</h1>
          <p className="text-gray-600">Monitor attendance performance across the school</p>
        </div>
        <div className="flex gap-2">
          <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="border rounded px-3 py-2" />
          <Button variant="outline" onClick={() => setShowMissingModal(true)}><AlertTriangle className="w-4 h-4 mr-2" />Missing Submissions</Button>
          <Button variant="outline" onClick={() => setShowReminderModal(true)}><Send className="w-4 h-4 mr-2" />Send Reminder</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <p className="text-sm text-gray-600">Present</p>
          <p className="text-3xl font-bold">{summary.present || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Attendance Rate</p>
          <p className="text-3xl font-bold">{summary.attendance_rate || 0}%</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Absent</p>
          <p className="text-3xl font-bold text-red-600">{summary.absent || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Late</p>
          <p className="text-3xl font-bold text-orange-600">{summary.late || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-gray-600">Excused</p>
          <p className="text-3xl font-bold">{summary.excused || 0}</p>
        </Card>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Class Attendance Summary</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left">Grade</th>
                <th className="px-4 py-3 text-left">Class</th>
                <th className="px-4 py-3 text-left">Teacher</th>
                <th className="px-4 py-3 text-left">Submission Status</th>
                <th className="px-4 py-3 text-left">Attendance Rate</th>
                <th className="px-4 py-3 text-left">Absent</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {classes.map((cls) => (
                <tr key={cls.id}>
                  <td className="px-4 py-3">{cls.grade}</td>
                  <td className="px-4 py-3">{cls.name}</td>
                  <td className="px-4 py-3">{cls.teacher}</td>
                  <td className="px-4 py-3">
                    <Badge className={cls.submitted ? "bg-green-500" : "bg-red-500"}>
                      {cls.submitted ? "Submitted" : "Not Submitted"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">{cls.attendance_rate || 0}%</td>
                  <td className="px-4 py-3">{cls.absent || 0}</td>
                  <td className="px-4 py-3">
                    <Button size="sm" variant="outline">View</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={showMissingModal} onOpenChange={setShowMissingModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Missing Attendance Submissions</DialogTitle></DialogHeader>
          <p>Classes where attendance has not been submitted for {selectedDate}</p>
        </DialogContent>
      </Dialog>

      <Dialog open={showReminderModal} onOpenChange={setShowReminderModal}>
        <DialogContent>
          <DialogHeader><DialogTitle>Send Attendance Reminder</DialogTitle></DialogHeader>
          <form className="space-y-4">
            <Button type="submit">Send Reminder</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
