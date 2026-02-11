import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
    title: string;
    value: string | number;
    description?: string;
    icon?: LucideIcon;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    className?: string;
}

export function StatCard({
    title,
    value,
    description,
    icon: Icon,
    trend,
    className,
}: StatCardProps) {
    return (
        <Card className={cn('relative overflow-hidden', className)}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">
                    {title}
                </CardTitle>
                {Icon && (
                    <div className="h-10 w-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                        <Icon className="h-5 w-5 text-emerald-600" />
                    </div>
                )}
            </CardHeader>
            <CardContent>
                <div className="text-3xl font-bold text-slate-900">{value}</div>
                {(description || trend) && (
                    <div className="flex items-center gap-2 mt-1">
                        {trend && (
                            <span
                                className={cn(
                                    'text-sm font-medium',
                                    trend.isPositive ? 'text-emerald-600' : 'text-red-600'
                                )}
                            >
                                {trend.isPositive ? '+' : ''}{trend.value}%
                            </span>
                        )}
                        {description && (
                            <span className="text-sm text-slate-500">{description}</span>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
