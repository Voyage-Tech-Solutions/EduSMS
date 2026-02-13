import Link from "next/link";
import { ArrowRight, CheckCircle, Shield, Users, TrendingUp } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-2xl font-semibold">EduCore</div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-gray-600 hover:text-gray-900">Features</a>
            <a href="#how-it-works" className="text-gray-600 hover:text-gray-900">How it works</a>
            <a href="#security" className="text-gray-600 hover:text-gray-900">Security</a>
            <Link href="/login" className="text-gray-600 hover:text-gray-900">Sign in</Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-24 text-center">
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
          School management, in one place
        </h1>
        <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
          Manage students, attendance, fees, and academic records through a single, structured system designed for schools.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-4">
          <Link href="/signup" className="px-8 py-4 bg-gray-900 text-white rounded-lg hover:bg-gray-800 font-medium">
            Get Started
          </Link>
          <Link href="/demo" className="px-8 py-4 border border-gray-300 rounded-lg hover:border-gray-400 font-medium">
            Request Demo
          </Link>
        </div>
        <p className="text-sm text-gray-500">No setup fees. Start with your school in minutes.</p>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-16">
            Everything your school needs to operate efficiently
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-12">
            <div>
              <h3 className="text-xl font-semibold mb-3">Student Management</h3>
              <p className="text-gray-600">
                Maintain accurate student records, admissions, and enrollment history in one place.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Fees & Billing</h3>
              <p className="text-gray-600">
                Create invoices, track payments, and monitor outstanding balances without manual spreadsheets.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Attendance</h3>
              <p className="text-gray-600">
                Record daily attendance and access reports across classes and grades.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Academics</h3>
              <p className="text-gray-600">
                Manage assessments, gradebooks, and report cards with structured data.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Access Control</h3>
              <p className="text-gray-600">
                Role-based access for administrators, teachers, and parents.
              </p>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-3">Reports</h3>
              <p className="text-gray-600">
                Generate comprehensive reports for academics, attendance, and finances.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How Schools Use It */}
      <section id="how-it-works" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-6">
            A system that supports your daily operations
          </h2>
          <div className="max-w-3xl mx-auto space-y-6 mt-12">
            <div className="flex gap-4">
              <CheckCircle className="w-6 h-6 text-gray-900 flex-shrink-0 mt-1" />
              <div>
                <p className="text-lg">Admin staff manage admissions, documents, and billing</p>
              </div>
            </div>
            <div className="flex gap-4">
              <CheckCircle className="w-6 h-6 text-gray-900 flex-shrink-0 mt-1" />
              <div>
                <p className="text-lg">Teachers record attendance, grades, and assignments</p>
              </div>
            </div>
            <div className="flex gap-4">
              <CheckCircle className="w-6 h-6 text-gray-900 flex-shrink-0 mt-1" />
              <div>
                <p className="text-lg">Principals monitor performance, reports, and approvals</p>
              </div>
            </div>
            <div className="flex gap-4">
              <CheckCircle className="w-6 h-6 text-gray-900 flex-shrink-0 mt-1" />
              <div>
                <p className="text-lg">Parents stay informed on attendance, academics, and fees</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-16">Used by growing schools</h2>
          <div className="grid md:grid-cols-4 gap-12 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">500+</div>
              <div className="text-gray-600">Schools</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">50,000+</div>
              <div className="text-gray-600">Students</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">99.9%</div>
              <div className="text-gray-600">Uptime</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">24/7</div>
              <div className="text-gray-600">Support</div>
            </div>
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section id="security" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-6">
            Built with data protection in mind
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mt-12">
            <div className="text-center">
              <Shield className="w-12 h-12 mx-auto mb-4 text-gray-900" />
              <h3 className="font-semibold mb-2">Data Separation</h3>
              <p className="text-sm text-gray-600">School-level data isolation</p>
            </div>
            <div className="text-center">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-900" />
              <h3 className="font-semibold mb-2">Access Control</h3>
              <p className="text-sm text-gray-600">Role-based permissions</p>
            </div>
            <div className="text-center">
              <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-900" />
              <h3 className="font-semibold mb-2">Cloud Infrastructure</h3>
              <p className="text-sm text-gray-600">Secure and scalable</p>
            </div>
            <div className="text-center">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-gray-900" />
              <h3 className="font-semibold mb-2">Audit Tracking</h3>
              <p className="text-sm text-gray-600">Track key actions</p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-gray-900 text-white py-24">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold mb-6">Get started with EduCore</h2>
          <p className="text-xl text-gray-300 mb-12">
            Set up your school and begin managing your operations from a single system.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup" className="px-8 py-4 bg-white text-gray-900 rounded-lg hover:bg-gray-100 font-medium inline-flex items-center justify-center gap-2">
              Get Started <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="/demo" className="px-8 py-4 border border-white rounded-lg hover:bg-white hover:text-gray-900 font-medium">
              Request Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="text-xl font-semibold mb-4">EduCore</div>
              <p className="text-sm text-gray-600">School management, simplified.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#features" className="hover:text-gray-900">Features</a></li>
                <li><a href="#security" className="hover:text-gray-900">Security</a></li>
                <li><Link href="/pricing" className="hover:text-gray-900">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><Link href="/about" className="hover:text-gray-900">About</Link></li>
                <li><Link href="/contact" className="hover:text-gray-900">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><Link href="/privacy" className="hover:text-gray-900">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-gray-900">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t mt-12 pt-8 text-center text-sm text-gray-600">
            © 2026 EduCore. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
