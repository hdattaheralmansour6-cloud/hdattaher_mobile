-- ============================================================
-- HDATTAHER MOBILE - Mise à jour : zones de livraison, variantes, avis clients
-- À lancer UNE SEULE FOIS : Supabase → SQL Editor → New query → coller tout → Run
-- Sans danger : rien n'est effacé, et le fichier peut être relancé.
-- ============================================================

-- ---------- 1. ZONES DE LIVRAISON ----------
CREATE TABLE IF NOT EXISTS delivery_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    name_en TEXT,
    name_ar TEXT,
    fee NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (fee >= 0),
    delay TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_zone TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_fee NUMERIC(12,2) DEFAULT 0;

-- ---------- 2. VARIANTES (stockage / couleur) ----------
CREATE TABLE IF NOT EXISTS product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    storage TEXT,
    color TEXT,
    price NUMERIC(12,2) CHECK (price IS NULL OR price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_variants_product ON product_variants(product_id);
ALTER TABLE products ADD COLUMN IF NOT EXISTS has_variants BOOLEAN DEFAULT false;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL;

-- ---------- 3. AVIS CLIENTS ----------
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    is_approved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_pending ON reviews(is_approved);
ALTER TABLE products ADD COLUMN IF NOT EXISTS rating_avg NUMERIC(3,2) DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS rating_count INTEGER DEFAULT 0;

-- ---------- Sécurité : tables fermées au public, seul le serveur du site y accède ----------
ALTER TABLE delivery_zones   ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews          ENABLE ROW LEVEL SECURITY;
GRANT ALL ON delivery_zones, product_variants, reviews TO service_role;

-- ✅ Terminé.
