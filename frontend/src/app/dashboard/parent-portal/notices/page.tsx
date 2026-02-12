"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Bell, Calendar, AlertCircle, Info, Download, CheckCircle } from "lucide-react";

export default function ParentNoticesPage() {
  const [notices, setNotices] = useState<any>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotices();
  }, []);

  const fetchNotices = async () => {
    const response = await fetch("/api/v1/parent/notices");
    const data = await response.json();
    setNotices(data.notices || []);
    setLoading(false);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "event": return <Calendar className="w-5 h-5 text-blue-500" />;
      case "holiday": return <Calendar className="w-5 h-5 text-green-500" />;
      case "meeting": return <Bell className="w-5 h-5 text-orange-500" />;
      case "urgent": return <AlertCircle className="w-5 h-5 text-red-500" />;
      default: return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getTypeBadge = (type: string) => {
    const colors: any = {
      event: "bg-blue-100 text-blue-800",
      holiday: "bg-green-100 text-green-800",
      meeting: "bg-orange-100 text-orange-800",
      policy: "bg-purple-100 text-purple-800",
      urgent: "bg-red-100 text-red-800",
      general: "bg-gray-100 text-gray-800"
    };
    return <Badge className={colors[type] || ""}>{type}</Badge>;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">School Notices</h1>
        <p className="text-muted-foreground">Stay updated with school announcements</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Notices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{notices.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {notices.filter((n: any) => n.notice_type === "event").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Urgent</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {notices.filter((n: any) => n.notice_type === "urgent").length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Meetings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {notices.filter((n: any) => n.notice_type === "meeting").length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Notices List */}
      <div className="space-y-4">
        {loading ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">Loading...</CardContent>
          </Card>
        ) : notices.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">No notices available</CardContent>
          </Card>
        ) : (
          notices.map((notice: any) => (
            <Card key={notice.id} className={notice.notice_type === "urgent" ? "border-red-300 bg-red-50" : ""}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    {getTypeIcon(notice.notice_type)}
                    <div>
                      <CardTitle className="text-lg">{notice.title}</CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {new Date(notice.published_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  {getTypeBadge(notice.notice_type)}
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm mb-4 whitespace-pre-wrap">{notice.content}</p>
                <div className="flex gap-2">
                  <NoticeDetailsDialog notice={notice} />
                  {notice.attachment_url && (
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </Button>
                  )}
                  <AcknowledgeButton noticeId={notice.id} onSuccess={fetchNotices} />
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

function NoticeDetailsDialog({ notice }: any) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">View Details</Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{notice.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Type</Label>
            <p className="text-sm capitalize">{notice.notice_type}</p>
          </div>
          <div>
            <Label>Published Date</Label>
            <p className="text-sm">{new Date(notice.published_at).toLocaleString()}</p>
          </div>
          {notice.expires_at && (
            <div>
              <Label>Expires</Label>
              <p className="text-sm">{new Date(notice.expires_at).toLocaleDateString()}</p>
            </div>
          )}
          <div>
            <Label>Content</Label>
            <div className="mt-2 p-4 bg-gray-50 rounded border">
              <p className="text-sm whitespace-pre-wrap">{notice.content}</p>
            </div>
          </div>
          {notice.attachment_url && (
            <div>
              <Label>Attachment</Label>
              <Button variant="outline" size="sm" className="mt-2 w-full">
                <Download className="w-4 h-4 mr-2" />
                Download Attachment
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AcknowledgeButton({ noticeId, onSuccess }: any) {
  const [acknowledged, setAcknowledged] = useState(false);

  const handleAcknowledge = async () => {
    await fetch(`/api/v1/parent/notices/${noticeId}/acknowledge`, {
      method: "POST",
    });
    setAcknowledged(true);
    onSuccess();
  };

  return (
    <Button
      size="sm"
      variant={acknowledged ? "outline" : "default"}
      onClick={handleAcknowledge}
      disabled={acknowledged}
    >
      <CheckCircle className="w-4 h-4 mr-2" />
      {acknowledged ? "Acknowledged" : "Acknowledge"}
    </Button>
  );
}
