/**
 * EduCore SaaS - Type Definitions
 */

// ============== ENUMS ==============

export type UserRole = 'system_admin' | 'principal' | 'office_admin' | 'teacher' | 'parent' | 'student';
export type Gender = 'male' | 'female' | 'other';
export type StudentStatus = 'active' | 'inactive' | 'transferred' | 'graduated';
export type PaymentStatus = 'pending' | 'paid' | 'partial' | 'overdue';
export type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused';

// ============== USER & AUTH ==============

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  school_id?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  school_id?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ============== SCHOOL ==============

export interface School {
  id: string;
  name: string;
  address?: string;
  phone?: string;
  email?: string;
  logo_url?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// ============== STUDENT ==============

export interface Student {
  id: string;
  school_id: string;
  admission_number: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: Gender;
  grade_id?: string;
  class_id?: string;
  status: StudentStatus;
  created_at?: string;
  updated_at?: string;
}

export interface Guardian {
  id: string;
  student_id: string;
  first_name: string;
  last_name: string;
  relationship: string;
  phone: string;
  email?: string;
  is_primary: boolean;
}

// ============== ACADEMICS ==============

export interface Grade {
  id: string;
  school_id: string;
  name: string;
  order: number;
}

export interface Class {
  id: string;
  school_id: string;
  grade_id: string;
  name: string;
  teacher_id?: string;
}

export interface Subject {
  id: string;
  school_id: string;
  name: string;
  code?: string;
}

// ============== FEES ==============

export interface FeeStructure {
  id: string;
  school_id: string;
  name: string;
  amount: number;
  grade_id?: string;
  term?: string;
  year: number;
}

export interface Invoice {
  id: string;
  school_id: string;
  student_id: string;
  invoice_number: string;
  amount: number;
  amount_paid: number;
  due_date: string;
  description?: string;
  status: PaymentStatus;
  created_at?: string;
}

export interface Payment {
  id: string;
  invoice_id: string;
  receipt_number: string;
  amount: number;
  payment_method: string;
  reference?: string;
  created_at?: string;
}

// ============== ATTENDANCE ==============

export interface AttendanceRecord {
  id: string;
  school_id: string;
  student_id: string;
  date: string;
  status: AttendanceStatus;
  notes?: string;
  recorded_by: string;
  created_at?: string;
}

export interface AttendanceSummary {
  period: { year: number; month: number };
  total_records: number;
  present: number;
  absent: number;
  late: number;
  excused: number;
  attendance_rate: number;
}

// ============== DASHBOARD ==============

export interface DashboardStats {
  total_students: number;
  total_teachers: number;
  attendance_rate: number;
  fees_collected: number;
  fees_outstanding: number;
  recent_enrollments: number;
}

// ============== API ==============

export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}
