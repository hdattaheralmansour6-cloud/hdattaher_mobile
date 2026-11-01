-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : téléphones d'occasion
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- ============================================================

-- État : neuf | comme_neuf | tres_bon | bon | correct  (tous les produits actuels restent « neuf »)
ALTER TABLE products ADD COLUMN IF NOT EXISTS etat TEXT NOT NULL DEFAULT 'neuf';
-- Santé de la batterie en % (pour l'occasion)
ALTER TABLE products ADD COLUMN IF NOT EXISTS battery_health INTEGER CHECK (battery_health IS NULL OR battery_health BETWEEN 1 AND 100);
-- Garantie en mois (0 = sans garantie)
ALTER TABLE products ADD COLUMN IF NOT EXISTS warranty_months INTEGER CHECK (warranty_months IS NULL OR warranty_months BETWEEN 0 AND 36);
-- Remarques (petite rayure, accessoires fournis…) + traductions automatiques
ALTER TABLE products ADD COLUMN IF NOT EXISTS etat_note TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS etat_note_en TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS etat_note_ar TEXT;
CREATE INDEX IF NOT EXISTS idx_products_etat ON products(etat);

-- ✅ Terminé.
