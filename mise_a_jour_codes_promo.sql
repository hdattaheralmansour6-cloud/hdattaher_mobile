-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : codes promo
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- ============================================================
CREATE TABLE IF NOT EXISTS coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL DEFAULT 'percent' CHECK (kind IN ('percent', 'amount')),
    value NUMERIC(12,2) NOT NULL CHECK (value > 0),
    min_total NUMERIC(12,2) DEFAULT 0,
    max_uses INTEGER CHECK (max_uses IS NULL OR max_uses > 0),
    uses INTEGER NOT NULL DEFAULT 0,
    ends_at DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS coupon_code TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2) DEFAULT 0;
ALTER TABLE coupons ENABLE ROW LEVEL SECURITY;
GRANT ALL ON coupons TO service_role;
-- ✅ Terminé.
