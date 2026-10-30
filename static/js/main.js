/**
 * HDATTAHER MOBILE - JavaScript Principal
 * Gère le thème, la langue, la navigation, les animations
 */

// ============================================================
//  THEME (Mode sombre / clair)
// ============================================================
const ThemeManager = {
  init() {
    // Thème Noir & Or : sombre par défaut (nouvelle clé pour repartir de zéro)
    let saved = 'dark';
    try { saved = localStorage.getItem('theme2') || 'dark'; } catch (e) {}
    this.set(saved);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () => this.toggle());
  },
  set(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('theme2', theme); } catch (e) {}
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  },
  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    this.set(current === 'dark' ? 'light' : 'dark');
  }
};

// ============================================================
//  MULTILINGUE
// ============================================================
const translations = {
  fr: {
    home: 'Accueil', products: 'Produits', about: 'À propos', contact: 'Contact', whatsapp_contact: 'Contactez-nous via WhatsApp',
    search: 'Rechercher...', all_categories: 'Toutes les catégories',
    sort_by: 'Trier par', newest: 'Plus récent', price_asc: 'Prix croissant',
    price_desc: 'Prix décroissant', popular: 'Populaire',
    in_stock: 'En stock', low_stock: 'Stock faible', out_of_stock: 'Rupture',
    in_stock_count: 'en stock', buy: 'Acheter', add_to_cart: 'Ajouter au panier', back: 'Retour',
    buy_whatsapp: 'Commander via WhatsApp', view_details: 'Voir détails',
    hero_title: 'La technologie', hero_title2: 'que vous méritez.',
    hero_desc: 'Découvrez des smartphones et accessoires sélectionnés pour vous, avec qualité, prix compétitifs et service fiable au Niger.',
    shop_now: 'Découvrir les produits', order_whatsapp: 'Commander sur WhatsApp', our_products: 'Nos Produits',
    trust_payment: 'Paiement sécurisé', trust_delivery: 'Livraison rapide',
    trust_verified: 'Produits vérifiés', trust_support: 'Support WhatsApp',
    favorites: 'Mes Favoris', favorites_title: 'Mes Favoris', favorites_empty: 'Aucun favori pour le moment.',
    all_brands: 'Toutes les marques', reset_filters: 'Réinitialiser',
    footer_desc: 'Votre destination de confiance pour les smartphones et accessoires au Niger.',
    featured: 'Produits Vedettes', new_arrivals: 'Nouveautés',
    featured_products: 'Produits en Vedette',
    categories_desc: 'Trouvez exactement ce que vous cherchez',
    featured_desc: 'Nos meilleurs produits sélectionnés pour vous',
    special_offers: 'Offres Spéciales', view_all: 'Voir tout',
    views: 'vues', fcfa: 'FCFA',
    about_us: 'À Propos de Nous', our_categories: 'Nos Catégories',
    quick_links: 'Liens Rapides', contact_us: 'Contactez-nous',
    follow_us: 'Suivez-nous', all_rights: 'Tous droits réservés',
    products_count: 'Produits', brands_count: 'Marques', clients_count: 'Clients satisfaits',
    min_price: 'Prix min', max_price: 'Prix max', filter: 'Filtrer',
    related_products: 'Produits Similaires', category: 'Catégorie',
    stock: 'Stock', brand: 'Marque',
    login_title: 'Connexion', login_subtitle: 'Content de vous revoir !',
    email_label: 'Email', password_label: 'Mot de passe', login_btn: 'Se connecter',
    forgot_password_link: 'Mot de passe oublié ?', no_account: 'Pas encore de compte ?',
    signup_link: "S'inscrire", register_title: 'Créer un compte',
    register_subtitle: 'Suivez vos commandes et gagnez du temps à chaque achat.',
    fullname_label: 'Nom complet', phone_label: 'Téléphone',
    confirm_password_label: 'Confirmer le mot de passe', register_btn: 'Créer mon compte',
    already_account: 'Déjà un compte ?', login_link: 'Se connecter',
    forgot_title: 'Mot de passe oublié',
    forgot_subtitle: 'Entrez votre email, nous générerons un lien de réinitialisation.',
    send_link_btn: 'Envoyer le lien', back_to_login: 'Retour à la connexion',
    reset_title: 'Nouveau mot de passe',
    reset_subtitle: 'Choisissez un nouveau mot de passe pour votre compte.',
    new_password_label: 'Nouveau mot de passe', reset_btn: 'Réinitialiser',
    member_since: 'Membre depuis', avatar_add: 'Ajouter une photo', avatar_change: 'Changer la photo', avatar_remove: 'Supprimer', stat_orders: 'Commandes', stat_in_progress: 'En cours', stat_delivered: 'Livrées', order_items_title: 'Articles', receipt_sent: 'Reçu de transfert envoyé', order_cancelled_note: 'Cette commande a été annulée.',
    auth_or: 'ou', create_account_btn: 'Créer un compte', perk_track: 'Suivi de vos commandes', perk_invoice: 'Factures PDF', perk_fast: 'Commande plus rapide', pw_min: '6 caractères minimum', pw_weak: 'Faible', pw_medium: 'Moyen', pw_strong: 'Fort', pw_match: 'Les mots de passe correspondent', pw_nomatch: 'Les mots de passe ne correspondent pas', fp_step1: 'Votre email', fp_step2: 'Code WhatsApp', fp_step3: 'Nouveau mot de passe', trust_secure: 'Compte sécurisé',
    add_cart_short: 'Ajouter',
    added_to_cart: "Ajouté au panier",
    all: "Tout",
    all_brands_short: "Toutes",
    articles: "article(s)",
    ask_whatsapp: "Demandez-nous sur WhatsApp",
    ask_whatsapp_product: "Une question ? Écrivez-nous",
    cancel: "Annuler",
    cart_empty_hint: "Découvrez nos smartphones et accessoires.",
    checkout_short: "Commander",
    clear: "Effacer",
    continue_shopping: "Continuer mes achats",
    deals: "Offres du moment",
    delivery: "Livraison",
    delivery_confirmed: "Confirmée par WhatsApp",
    description: "Description",
    favorites_hint: "Touchez le cœur d'un produit pour le retrouver ici.",
    featured_short: "Nos coups de cœur",
    filters: "Filtres",
    h_title1: "Le smartphone de vos rêves,",
    h_title2: "livré au Niger.",
    hello: "Bonjour",
    link_copied: "Lien copié",
    max: "Max",
    min: "Min",
    need_help: "Besoin d'aide pour choisir ?",
    no_results: "Aucun produit trouvé.",
    no_results_hint: "Essayez un autre mot ou retirez des filtres.",
    notify_short: "Me prévenir",
    notify_whatsapp: "Être prévenu du retour en stock",
    only_left: "Plus que",
    order_number: "Numéro de commande",
    out_of_stock_long: "Rupture de stock",
    pay_with: "Paiement par",
    perk_delivery: "Livraison au Niger",
    perk_delivery_d: "Rapide et suivie",
    perk_original: "Produits authentiques",
    perk_original_d: "Vérifiés avant envoi",
    perk_payment: "Amanata & Nita",
    perk_payment_t: "Paiement mobile",
    price: "Prix",
    price_fcfa: "Prix (FCFA)",
    price_up: "Prix ↑",
    price_down: "Prix ↓",
    product_many: "produits",
    product_one: "produit",
    promo_only: "Seulement les promos",
    promos: "Promos",
    read_more: "Lire la suite",
    recent_searches: "Recherches récentes",
    recently_viewed: "Vus récemment",
    search_ph: "iPhone, Samsung, écouteurs…",
    see_all: "Tout voir",
    see_all_results: "Voir tous les résultats",
    shop_by_brand: "Par marque",
    shop_title: "La boutique",
    show_results: "Voir les produits",
    subtotal: "Sous-total",
    summary: "Récapitulatif",
    tab_account: "Compte",
    tab_cart: "Panier",
    tab_favs: "Favoris",
    tab_home: "Accueil",
    tab_shop: "Boutique",
    track_btn: "Voir ma commande",
    track_hint: "Avec votre numéro de commande",
    track_intro: "Entrez le numéro de commande et le téléphone utilisés lors de l'achat.",
    track_missing: "Indiquez le numéro de commande et un téléphone valide.",
    track_not_found: "Aucune commande ne correspond. Vérifiez le numéro et le téléphone.",
    track_order: "Suivre ma commande",
    track_question: "Une question sur cette commande ?",
    track_where: "Le numéro figure sur la page de confirmation et dans « Mes commandes ».",
    view_cart: "Voir le panier",
    views_label: "Consultations",
    welcome: "Bienvenue chez HDATTAHER",
    why1_d: "Partout au Niger",
    why1_t: "Livraison rapide",
    why2_d: "Produits vérifiés",
    why2_t: "100 % authentique",
    why3_d: "Amanata & Nita",
    why3_t: "Paiement sûr",
    why4_d: "Réponse rapide",
    why4_t: "Conseil WhatsApp",
    write_us: "Écrivez-nous sur WhatsApp",
    you_save: "Vous économisez",
    my_profile_tab: 'Mon profil', my_orders_tab: 'Mes commandes', logout_tab: 'Déconnexion',
    personal_info: 'Informations personnelles', address_label: 'Adresse', save_btn: 'Enregistrer',
    change_password_title: 'Changer le mot de passe', current_password_label: 'Mot de passe actuel',
    change_password_btn: 'Changer le mot de passe',
    orders_history_title: 'Historique de mes commandes',
    no_orders: "Vous n'avez pas encore de commande.",
    orders_coming_soon: 'Le système de commandes en ligne arrive très bientôt !',
    my_account_nav: 'Mon compte', login_signup_nav: 'Connexion / Inscription',
    cart_title: 'Mon panier', update_btn: 'Mettre à jour', cart_total: 'Total',
    validate_order_btn: 'Valider la commande', cart_empty: 'Votre panier est vide.',
    discover_products: 'Découvrir nos produits',
    checkout_title: 'Valider ma commande', order_summary: 'Récapitulatif',
    shipping_info_title: 'Informations de livraison', shipping_name_label: 'Nom complet',
    shipping_phone_label: 'Téléphone', shipping_address_label: 'Adresse de livraison',
    notes_label: 'Notes (optionnel)', confirm_order_btn: 'Confirmer la commande',
    pay_title: 'Paiement', pay_intro: "Avant de valider, envoyez le montant de votre commande par Amanata ou Nita, puis joignez la capture d'écran du reçu.",
    pay_amount_label: 'Montant à envoyer', pay_method_label: 'Moyen de paiement *', pay_send_to: 'Numéro Amanata / Nita',
    pay_copy: 'Copier', pay_proof_label: "Capture d'écran du reçu *", pay_proof_hint: "Image du reçu d'envoi (png, jpg, webp).",
    order_confirmed_title: 'Commande confirmée !', order_number_label: 'Numéro de commande :',
    contact_soon_prefix: 'Nous vous contacterons bientôt au',
    contact_soon_suffix: 'pour confirmer la livraison.',
    continue_shopping_btn: 'Continuer mes achats',
    order_prefix: 'Commande #', status_label: 'Statut :', delivery_title: 'Livraison',
    download_invoice: 'Télécharger la facture',
    invoice_pending: 'La facture sera disponible après confirmation de votre commande.',
    invoice_cancelled: 'Pas de facture pour une commande annulée.',
    status_pending: 'En attente', status_confirmed: 'Confirmée', status_preparing: 'Préparation',
    status_shipped: 'Expédiée', status_delivered: 'Livrée', status_cancelled: 'Annulée',
    reset_code_instructions: 'Contactez-nous sur WhatsApp avec votre adresse email pour recevoir votre code de réinitialisation.',
    forgot_subtitle_code: 'Entrez votre email, nous générerons un code de réinitialisation à récupérer sur WhatsApp.',
    send_code_btn: 'Obtenir mon code', have_code_link: "J'ai déjà un code", no_code_link: "Je n'ai pas encore de code",
    reset_subtitle_code: 'Entrez le code reçu sur WhatsApp ainsi que votre nouveau mot de passe.',
    reset_code_label: 'Code reçu sur WhatsApp',
    about_page_title: 'À Propos de HDATTAHER MOBILE',
    about_page_text: 'HDATTAHER MOBILE est votre destination de confiance pour les smartphones et accessoires au Niger. Nous offrons les meilleurs produits aux prix les plus compétitifs, avec un service client exceptionnel.',
    feature_authentic: 'Produits authentiques', feature_delivery: 'Livraison rapide',
    feature_warranty: 'Garantie assurée', feature_support: 'Support 24/7',
    feature_prices: 'Meilleurs prix', feature_quality: 'Qualité premium',
    contact_page_title: 'Contactez-nous',
    contact_page_subtitle: "Nous sommes à votre écoute. N'hésitez pas à nous contacter pour toute question.",
    send_message: 'Envoyer un message', our_shop: 'Notre Boutique',
    hours_title: 'Horaires', hours_days: 'Lundi - Samedi', open_now: 'Ouverts maintenant',
    follow_social: 'Suivez-nous sur les réseaux sociaux',
    product_question_title: 'Une question sur un produit ?',
    product_question_desc: 'Notre équipe est disponible pour vous conseiller et vous aider à trouver le smartphone parfait.',
    chat_now: 'Discuter maintenant',
    email_not_found: "Cet email n'a pas de compte. Vérifiez l'adresse ou créez un compte.",
    account_blocked: 'Votre compte a été bloqué. Contactez-nous sur WhatsApp pour obtenir de l\'aide.',
    ask_help_whatsapp: "Demander de l'aide sur WhatsApp",
    open_whatsapp_code: 'Ouvrir WhatsApp pour demander mon code',
  },
  en: {
    home: 'Home', products: 'Products', about: 'About', contact: 'Contact', whatsapp_contact: 'Contact us via WhatsApp',
    search: 'Search...', all_categories: 'All categories',
    sort_by: 'Sort by', newest: 'Newest', price_asc: 'Price ascending',
    price_desc: 'Price descending', popular: 'Popular',
    in_stock: 'In stock', low_stock: 'Low stock', out_of_stock: 'Out of stock',
    in_stock_count: 'in stock', buy: 'Buy', add_to_cart: 'Add to cart', back: 'Back',
    buy_whatsapp: 'Order via WhatsApp', view_details: 'View details',
    hero_title: 'The technology', hero_title2: 'you deserve.',
    hero_desc: 'Discover smartphones and accessories selected for you, with quality, competitive prices and reliable service in Niger.',
    shop_now: 'Discover products', order_whatsapp: 'Order on WhatsApp', our_products: 'Our Products',
    trust_payment: 'Secure payment', trust_delivery: 'Fast delivery',
    trust_verified: 'Verified products', trust_support: 'WhatsApp support',
    favorites: 'My Favorites', favorites_title: 'My Favorites', favorites_empty: 'No favorites yet.',
    all_brands: 'All brands', reset_filters: 'Reset',
    footer_desc: 'Your trusted destination for smartphones and accessories in Niger.',
    featured: 'Featured Products', new_arrivals: 'New Arrivals',
    featured_products: 'Featured Products',
    categories_desc: 'Find exactly what you are looking for',
    featured_desc: 'Our best products selected for you',
    special_offers: 'Special Offers', view_all: 'View all',
    views: 'views', fcfa: 'FCFA',
    about_us: 'About Us', our_categories: 'Our Categories',
    quick_links: 'Quick Links', contact_us: 'Contact Us',
    follow_us: 'Follow Us', all_rights: 'All rights reserved',
    products_count: 'Products', brands_count: 'Brands', clients_count: 'Happy clients',
    min_price: 'Min price', max_price: 'Max price', filter: 'Filter',
    related_products: 'Related Products', category: 'Category',
    stock: 'Stock', brand: 'Brand',
    login_title: 'Login', login_subtitle: 'Welcome back!',
    email_label: 'Email', password_label: 'Password', login_btn: 'Log in',
    forgot_password_link: 'Forgot password?', no_account: "Don't have an account?",
    signup_link: 'Sign up', register_title: 'Create an account',
    register_subtitle: 'Track your orders and save time on every purchase.',
    fullname_label: 'Full name', phone_label: 'Phone',
    confirm_password_label: 'Confirm password', register_btn: 'Create my account',
    already_account: 'Already have an account?', login_link: 'Log in',
    forgot_title: 'Forgot password',
    forgot_subtitle: "Enter your email, we'll generate a reset link.",
    send_link_btn: 'Send link', back_to_login: 'Back to login',
    reset_title: 'New password',
    reset_subtitle: 'Choose a new password for your account.',
    new_password_label: 'New password', reset_btn: 'Reset',
    member_since: 'Member since', avatar_add: 'Add a photo', avatar_change: 'Change photo', avatar_remove: 'Remove', stat_orders: 'Orders', stat_in_progress: 'In progress', stat_delivered: 'Delivered', order_items_title: 'Items', receipt_sent: 'Transfer receipt sent', order_cancelled_note: 'This order has been cancelled.',
    auth_or: 'or', create_account_btn: 'Create an account', perk_track: 'Track your orders', perk_invoice: 'PDF invoices', perk_fast: 'Faster checkout', pw_min: '6 characters minimum', pw_weak: 'Weak', pw_medium: 'Medium', pw_strong: 'Strong', pw_match: 'Passwords match', pw_nomatch: 'Passwords do not match', fp_step1: 'Your email', fp_step2: 'WhatsApp code', fp_step3: 'New password', trust_secure: 'Secure account',
    add_cart_short: 'Add',
    added_to_cart: "Added to cart",
    all: "All",
    all_brands_short: "All",
    articles: "item(s)",
    ask_whatsapp: "Ask us on WhatsApp",
    ask_whatsapp_product: "A question? Message us",
    cancel: "Cancel",
    cart_empty_hint: "Discover our smartphones and accessories.",
    checkout_short: "Checkout",
    clear: "Clear",
    continue_shopping: "Continue shopping",
    deals: "Current deals",
    delivery: "Delivery",
    delivery_confirmed: "Confirmed on WhatsApp",
    description: "Description",
    favorites_hint: "Tap a product's heart to find it here.",
    featured_short: "Our favourites",
    filters: "Filters",
    h_title1: "The smartphone of your dreams,",
    h_title2: "delivered in Niger.",
    hello: "Hello",
    link_copied: "Link copied",
    max: "Max",
    min: "Min",
    need_help: "Need help choosing?",
    no_results: "No products found.",
    no_results_hint: "Try another word or remove filters.",
    notify_short: "Notify me",
    notify_whatsapp: "Get notified when back in stock",
    only_left: "Only",
    order_number: "Order number",
    out_of_stock_long: "Out of stock",
    pay_with: "Pay with",
    perk_delivery: "Delivery in Niger",
    perk_delivery_d: "Fast and tracked",
    perk_original: "Genuine products",
    perk_original_d: "Checked before shipping",
    perk_payment: "Amanata & Nita",
    perk_payment_t: "Mobile payment",
    price: "Price",
    price_fcfa: "Price (FCFA)",
    price_up: "Price ↑",
    price_down: "Price ↓",
    product_many: "products",
    product_one: "product",
    promo_only: "Deals only",
    promos: "Deals",
    read_more: "Read more",
    recent_searches: "Recent searches",
    recently_viewed: "Recently viewed",
    search_ph: "iPhone, Samsung, earbuds…",
    see_all: "See all",
    see_all_results: "See all results",
    shop_by_brand: "By brand",
    shop_title: "The shop",
    show_results: "Show products",
    subtotal: "Subtotal",
    summary: "Summary",
    tab_account: "Account",
    tab_cart: "Cart",
    tab_favs: "Favourites",
    tab_home: "Home",
    tab_shop: "Shop",
    track_btn: "Find my order",
    track_hint: "With your order number",
    track_intro: "Enter the order number and phone used when ordering.",
    track_missing: "Enter the order number and a valid phone.",
    track_not_found: "No matching order. Check the number and phone.",
    track_order: "Track my order",
    track_question: "A question about this order?",
    track_where: "The number is on the confirmation page and in “My orders”.",
    view_cart: "View cart",
    views_label: "Views",
    welcome: "Welcome to HDATTAHER",
    why1_d: "Across Niger",
    why1_t: "Fast delivery",
    why2_d: "Checked products",
    why2_t: "100% genuine",
    why3_d: "Amanata & Nita",
    why3_t: "Safe payment",
    why4_d: "Quick reply",
    why4_t: "WhatsApp advice",
    write_us: "Message us on WhatsApp",
    you_save: "You save",
    my_profile_tab: 'My profile', my_orders_tab: 'My orders', logout_tab: 'Logout',
    personal_info: 'Personal information', address_label: 'Address', save_btn: 'Save',
    change_password_title: 'Change password', current_password_label: 'Current password',
    change_password_btn: 'Change password',
    orders_history_title: 'My order history',
    no_orders: "You don't have any orders yet.",
    orders_coming_soon: 'Online ordering is coming very soon!',
    my_account_nav: 'My account', login_signup_nav: 'Login / Sign up',
    cart_title: 'My cart', update_btn: 'Update', cart_total: 'Total',
    validate_order_btn: 'Place order', cart_empty: 'Your cart is empty.',
    discover_products: 'Discover our products',
    checkout_title: 'Place my order', order_summary: 'Summary',
    shipping_info_title: 'Shipping information', shipping_name_label: 'Full name',
    shipping_phone_label: 'Phone', shipping_address_label: 'Shipping address',
    notes_label: 'Notes (optional)', confirm_order_btn: 'Confirm order',
    pay_title: 'Payment', pay_intro: 'Before confirming, send the order amount via Amanata or Nita, then attach a screenshot of the receipt.',
    pay_amount_label: 'Amount to send', pay_method_label: 'Payment method *', pay_send_to: 'Amanata / Nita number',
    pay_copy: 'Copy', pay_proof_label: 'Receipt screenshot *', pay_proof_hint: 'Image of the transfer receipt (png, jpg, webp).',
    order_confirmed_title: 'Order confirmed!', order_number_label: 'Order number:',
    contact_soon_prefix: "We'll contact you soon at",
    contact_soon_suffix: 'to confirm delivery.',
    continue_shopping_btn: 'Continue shopping',
    order_prefix: 'Order #', status_label: 'Status:', delivery_title: 'Delivery',
    download_invoice: 'Download invoice',
    invoice_pending: 'The invoice will be available once your order is confirmed.',
    invoice_cancelled: 'No invoice for a cancelled order.',
    status_pending: 'Pending', status_confirmed: 'Confirmed', status_preparing: 'Preparing',
    status_shipped: 'Shipped', status_delivered: 'Delivered', status_cancelled: 'Cancelled',
    reset_code_instructions: 'Contact us on WhatsApp with your email address to receive your reset code.',
    forgot_subtitle_code: "Enter your email, we'll generate a reset code for you to get on WhatsApp.",
    send_code_btn: 'Get my code', have_code_link: 'I already have a code', no_code_link: "I don't have a code yet",
    reset_subtitle_code: 'Enter the code received on WhatsApp along with your new password.',
    reset_code_label: 'Code received on WhatsApp',
    about_page_title: 'About HDATTAHER MOBILE',
    about_page_text: 'HDATTAHER MOBILE is your trusted destination for smartphones and accessories in Niger. We offer the best products at the most competitive prices, with exceptional customer service.',
    feature_authentic: 'Authentic products', feature_delivery: 'Fast delivery',
    feature_warranty: 'Guaranteed warranty', feature_support: '24/7 Support',
    feature_prices: 'Best prices', feature_quality: 'Premium quality',
    contact_page_title: 'Contact us',
    contact_page_subtitle: "We are here to listen. Don't hesitate to contact us with any questions.",
    send_message: 'Send a message', our_shop: 'Our Shop',
    hours_title: 'Opening Hours', hours_days: 'Monday - Saturday', open_now: 'Open now',
    follow_social: 'Follow us on social media',
    product_question_title: 'A question about a product?',
    product_question_desc: 'Our team is available to advise you and help you find the perfect smartphone.',
    chat_now: 'Chat now',
    email_not_found: 'This email has no account. Check the address or create an account.',
    account_blocked: 'Your account has been blocked. Contact us on WhatsApp for help.',
    ask_help_whatsapp: 'Ask for help on WhatsApp',
    open_whatsapp_code: 'Open WhatsApp to request my code',
  },
  ar: {
    home: 'الرئيسية', products: 'المنتجات', about: 'حولنا', contact: 'اتصل بنا', whatsapp_contact: 'تواصل معنا عبر واتساب',
    search: '...بحث', all_categories: 'جميع الفئات',
    sort_by: 'ترتيب حسب', newest: 'الأحدث', price_asc: 'السعر تصاعدياً',
    price_desc: 'السعر تنازلياً', popular: 'الأكثر شعبية',
    in_stock: 'متوفر', low_stock: 'مخزون منخفض', out_of_stock: 'نفذ',
    in_stock_count: 'متوفر', buy: 'اشترِ', add_to_cart: 'أضف إلى السلة', back: 'رجوع',
    buy_whatsapp: 'اطلب عبر واتساب', view_details: 'عرض التفاصيل',
    hero_title: 'التكنولوجيا', hero_title2: 'التي تستحقها.',
    hero_desc: 'اكتشف هواتف ذكية وإكسسوارات مختارة لك، بجودة وأسعار تنافسية وخدمة موثوقة في النيجر.',
    shop_now: 'اكتشف المنتجات', order_whatsapp: 'اطلب عبر واتساب', our_products: 'منتجاتنا',
    trust_payment: 'دفع آمن', trust_delivery: 'توصيل سريع',
    trust_verified: 'منتجات موثوقة', trust_support: 'دعم عبر واتساب',
    favorites: 'المفضلة', favorites_title: 'المفضلة', favorites_empty: 'لا توجد عناصر مفضلة بعد.',
    all_brands: 'كل الماركات', reset_filters: 'إعادة تعيين',
    footer_desc: 'وجهتك الموثوقة للهواتف الذكية والإكسسوارات في النيجر.',
    featured: 'منتجات مميزة', new_arrivals: 'وصل حديثاً',
    featured_products: 'منتجات مميزة',
    categories_desc: 'اعثر على ما تبحث عنه تمامًا',
    featured_desc: 'أفضل منتجاتنا المختارة لكم',
    special_offers: 'عروض خاصة', view_all: 'عرض الكل',
    views: 'مشاهدات', fcfa: 'فرنك',
    about_us: 'من نحن', our_categories: 'فئاتنا',
    quick_links: 'روابط سريعة', contact_us: 'اتصل بنا',
    follow_us: 'تابعنا', all_rights: 'جميع الحقوق محفوظة',
    products_count: 'منتجات', brands_count: 'علامات', clients_count: 'عملاء سعداء',
    min_price: 'أقل سعر', max_price: 'أعلى سعر', filter: 'تصفية',
    related_products: 'منتجات مشابهة', category: 'الفئة',
    stock: 'المخزون', brand: 'العلامة',
    login_title: 'تسجيل الدخول', login_subtitle: 'سعداء بعودتك!',
    email_label: 'البريد الإلكتروني', password_label: 'كلمة المرور', login_btn: 'تسجيل الدخول',
    forgot_password_link: 'نسيت كلمة المرور؟', no_account: 'ليس لديك حساب؟',
    signup_link: 'إنشاء حساب', register_title: 'إنشاء حساب',
    register_subtitle: 'تابع طلباتك ووفر الوقت في كل عملية شراء.',
    fullname_label: 'الاسم الكامل', phone_label: 'الهاتف',
    confirm_password_label: 'تأكيد كلمة المرور', register_btn: 'إنشاء حسابي',
    already_account: 'لديك حساب بالفعل؟', login_link: 'تسجيل الدخول',
    forgot_title: 'نسيت كلمة المرور',
    forgot_subtitle: 'أدخل بريدك الإلكتروني، وسننشئ رابط إعادة التعيين.',
    send_link_btn: 'إرسال الرابط', back_to_login: 'العودة لتسجيل الدخول',
    reset_title: 'كلمة مرور جديدة',
    reset_subtitle: 'اختر كلمة مرور جديدة لحسابك.',
    new_password_label: 'كلمة المرور الجديدة', reset_btn: 'إعادة التعيين',
    member_since: 'عضو منذ', avatar_add: 'إضافة صورة', avatar_change: 'تغيير الصورة', avatar_remove: 'حذف', stat_orders: 'الطلبات', stat_in_progress: 'قيد التنفيذ', stat_delivered: 'تم التسليم', order_items_title: 'المنتجات', receipt_sent: 'تم إرسال إيصال التحويل', order_cancelled_note: 'تم إلغاء هذا الطلب.',
    auth_or: 'أو', create_account_btn: 'إنشاء حساب', perk_track: 'تتبع طلباتك', perk_invoice: 'فواتير PDF', perk_fast: 'طلب أسرع', pw_min: '6 أحرف على الأقل', pw_weak: 'ضعيفة', pw_medium: 'متوسطة', pw_strong: 'قوية', pw_match: 'كلمتا المرور متطابقتان', pw_nomatch: 'كلمتا المرور غير متطابقتين', fp_step1: 'بريدك الإلكتروني', fp_step2: 'رمز واتساب', fp_step3: 'كلمة مرور جديدة', trust_secure: 'حساب آمن',
    add_cart_short: 'أضف',
    added_to_cart: "تمت الإضافة إلى السلة",
    all: "الكل",
    all_brands_short: "الكل",
    articles: "منتج(ات)",
    ask_whatsapp: "اسألنا عبر واتساب",
    ask_whatsapp_product: "لديك سؤال؟ راسلنا",
    cancel: "إلغاء",
    cart_empty_hint: "اكتشف هواتفنا وإكسسواراتنا.",
    checkout_short: "اطلب الآن",
    clear: "مسح",
    continue_shopping: "متابعة التسوق",
    deals: "عروض اللحظة",
    delivery: "التوصيل",
    delivery_confirmed: "يتم تأكيده عبر واتساب",
    description: "الوصف",
    favorites_hint: "اضغط على قلب المنتج لتجده هنا.",
    featured_short: "اختياراتنا المميزة",
    filters: "الفلاتر",
    h_title1: "هاتف أحلامك،",
    h_title2: "يصلك في النيجر.",
    hello: "مرحبًا",
    link_copied: "تم نسخ الرابط",
    max: "الأقصى",
    min: "الأدنى",
    need_help: "تحتاج مساعدة في الاختيار؟",
    no_results: "لم يتم العثور على منتجات.",
    no_results_hint: "جرّب كلمة أخرى أو أزل بعض الفلاتر.",
    notify_short: "أعلمني",
    notify_whatsapp: "أعلمني عند توفره",
    only_left: "متبقٍ",
    order_number: "رقم الطلب",
    out_of_stock_long: "نفد من المخزون",
    pay_with: "الدفع عبر",
    perk_delivery: "التوصيل في النيجر",
    perk_delivery_d: "سريع ومتابع",
    perk_original: "منتجات أصلية",
    perk_original_d: "يتم فحصها قبل الإرسال",
    perk_payment: "أمانة و نيتا",
    perk_payment_t: "الدفع عبر الهاتف",
    price: "السعر",
    price_fcfa: "السعر (فرنك)",
    price_up: "السعر ↑",
    price_down: "السعر ↓",
    product_many: "منتجات",
    product_one: "منتج",
    promo_only: "العروض فقط",
    promos: "عروض",
    read_more: "اقرأ المزيد",
    recent_searches: "عمليات البحث الأخيرة",
    recently_viewed: "شوهدت مؤخرًا",
    search_ph: "آيفون، سامسونج، سماعات…",
    see_all: "عرض الكل",
    see_all_results: "عرض كل النتائج",
    shop_by_brand: "حسب العلامة",
    shop_title: "المتجر",
    show_results: "عرض المنتجات",
    subtotal: "المجموع الفرعي",
    summary: "الملخص",
    tab_account: "حسابي",
    tab_cart: "السلة",
    tab_favs: "المفضلة",
    tab_home: "الرئيسية",
    tab_shop: "المتجر",
    track_btn: "عرض طلبي",
    track_hint: "برقم طلبك",
    track_intro: "أدخل رقم الطلب والهاتف المستخدمين عند الشراء.",
    track_missing: "أدخل رقم الطلب ورقم هاتف صحيح.",
    track_not_found: "لا يوجد طلب مطابق. تحقق من الرقم والهاتف.",
    track_order: "تتبع طلبي",
    track_question: "سؤال حول هذا الطلب؟",
    track_where: "الرقم موجود في صفحة التأكيد وفي «طلباتي».",
    view_cart: "عرض السلة",
    views_label: "المشاهدات",
    welcome: "مرحبًا بك في HDATTAHER",
    why1_d: "في كل أنحاء النيجر",
    why1_t: "توصيل سريع",
    why2_d: "منتجات مفحوصة",
    why2_t: "أصلي 100%",
    why3_d: "أمانة و نيتا",
    why3_t: "دفع آمن",
    why4_d: "رد سريع",
    why4_t: "نصيحة عبر واتساب",
    write_us: "راسلنا عبر واتساب",
    you_save: "توفّر",
    my_profile_tab: 'ملفي الشخصي', my_orders_tab: 'طلباتي', logout_tab: 'تسجيل الخروج',
    personal_info: 'المعلومات الشخصية', address_label: 'العنوان', save_btn: 'حفظ',
    change_password_title: 'تغيير كلمة المرور', current_password_label: 'كلمة المرور الحالية',
    change_password_btn: 'تغيير كلمة المرور',
    orders_history_title: 'سجل طلباتي',
    no_orders: 'ليس لديك أي طلبات بعد.',
    orders_coming_soon: 'نظام الطلب عبر الإنترنت قادم قريبًا جدًا!',
    my_account_nav: 'حسابي', login_signup_nav: 'تسجيل الدخول / إنشاء حساب',
    cart_title: 'سلة التسوق', update_btn: 'تحديث', cart_total: 'المجموع',
    validate_order_btn: 'تأكيد الطلب', cart_empty: 'سلتك فارغة.',
    discover_products: 'اكتشف منتجاتنا',
    checkout_title: 'تأكيد طلبي', order_summary: 'الملخص',
    shipping_info_title: 'معلومات التوصيل', shipping_name_label: 'الاسم الكامل',
    shipping_phone_label: 'الهاتف', shipping_address_label: 'عنوان التوصيل',
    notes_label: 'ملاحظات (اختياري)', confirm_order_btn: 'تأكيد الطلب',
    pay_title: 'الدفع', pay_intro: 'قبل التأكيد، أرسل مبلغ الطلب عبر أمانة أو نيتا، ثم أرفق لقطة شاشة للإيصال.',
    pay_amount_label: 'المبلغ المطلوب إرساله', pay_method_label: 'طريقة الدفع *', pay_send_to: 'رقم أمانة / نيتا',
    pay_copy: 'نسخ', pay_proof_label: 'لقطة شاشة للإيصال *', pay_proof_hint: 'صورة إيصال التحويل (png, jpg, webp).',
    order_confirmed_title: 'تم تأكيد الطلب!', order_number_label: 'رقم الطلب:',
    contact_soon_prefix: 'سنتواصل معك قريبًا على الرقم',
    contact_soon_suffix: 'لتأكيد التوصيل.',
    continue_shopping_btn: 'متابعة التسوق',
    order_prefix: 'الطلب #', status_label: 'الحالة:', delivery_title: 'التوصيل',
    download_invoice: 'تحميل الفاتورة',
    invoice_pending: 'ستكون الفاتورة متاحة بعد تأكيد طلبك.',
    invoice_cancelled: 'لا توجد فاتورة للطلبات الملغاة.',
    status_pending: 'قيد الانتظار', status_confirmed: 'مؤكد', status_preparing: 'قيد التحضير',
    status_shipped: 'تم الشحن', status_delivered: 'تم التوصيل', status_cancelled: 'ملغى',
    reset_code_instructions: 'تواصل معنا عبر واتساب مع بريدك الإلكتروني للحصول على رمز إعادة التعيين.',
    forgot_subtitle_code: 'أدخل بريدك الإلكتروني، وسننشئ رمز إعادة تعيين يمكنك الحصول عليه عبر واتساب.',
    send_code_btn: 'الحصول على رمزي', have_code_link: 'لدي رمز بالفعل', no_code_link: 'ليس لدي رمز بعد',
    reset_subtitle_code: 'أدخل الرمز المستلم عبر واتساب مع كلمة المرور الجديدة.',
    reset_code_label: 'الرمز المستلم عبر واتساب',
    about_page_title: 'حول HDATTAHER MOBILE',
    about_page_text: 'HDATTAHER MOBILE هي وجهتك الموثوقة للهواتف الذكية والإكسسوارات في النيجر. نقدم أفضل المنتجات بأسعار تنافسية، مع خدمة عملاء استثنائية.',
    feature_authentic: 'منتجات أصلية', feature_delivery: 'توصيل سريع',
    feature_warranty: 'ضمان مؤكد', feature_support: 'دعم 24/7',
    feature_prices: 'أفضل الأسعار', feature_quality: 'جودة ممتازة',
    contact_page_title: 'اتصل بنا',
    contact_page_subtitle: 'نحن في خدمتك. لا تتردد في التواصل معنا لأي استفسار.',
    send_message: 'إرسال رسالة', our_shop: 'متجرنا',
    hours_title: 'ساعات العمل', hours_days: 'الاثنين - السبت', open_now: 'مفتوح الآن',
    follow_social: 'تابعنا على وسائل التواصل الاجتماعي',
    product_question_title: 'سؤال حول منتج؟',
    product_question_desc: 'فريقنا متاح لتقديم النصح ومساعدتك في العثور على الهاتف الذكي المثالي.',
    chat_now: 'تحدث الآن',
    email_not_found: 'هذا البريد الإلكتروني ليس له حساب. تحقق من العنوان أو أنشئ حساباً.',
    account_blocked: 'تم حظر حسابك. تواصل معنا عبر واتساب للحصول على المساعدة.',
    ask_help_whatsapp: 'اطلب المساعدة عبر واتساب',
    open_whatsapp_code: 'افتح واتساب لطلب الرمز',
  }
};

