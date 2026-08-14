/**
 * HDATTAHER MOBILE - JavaScript Principal
 * Gère le thème, la langue, la navigation, les animations
 */

// ============================================================
//  THEME (Mode sombre / clair)
// ============================================================
const ThemeManager = {
  init() {
    const saved = localStorage.getItem('theme') || 'light';
    this.set(saved);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () => this.toggle());
  },
  set(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  },
  toggle() {
    const current = localStorage.getItem('theme') || 'light';
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
    footer_desc: 'Smartphones & accessoires premium au Niger.',
    footer_trust_badge: '🇳🇪 Votre boutique tech de confiance au Niger',
    footer_shop: 'Boutique', footer_help: 'Aide',
    footer_help_title: "Besoin d'aide ?", footer_help_desc: 'Nous sommes disponibles sur WhatsApp.',
    footer_whatsapp_btn: 'Parler sur WhatsApp',
    footer_newsletter_title: 'Restez informé des nouveautés 📱',
    footer_newsletter_desc: 'Recevez nos nouveaux produits et promotions.',
    footer_newsletter_placeholder: 'Votre adresse e-mail', footer_newsletter_btn: "S'inscrire",
    footer_legal_mentions: 'Mentions légales', footer_legal_privacy: 'Confidentialité', footer_legal_terms: 'Conditions',
    footer_made: 'Fait avec ❤️ au Niger 🇳🇪',
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
    order_confirmed_title: 'Commande confirmée !', order_number_label: 'Numéro de commande :',
    contact_soon_prefix: 'Nous vous contacterons bientôt au',
    contact_soon_suffix: 'pour confirmer la livraison.',
    continue_shopping_btn: 'Continuer mes achats',
    order_prefix: 'Commande #', status_label: 'Statut :', delivery_title: 'Livraison',
    download_invoice: 'Télécharger la facture',
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
    footer_desc: 'Premium smartphones & accessories in Niger.',
    footer_trust_badge: '🇳🇪 Your trusted tech shop in Niger',
    footer_shop: 'Shop', footer_help: 'Help',
    footer_help_title: 'Need help?', footer_help_desc: 'We are available on WhatsApp.',
    footer_whatsapp_btn: 'Chat on WhatsApp',
    footer_newsletter_title: 'Stay updated 📱',
    footer_newsletter_desc: 'Get our new products and promotions.',
    footer_newsletter_placeholder: 'Your email address', footer_newsletter_btn: 'Subscribe',
    footer_legal_mentions: 'Legal notice', footer_legal_privacy: 'Privacy', footer_legal_terms: 'Terms',
    footer_made: 'Made with ❤️ in Niger 🇳🇪',
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
    order_confirmed_title: 'Order confirmed!', order_number_label: 'Order number:',
    contact_soon_prefix: "We'll contact you soon at",
    contact_soon_suffix: 'to confirm delivery.',
    continue_shopping_btn: 'Continue shopping',
    order_prefix: 'Order #', status_label: 'Status:', delivery_title: 'Delivery',
    download_invoice: 'Download invoice',
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
    footer_desc: 'هواتف ذكية وإكسسوارات فاخرة في النيجر.',
    footer_trust_badge: '🇳🇪 متجرك التقني الموثوق في النيجر',
    footer_shop: 'المتجر', footer_help: 'المساعدة',
    footer_help_title: 'تحتاج مساعدة؟', footer_help_desc: 'نحن متوفرون عبر واتساب.',
    footer_whatsapp_btn: 'تحدث عبر واتساب',
    footer_newsletter_title: 'ابق على اطلاع 📱',
    footer_newsletter_desc: 'احصل على منتجاتنا الجديدة وعروضنا.',
    footer_newsletter_placeholder: 'بريدك الإلكتروني', footer_newsletter_btn: 'اشترك',
    footer_legal_mentions: 'الإشعار القانوني', footer_legal_privacy: 'الخصوصية', footer_legal_terms: 'الشروط',
    footer_made: 'صنع بحب ❤️ في النيجر 🇳🇪',
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
    order_confirmed_title: 'تم تأكيد الطلب!', order_number_label: 'رقم الطلب:',
    contact_soon_prefix: 'سنتواصل معك قريبًا على الرقم',
    contact_soon_suffix: 'لتأكيد التوصيل.',
    continue_shopping_btn: 'متابعة التسوق',
    order_prefix: 'الطلب #', status_label: 'الحالة:', delivery_title: 'التوصيل',
    download_invoice: 'تحميل الفاتورة',
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
    }, { threshold: 0.1 });
    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
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
            if (data.length === 0) { results.style.display = 'none'; return; }
            results.innerHTML = data.map(p => `
              <a href="/product/${p.id}" class="search-result-item">
                <span>${p.name}</span>
                <span class="search-price">${formatPrice(p.price)}</span>
              </a>
            `).join('');
            results.style.display = 'block';
          });
      }, 300);
    });
    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !results.contains(e.target))
        results.style.display = 'none';
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
  if (favs.length === 0) {
    container.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }
  if (emptyState) emptyState.style.display = 'none';
  container.style.display = 'grid';
  container.innerHTML = favs.map((p) => `
    <div class="product-card animate-on-scroll">
      <a href="/product/${p.id}">
        <div class="product-image">
          ${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy">` : `<div class="placeholder-icon">📱</div>`}
        </div>
      </a>
      <div class="product-info">
        <h3 class="product-name">${p.name}</h3>
        <div class="product-price-row">
          <span class="product-price">${formatPrice(p.price)}</span>
        </div>
        <div class="product-actions" style="margin-top:10px;">
          <a href="/product/${p.id}" class="btn btn-outline btn-sm">Voir détails</a>
          <button class="btn btn-danger btn-sm" onclick="toggleFavorite(event, '${p.id}'); renderFavoritesPage();">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

// ============================================================
//  FOOTER — accordéon mobile + newsletter (design only)
// ============================================================
function toggleFooterAccordion(btn) {
  if (window.innerWidth > 900) return;
  const col = btn.closest('.footer-col');
  if (!col) return;
  const wasOpen = col.classList.contains('open');
  document.querySelectorAll('.footer-col.open').forEach((c) => c.classList.remove('open'));
  if (!wasOpen) col.classList.add('open');
}

function handleFooterNewsletter(event) {
  event.preventDefault();
  const form = event.target;
  const input = form.querySelector('input[type="email"]');
  const btn = form.querySelector('button');
  if (!input || !input.value) return false;
  const originalText = btn.textContent;
  btn.textContent = '✓';
  input.value = '';
  setTimeout(() => { btn.textContent = originalText; }, 2000);
  return false;
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
});
