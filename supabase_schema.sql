-- ============================================================
-- HDATTAHER MOBILE - Schéma PostgreSQL complet pour Supabase
-- ============================================================
-- INSTRUCTIONS :
-- 1. Ouvrez le SQL Editor dans votre dashboard Supabase
-- 2. Cliquez sur "New query"
-- 3. Collez TOUT ce fichier
-- 4. Cliquez sur "Run"
-- ============================================================

-- Extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLE : admins
-- ============================================================
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);

-- ============================================================
-- TABLE : categories
-- ============================================================
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    name_en TEXT,
    name_ar TEXT,
    icon TEXT DEFAULT 'fas fa-mobile-alt',
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_categories_sort ON categories(sort_order);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);

-- ============================================================
-- TABLE : products
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    name_en TEXT,
    name_ar TEXT,
    description TEXT,
    description_en TEXT,
    description_ar TEXT,
    price NUMERIC(12,2) NOT NULL CHECK (price >= 0),
    old_price NUMERIC(12,2) DEFAULT 0 CHECK (old_price >= 0),
    discount INTEGER DEFAULT 0 CHECK (discount >= 0 AND discount <= 100),
    stock INTEGER DEFAULT 0 CHECK (stock >= 0),
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    image TEXT DEFAULT 'default.png',
    brand TEXT,
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_featured ON products(is_featured);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_created ON products(created_at DESC);

-- ============================================================
-- TABLE : product_views
-- ============================================================
CREATE TABLE IF NOT EXISTS product_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    viewed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_views_product ON product_views(product_id);
CREATE INDEX IF NOT EXISTS idx_views_date ON product_views(viewed_at DESC);

-- ============================================================
-- TABLE : settings
-- ============================================================
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);

-- ============================================================
-- TABLE : admin_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action TEXT NOT NULL,
    details TEXT,
    admin_id UUID REFERENCES admins(id) ON DELETE SET NULL,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_logs_admin ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_logs_date ON admin_logs(created_at DESC);

-- ============================================================
-- TRIGGERS : updated_at automatique
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_admins_updated ON admins;
CREATE TRIGGER tr_admins_updated
    BEFORE UPDATE ON admins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS tr_products_updated ON products;
CREATE TRIGGER tr_products_updated
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- TRIGGER : Compteur de vues automatique
-- ============================================================
CREATE OR REPLACE FUNCTION increment_product_views()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products SET views = views + 1 WHERE id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_increment_views ON product_views;
CREATE TRIGGER tr_increment_views
    AFTER INSERT ON product_views
    FOR EACH ROW EXECUTE FUNCTION increment_product_views();

-- ============================================================
-- FONCTION RPC : Vérification login admin (bcrypt côté serveur)
-- ============================================================
CREATE OR REPLACE FUNCTION verify_admin_login(p_username TEXT, p_password TEXT)
RETURNS TABLE (
    id UUID,
    username TEXT,
    email TEXT,
    is_active BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT a.id, a.username, a.email, a.is_active
    FROM admins a
    WHERE a.username = p_username
      AND a.password_hash = crypt(p_password, a.password_hash)
      AND a.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FONCTION RPC : Changer le mot de passe admin
-- ============================================================
CREATE OR REPLACE FUNCTION change_admin_password(
    p_admin_id UUID,
    p_old_password TEXT,
    p_new_password TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_valid BOOLEAN;
BEGIN
    -- Vérifier l'ancien mot de passe
    SELECT EXISTS(
        SELECT 1 FROM admins
        WHERE id = p_admin_id
          AND password_hash = crypt(p_old_password, password_hash)
    ) INTO v_valid;

    IF NOT v_valid THEN
        RETURN false;
    END IF;

    -- Mettre à jour avec le nouveau hash
    UPDATE admins
    SET password_hash = crypt(p_new_password, gen_salt('bf', 10))
    WHERE id = p_admin_id;

    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FONCTION : Prix après promotion
-- ============================================================
CREATE OR REPLACE FUNCTION get_discounted_price(p_price NUMERIC, p_discount INTEGER)
RETURNS NUMERIC AS $$
BEGIN
    IF p_discount > 0 AND p_discount <= 100 THEN
        RETURN ROUND(p_price * (1 - p_discount::NUMERIC / 100), 2);
    END IF;
    RETURN p_price;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TABLE : customers (comptes clients)
-- ============================================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    address TEXT,
    password_hash TEXT NOT NULL,
    is_blocked BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
-- Bases déjà existantes : ajoute la colonne si elle manque
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- ============================================================
-- TABLE : orders (commandes)
-- Statuts : En attente, Confirmée, Préparation, Expédiée, Livrée, Annulée
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number TEXT UNIQUE NOT NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'En attente',
    total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    shipping_name TEXT,
    shipping_phone TEXT,
    shipping_address TEXT,
    notes TEXT,
    payment_method TEXT,
    payment_proof TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
-- Bases déjà existantes
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_proof TEXT;

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);

-- ============================================================
-- TABLE : order_items (lignes de commande)
-- ============================================================
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- ============================================================
-- TABLE : password_resets (codes à 6 chiffres, valables 30 min)
-- "used"      : code consommé par le client
-- "dismissed" : demande masquée dans l'admin (n'invalide pas le code)
-- La colonne "token" est un reste de l'ancien système par lien : nullable.
-- ============================================================
CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT false,
    dismissed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);