// Traduit tout élément portant data-name-fr / data-name-en / data-name-ar
// (catégories et produits venant de la base de données) selon la langue active.
function applyDataNameTranslations() {
  const lang = localStorage.getItem('lang') || 'fr';
  document.querySelectorAll('[data-name-fr]').forEach(el => {
    const value = el.getAttribute('data-name-' + lang) || el.getAttribute('data-name-fr');
    if (value) el.textContent = value;
  });
}

const LangManager = {
  init() {
    const saved = localStorage.getItem('lang') || 'fr';
    this.set(saved);
    const sel = document.getElementById('langSelect');
    if (sel) {
      sel.value = saved;
      sel.addEventListener('change', (e) => this.set(e.target.value));
    }
  },
  set(lang) {
    localStorage.setItem('lang', lang);
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
    const t = translations[lang] || translations['fr'];
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (t[key]) el.textContent = t[key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (t[key]) el.placeholder = t[key];
    });
    applyDataNameTranslations();
  }
};

// ============================================================
//  NAVIGATION
// ============================================================
const NavManager = {
  init() {
    const toggle = document.querySelector('.mobile-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', () => links.classList.toggle('active'));
      links.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => links.classList.remove('active'));
      });
    }
    window.addEventListener('scroll', () => {
      const nav = document.querySelector('.navbar');
      if (nav) nav.classList.toggle('scrolled', window.scrollY > 50);
    });
  }
};

