-- Practice 8 upsert procedure adapted to the new schema.
CREATE OR REPLACE PROCEDURE upsert_contact(p_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    INSERT INTO contacts (name) VALUES (p_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id INTO v_contact_id FROM contacts WHERE name = p_name;

    IF EXISTS (SELECT 1 FROM phones WHERE contact_id = v_contact_id) THEN
        UPDATE phones SET phone = p_phone, type = 'mobile'
        WHERE id = (
            SELECT id FROM phones WHERE contact_id = v_contact_id
            ORDER BY id LIMIT 1
        );
    ELSE
        INSERT INTO phones (contact_id, phone, type)
        VALUES (v_contact_id, p_phone, 'mobile');
    END IF;
END;
$$;

-- Practice 8 bulk insert with validation.
CREATE OR REPLACE PROCEDURE insert_many_contacts(
    p_names TEXT[],
    p_phones TEXT[],
    INOUT bad_data TEXT[] DEFAULT ARRAY[]::TEXT[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1 .. COALESCE(array_length(p_names, 1), 0) LOOP
        IF p_phones[i] ~ '^\+?[0-9]{10,15}$' THEN
            CALL upsert_contact(p_names[i], p_phones[i]);
        ELSE
            bad_data := array_append(
                bad_data, p_names[i] || ':' || COALESCE(p_phones[i], 'NULL')
            );
        END IF;
    END LOOP;
END;
$$;

-- Practice 8 delete procedure, now searches in the phones table too.
CREATE OR REPLACE PROCEDURE delete_contact(p_value VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts c
    WHERE c.name = p_value
       OR EXISTS (
            SELECT 1 FROM phones ph
            WHERE ph.contact_id = c.id AND ph.phone = p_value
       );
END;
$$;

-- TSIS 1 procedure: add a phone to an existing contact.
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR, p_phone VARCHAR, p_type VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Phone type must be home, work, or mobile';
    END IF;

    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" does not exist', p_contact_name;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);
END;
$$;

-- TSIS 1 procedure: create a group if needed and move the contact to it.
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR, p_group_name VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id INTEGER;
BEGIN
    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" does not exist', p_contact_name;
    END IF;

    INSERT INTO groups (name) VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;
END;
$$;