-- Bases déjà existantes
ALTER TABLE password_resets ADD COLUMN IF NOT EXISTS dismissed BOOLEAN DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_resets_customer ON password_resets(customer_id);
CREATE INDEX IF NOT EXISTS idx_resets_created ON password_resets(created_at DESC);

-- ============================================================
-- TABLE : banners (carrousel de la page d'accueil)
-- title_en/ar et subtitle_en/ar sont générés automatiquement à l'enregistrement
-- ============================================================
CREATE TABLE IF NOT EXISTS banners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT,
    subtitle TEXT,
    title_en TEXT,
    title_ar TEXT,
    subtitle_en TEXT,
    subtitle_ar TEXT,
    link_url TEXT,
    image TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
-- Bases déjà existantes
ALTER TABLE banners ADD COLUMN IF NOT EXISTS title_en TEXT;
ALTER TABLE banners ADD COLUMN IF NOT EXISTS title_ar TEXT;
ALTER TABLE banners ADD COLUMN IF NOT EXISTS subtitle_en TEXT;
ALTER TABLE banners ADD COLUMN IF NOT EXISTS subtitle_ar TEXT;

CREATE INDEX IF NOT EXISTS idx_banners_sort ON banners(sort_order);
CREATE INDEX IF NOT EXISTS idx_banners_active ON banners(is_active);

-- updated_at automatique pour les nouvelles tables
DROP TRIGGER IF EXISTS tr_customers_updated ON customers;
CREATE TRIGGER tr_customers_updated
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS tr_orders_updated ON orders;
CREATE TRIGGER tr_orders_updated
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- RLS activé sans policy publique : seules les clés serveur (service_role) y accèdent
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_resets ENABLE ROW LEVEL SECURITY;
ALTER TABLE banners ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_logs ENABLE ROW LEVEL SECURITY;

-- Lecture publique
CREATE POLICY "public_read_products" ON products
    FOR SELECT TO anon USING (is_active = true);

CREATE POLICY "public_read_categories" ON categories
    FOR SELECT TO anon USING (is_active = true);

CREATE POLICY "public_read_settings" ON settings
    FOR SELECT TO anon USING (true);

CREATE POLICY "public_insert_views" ON product_views
    FOR INSERT TO anon WITH CHECK (true);

-- Accès authentifié (pour usage futur avec Supabase Auth)
CREATE POLICY "auth_all_products" ON products
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "auth_all_categories" ON categories
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "auth_all_settings" ON settings
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "auth_read_views" ON product_views
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "auth_all_logs" ON admin_logs
    FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "auth_read_admins" ON admins
    FOR SELECT TO authenticated USING (true);

-- ============================================================
-- DONNÉES INITIALES
-- ============================================================

-- Admin par défaut (mot de passe : admin2026)
INSERT INTO admins (username, password_hash, email) VALUES (
    'admin',
    crypt('admin2026', gen_salt('bf', 10)),
    'admin@hdattaher.com'
) ON CONFLICT (username) DO NOTHING;

-- Catégories
INSERT INTO categories (name, name_en, name_ar, icon, description, sort_order) VALUES
    ('Smartphones', 'Smartphones', 'الهواتف الذكية', 'fas fa-mobile-alt', 'Les derniers smartphones', 1),
    ('Accessoires', 'Accessories', 'الإكسسوارات', 'fas fa-headphones', 'Tous les accessoires', 2),
    ('Promotions', 'Promotions', 'العروض', 'fas fa-tags', 'Offres spéciales', 3)
ON CONFLICT (name) DO NOTHING;

-- Paramètres du site
INSERT INTO settings (key, value) VALUES
    ('site_name', 'HDATTAHER MOBILE'),
    ('owner_name', 'Hdattaher'),
    ('whatsapp', '+22791720755'),
    ('location', 'Niger'),
    ('primary_color', '#6C63FF'),
    ('secondary_color', '#FF6584'),
    ('accent_color', '#00D9FF'),
    ('about_title', 'À Propos de HDATTAHER MOBILE'),
    ('about_title_en', 'About HDATTAHER MOBILE'),
    ('about_title_ar', 'حول HDATTAHER MOBILE'),
    ('about_text', 'HDATTAHER MOBILE est votre destination de confiance pour les smartphones et accessoires au Niger. Nous offrons les meilleurs produits aux prix les plus compétitifs, avec un service client exceptionnel.'),
    ('about_text_en', 'HDATTAHER MOBILE is your trusted destination for smartphones and accessories in Niger. We offer the best products at the most competitive prices, with exceptional customer service.'),
    ('about_text_ar', 'HDATTAHER MOBILE هو وجهتك الموثوقة للهواتف الذكية والإكسسوارات في النيجر. نقدم أفضل المنتجات بأسعار تنافسية مع خدمة عملاء استثنائية.'),
    ('facebook', 'https://facebook.com/hdattahermobile'),
    ('instagram', 'https://instagram.com/hdattahermobile'),
    ('tiktok', 'https://tiktok.com/@hdattahermobile'),
    ('theme_mode', 'light'),
    ('dark_mode', '0'),
    ('logo_path', ''),
    ('promotions_active', '1')
ON CONFLICT (key) DO NOTHING;

-- Produits de démonstration
INSERT INTO products (name, name_en, name_ar, description, description_en, description_ar,
                      price, old_price, discount, stock, category_id, image, brand, is_featured) VALUES
    ('iPhone 15 Pro Max', 'iPhone 15 Pro Max', 'آيفون 15 برو ماكس',
     'Le dernier iPhone avec puce A17 Pro, écran Super Retina XDR et appareil photo 48MP.',
     'The latest iPhone with A17 Pro chip, Super Retina XDR display and 48MP camera.',
     'أحدث آيفون مع شريحة A17 Pro وشاشة Super Retina XDR وكاميرا 48 ميجابكسل.',
     850000, 950000, 10, 15,
     (SELECT id FROM categories WHERE name = 'Smartphones'),
     'iphone15.png', 'Apple', true),

    ('Samsung Galaxy S24 Ultra', 'Samsung Galaxy S24 Ultra', 'سامسونج جالاكسي S24 ألترا',
     'Galaxy S24 Ultra avec Galaxy AI, S Pen intégré et appareil photo 200MP.',
     'Galaxy S24 Ultra with Galaxy AI, built-in S Pen and 200MP camera.',
     'جالاكسي S24 ألترا مع Galaxy AI وقلم S Pen مدمج وكاميرا 200 ميجابكسل.',
     750000, 850000, 12, 10,
     (SELECT id FROM categories WHERE name = 'Smartphones'),
     'samsung_s24.png', 'Samsung', true),

    ('Tecno Camon 30 Pro', 'Tecno Camon 30 Pro', 'تكنو كامون 30 برو',
     'Tecno Camon 30 Pro, le meilleur rapport qualité-prix avec appareil photo 50MP.',
     'Tecno Camon 30 Pro, the best value with 50MP camera.',
     'تكنو كامون 30 برو، أفضل قيمة مع كاميرا 50 ميجابكسل.',
     180000, 220000, 18, 30,
     (SELECT id FROM categories WHERE name = 'Smartphones'),
     'tecno_camon30.png', 'Tecno', true),

    ('AirPods Pro 2', 'AirPods Pro 2', 'إيربودز برو 2',
     'AirPods Pro 2ème génération avec réduction de bruit active et audio spatial.',
     'AirPods Pro 2nd generation with active noise cancellation and spatial audio.',
     'إيربودز برو الجيل الثاني مع إلغاء الضوضاء النشط والصوت المكاني.',
     120000, 150000, 20, 25,
     (SELECT id FROM categories WHERE name = 'Accessoires'),
     'airpods.png', 'Apple', true),

    ('Chargeur Rapide 65W', 'Fast Charger 65W', 'شاحن سريع 65 واط',
     'Chargeur rapide universel 65W compatible avec tous les smartphones.',
     'Universal 65W fast charger compatible with all smartphones.',
     'شاحن سريع عالمي 65 واط متوافق مع جميع الهواتف.',
     25000, 35000, 28, 50,
     (SELECT id FROM categories WHERE name = 'Accessoires'),
     'charger65.png', 'Universel', false)
ON CONFLICT DO NOTHING;

-- ============================================================
-- ✅ TERMINÉ ! Votre base de données est prête.
-- ============================================================
