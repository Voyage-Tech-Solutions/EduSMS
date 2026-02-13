"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail } from "lucide-react";

export default function TeacherMessagesPage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Messages</h1>
        <p className="text-slate-500">Communicate with parents and admin</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            Inbox
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-slate-500">
            <Mail className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No messages yet</p>
            <p className="text-sm mt-2">Your messages will appear here</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
