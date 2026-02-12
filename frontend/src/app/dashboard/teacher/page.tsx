"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Clock, Users, FileText, AlertTriangle, BookOpen, CheckCircle } from "lucide-react";
import Link from "next/link";

export default function TeacherDashboard() {
  const [dashboard, setDashboard] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/teacher/dashboard")
      .then(res => res.json())
      .then(data => setDashboard(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Teacher Dashboard</h1>
        <p className="text-muted-foreground">Your teaching control center</p>
      </div>

      {/* Next Class Card */}
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Next Class
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dashboard.next_class ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Time</p>
                  <p className="text-lg font-bold">{dashboard.next_class.time}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Subject</p>
                  <p className="text-lg font-bold">{dashboard.next_class.subject}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Class</p>
                  <p className="text-lg font-bold">{dashboard.next_class.class}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Room</p>
                  <p className="text-lg font-bold">{dashboard.next_class.room}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Link href="/dashboard/teacher/attendance">
                  <Button>Take Attendance</Button>
                </Link>
                <Link href={`/dashboard/teacher/classes/${dashboard.next_class.class_id}`}>
                  <Button variant="outline">Open Class</Button>
                </Link>
                <Link href="/dashboard/teacher/planning">
                  <Button variant="outline">Lesson Plan</Button>
                </Link>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">No upcoming classes today</p>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Grading Tasks */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Grading Tasks
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm">Submissions Waiting</span>
              <Badge variant="destructive">{dashboard.grading?.submissions_waiting || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Overdue Grading</span>
              <Badge variant="destructive">{dashboard.grading?.overdue || 0}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Assessments Unmarked</span>
              <Badge>{dashboard.grading?.unmarked || 0}</Badge>
            </div>
            <div className="flex gap-2">
              <Link href="/dashboard/teacher/gradebook">
                <Button size="sm" className="w-full">Open Gradebook</Button>
              </Link>
              <Link href="/dashboard/teacher/assignments?filter=grading">
                <Button size="sm" variant="outline" className="w-full">Grade Next</Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
              Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboard.alerts?.map((alert: any, idx: number) => (
              <div key={idx} className="p-3 bg-orange-50 border border-orange-200 rounded flex justify-between items-center">
                <span className="text-sm">{alert.message}</span>
                <Button size="sm" variant="outline">View</Button>
              </div>
            ))}
            {(!dashboard.alerts || dashboard.alerts.length === 0) && (
              <div className="text-center py-4">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">All clear!</p>
              </div>
            )}
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
                <TableHead>Attendance</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dashboard.schedule?.map((session: any) => (
                <TableRow key={session.id}>
                  <TableCell>{session.time}</TableCell>
                  <TableCell>{session.subject}</TableCell>
                  <TableCell>{session.class}</TableCell>
                  <TableCell>{session.room}</TableCell>
                  <TableCell>
                    <Badge variant={session.status === 'completed' ? 'default' : 'secondary'}>
                      {session.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {session.attendance_taken ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <span className="text-red-500">Missing</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline">Attendance</Button>
                      <Button size="sm" variant="outline">Gradebook</Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

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
                <TableHead>Attendance Avg</TableHead>
                <TableHead>Class Avg</TableHead>
                <TableHead>At-Risk</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dashboard.classes?.map((cls: any) => (
                <TableRow key={cls.id}>
                  <TableCell className="font-medium">{cls.name}</TableCell>
                  <TableCell>{cls.student_count}</TableCell>
                  <TableCell>{cls.attendance_avg}%</TableCell>
                  <TableCell>{cls.class_avg}%</TableCell>
                  <TableCell>
                    <Badge variant="destructive">{cls.at_risk_count}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Link href={`/dashboard/teacher/classes/${cls.id}`}>
                        <Button size="sm" variant="outline">Open</Button>
                      </Link>
                      <Link href={`/dashboard/teacher/gradebook?class=${cls.id}`}>
                        <Button size="sm" variant="outline">Gradebook</Button>
                      </Link>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
