"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar } from "lucide-react";

export default function TeacherTimetablePage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">My Timetable</h1>
        <p className="text-slate-500">Your weekly teaching schedule</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Weekly Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-slate-500">
            <Calendar className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Timetable feature will be available soon</p>
            <p className="text-sm mt-2">Contact admin to set up your teaching schedule</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