// ============================================================
//  ANIMATIONS (Intersection Observer)
// ============================================================
const AnimationManager = {
  init() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
    // Sécurité : rien ne doit rester invisible
    setTimeout(() => document.querySelectorAll('.animate-on-scroll').forEach(el => el.classList.add('animate-in')), 2500);
  }
};

// ============================================================
//  FORMAT PRIX
// ============================================================
function formatPrice(price) {
  return new Intl.NumberFormat('fr-FR').format(price) + ' FCFA';
}

// ============================================================
//  FLASH MESSAGES AUTO-DISMISS
// ============================================================
function initFlashMessages() {
  document.querySelectorAll('.flash-msg').forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transform = 'translateX(100%)';
      setTimeout(() => msg.remove(), 400);
    }, 4000);
  });
}

// ============================================================
//  SEARCH LIVE
// ============================================================
function initSearch() {
  document.querySelectorAll('.live-search-input').forEach(function (input) {
    const wrapper = input.closest('.search-box');
    const results = wrapper ? wrapper.querySelector('.search-results-dropdown') : null;
    if (!results) return;
    let timeout;
    input.addEventListener('input', function () {
      clearTimeout(timeout);
      const q = this.value.trim();
      if (q.length < 2) { results.style.display = 'none'; return; }
      timeout = setTimeout(() => {
        fetch('/api/products?q=' + encodeURIComponent(q))
          .then(r => r.json())
          .then(data => {
            if (!data.length) { results.style.display = 'none'; return; }
            results.innerHTML = data.map(p => `
              <a href="/product/${encodeURIComponent(p.id)}" class="search-result-item">
                <span>${esc(p.name)}</span>
                <span class="search-price">${formatPrice(p.price)}</span>
              </a>`).join('');
            results.style.display = 'block';
          })
          .catch(() => { results.style.display = 'none'; });
      }, 300);
    });
    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !results.contains(e.target)) results.style.display = 'none';
    });
  });
}

