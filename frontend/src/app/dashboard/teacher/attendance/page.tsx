"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { CalendarCheck, Save, CheckCircle } from "lucide-react";

export default function TeacherAttendancePage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [selectedClass, setSelectedClass] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [students, setStudents] = useState<any[]>([]);
  const [attendance, setAttendance] = useState<Record<string, string>>({});

  useEffect(() => {
    fetch("/api/v1/teacher/classes")
      .then(res => res.json())
      .then(data => setClasses(data));
  }, []);

  useEffect(() => {
    if (selectedClass) {
      fetch(`/api/v1/teacher/classes/${selectedClass}/students`)
        .then(res => res.json())
        .then(data => {
          setStudents(data);
          const initial: Record<string, string> = {};
          data.forEach((s: any) => initial[s.id] = 'present');
          setAttendance(initial);
        });
    }
  }, [selectedClass]);

  const markAll = (status: string) => {
    const updated: Record<string, string> = {};
    students.forEach(s => updated[s.id] = status);
    setAttendance(updated);
  };

  const handleSave = async () => {
    const records = Object.entries(attendance).map(([student_id, status]) => ({
      student_id,
      status
    }));

    await fetch("/api/v1/teacher/attendance/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ class_id: selectedClass, date, records })
    });

    alert("Attendance saved successfully!");
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <CalendarCheck className="w-8 h-8" />
          Take Attendance
        </h1>
        <p className="text-muted-foreground">Record student attendance quickly</p>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Select value={selectedClass} onValueChange={setSelectedClass}>
              <SelectTrigger>
                <SelectValue placeholder="Select Class" />
              </SelectTrigger>
              <SelectContent>
                {classes.map(cls => (
                  <SelectItem key={cls.id} value={cls.id}>{cls.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />

            <Button variant="outline" onClick={() => markAll('present')}>
              Mark All Present
            </Button>

            <Button onClick={handleSave} disabled={!selectedClass}>
              <Save className="w-4 h-4 mr-2" />
              Save Attendance
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Attendance Table */}
      {selectedClass && (
        <Card>
          <CardHeader>
            <CardTitle>Students ({students.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {students.map((student, idx) => (
                <div key={student.id} className="flex items-center gap-4 p-3 border rounded hover:bg-gray-50">
                  <span className="w-8 text-sm text-muted-foreground">{idx + 1}</span>
                  <span className="w-32 text-sm font-mono">{student.admission_number}</span>
                  <span className="flex-1 font-medium">{student.first_name} {student.last_name}</span>
                  
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant={attendance[student.id] === 'present' ? 'default' : 'outline'}
                      onClick={() => setAttendance({...attendance, [student.id]: 'present'})}
                    >
                      Present
                    </Button>
                    <Button
                      size="sm"
                      variant={attendance[student.id] === 'absent' ? 'destructive' : 'outline'}
                      onClick={() => setAttendance({...attendance, [student.id]: 'absent'})}
                    >
                      Absent
                    </Button>
                    <Button
                      size="sm"
                      variant={attendance[student.id] === 'late' ? 'secondary' : 'outline'}
                      onClick={() => setAttendance({...attendance, [student.id]: 'late'})}
                    >
                      Late
                    </Button>
                    <Button
                      size="sm"
                      variant={attendance[student.id] === 'excused' ? 'secondary' : 'outline'}
                      onClick={() => setAttendance({...attendance, [student.id]: 'excused'})}
                    >
                      Excused
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
