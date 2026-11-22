-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : stories (comme les statuts WhatsApp)
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- ============================================================
CREATE TABLE IF NOT EXISTS stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label TEXT,                          -- petit nom sous le rond (ex : Arrivage)
    tag TEXT,                            -- étiquette : NOUVEL ARRIVAGE, PROMO, OCCASION…
    title TEXT,                          -- texte principal
    media_url TEXT NOT NULL,             -- photo ou vidéo
    media_type TEXT NOT NULL DEFAULT 'image' CHECK (media_type IN ('image', 'video')),
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    expires_at TIMESTAMPTZ,              -- vide = sans limite
    views INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_stories_active ON stories (created_at DESC) WHERE is_active = true;
ALTER TABLE stories ENABLE ROW LEVEL SECURITY;
GRANT ALL ON stories TO service_role;

-- +1 vue (sans risque de perdre des vues si plusieurs clients regardent en même temps)
CREATE OR REPLACE FUNCTION story_add_view(p_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE stories SET views = views + 1 WHERE id = p_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
REVOKE ALL ON FUNCTION story_add_view(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION story_add_view(UUID) TO service_role;
-- ✅ Terminé.
