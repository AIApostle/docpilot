-- Per-doctor MemWal access preference. This stores a setting only, never memory.
CREATE TABLE IF NOT EXISTS public.doctor_memory_preferences (
    doctor_id text PRIMARY KEY,
    walrus_memory_enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz DEFAULT timezone('utc'::text, now()),
    updated_at timestamptz DEFAULT timezone('utc'::text, now())
);

-- Optional foreign key constraint to public.doctors if the table exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'doctors'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'doctor_memory_preferences' 
        AND constraint_name = 'fk_doctor_memory_preferences_doctor'
    ) THEN
        ALTER TABLE public.doctor_memory_preferences
            ADD CONSTRAINT fk_doctor_memory_preferences_doctor
            FOREIGN KEY (doctor_id) REFERENCES public.doctors(id) ON DELETE CASCADE;
    END IF;
END $$;

ALTER TABLE public.doctor_memory_preferences ENABLE ROW LEVEL SECURITY;
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL ON public.doctor_memory_preferences TO service_role;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'doctor_memory_preferences' 
        AND policyname = 'authenticated_select_own_memory_preference'
    ) THEN
        CREATE POLICY "authenticated_select_own_memory_preference"
            ON public.doctor_memory_preferences
            FOR SELECT
            TO authenticated
            USING (auth.uid()::text = doctor_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'doctor_memory_preferences' 
        AND policyname = 'authenticated_update_own_memory_preference'
    ) THEN
        CREATE POLICY "authenticated_update_own_memory_preference"
            ON public.doctor_memory_preferences
            FOR UPDATE
            TO authenticated
            USING (auth.uid()::text = doctor_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'doctor_memory_preferences' 
        AND policyname = 'authenticated_insert_own_memory_preference'
    ) THEN
        CREATE POLICY "authenticated_insert_own_memory_preference"
            ON public.doctor_memory_preferences
            FOR INSERT
            TO authenticated
            WITH CHECK (auth.uid()::text = doctor_id);
    END IF;
END $$;

GRANT SELECT, INSERT, UPDATE ON public.doctor_memory_preferences TO authenticated;

-- Instruct PostgREST to immediately refresh its schema cache
NOTIFY pgrst, 'reload schema';
