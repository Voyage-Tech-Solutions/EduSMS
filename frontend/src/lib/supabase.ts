import { createBrowserClient } from '@supabase/ssr';

// Supabase client for browser usage (frontend)
export const createClient = () => {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
        throw new Error('Missing Supabase environment variables');
    }

    return createBrowserClient(supabaseUrl, supabaseAnonKey);
};

// Helper to get current session
export const getSession = async () => {
    const supabase = createClient();
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw error;
    return session;
};

// Helper to get current user profile
export const getUserProfile = async () => {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) return null;

    const { data: profile, error } = await supabase
        .from('user_profiles')
        .select('*, schools(*)')
        .eq('id', user.id)
        .single();

    if (error) throw error;
    return profile;
};

// Auth helper functions
export const auth = {
    // Sign up with email and password
    signUp: async (email: string, password: string, profileData: {
        firstName: string;
        lastName: string;
        phone?: string;
        role: 'parent' | 'student';
        schoolId: string;
    }) => {
        const supabase = createClient();

        // 1. Create auth user
        const { data: authData, error: authError } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    first_name: profileData.firstName,
                    last_name: profileData.lastName,
                }
            }
        });

        if (authError) throw authError;
        if (!authData.user) throw new Error('User creation failed');

        // 2. Create user profile
        const { error: profileError } = await supabase.from('user_profiles').insert({
            id: authData.user.id,
            email,
            first_name: profileData.firstName,
            last_name: profileData.lastName,
            phone: profileData.phone,
            role: profileData.role,
            school_id: profileData.schoolId,
            is_approved: false, // Requires admin approval
        });

        if (profileError) throw profileError;

        return authData;
    },

    // Sign in with email and password
    signIn: async (email: string, password: string) => {
        const supabase = createClient();
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        if (error) throw error;
        return data;
    },

    // Sign out
    signOut: async () => {
        const supabase = createClient();
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
    },

    // Reset password
    resetPassword: async (email: string) => {
        const supabase = createClient();
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/reset-password`,
        });
        if (error) throw error;
    },

    // Accept invitation (for teachers/staff)
    acceptInvitation: async (token: string, password: string, profileData: {
        firstName: string;
        lastName: string;
        phone?: string;
    }) => {
        const supabase = createClient();

        // 1. Verify invitation token
        const { data: invitation, error: inviteError } = await supabase
            .from('invitations')
            .select('*')
            .eq('token', token)
            .is('accepted_at', null)
            .gt('expires_at', new Date().toISOString())
            .single();

        if (inviteError || !invitation) {
            throw new Error('Invalid or expired invitation');
        }

        // 2. Create auth user
        const { data: authData, error: authError } = await supabase.auth.signUp({
            email: invitation.email,
            password,
        });

        if (authError) throw authError;
        if (!authData.user) throw new Error('User creation failed');

        // 3. Create user profile
        const { error: profileError } = await supabase.from('user_profiles').insert({
            id: authData.user.id,
            email: invitation.email,
            first_name: profileData.firstName,
            last_name: profileData.lastName,
            phone: profileData.phone,
            role: invitation.role,
            school_id: invitation.school_id,
            is_approved: true, // Auto-approved for invited staff
        });

        if (profileError) throw profileError;

        // 4. Mark invitation as accepted
        await supabase
            .from('invitations')
            .update({ accepted_at: new Date().toISOString() })
            .eq('id', invitation.id);

        return authData;
    },
};

// School helper functions
export const schools = {
    // Get all active schools for registration dropdown
    getAll: async () => {
        const supabase = createClient();
        const { data, error } = await supabase
            .from('schools')
            .select('id, name, code')
            .eq('is_active', true)
            .order('name');

        if (error) throw error;
        return data;
    },

    // Get school by code
    getByCode: async (code: string) => {
        const supabase = createClient();
        const { data, error } = await supabase
            .from('schools')
            .select('id, name, code')
            .eq('code', code.toUpperCase())
            .eq('is_active', true)
            .single();

        if (error) throw error;
        return data;
    },
};
