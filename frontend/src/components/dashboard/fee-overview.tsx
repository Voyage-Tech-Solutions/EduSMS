'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface FeeStatus {
    label: string;
    amount: number;
    percentage: number;
    color: string;
}

const feeData: FeeStatus[] = [
    { label: 'Collected', amount: 125000, percentage: 65, color: 'bg-emerald-500' },
    { label: 'Pending', amount: 45000, percentage: 23, color: 'bg-amber-500' },
    { label: 'Overdue', amount: 23000, percentage: 12, color: 'bg-red-500' },
];

export function FeeOverview() {
    const total = feeData.reduce((acc, item) => acc + item.amount, 0);

    return (
        <Card>
            <CardHeader>
                <CardTitle>Fee Collection Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Total */}
                <div className="text-center pb-4 border-b">
                    <p className="text-sm text-slate-500">Total Expected</p>
                    <p className="text-3xl font-bold text-slate-900">
                        ${total.toLocaleString()}
                    </p>
                </div>

                {/* Breakdown */}
                <div className="space-y-4">
                    {feeData.map((item) => (
                        <div key={item.label}>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-600">{item.label}</span>
                                <span className="font-medium">
                                    ${item.amount.toLocaleString()} ({item.percentage}%)
                                </span>
                            </div>
                            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${item.color} rounded-full transition-all`}
                                    style={{ width: `${item.percentage}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
