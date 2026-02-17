"use client";

import { useState, useEffect } from "react";
import { authFetch } from "@/lib/authFetch";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Mail, MessageSquare, Bell, Send, Search, Trash2, Archive,
  Star, Paperclip, Users, RefreshCw, Plus, Eye
} from "lucide-react";

interface Message {
  id: string;
  subject: string;
  body: string;
  sender_id: string;
  sender_name?: string;
  is_read: boolean;
  priority: string;
  created_at: string;
  folder: string;
}

interface Announcement {
  id: string;
  title: string;
  content: string;
  category: string;
  priority: string;
  status: string;
  publish_at: string;
  author_name?: string;
  view_count?: number;
}

export default function CommunicationHubPage() {
  const [activeTab, setActiveTab] = useState("inbox");
  const [messages, setMessages] = useState<Message[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [composeModal, setComposeModal] = useState(false);
  const [announcementModal, setAnnouncementModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Compose message form
  const [newMessage, setNewMessage] = useState({
    recipients: [] as string[],
    subject: "",
    body: "",
    priority: "normal"
  });

  // New announcement form
  const [newAnnouncement, setNewAnnouncement] = useState({
    title: "",
    content: "",
    category: "general",
    priority: "normal",
    target_audience: ["all"]
  });

  useEffect(() => {
    fetchMessages();
    fetchAnnouncements();
  }, []);

  const fetchMessages = async (folder = "inbox") => {
    setLoading(true);
    try {
      const res = await authFetch(`/api/v1/communication/messages?folder=${folder}`);
      const data = await res.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error("Failed to fetch messages", error);
    }
    setLoading(false);
  };

  const fetchAnnouncements = async () => {
    try {
      const res = await authFetch(`/api/v1/communication/announcements`);
      const data = await res.json();
      setAnnouncements(data.announcements || []);
    } catch (error) {
      console.error("Failed to fetch announcements", error);
    }
  };

  const sendMessage = async () => {
    try {
      await authFetch(`/api/v1/communication/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newMessage)
      });
      setComposeModal(false);
      setNewMessage({ recipients: [], subject: "", body: "", priority: "normal" });
      fetchMessages();
    } catch (error) {
      console.error("Failed to send message", error);
    }
  };

  const createAnnouncement = async () => {
    try {
      await authFetch(`/api/v1/communication/announcements`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newAnnouncement)
      });
      setAnnouncementModal(false);
      setNewAnnouncement({ title: "", content: "", category: "general", priority: "normal", target_audience: ["all"] });
      fetchAnnouncements();
    } catch (error) {
      console.error("Failed to create announcement", error);
    }
  };

  const markAsRead = async (messageId: string) => {
    try {
      await authFetch(`/api/v1/communication/messages/${messageId}/read`, {
        method: "POST"
      });
      fetchMessages();
    } catch (error) {
      console.error("Failed to mark as read", error);
    }
  };

  const moveToFolder = async (messageId: string, folder: string) => {
    try {
      await authFetch(`/api/v1/communication/messages/${messageId}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder })
      });
      fetchMessages();
    } catch (error) {
      console.error("Failed to move message", error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent": return "destructive";
      case "high": return "default";
      default: return "secondary";
    }
  };

  const filteredMessages = messages.filter(m =>
    m.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.body.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Communication Hub</h1>
          <p className="text-gray-600">Messages, announcements, and notifications</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setComposeModal(true)}>
            <Plus className="w-4 h-4 mr-2" /> New Message
          </Button>
          <Button variant="outline" onClick={() => setAnnouncementModal(true)}>
            <Bell className="w-4 h-4 mr-2" /> New Announcement
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="inbox">
            <Mail className="w-4 h-4 mr-2" /> Inbox
          </TabsTrigger>
          <TabsTrigger value="sent">
            <Send className="w-4 h-4 mr-2" /> Sent
          </TabsTrigger>
          <TabsTrigger value="announcements">
            <Bell className="w-4 h-4 mr-2" /> Announcements
          </TabsTrigger>
        </TabsList>

        {/* Inbox Tab */}
        <TabsContent value="inbox" className="space-y-4">
          <div className="flex gap-4">
            {/* Message List */}
            <Card className="w-1/3 p-4">
              <div className="flex items-center gap-2 mb-4">
                <Search className="w-4 h-4 text-gray-500" />
                <Input
                  placeholder="Search messages..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1"
                />
                <Button variant="ghost" size="sm" onClick={() => fetchMessages()}>
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {loading ? (
                  <p className="text-center text-gray-500 py-4">Loading...</p>
                ) : filteredMessages.length === 0 ? (
                  <p className="text-center text-gray-500 py-4">No messages</p>
                ) : (
                  filteredMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`p-3 rounded cursor-pointer hover:bg-gray-100 ${
                        selectedMessage?.id === message.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                      } ${!message.is_read ? 'font-semibold bg-gray-50' : ''}`}
                      onClick={() => {
                        setSelectedMessage(message);
                        if (!message.is_read) markAsRead(message.id);
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm truncate">{message.sender_name || 'Unknown'}</span>
                        {message.priority !== 'normal' && (
                          <Badge variant={getPriorityColor(message.priority)} className="text-xs">
                            {message.priority}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm truncate">{message.subject}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(message.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {/* Message Detail */}
            <Card className="flex-1 p-6">
              {selectedMessage ? (
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h2 className="text-xl font-semibold">{selectedMessage.subject}</h2>
                      <p className="text-sm text-gray-500">
                        From: {selectedMessage.sender_name || 'Unknown'} •{' '}
                        {new Date(selectedMessage.created_at).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => moveToFolder(selectedMessage.id, 'archive')}>
                        <Archive className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => moveToFolder(selectedMessage.id, 'trash')}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="prose max-w-none">
                    <p className="whitespace-pre-wrap">{selectedMessage.body}</p>
                  </div>
                  <div className="mt-6 pt-4 border-t">
                    <Button onClick={() => {
                      setNewMessage({
                        ...newMessage,
                        subject: `Re: ${selectedMessage.subject}`,
                        recipients: [selectedMessage.sender_id]
                      });
                      setComposeModal(true);
                    }}>
                      Reply
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <div className="text-center">
                    <Mail className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>Select a message to read</p>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </TabsContent>

        {/* Sent Tab */}
        <TabsContent value="sent">
          <Card className="p-6">
            <p className="text-gray-500">Sent messages will appear here</p>
          </Card>
        </TabsContent>

        {/* Announcements Tab */}
        <TabsContent value="announcements" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {announcements.map((announcement) => (
              <Card key={announcement.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <Badge variant={getPriorityColor(announcement.priority)}>
                    {announcement.category}
                  </Badge>
                  <Badge variant="outline">{announcement.status}</Badge>
                </div>
                <h3 className="font-semibold mb-2">{announcement.title}</h3>
                <p className="text-sm text-gray-600 line-clamp-3">{announcement.content}</p>
                <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
                  <span>{announcement.author_name}</span>
                  <div className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {announcement.view_count || 0}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Compose Message Modal */}
      <Dialog open={composeModal} onOpenChange={setComposeModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Message</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>To</Label>
              <Input
                placeholder="Enter recipient email or select from list"
                onChange={(e) => setNewMessage({ ...newMessage, recipients: [e.target.value] })}
              />
            </div>
            <div>
              <Label>Subject</Label>
              <Input
                value={newMessage.subject}
                onChange={(e) => setNewMessage({ ...newMessage, subject: e.target.value })}
              />
            </div>
            <div>
              <Label>Priority</Label>
              <Select
                value={newMessage.priority}
                onValueChange={(v) => setNewMessage({ ...newMessage, priority: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Message</Label>
              <Textarea
                rows={6}
                value={newMessage.body}
                onChange={(e) => setNewMessage({ ...newMessage, body: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setComposeModal(false)}>Cancel</Button>
            <Button onClick={sendMessage}>
              <Send className="w-4 h-4 mr-2" /> Send
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New Announcement Modal */}
      <Dialog open={announcementModal} onOpenChange={setAnnouncementModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Announcement</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Title</Label>
              <Input
                value={newAnnouncement.title}
                onChange={(e) => setNewAnnouncement({ ...newAnnouncement, title: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Category</Label>
                <Select
                  value={newAnnouncement.category}
                  onValueChange={(v) => setNewAnnouncement({ ...newAnnouncement, category: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="general">General</SelectItem>
                    <SelectItem value="academic">Academic</SelectItem>
                    <SelectItem value="events">Events</SelectItem>
                    <SelectItem value="emergency">Emergency</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Priority</Label>
                <Select
                  value={newAnnouncement.priority}
                  onValueChange={(v) => setNewAnnouncement({ ...newAnnouncement, priority: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>Content</Label>
              <Textarea
                rows={6}
                value={newAnnouncement.content}
                onChange={(e) => setNewAnnouncement({ ...newAnnouncement, content: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAnnouncementModal(false)}>Cancel</Button>
            <Button onClick={createAnnouncement}>
              <Bell className="w-4 h-4 mr-2" /> Publish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
