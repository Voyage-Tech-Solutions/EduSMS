"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users } from "lucide-react";

export default function TeacherClassDetailPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Class Details</h1>
        <p className="text-slate-500">View and manage class information</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Class Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-slate-500">
            <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Class not found</p>
            <p className="text-sm mt-2">This class may not be assigned to you</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
