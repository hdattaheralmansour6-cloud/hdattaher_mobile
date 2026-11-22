-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : équipe (compte « produits seulement » pour un ami)
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- Votre compte actuel devient automatiquement « propriétaire » (tous les droits).
-- ============================================================

ALTER TABLE admins ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'owner';
ALTER TABLE admins DROP CONSTRAINT IF EXISTS admins_role_check;
ALTER TABLE admins ADD CONSTRAINT admins_role_check CHECK (role IN ('owner', 'products'));

-- Créer un membre de l'équipe (mot de passe chiffré bcrypt, comme le vôtre)
CREATE OR REPLACE FUNCTION create_admin_member(p_username TEXT, p_password TEXT, p_role TEXT)
RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    IF p_role NOT IN ('owner', 'products') THEN
        RAISE EXCEPTION 'role invalide';
    END IF;
    INSERT INTO admins (username, password_hash, role, is_active)
    VALUES (p_username, crypt(p_password, gen_salt('bf', 10)), p_role, true)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Donner un nouveau mot de passe à un membre (s'il l'a oublié)
CREATE OR REPLACE FUNCTION set_admin_password(p_admin_id UUID, p_new_password TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE admins SET password_hash = crypt(p_new_password, gen_salt('bf', 10)) WHERE id = p_admin_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Seul le serveur du site peut utiliser ces 2 fonctions
REVOKE ALL ON FUNCTION create_admin_member(TEXT, TEXT, TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION set_admin_password(UUID, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION create_admin_member(TEXT, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION set_admin_password(UUID, TEXT) TO service_role;
-- ✅ Terminé.
