"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users } from "lucide-react";

export default function TeacherClassesPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">My Classes</h1>
        <p className="text-slate-500">Manage your assigned classes</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Class List
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-slate-500">
            <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No classes assigned yet</p>
            <p className="text-sm mt-2">Contact admin to assign classes to your account</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
