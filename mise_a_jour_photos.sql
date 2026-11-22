-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : plusieurs photos par produit
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- ============================================================
ALTER TABLE products ADD COLUMN IF NOT EXISTS extra_images JSONB NOT NULL DEFAULT '[]'::jsonb;
-- ✅ Terminé.
