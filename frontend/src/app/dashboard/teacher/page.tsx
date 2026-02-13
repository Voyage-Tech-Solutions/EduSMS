"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Clock, FileText, AlertTriangle, Users } from "lucide-react";
import Link from "next/link";

export default function TeacherDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { getSession } = await import('@/lib/supabase');
        const session = await getSession();
        if (!session?.access_token) return;
        
        const headers = { 'Authorization': `Bearer ${session.access_token}` };
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        
        const res = await fetch(`${baseUrl}/teacher/dashboard`, { headers });
        if (res.ok) {
          const result = await res.json();
          setData(result);
        }
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-slate-200 rounded w-1/4"></div>
          <div className="h-32 bg-slate-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Teacher Dashboard</h1>
        <p className="text-slate-500">Your teaching control center</p>
      </div>

      {/* Today's Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Next Class */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Next Class
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.next_class ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Subject</p>
                    <p className="font-bold">{data.next_class.subject}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Class</p>
                    <p className="font-bold">{data.next_class.class}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Time</p>
                    <p className="font-bold">{data.next_class.time}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Students</p>
                    <p className="font-bold">{data.next_class.students}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link href="/dashboard/teacher/attendance">
                    <Button size="sm">Take Attendance</Button>
                  </Link>
                  <Link href={`/dashboard/teacher/classes/${data.next_class.class_id}`}>
                    <Button size="sm" variant="outline">Open Class</Button>
                  </Link>
                </div>
              </div>
            ) : (
              <p className="text-slate-500">No upcoming classes today</p>
            )}
          </CardContent>
        </Card>

        {/* Pending Work */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Pending Work
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span>Assignments to grade</span>
              <Badge variant="destructive">{data.pending?.assignments || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Late submissions</span>
              <Badge variant="destructive">{data.pending?.late || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Missing marks</span>
              <Badge>{data.pending?.missing_marks || 0}</Badge>
            </div>
            <div className="flex gap-2 mt-4">
              <Link href="/dashboard/teacher/gradebook" className="flex-1">
                <Button size="sm" className="w-full">Open Gradebook</Button>
              </Link>
              <Link href="/dashboard/teacher/assignments?filter=grading" className="flex-1">
                <Button size="sm" variant="outline" className="w-full">Grade Next</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Today's Schedule */}
      <Card>
        <CardHeader>
          <CardTitle>Today's Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Subject</TableHead>
                <TableHead>Class</TableHead>
                <TableHead>Room</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.schedule?.length > 0 ? data.schedule.map((session: any, idx: number) => (
                <TableRow key={idx}>
                  <TableCell>{session.time}</TableCell>
                  <TableCell>{session.subject}</TableCell>
                  <TableCell>{session.class}</TableCell>
                  <TableCell>{session.room}</TableCell>
                  <TableCell>
                    <Badge variant={session.status === 'done' ? 'default' : 'secondary'}>
                      {session.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Link href="/dashboard/teacher/attendance">
                      <Button size="sm" variant="outline">Take Attendance</Button>
                    </Link>
                  </TableCell>
                </TableRow>
              )) : (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-slate-500 py-8">
                    No classes scheduled for today
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Alerts */}
      {data.alerts?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.alerts.map((alert: any, idx: number) => (
              <div key={idx} className="p-3 bg-orange-50 border border-orange-200 rounded flex justify-between items-center">
                <span className="text-sm">{alert.message}</span>
                <Button size="sm" variant="outline">View</Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* My Classes Snapshot */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            My Classes Snapshot
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Class</TableHead>
                <TableHead>Students</TableHead>
                <TableHead>Attendance</TableHead>
                <TableHead>Avg Score</TableHead>
                <TableHead>At Risk</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.classes?.length > 0 ? data.classes.map((cls: any) => (
                <TableRow key={cls.id}>
                  <TableCell className="font-medium">{cls.name}</TableCell>
                  <TableCell>{cls.students}</TableCell>
                  <TableCell>{cls.attendance}%</TableCell>
                  <TableCell>{cls.avg_score}%</TableCell>
                  <TableCell>
                    <Badge variant="destructive">{cls.at_risk}</Badge>
                  </TableCell>
                  <TableCell>
                    <Link href={`/dashboard/teacher/classes/${cls.id}`}>
                      <Button size="sm" variant="outline">Open</Button>
                    </Link>
                  </TableCell>
                </TableRow>
              )) : (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-slate-500 py-8">
                    No classes assigned
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
