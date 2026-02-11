'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare } from 'lucide-react';

export default function MessagesPage() {
    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Messages</h1>
                <p className="text-slate-500 mt-1">Communicate with teachers and school staff</p>
            </div>

            <Card>
                <CardContent className="py-16 text-center text-slate-500">
                    <MessageSquare className="h-16 w-16 mx-auto mb-4 text-slate-300" />
                    <h3 className="text-lg font-semibold text-slate-700 mb-2">Messaging Coming Soon</h3>
                    <p className="text-sm max-w-md mx-auto">
                        You&apos;ll be able to message teachers and school staff directly from here.
                        For now, please contact the school office for any inquiries.
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
