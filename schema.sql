CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

INSERT INTO groups (name)
VALUES ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100),
    birthday DATE,
    group_id INTEGER REFERENCES groups(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phones (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('home', 'work', 'mobile'))
);

-- Copy old Practice 7/8 data if the old phonebook table exists.
DO $$
BEGIN
    IF to_regclass('public.phonebook') IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'phonebook'
              AND column_name = 'first_name'
        ) THEN
            EXECUTE $m$
                INSERT INTO contacts (name)
                SELECT DISTINCT first_name FROM phonebook
                WHERE first_name IS NOT NULL AND first_name <> ''
                ON CONFLICT (name) DO NOTHING
            $m$;
            EXECUTE $m$
                INSERT INTO phones (contact_id, phone, type)
                SELECT c.id, p.phone, 'mobile'
                FROM phonebook p JOIN contacts c ON c.name = p.first_name
                WHERE p.phone IS NOT NULL AND p.phone <> ''
                  AND NOT EXISTS (
                      SELECT 1 FROM phones ph
                      WHERE ph.contact_id = c.id AND ph.phone = p.phone
                  )
            $m$;
        ELSIF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'phonebook'
              AND column_name = 'name'
        ) THEN
            EXECUTE $m$
                INSERT INTO contacts (name)
                SELECT DISTINCT name FROM phonebook
                WHERE name IS NOT NULL AND name <> ''
                ON CONFLICT (name) DO NOTHING
            $m$;
            EXECUTE $m$
                INSERT INTO phones (contact_id, phone, type)
                SELECT c.id, p.phone, 'mobile'
                FROM phonebook p JOIN contacts c ON c.name = p.name
                WHERE p.phone IS NOT NULL AND p.phone <> ''
                  AND NOT EXISTS (
                      SELECT 1 FROM phones ph
                      WHERE ph.contact_id = c.id AND ph.phone = p.phone
                  )
            $m$;
        END IF;
    END IF;
END;
$$;

UPDATE contacts
SET group_id = (SELECT id FROM groups WHERE name = 'Other')
WHERE group_id IS NULL;
