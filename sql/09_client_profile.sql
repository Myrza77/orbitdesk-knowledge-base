-- 09_client_profile.sql
-- Aggregates per-client behavioral profile from canonical inquiries --
-- total volume, top categories touched, most recent contact. Same shape
-- as the real project's client_profile_v: computed from the canonical
-- layer, not hand-maintained.

SET search_path TO orbitdesk;

TRUNCATE client_profile;

INSERT INTO client_profile (client_name, total_inquiries, top_categories, last_contact)
SELECT
    i.client_name,
    COUNT(*) AS total_inquiries,
    ARRAY(
        SELECT cat.category_name
        FROM classifications c2
        JOIN categories cat ON cat.category_id = c2.category_id
        JOIN inquiries i2 ON i2.inquiry_id = c2.inquiry_id
        WHERE i2.client_name = i.client_name
        GROUP BY cat.category_name
        ORDER BY COUNT(*) DESC
        LIMIT 3
    ) AS top_categories,
    MAX(i.opened_at) AS last_contact
FROM inquiries i
GROUP BY i.client_name;

SELECT COUNT(*) AS client_profiles FROM client_profile;
SELECT client_name, total_inquiries, top_categories FROM client_profile ORDER BY total_inquiries DESC LIMIT 5;
