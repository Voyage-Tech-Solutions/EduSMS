/**
 * EduCore SaaS - API Client
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface RequestOptions extends RequestInit {
    token?: string;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async getAuthHeader(token?: string): Promise<Record<string, string>> {
        if (token) {
            return { Authorization: `Bearer ${token}` };
        }

        // Try to get session from Supabase
        if (typeof window !== 'undefined') {
            try {
                // Dynamically import to avoid server-side issues
                const { getSession } = await import('./supabase');
                const session = await getSession();
                if (session?.access_token) {
                    return { Authorization: `Bearer ${session.access_token}` };
                }
            } catch (e) {
                // Fallback or ignore
            }
        }
        return {};
    }

    async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
        const { token, ...fetchOptions } = options;

        const url = `${this.baseUrl}${endpoint}`;

        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(await this.getAuthHeader(token)),
            ...(options.headers as Record<string, string> || {}),
        };

        const response = await fetch(url, {
            ...fetchOptions,
            headers,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        // Handle 204 No Content
        if (response.status === 204) {
            return {} as T;
        }

        return response.json();
    }

    // Auth endpoints
    // Auth endpoints - DEPRECATED in favor of direct Supabase usage in frontend components
    async login(email: string, password: string) {
        // This endpoint is effectively deprecated for frontend use
        return this.request<{ access_token: string; user: any }>('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    }

    async register(data: {
        email: string;
        password: string;
        first_name: string;
        last_name: string;
        role: string;
        school_id?: string;
    }) {
        // This endpoint is effectively deprecated for frontend use
        return this.request<{ access_token: string; user: any }>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getMe() {
        // This endpoint validates the token on the backend
        return this.request<any>('/auth/me');
    }

    // Students
    async getStudents(params?: { grade_id?: string; class_id?: string; search?: string }) {
        const searchParams = new URLSearchParams();
        if (params?.grade_id) searchParams.set('grade_id', params.grade_id);
        if (params?.class_id) searchParams.set('class_id', params.class_id);
        if (params?.search) searchParams.set('search', params.search);

        const query = searchParams.toString();
        return this.request<any[]>(`/students${query ? `?${query}` : ''}`);
    }

    async getStudent(id: string) {
        return this.request<any>(`/students/${id}`);
    }

    async createStudent(data: any) {
        return this.request<any>('/students', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateStudent(id: string, data: any) {
        return this.request<any>(`/students/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    // Fees
    async getFeeStructures() {
        return this.request<any[]>('/fees/structures');
    }

    async getInvoices(params?: { student_id?: string; status?: string }) {
        const searchParams = new URLSearchParams();
        if (params?.student_id) searchParams.set('student_id', params.student_id);
        if (params?.status) searchParams.set('status', params.status);

        const query = searchParams.toString();
        return this.request<any[]>(`/fees/invoices${query ? `?${query}` : ''}`);
    }

    async createInvoice(data: any) {
        return this.request<any>('/fees/invoices', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async recordPayment(data: any) {
        return this.request<any>('/fees/payments', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // Attendance
    async getAttendance(params?: { class_id?: string; date?: string }) {
        const searchParams = new URLSearchParams();
        if (params?.class_id) searchParams.set('class_id', params.class_id);
        if (params?.date) searchParams.set('date_from', params.date);

        const query = searchParams.toString();
        return this.request<any[]>(`/attendance${query ? `?${query}` : ''}`);
    }

    async recordAttendance(data: any) {
        return this.request<any>('/attendance', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async recordBulkAttendance(data: any) {
        return this.request<any[]>('/attendance/bulk', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getAttendanceSummary(params?: { class_id?: string; month?: number; year?: number }) {
        const searchParams = new URLSearchParams();
        if (params?.class_id) searchParams.set('class_id', params.class_id);
        if (params?.month) searchParams.set('month', params.month.toString());
        if (params?.year) searchParams.set('year', params.year.toString());

        const query = searchParams.toString();
        return this.request<any>(`/attendance/summary${query ? `?${query}` : ''}`);
    }

    // Schools
    async getCurrentSchool() {
        return this.request<any>('/schools/current');
    }

    async getGrades() {
        return this.request<any[]>('/schools/grades');
    }

    async getClasses(gradeId?: string) {
        const query = gradeId ? `?grade_id=${gradeId}` : '';
        return this.request<any[]>(`/schools/classes${query}`);
    }

    async getSubjects() {
        return this.request<any[]>('/schools/subjects');
    }
}

export const api = new ApiClient(API_BASE_URL);
