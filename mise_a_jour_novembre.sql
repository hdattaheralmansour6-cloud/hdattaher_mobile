-- ============================================================
-- HDATTAHER MOBILE - Mise à jour de novembre 2026 (photos + codes promo + alertes stock)
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- ============================================================

-- ----- mise_a_jour_photos.sql -----
ALTER TABLE products ADD COLUMN IF NOT EXISTS extra_images JSONB NOT NULL DEFAULT '[]'::jsonb;

-- ----- mise_a_jour_codes_promo.sql -----
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

-- ----- mise_a_jour_alertes_stock.sql -----
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
