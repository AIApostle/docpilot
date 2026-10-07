-- Per-doctor MemWal access preference. This stores a setting only, never memory.
CREATE TABLE IF NOT EXISTS public.doctor_memory_preferences (
    doctor_id uuid PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    walrus_memory_enabled boolean NOT NULL DEFAULT true
);

ALTER TABLE public.doctor_memory_preferences ENABLE ROW LEVEL SECURITY;
GRANT USAGE ON SCHEMA public TO service_role;
REVOKE ALL ON public.doctor_memory_preferences FROM anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.doctor_memory_preferences TO service_role;