// ============================================================
//  COUNTER ANIMATION
// ============================================================
function initCounters() {
  const counters = document.querySelectorAll('.counter');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.getAttribute('data-target'));
        let current = 0;
        const increment = target / 60;
        const timer = setInterval(() => {
          current += increment;
          if (current >= target) { current = target; clearInterval(timer); }
          el.textContent = Math.floor(current).toLocaleString('fr-FR');
        }, 25);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(c => observer.observe(c));
}

// ============================================================
//  CARROUSEL DE BANNIÈRES
// ============================================================
let bannerIndex = 0;
let bannerTimer = null;

function bannerCarouselGoTo(index) {
  const track = document.getElementById('bannerTrack');
  if (!track) return;
  const slides = track.children.length;
  if (slides === 0) return;
  bannerIndex = ((index % slides) + slides) % slides;
  track.style.transform = `translateX(-${bannerIndex * 100}%)`;
  document.querySelectorAll('.banner-dot').forEach((dot, i) => {
    dot.classList.toggle('active', i === bannerIndex);
  });
  resetBannerAutoplay();
}

function bannerCarouselGo(direction) {
  bannerCarouselGoTo(bannerIndex + direction);
}

function resetBannerAutoplay() {
  if (bannerTimer) clearInterval(bannerTimer);
  const track = document.getElementById('bannerTrack');
  if (!track || track.children.length < 2) return;
  bannerTimer = setInterval(() => bannerCarouselGoTo(bannerIndex + 1), 4000);
}

