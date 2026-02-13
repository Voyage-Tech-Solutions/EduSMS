"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Send, Paperclip } from "lucide-react";

export default function ParentMessagesPage() {
  const [messages, setMessages] = useState<any>([]);
  const [selectedMessage, setSelectedMessage] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMessages();
  }, []);

  const fetchMessages = async () => {
    const response = await authFetch("/api/v1/parent/messages");
    const data = await response.json();
    setMessages(data.messages || []);
    setLoading(false);
  };

  const markAsRead = async (messageId: string) => {
    // Mark message as read
    setSelectedMessage(messages.find((m: any) => m.id === messageId));
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Messages</h1>
          <p className="text-muted-foreground">Communicate with teachers and school</p>
        </div>
        <ComposeMessageDialog onSuccess={fetchMessages} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Message List */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Inbox</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {loading ? (
                <div className="p-4 text-center text-muted-foreground">Loading...</div>
              ) : messages.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground">No messages</div>
              ) : (
                messages.map((message: any) => (
                  <div
                    key={message.id}
                    className={`p-4 cursor-pointer hover:bg-accent ${!message.is_read ? "bg-blue-50" : ""}`}
                    onClick={() => markAsRead(message.id)}
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-semibold text-sm">
                        {message.sender?.first_name} {message.sender?.last_name}
                      </span>
                      {!message.is_read && <Badge variant="default" className="text-xs">New</Badge>}
                    </div>
                    <p className="text-sm font-medium">{message.subject}</p>
                    <p className="text-xs text-muted-foreground truncate">{message.message}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(message.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Message Detail */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Message Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedMessage ? (
              <div className="space-y-4">
                <div>
                  <Label>From</Label>
                  <p className="text-sm">
                    {selectedMessage.sender?.first_name} {selectedMessage.sender?.last_name}
                  </p>
                </div>
                <div>
                  <Label>Subject</Label>
                  <p className="text-sm font-semibold">{selectedMessage.subject}</p>
                </div>
                <div>
                  <Label>Date</Label>
                  <p className="text-sm">{new Date(selectedMessage.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <Label>Message</Label>
                  <div className="mt-2 p-4 bg-gray-50 rounded border">
                    <p className="text-sm whitespace-pre-wrap">{selectedMessage.message}</p>
                  </div>
                </div>
                {selectedMessage.attachment_url && (
                  <div>
                    <Label>Attachment</Label>
                    <Button variant="outline" size="sm" className="mt-2">
                      <Paperclip className="w-4 h-4 mr-2" />
                      Download Attachment
                    </Button>
                  </div>
                )}
                <Button className="w-full">
                  <Send className="w-4 h-4 mr-2" />
                  Reply
                </Button>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Select a message to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ComposeMessageDialog({ onSuccess }: any) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState({
    recipient_id: "",
    subject: "",
    message: ""
  });

  const handleSend = async () => {
    await authFetch("/api/v1/parent/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(message),
    });
    setOpen(false);
    onSuccess();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Send className="w-4 h-4 mr-2" />
          New Message
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Compose Message</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>To</Label>
            <Input placeholder="Select recipient" />
          </div>
          <div>
            <Label>Subject</Label>
            <Input
              placeholder="Message subject"
              value={message.subject}
              onChange={(e) => setMessage({ ...message, subject: e.target.value })}
            />
          </div>
          <div>
            <Label>Message</Label>
            <Textarea
              placeholder="Type your message..."
              rows={6}
              value={message.message}
              onChange={(e) => setMessage({ ...message, message: e.target.value })}
            />
          </div>
          <div>
            <Label>Attachment (Optional)</Label>
            <Input type="file" />
          </div>
          <Button onClick={handleSend} className="w-full">
            <Send className="w-4 h-4 mr-2" />
            Send Message
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
