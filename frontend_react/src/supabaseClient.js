import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = 'https://kwozfcivubtkjzcezlum.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3b3pmY2l2dWJ0a2p6Y2V6bHVtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODMyNTUyNTEsImV4cCI6MjA5ODgzMTI1MX0.aJLkloiOilSJYhw8vm4a6gapGQWcswHpjzLw8O5ObCw';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