function initBannerCarousel() {
  const track = document.getElementById('bannerTrack');
  if (!track) return;
  resetBannerAutoplay();
}

// ============================================================
//  FAVORIS (localStorage, aucune donnée envoyée au serveur)
// ============================================================
const FAV_KEY = 'hm_favorites';

function getFavorites() {
  try {
    return JSON.parse(localStorage.getItem(FAV_KEY) || '{}');
  } catch (e) {
    return {};
  }
}

function saveFavorites(favs) {
  localStorage.setItem(FAV_KEY, JSON.stringify(favs));
  updateFavCountBadges();
}

function isFavorite(id) {
  return !!getFavorites()[id];
}

function toggleFavorite(event, id, name, price, image) {
  if (event) { event.preventDefault(); event.stopPropagation(); }
  const favs = getFavorites();
  if (favs[id]) {
    delete favs[id];
  } else {
    favs[id] = { id: id, name: name, price: price, image: image };
  }
  saveFavorites(favs);
  document.querySelectorAll('[data-fav-id="' + id + '"]').forEach((btn) => {
    btn.classList.toggle('active', !!favs[id]);
    if (favs[id]) {
      btn.classList.add('pop');
      setTimeout(() => btn.classList.remove('pop'), 450);
    }
  });
}

// Bouton cœur : les infos du produit sont lues dans ses attributs data-*
function toggleFavoriteBtn(event, btn) {
  toggleFavorite(event, btn.dataset.favId, btn.dataset.favName, parseFloat(btn.dataset.favPrice) || 0, btn.dataset.favImage || '');
}

