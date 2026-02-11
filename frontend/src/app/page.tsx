'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { School, Users, CreditCard, CalendarCheck, BookOpen, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import Link from 'next/link';

const features = [
  {
    icon: Users,
    title: 'Student Management',
    description: 'Complete student records, admissions, and enrollment tracking',
  },
  {
    icon: CreditCard,
    title: 'Fees & Billing',
    description: 'Automated invoicing, payment tracking, and financial reports',
  },
  {
    icon: CalendarCheck,
    title: 'Attendance',
    description: 'Digital attendance with real-time alerts and analytics',
  },
  {
    icon: BookOpen,
    title: 'Academics',
    description: 'Grade books, report cards, and academic performance tracking',
  },
  {
    icon: Shield,
    title: 'Multi-Tenant Security',
    description: 'Complete data isolation with role-based access control',
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <School className="h-8 w-8 text-emerald-400" />
            <span className="text-2xl font-bold text-white">EduCore</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" className="text-white hover:text-emerald-400">
                Sign In
              </Button>
            </Link>
            <Link href="/login">
              <Button className="bg-emerald-600 hover:bg-emerald-700 text-white">
                Get Started
              </Button>
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-6 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Modern School Management
            <span className="text-emerald-400"> Made Simple</span>
          </h1>
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            A comprehensive multi-tenant SaaS platform for schools. Manage students,
            fees, attendance, and academics — all in one place.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/login">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-6 text-lg">
                Start Free Trial
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="text-white border-white hover:bg-white/10 px-8 py-6 text-lg">
                View Demo
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Card key={feature.title} className="bg-white/10 border-white/20 backdrop-blur">
              <CardContent className="pt-6">
                <div className="h-12 w-12 rounded-lg bg-emerald-500/20 flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-slate-300">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Stats */}
        <div className="mt-24 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: '500+', label: 'Schools' },
            { value: '50K+', label: 'Students' },
            { value: '99.9%', label: 'Uptime' },
            { value: '24/7', label: 'Support' },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-4xl font-bold text-emerald-400">{stat.value}</div>
              <div className="text-slate-400 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-6 py-12 border-t border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <School className="h-6 w-6 text-emerald-400" />
            <span className="text-white font-semibold">EduCore</span>
          </div>
          <p className="text-slate-400 text-sm">
            © 2024 EduCore SaaS. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
