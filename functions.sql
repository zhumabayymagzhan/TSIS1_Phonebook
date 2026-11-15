CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    email VARCHAR,
    birthday DATE,
    group_name VARCHAR,
    phones TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.name, c.email, c.birthday, g.name,
           COALESCE(STRING_AGG(ph.phone || ' (' || ph.type || ')', ', ' ORDER BY ph.id), '')
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones ph ON ph.contact_id = c.id
    WHERE c.name ILIKE '%' || COALESCE(p_query, '') || '%'
       OR COALESCE(c.email, '') ILIKE '%' || COALESCE(p_query, '') || '%'
       OR EXISTS (
            SELECT 1 FROM phones p
            WHERE p.contact_id = c.id
              AND p.phone ILIKE '%' || COALESCE(p_query, '') || '%'
       )
    GROUP BY c.id, c.name, c.email, c.birthday, g.name
    ORDER BY c.name;
END;
$$;

-- Retain the Practice 8 pagination function name and arguments.
CREATE OR REPLACE FUNCTION get_contacts_page(p_limit INT, p_offset INT)
RETURNS TABLE(id INT, first_name VARCHAR, phone VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id::INT, c.name::VARCHAR,
           COALESCE(
               (SELECT ph.phone FROM phones ph
                WHERE ph.contact_id = c.id ORDER BY ph.id LIMIT 1), ''
           )::VARCHAR
    FROM contacts c
    ORDER BY c.id
    LIMIT p_limit OFFSET p_offset;
END;
$$;

-- Compatibility with the Practice 8 pattern-search function.
CREATE OR REPLACE FUNCTION get_contacts_by_pattern(p TEXT)
RETURNS TABLE(id INT, first_name VARCHAR, phone VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id::INT, c.name::VARCHAR,
           COALESCE(
               (SELECT ph.phone FROM phones ph
                WHERE ph.contact_id = c.id ORDER BY ph.id LIMIT 1), ''
           )::VARCHAR
    FROM contacts c
    WHERE c.name ILIKE '%' || COALESCE(p, '') || '%'
       OR EXISTS (
            SELECT 1 FROM phones ph
            WHERE ph.contact_id = c.id
              AND ph.phone ILIKE '%' || COALESCE(p, '') || '%'
       )
    ORDER BY c.name;
END;
$$;