function updateFavCountBadges() {
  const count = Object.keys(getFavorites()).length;
  document.querySelectorAll('.fav-count-badge').forEach((el) => {
    el.textContent = count;
    el.style.display = count > 0 ? 'flex' : 'none';
  });
}

function initFavoriteButtons() {
  const favs = getFavorites();
  document.querySelectorAll('[data-fav-id]').forEach((btn) => {
    const id = btn.getAttribute('data-fav-id');
    btn.classList.toggle('active', !!favs[id]);
  });
  updateFavCountBadges();
}

// Rendu de la page /favoris (100% côté client depuis localStorage)
function renderFavoritesPage() {
  const container = document.getElementById('favoritesGrid');
  const emptyState = document.getElementById('favoritesEmpty');
  if (!container) return;
  const favs = Object.values(getFavorites());
  const countText = document.getElementById('favCountText');
  if (countText) countText.innerHTML = favs.length ? '<b>' + favs.length + '</b> ' + (favs.length === 1 ? t('product_one', 'produit') : t('product_many', 'produits')) : '';
  if (favs.length === 0) {
    container.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }
  if (emptyState) emptyState.style.display = 'none';
  container.style.display = 'grid';
  container.innerHTML = favs.map((p) => {
    const id = esc(p.id), url = '/product/' + encodeURIComponent(p.id);
    return `
    <div class="pc-card">
      <a href="${url}" class="pc-media">
        ${p.image ? `<img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy">` : '<span class="pc-placeholder"><i class="fas fa-mobile-screen"></i></span>'}
      </a>
      <button type="button" class="pc-fav product-fav-btn active" data-fav-id="${id}" aria-label="Retirer"
              onclick="toggleFavorite(event, this.dataset.favId); renderFavoritesPage();"><i class="fas fa-heart"></i></button>
      <div class="pc-body">
        <a href="${url}" class="pc-name">${esc(p.name)}</a>
        <div class="pc-price"><strong>${formatPrice(p.price)}</strong></div>
        <div class="pc-actions"><a href="${url}" class="pc-btn pc-btn-ghost">${esc(t('view_details', 'Voir détails'))}</a></div>
      </div>
    </div>`;
  }).join('');
}

// ============================================================
//  FOOTER — accordéon mobile
// ============================================================
function toggleFooterAccordion(btn) {
  if (window.innerWidth > 900) return;
  const col = btn.closest('.footer-col');
  if (!col) return;
  const wasOpen = col.classList.contains('open');
  document.querySelectorAll('.footer-col.open').forEach((c) => c.classList.remove('open'));
  if (!wasOpen) col.classList.add('open');
}


// ============================================================
//  OUTILS
// ============================================================
function esc(v) {
  return String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function t(key, fallback) {
  let lang = 'fr';
  try { lang = localStorage.getItem('lang') || 'fr'; } catch (e) {}
  const dict = translations[lang] || translations.fr;
  return (dict && dict[key]) || (translations.fr && translations.fr[key]) || fallback || key;
}
function store(key, val) {
  try {
    if (val === undefined) return JSON.parse(localStorage.getItem(key) || 'null');
    localStorage.setItem(key, JSON.stringify(val));
  } catch (e) { return null; }
}

// ============================================================
//  MESSAGE « AJOUTÉ AU PANIER »
// ============================================================
let toastTimer = null;
function showToast(text, withLink) {
  const box = document.getElementById('toast');
  if (!box) return;
  document.getElementById('toastText').textContent = text;
  const link = document.getElementById('toastLink');
  if (link) link.hidden = !withLink;
  box.hidden = false;
  requestAnimationFrame(() => box.classList.add('show'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    box.classList.remove('show');
    setTimeout(() => { box.hidden = true; }, 300);
  }, 3200);
}

function setCartCount(n) {
  document.querySelectorAll('.cart-count-badge').forEach(el => {
    el.textContent = n;
    el.hidden = !n;
    el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump');
  });
}

// Ajout au panier sans recharger la page (le formulaire marche aussi sans JavaScript)
function initAjaxCart() {
  document.addEventListener('submit', function (e) {
    const form = e.target.closest('.pc-cart-form');
    if (!form || !window.fetch) return;
    e.preventDefault();
    const btn = form.querySelector('button[type=submit]');
    if (btn) btn.classList.add('is-busy');
    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'fetch' },
      credentials: 'same-origin'
    })
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(data => {
        setCartCount(data.count || 0);
        showToast(t('added_to_cart', 'Ajouté au panier'), true);
        if (btn) { btn.classList.add('is-done'); setTimeout(() => btn.classList.remove('is-done'), 1400); }
      })
      .catch(() => form.submit())
      .finally(() => { if (btn) btn.classList.remove('is-busy'); });
  });
}

// ============================================================
//  BOUTONS + / − (fiche produit et panier)
// ============================================================
function initQty() {
  document.querySelectorAll('.qty').forEach(box => {
    const input = box.querySelector('input[type=number]');
    if (!input) return;
    const max = parseInt(box.dataset.max || input.max || '99', 10) || 99;
    const sync = () => {
      const v = parseInt(input.value, 10) || 1;
      box.querySelectorAll('.qty-btn').forEach(b => {
        const step = parseInt(b.dataset.step, 10);
        b.disabled = (step < 0 && v <= 1) || (step > 0 && v >= max);
      });
    };
    box.querySelectorAll('.qty-btn').forEach(b => b.addEventListener('click', () => {
      const v = Math.min(max, Math.max(1, (parseInt(input.value, 10) || 1) + parseInt(b.dataset.step, 10)));
      if (String(v) === input.value) return;
      input.value = v;
      sync();
      if (box.classList.contains('qty-auto')) { box.classList.add('is-busy'); box.submit(); }
    }));
    input.addEventListener('change', () => {
      input.value = Math.min(max, Math.max(1, parseInt(input.value, 10) || 1));
      sync();
      if (box.classList.contains('qty-auto')) box.submit();
    });
    sync();
  });
}

// ============================================================
//  RECHERCHE PLEIN ÉCRAN
// ============================================================
const RECENT_SEARCH_KEY = 'hm_recent_searches';
let sxTimer = null, sxLast = '';

function openSearch() {
  const box = document.getElementById('searchOverlay');
  if (!box) { window.location.href = '/products'; return; }
  box.hidden = false;
  document.body.classList.add('no-scroll');
  renderRecentSearches();
  requestAnimationFrame(() => box.classList.add('open'));
  setTimeout(() => { const i = document.getElementById('sxInput'); if (i) i.focus(); }, 60);
}
function closeSearch() {
  const box = document.getElementById('searchOverlay');
  if (!box) return;
  box.classList.remove('open');
  document.body.classList.remove('no-scroll');
  setTimeout(() => { box.hidden = true; }, 220);
}
function saveRecentSearch(q) {
  q = (q || '').trim();
  if (q.length < 2) return;
  const list = (store(RECENT_SEARCH_KEY) || []).filter(x => x.toLowerCase() !== q.toLowerCase());
  list.unshift(q);
  store(RECENT_SEARCH_KEY, list.slice(0, 8));
}
function clearRecentSearches() { store(RECENT_SEARCH_KEY, []); renderRecentSearches(); }
function renderRecentSearches() {
  const wrap = document.getElementById('sxRecent'), block = document.getElementById('sxRecentBlock');
  if (!wrap || !block) return;
  const list = store(RECENT_SEARCH_KEY) || [];
  block.hidden = !list.length;
  wrap.innerHTML = list.map(q => `<button type="button" class="sx-chip" data-q="${esc(q)}"><i class="fas fa-clock-rotate-left"></i> ${esc(q)}</button>`).join('');
  wrap.querySelectorAll('.sx-chip').forEach(b => b.addEventListener('click', () => {
    const i = document.getElementById('sxInput'); i.value = b.dataset.q; i.dispatchEvent(new Event('input'));
  }));
}
function goSearch(q) {
  saveRecentSearch(q);
  window.location.href = '/products?search=' + encodeURIComponent(q);
}
function initSearchOverlay() {
  const input = document.getElementById('sxInput');
  if (!input) return;
  const results = document.getElementById('sxResults'), idle = document.getElementById('sxIdle');
  const empty = document.getElementById('sxEmpty'), all = document.getElementById('sxAll'), clear = document.getElementById('sxClear');
  const lang = () => { try { return localStorage.getItem('lang') || 'fr'; } catch (e) { return 'fr'; } };

  const show = (state) => {
    idle.hidden = state !== 'idle';
    results.hidden = state !== 'results';
    empty.hidden = state !== 'empty';
    all.hidden = state !== 'results';
  };
  input.addEventListener('input', () => {
    const q = input.value.trim();
    clear.hidden = !input.value;
    clearTimeout(sxTimer);
    if (q.length < 2) { show('idle'); return; }
    results.innerHTML = '<div class="sx-loading"><span></span><span></span><span></span></div>';
    show('results');
    sxTimer = setTimeout(() => {
      sxLast = q;
      fetch('/api/products?q=' + encodeURIComponent(q))
        .then(r => r.json())
        .then(data => {
          if (q !== sxLast) return;
          if (!data.length) { show('empty'); return; }
          results.innerHTML = data.map(p => {
            const name = p['name_' + lang()] || p.name;
            const old = p.old_price && p.old_price > p.price ? `<s>${formatPrice(p.old_price)}</s>` : '';
            return `<a href="/product/${encodeURIComponent(p.id)}" class="sx-item" data-q="${esc(q)}">
              <span class="sx-thumb">${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : '<i class="fas fa-mobile-screen"></i>'}</span>
              <span class="sx-txt"><small>${esc(p.brand || '')}</small><b>${esc(name)}</b>
                <span class="sx-price">${formatPrice(p.price)} ${old}</span></span>
              ${p.stock > 0 ? '' : `<span class="sx-out">${esc(t('out_of_stock', 'Rupture'))}</span>`}
            </a>`;
          }).join('');
          results.querySelectorAll('.sx-item').forEach(a => a.addEventListener('click', () => saveRecentSearch(a.dataset.q)));
          all.href = '/products?search=' + encodeURIComponent(q);
          all.onclick = () => saveRecentSearch(q);
          show('results');
        })
        .catch(() => show('empty'));
    }, 250);
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && input.value.trim()) { e.preventDefault(); goSearch(input.value.trim()); }
  });
  clear.addEventListener('click', () => { input.value = ''; input.dispatchEvent(new Event('input')); input.focus(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeSearch(); });
}

// ============================================================
//  PANNEAU QUI GLISSE DEPUIS LE BAS (filtres)
// ============================================================
function openSheet(id) {
  const sheet = document.getElementById(id), back = document.getElementById(id + 'Backdrop');
  if (!sheet) return;
  sheet.hidden = false; if (back) back.hidden = false;
  document.body.classList.add('no-scroll');
  requestAnimationFrame(() => { sheet.classList.add('open'); if (back) back.classList.add('open'); });
}
function closeSheet(id) {
  const sheet = document.getElementById(id), back = document.getElementById(id + 'Backdrop');
  if (!sheet) return;
  sheet.classList.remove('open'); if (back) back.classList.remove('open');
  document.body.classList.remove('no-scroll');
  setTimeout(() => { sheet.hidden = true; if (back) back.hidden = true; }, 250);
}
function initFilterSheet() {
  const sheet = document.getElementById('filterSheet');
  if (!sheet) return;
  sheet.querySelectorAll('.preset').forEach(b => b.addEventListener('click', () => {
    sheet.querySelector('[name=min_price]').value = b.dataset.min;
    sheet.querySelector('[name=max_price]').value = b.dataset.max;
    sheet.querySelectorAll('.preset').forEach(x => x.classList.toggle('on', x === b));
  }));
  // On n'envoie pas les champs vides (adresse plus propre)
  sheet.addEventListener('submit', () => {
    sheet.querySelectorAll('input').forEach(i => {
      if ((i.type === 'number' || i.type === 'hidden') && !i.value) i.disabled = true;
      if (i.type === 'radio' && i.checked && !i.value) i.disabled = true;
    });
  });
}

// ============================================================
//  FICHE PRODUIT : zoom, partage, description, vus récemment
// ============================================================
function openZoom(src) {
  const z = document.getElementById('zoom');
  if (!z || !src) return;
  document.getElementById('zoomImg').src = src;
  z.hidden = false;
  document.body.classList.add('no-scroll');
  requestAnimationFrame(() => z.classList.add('open'));
}
function closeZoom() {
  const z = document.getElementById('zoom');
  if (!z) return;
  z.classList.remove('open');
  document.body.classList.remove('no-scroll');
  setTimeout(() => { z.hidden = true; }, 200);
}
function shareProduct(name) {
  const data = { title: name, text: name + ' — HDATTAHER MOBILE', url: window.location.href };
  if (navigator.share) { navigator.share(data).catch(() => {}); return; }
  if (navigator.clipboard) {
    navigator.clipboard.writeText(window.location.href)
      .then(() => showToast(t('link_copied', 'Lien copié'), false))
      .catch(() => {});
  }
}

const RECENT_VIEW_KEY = 'hm_recently_viewed';
function rememberProduct() {
  const el = document.querySelector('[data-recent-id]');
  if (!el) return;
  const item = { id: el.dataset.recentId, name: el.dataset.recentName, price: parseFloat(el.dataset.recentPrice) || 0,
                 image: el.dataset.recentImage, brand: el.dataset.recentBrand };
  const list = (store(RECENT_VIEW_KEY) || []).filter(x => x.id !== item.id);
  list.unshift(item);
  store(RECENT_VIEW_KEY, list.slice(0, 10));
}
function clearRecentlyViewed() {
  store(RECENT_VIEW_KEY, []);
  const sec = document.getElementById('recentSection');
  if (sec) sec.hidden = true;
}
function renderRecentlyViewed() {
  const sec = document.getElementById('recentSection'), rail = document.getElementById('recentRail');
  if (!sec || !rail) return;
  const list = store(RECENT_VIEW_KEY) || [];
  if (!list.length) return;
  rail.innerHTML = list.map(p => `
    <a href="/product/${encodeURIComponent(p.id)}" class="mini-card">
      <span class="mini-img">${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy">` : '<i class="fas fa-mobile-screen"></i>'}</span>
      <small>${esc(p.brand || '')}</small>
      <b>${esc(p.name)}</b>
      <span>${formatPrice(p.price)}</span>
    </a>`).join('');
  sec.hidden = false;
}
function initDescription() {
  const box = document.getElementById('pdDesc'), more = document.getElementById('pdMore');
  if (box && more && box.scrollHeight > box.clientHeight + 8) more.hidden = false;
}

// ============================================================
//  BANNIÈRES : glisser avec le doigt
// ============================================================
function initBannerSwipe() {
  const track = document.getElementById('bannerTrack');
  if (!track || track.children.length < 2) return;
  let x0 = null, y0 = null;
  track.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
  track.addEventListener('touchend', (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) bannerCarouselGo(dx < 0 ? 1 : -1);
    x0 = y0 = null;
  }, { passive: true });
}

// Fiche produit : la barre d'achat fixe n'apparaît qu'une fois le bouton principal dépassé
function initStickyBuy() {
  const bar = document.querySelector('.pd-sticky');
  if (!bar) return;
  document.body.classList.add('has-sticky');
  const target = document.getElementById('pdBuy') || document.querySelector('.pd-wa');
  if (!target || !('IntersectionObserver' in window)) { bar.classList.add('show'); return; }
  new IntersectionObserver((entries) => {
    entries.forEach(e => bar.classList.toggle('show', !e.isIntersecting && e.boundingClientRect.top < 0));
  }).observe(target);
}

function initShop() {
  initAjaxCart();
  initQty();
  initSearchOverlay();
  initFilterSheet();
  initDescription();
  initStickyBuy();
  initBannerSwipe();
  rememberProduct();
  renderRecentlyViewed();
}

// ============================================================
//  INITIALISATION
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  LangManager.init();
  NavManager.init();
  AnimationManager.init();
  initFlashMessages();
  initSearch();
  initBannerCarousel();
  
  applyDataNameTranslations();

  initCounters();
  initFavoriteButtons();
  renderFavoritesPage();
  initShop();
});
