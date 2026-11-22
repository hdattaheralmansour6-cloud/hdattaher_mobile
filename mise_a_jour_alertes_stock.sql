-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : alertes « de retour en stock »
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    phone TEXT NOT NULL,
    name TEXT,
    notified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_waiting ON stock_alerts (product_id) WHERE notified = false;
ALTER TABLE stock_alerts ENABLE ROW LEVEL SECURITY;
GRANT ALL ON stock_alerts TO service_role;
-- ✅ Terminé.
