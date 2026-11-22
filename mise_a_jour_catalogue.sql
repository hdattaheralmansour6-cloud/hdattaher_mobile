-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : catalogue PDF
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- Ajoute la case « Mettre dans le catalogue PDF » sur chaque produit (cochée par défaut).
-- ============================================================
ALTER TABLE products ADD COLUMN IF NOT EXISTS in_catalog BOOLEAN NOT NULL DEFAULT true;
-- ✅ Terminé.
