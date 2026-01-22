-- EXFIN REST - Tüm Kategoriler ve Ürünler Tam Scripti
-- Bu script tüm kategorileri ve ürünleri içerir

-- =====================================================
-- MEVCUT VERİLERİ TEMİZLE
-- =====================================================

DELETE FROM order_items;
DELETE FROM products;
DELETE FROM categories;

ALTER SEQUENCE categories_id_seq RESTART WITH 1;
ALTER SEQUENCE products_id_seq RESTART WITH 1;

-- =====================================================
-- KATEGORİLERİ EKLE (28 Kategori)
-- =====================================================

INSERT INTO categories (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, icon, color, sort_order, is_featured) VALUES
-- İçecekler
('İçecekler', 'Beverages', 'مشروبات', 'Şerab', 'شەراب', 'Soğuk ve sıcak içecekler', 'Cold and hot beverages', 'مشروبات باردة وساخنة', 'Şerabên sar û germ', 'شەرابە سارد و گەرمەکان', 'local_drink', '#2196F3', 1, true),
('Kahve & Çay', 'Coffee & Tea', 'قهوة وشاي', 'Qehwe û Çay', 'قەهوە و چای', 'Sıcak içecekler', 'Hot beverages', 'مشروبات ساخنة', 'Şerabên germ', 'شەرابە گەرمەکان', 'coffee', '#795548', 2, true),
('Alkollü İçecekler', 'Alcoholic Beverages', 'مشروبات كحولية', 'Şerabên Alkolî', 'شەرابە ئەلکۆلییەکان', 'Bira, şarap ve kokteyl', 'Beer, wine and cocktails', 'بيرة ونبيذ وكوكتيل', 'Bîra, mey û kokteyl', 'بیرە و مەی و کۆکتەیل', 'local_bar', '#8BC34A', 3, false),

-- Başlangıçlar
('Çorbalar', 'Soups', 'حساء', 'Şorba', 'شۆربا', 'Sıcak ve soğuk çorbalar', 'Hot and cold soups', 'حساء ساخن وبارد', 'Şorba germ û sar', 'شۆربای گەرم و سارد', 'soup_kitchen', '#FF9800', 4, true),
('Salatalar', 'Salads', 'سلطات', 'Salata', 'سەلاتە', 'Taze salatalar', 'Fresh salads', 'سلطات طازجة', 'Salata taze', 'سەلاتەی تازە', 'eco', '#4CAF50', 5, true),
('Mezeler', 'Appetizers', 'مقبلات', 'Meze', 'مەزە', 'Geleneksel mezeler', 'Traditional appetizers', 'مقبلات تقليدية', 'Mezeyên kevneşopî', 'مەزەی کۆنەپارێز', 'tapas', '#9C27B0', 6, true),

-- Ana Yemekler
('Türk Mutfağı', 'Turkish Cuisine', 'المطبخ التركي', 'Pêjgeha Tirkî', 'پێشگەی تورکی', 'Geleneksel Türk yemekleri', 'Traditional Turkish dishes', 'أطباق تركية تقليدية', 'Xwarinên kevneşopî yên Tirkî', 'خواردنە کۆنەپارێزە تورکییەکان', 'restaurant', '#E91E63', 7, true),
('İtalyan Mutfağı', 'Italian Cuisine', 'المطبخ الإيطالي', 'Pêjgeha Îtalî', 'پێشگەی ئیتاڵی', 'İtalyan yemekleri', 'Italian dishes', 'أطباق إيطالية', 'Xwarinên Îtalî', 'خواردنە ئیتاڵییەکان', 'pizza', '#F44336', 8, true),
('Çin Mutfağı', 'Chinese Cuisine', 'المطبخ الصيني', 'Pêjgeha Çînî', 'پێشگەی چینی', 'Çin yemekleri', 'Chinese dishes', 'أطباق صينية', 'Xwarinên Çînî', 'خواردنە چینییەکان', 'ramen_dining', '#FF5722', 9, true),
('Hint Mutfağı', 'Indian Cuisine', 'المطبخ الهندي', 'Pêjgeha Hindî', 'پێشگەی هیندی', 'Hint yemekleri', 'Indian dishes', 'أطباق هندية', 'Xwarinên Hindî', 'خواردنە هیندییەکان', 'curry', '#FF9800', 10, true),
('Japon Mutfağı', 'Japanese Cuisine', 'المطبخ الياباني', 'Pêjgeha Japonî', 'پێشگەی ژاپۆنی', 'Japon yemekleri', 'Japanese dishes', 'أطباق يابانية', 'Xwarinên Japonî', 'خواردنە ژاپۆنییەکان', 'sushi', '#3F51B5', 11, true),
('Meksika Mutfağı', 'Mexican Cuisine', 'المطبخ المكسيكي', 'Pêjgeha Meksîkî', 'پێشگەی مەکسیکی', 'Meksika yemekleri', 'Mexican dishes', 'أطباق مكسيكية', 'Xwarinên Meksîkî', 'خواردنە مەکسیکییەکان', 'taco', '#4CAF50', 12, true),
('Fransız Mutfağı', 'French Cuisine', 'المطبخ الفرنسي', 'Pêjgeha Fransî', 'پێشگەی فەرەنسی', 'Fransız yemekleri', 'French dishes', 'أطباق فرنسية', 'Xwarinên Fransî', 'خواردنە فەرەنسییەکان', 'bakery_dining', '#9C27B0', 13, true),
('Amerikan Mutfağı', 'American Cuisine', 'المطبخ الأمريكي', 'Pêjgeha Amerîkî', 'پێشگەی ئەمریکی', 'Amerikan yemekleri', 'American dishes', 'أطباق أمريكية', 'Xwarinên Amerîkî', 'خواردنە ئەمریکییەکان', 'fastfood', '#607D8B', 14, true),
('Arap Mutfağı', 'Arabic Cuisine', 'المطبخ العربي', 'Pêjgeha Erebî', 'پێشگەی عەرەبی', 'Arap yemekleri', 'Arabic dishes', 'أطباق عربية', 'Xwarinên Erebî', 'خواردنە عەرەبییەکان', 'kebab_dining', '#795548', 15, true),
('Yunan Mutfağı', 'Greek Cuisine', 'المطبخ اليوناني', 'Pêjgeha Yewnanî', 'پێشگەی یۆنانی', 'Yunan yemekleri', 'Greek dishes', 'أطباق يونانية', 'Xwarinên Yewnanî', 'خواردنە یۆنانییەکان', 'mediterranean', '#00BCD4', 16, true),

-- Özel Kategoriler
('Deniz Ürünleri', 'Seafood', 'مأكولات بحرية', 'Xwarinên Deryayî', 'خواردنە دەریایییەکان', 'Balık ve deniz ürünleri', 'Fish and seafood', 'أسماك ومأكولات بحرية', 'Masî û xwarinên deryayî', 'ماسی و خواردنە دەریایییەکان', 'set_meal', '#03A9F4', 17, true),
('Vejetaryen', 'Vegetarian', 'نباتي', 'Giyanî', 'گیانی', 'Vejetaryen yemekler', 'Vegetarian dishes', 'أطباق نباتية', 'Xwarinên giyanî', 'خواردنە گیانییەکان', 'eco', '#8BC34A', 18, true),
('Vegan', 'Vegan', 'نباتي صرف', 'Giyanî Saf', 'گیانی ساف', 'Vegan yemekler', 'Vegan dishes', 'أطباق نباتية صرفة', 'Xwarinên giyanî saf', 'خواردنە گیانی سافەکان', 'grass', '#4CAF50', 19, false),
('Glutensiz', 'Gluten Free', 'خالي من الغلوتين', 'Bê Gluten', 'بێ گلوتن', 'Glutensiz yemekler', 'Gluten free dishes', 'أطباق خالية من الغلوتين', 'Xwarinên bê gluten', 'خواردنە بێ گلوتنەکان', 'no_food', '#FF9800', 20, false),

-- Tatlılar
('Tatlılar', 'Desserts', 'حلويات', 'Şîrînî', 'شیرینی', 'Tatlı ve dondurma çeşitleri', 'Desserts and ice cream', 'حلويات وآيس كريم', 'Şîrînî û dondurma', 'شیرینی و دۆندوورما', 'cake', '#E91E63', 21, true),
('Dondurma', 'Ice Cream', 'آيس كريم', 'Dondurma', 'دۆندوورما', 'Dondurma çeşitleri', 'Ice cream varieties', 'أنواع الآيس كريم', 'Cureyên dondurmayê', 'جۆرەکانی دۆندوورما', 'icecream', '#2196F3', 22, true),

-- Kahvaltı
('Kahvaltı', 'Breakfast', 'فطور', 'Taştê', 'تاشتێ', 'Kahvaltı menüsü', 'Breakfast menu', 'قائمة الفطور', 'Menuyê taştêyê', 'مێنیوی تاشتێ', 'breakfast_dining', '#FFC107', 23, true),

-- Fast Food
('Pizzalar', 'Pizzas', 'بيتزا', 'Pîzza', 'پیتزا', 'Çeşitli pizza türleri', 'Various pizza types', 'أنواع البيتزا', 'Cureyên pîzzayê', 'جۆرەکانی پیتزا', 'local_pizza', '#F44336', 24, true),
('Burgerler', 'Burgers', 'برغر', 'Burger', 'بۆرگەر', 'Hamburger çeşitleri', 'Hamburger varieties', 'أنواع البرغر', 'Cureyên burgerê', 'جۆرەکانی بۆرگەر', 'lunch_dining', '#FF5722', 25, true),
('Sandviçler', 'Sandwiches', 'سندويتش', 'Sandwîç', 'ساندویچ', 'Sandviç çeşitleri', 'Sandwich varieties', 'أنواع السندويتش', 'Cureyên sandwîçê', 'جۆرەکانی ساندویچ', 'bakery_dining', '#795548', 26, true),

-- Özel Menüler
('Şef Özel', 'Chef Special', 'خاص الشيف', 'Taybetiya Şef', 'تایبەتی شێف', 'Şef özel yemekleri', 'Chef special dishes', 'أطباق خاصة بالشيف', 'Xwarinên taybet ên şef', 'خواردنە تایبەتەکانی شێف', 'star', '#FFD700', 27, true),
('Çocuk Menüsü', 'Kids Menu', 'قائمة الأطفال', 'Menuyê Zarokan', 'مێنیوی منداڵان', 'Çocuklar için özel menü', 'Special menu for kids', 'قائمة خاصة للأطفال', 'Menuyê taybet ji bo zarokan', 'مێنیوی تایبەت بۆ منداڵان', 'child_care', '#FF9800', 28, false);

-- =====================================================
-- ÜRÜNLERİ EKLE (Tüm Kategoriler İçin)
-- =====================================================

-- İçecekler (Kategori 1) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_cold, calories, origin_country, popular) VALUES
('Coca Cola', 'Coca Cola', 'كوكا كولا', 'Coca Cola', 'کۆکا کۆلا', '330ml Coca Cola', '330ml Coca Cola', 'كوكا كولا 330 مل', 'Coca Cola 330ml', 'کۆکا کۆلای 330 مل', 15.00, 1, 0, true, true, true, true, 140, 'USA', true),
('Pepsi', 'Pepsi', 'بيبسي', 'Pepsi', 'پێپسی', '330ml Pepsi', '330ml Pepsi', 'بيبسي 330 مل', 'Pepsi 330ml', 'پێپسی 330 مل', 15.00, 1, 0, true, true, true, true, 150, 'USA', true),
('Fanta', 'Fanta', 'فانتا', 'Fanta', 'فانتا', '330ml Fanta Portakal', '330ml Fanta Orange', 'فانتا برتقال 330 مل', 'Fanta Porteqal 330ml', 'فانتای پرتەقاڵی 330 مل', 15.00, 1, 0, true, true, true, true, 160, 'Germany', true),
('Sprite', 'Sprite', 'سبرايت', 'Sprite', 'سپرایت', '330ml Sprite', '330ml Sprite', 'سبرايت 330 مل', 'Sprite 330ml', 'سپرایتی 330 مل', 15.00, 1, 0, true, true, true, true, 140, 'USA', true),
('Ayran', 'Ayran', 'عيران', 'Ayrûn', 'ئەیران', '500ml Taze Ayran', '500ml Fresh Ayran', 'عيران طازج 500 مل', 'Ayrûn taze 500ml', 'ئەیرانی تازەی 500 مل', 12.00, 1, 0, true, true, true, true, 60, 'Turkey', true),
('Su', 'Water', 'ماء', 'Av', 'ئاو', '500ml Doğal Su', '500ml Natural Water', 'ماء طبيعي 500 مل', 'Av xwezayî 500ml', 'ئاوی سروشتی 500 مل', 5.00, 1, 0, true, true, true, true, 0, 'Turkey', true),
('Meyve Suyu', 'Fruit Juice', 'عصير فواكه', 'Şîrê Mêweyan', 'شیری میوەکان', '250ml Karışık Meyve Suyu', '250ml Mixed Fruit Juice', 'عصير فواكه مختلط 250 مل', 'Şîrê mêweyan tevlihev 250ml', 'شیری میوە تێکەڵەکان 250 مل', 18.00, 1, 0, true, true, true, true, 120, 'Turkey', true),
('Limonata', 'Lemonade', 'ليموناضة', 'Lîmonata', 'لیمۆناتە', '300ml Taze Limonata', '300ml Fresh Lemonade', 'ليموناضة طازجة 300 مل', 'Lîmonata taze 300ml', 'لیمۆناتەی تازەی 300 مل', 20.00, 1, 0, true, true, true, true, 90, 'Turkey', true);

-- Kahve & Çay (Kategori 2) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular) VALUES
('Türk Kahvesi', 'Turkish Coffee', 'قهوة تركية', 'Qehweya Tirkî', 'قەهوەی تورکی', 'Geleneksel Türk Kahvesi', 'Traditional Turkish Coffee', 'قهوة تركية تقليدية', 'Qehweya kevneşopî ya Tirkî', 'قەهوەی کۆنەپارێزی تورکی', 12.00, 2, 0, true, true, true, true, 5, 'Turkey', true),
('Espresso', 'Espresso', 'اسبريسو', 'Espresso', 'ئێسپرێسۆ', 'Tek Shot Espresso', 'Single Shot Espresso', 'اسبريسو شوت واحد', 'Espresso tek shot', 'ئێسپرێسۆی تەک شۆت', 15.00, 2, 0, true, true, true, true, 5, 'Italy', true),
('Cappuccino', 'Cappuccino', 'كابتشينو', 'Cappuccino', 'کاپۆچینۆ', 'Espresso, Süt, Süt Köpüğü', 'Espresso, Milk, Milk Foam', 'اسبريسو وحليب ورغوة الحليب', 'Espresso, şîr, kefşîr', 'ئێسپرێسۆ، شیر، کەفشیر', 18.00, 2, 0, true, true, true, true, 80, 'Italy', true),
('Latte', 'Latte', 'لاتيه', 'Latte', 'لاتە', 'Espresso ve Buharlanmış Süt', 'Espresso and Steamed Milk', 'اسبريسو وحليب مبخر', 'Espresso û şîrê biharî', 'ئێسپرێسۆ و شیری بەهار', 20.00, 2, 0, true, true, true, true, 120, 'Italy', true),
('Çay', 'Tea', 'شاي', 'Çay', 'چای', 'Sıcak Çay', 'Hot Tea', 'شاي ساخن', 'Çay germ', 'چای گەرم', 8.00, 2, 0, true, true, true, true, 2, 'Turkey', true),
('Yeşil Çay', 'Green Tea', 'شاي اخضر', 'Çaya Kesk', 'چای سەوز', 'Sıcak Yeşil Çay', 'Hot Green Tea', 'شاي اخضر ساخن', 'Çaya kesk germ', 'چای سەوزی گەرم', 10.00, 2, 0, true, true, true, true, 2, 'China', true),
('Nane Çayı', 'Mint Tea', 'شاي نعناع', 'Çaya Pûng', 'چای پوونگ', 'Sıcak Nane Çayı', 'Hot Mint Tea', 'شاي نعناع ساخن', 'Çaya pûng germ', 'چای پوونگی گەرم', 12.00, 2, 0, true, true, true, true, 3, 'Morocco', true),
('Ihlamur Çayı', 'Linden Tea', 'شاي زيزفون', 'Çaya Gulî', 'چای گوڵی', 'Sıcak Ihlamur Çayı', 'Hot Linden Tea', 'شاي زيزفون ساخن', 'Çaya gulî germ', 'چای گوڵی گەرم', 10.00, 2, 0, true, true, true, true, 2, 'Turkey', true);

-- Alkollü İçecekler (Kategori 3) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_cold, calories, origin_country, popular) VALUES
('Efes Pilsen', 'Efes Pilsen', 'إيفس بيلسن', 'Efes Pilsen', 'ئێفەس پیلسەن', '330ml Bira', '330ml Beer', 'بيرة 330 مل', 'Bîra 330ml', 'بیرەی 330 مل', 25.00, 3, 0, true, true, true, true, 150, 'Turkey', true),
('Corona', 'Corona', 'كورونا', 'Corona', 'کۆرۆنا', '330ml Meksika Birası', '330ml Mexican Beer', 'بيرة مكسيكية 330 مل', 'Bîra Meksîkî 330ml', 'بیرەی مەکسیکی 330 مل', 30.00, 3, 0, true, true, true, true, 140, 'Mexico', true),
('Heineken', 'Heineken', 'هاينكن', 'Heineken', 'هاینکەن', '330ml Hollanda Birası', '330ml Dutch Beer', 'بيرة هولندية 330 مل', 'Bîra Holendî 330ml', 'بیرەی ھۆلەندی 330 مل', 28.00, 3, 0, true, true, true, true, 145, 'Netherlands', true),
('Kırmızı Şarap', 'Red Wine', 'نبيذ أحمر', 'Meya Sor', 'مەی سوور', '175ml Kırmızı Şarap', '175ml Red Wine', 'نبيذ أحمر 175 مل', 'Meya sor 175ml', 'مەی سووری 175 مل', 45.00, 3, 0, true, true, true, true, 125, 'Turkey', true),
('Beyaz Şarap', 'White Wine', 'نبيذ أبيض', 'Meya Spî', 'مەی سپی', '175ml Beyaz Şarap', '175ml White Wine', 'نبيذ أبيض 175 مل', 'Meya spî 175ml', 'مەی سپی 175 مل', 42.00, 3, 0, true, true, true, true, 120, 'Turkey', true),
('Mojito', 'Mojito', 'موجيتو', 'Mojito', 'مۆجیتۆ', 'Kokteyl', 'Cocktail', 'كوكتيل', 'Kokteyl', 'کۆکتەیل', 35.00, 3, 0, true, true, true, true, 180, 'Cuba', true),
('Margarita', 'Margarita', 'مارغريتا', 'Margarita', 'ماڕگەریتا', 'Kokteyl', 'Cocktail', 'كوكتيل', 'Kokteyl', 'کۆکتەیل', 40.00, 3, 0, true, true, true, true, 200, 'Mexico', true),
('Martini', 'Martini', 'مارتيني', 'Martini', 'ماڕتینی', 'Kokteyl', 'Cocktail', 'كوكتيل', 'Kokteyl', 'کۆکتەیل', 45.00, 3, 0, true, true, true, true, 160, 'Italy', true);

-- Çorbalar (Kategori 4) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular) VALUES
('Mercimek Çorbası', 'Lentil Soup', 'حساء عدس', 'Şorbaya Nîsk', 'شۆربای نیسک', 'Geleneksel mercimek çorbası', 'Traditional lentil soup', 'حساء عدس تقليدي', 'Şorbaya nîsk ya kevneşopî', 'شۆربای نیسکی کۆنەپارێز', 25.00, 4, 0, true, true, true, true, 180, 'Turkey', true),
('Ezogelin Çorbası', 'Ezogelin Soup', 'حساء إزوجلين', 'Şorbaya Ezogelin', 'شۆربای ئەزۆگەلین', 'Acılı mercimek çorbası', 'Spicy lentil soup', 'حساء عدس حار', 'Şorbaya nîsk ya tûj', 'شۆربای نیسکی تۆژ', 28.00, 4, 2, true, true, true, true, 200, 'Turkey', true),
('Tavuk Çorbası', 'Chicken Soup', 'حساء دجاج', 'Şorbaya Mirîşk', 'شۆربای مریشک', 'Tavuk suyu çorbası', 'Chicken broth soup', 'حساء مرق دجاج', 'Şorbaya avê mirîşkê', 'شۆربای ئاوی مریشک', 30.00, 4, 0, false, false, true, true, 150, 'Turkey', true),
('Domates Çorbası', 'Tomato Soup', 'حساء طماطم', 'Şorbaya Bacanaş', 'شۆربای باژەنگ', 'Domates çorbası', 'Tomato soup', 'حساء طماطم', 'Şorbaya bacanaş', 'شۆربای باژەنگ', 22.00, 4, 0, true, true, true, true, 120, 'Turkey', true),
('Mantar Çorbası', 'Mushroom Soup', 'حساء فطر', 'Şorbaya Kûvark', 'شۆربای کەوەرک', 'Mantar çorbası', 'Mushroom soup', 'حساء فطر', 'Şorbaya kûvark', 'شۆربای کەوەرک', 26.00, 4, 0, true, false, true, true, 140, 'Turkey', true),
('Sebze Çorbası', 'Vegetable Soup', 'حساء خضار', 'Şorbaya Sebzeyan', 'شۆربای سەوزەوات', 'Sebze çorbası', 'Vegetable soup', 'حساء خضار', 'Şorbaya sebzeyan', 'شۆربای سەوزەوات', 24.00, 4, 0, true, true, true, true, 130, 'Turkey', true),
('Balık Çorbası', 'Fish Soup', 'حساء سمك', 'Şorbaya Masî', 'شۆربای ماسی', 'Balık çorbası', 'Fish soup', 'حساء سمك', 'Şorbaya masî', 'شۆربای ماسی', 35.00, 4, 1, false, false, true, true, 180, 'Turkey', true),
('İşkembe Çorbası', 'Tripe Soup', 'حساء كرشة', 'Şorbaya Rûvî', 'شۆربای ڕووی', 'İşkembe çorbası', 'Tripe soup', 'حساء كرشة', 'Şorbaya rûvî', 'شۆربای ڕووی', 32.00, 4, 1, false, false, true, true, 220, 'Turkey', true);

-- Salatalar (Kategori 5) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_cold, calories, origin_country, popular) VALUES
('Çoban Salatası', 'Shepherd Salad', 'سلطة راعي', 'Salataya Şivan', 'سەلاتەی شوان', 'Domates, salatalık, soğan', 'Tomato, cucumber, onion', 'طماطم وخيار وبصل', 'Bacanaş, xiyar, pîvaz', 'باژەنگ، خەیار، پیاز', 25.00, 5, 0, true, true, true, true, 80, 'Turkey', true),
('Gavurdağı Salatası', 'Gavurdagi Salad', 'سلطة جاوورداغ', 'Salataya Gavurdax', 'سەلاتەی گەڤرداغ', 'Acılı domates salatası', 'Spicy tomato salad', 'سلطة طماطم حارة', 'Salataya bacanaş ya tûj', 'سەلاتەی باژەنگ تۆژ', 28.00, 5, 2, true, true, true, true, 90, 'Turkey', true),
('Sezar Salata', 'Caesar Salad', 'سلطة قيصر', 'Salataya Sezar', 'سەلاتەی سێزار', 'Marul, tavuk, peynir', 'Lettuce, chicken, cheese', 'خس ودجاج وجبن', 'Selata, mirîşk, penîr', 'سەلاتە، مریشک، پەنیر', 35.00, 5, 0, false, false, true, true, 150, 'Italy', true),
('Roka Salatası', 'Arugula Salad', 'سلطة جرجير', 'Salataya Roka', 'سەلاتەی ڕۆکا', 'Roka, domates, peynir', 'Arugula, tomato, cheese', 'جرجير وطماطم وجبن', 'Roka, bacanaş, penîr', 'ڕۆکا، باژەنگ، پەنیر', 30.00, 5, 0, true, false, true, true, 100, 'Italy', true),
('Mevsim Salatası', 'Seasonal Salad', 'سلطة موسمية', 'Salataya Demsal', 'سەلاتەی دەمساڵ', 'Mevsim sebzeleri', 'Seasonal vegetables', 'خضار موسمية', 'Sebzeyên demsal', 'سەوزەواتی دەمساڵ', 22.00, 5, 0, true, true, true, true, 70, 'Turkey', true),
('Akdeniz Salatası', 'Mediterranean Salad', 'سلطة متوسطية', 'Salataya Deryaya Navîn', 'سەلاتەی دەریای ناوین', 'Zeytin, domates, peynir', 'Olives, tomato, cheese', 'زيتون وطماطم وجبن', 'Zeytûn, bacanaş, penîr', 'زەیتون، باژەنگ، پەنیر', 32.00, 5, 0, true, false, true, true, 120, 'Greece', true),
('Kinoa Salatası', 'Quinoa Salad', 'سلطة كينوا', 'Salataya Kînoa', 'سەلاتەی کینۆا', 'Kinoa, sebze, fesleğen', 'Quinoa, vegetables, basil', 'كينوا وخضار وريحان', 'Kînoa, sebzeyan, reyhan', 'کینۆا، سەوزەوات، ڕەیحان', 38.00, 5, 0, true, true, true, true, 140, 'Peru', true),
('Avokado Salatası', 'Avocado Salad', 'سلطة أفوكادو', 'Salataya Avokado', 'سەلاتەی ئەڤۆکادۆ', 'Avokado, domates, soğan', 'Avocado, tomato, onion', 'أفوكادو وطماطم وبصل', 'Avokado, bacanaş, pîvaz', 'ئەڤۆکادۆ، باژەنگ، پیاز', 35.00, 5, 0, true, true, true, true, 160, 'Mexico', true);

-- Mezeler (Kategori 6) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_cold, calories, origin_country, popular) VALUES
('Humus', 'Hummus', 'حمص', 'Humus', 'حەمەس', 'Nohut ezmesi', 'Chickpea paste', 'عجينة حمص', 'Nîskê hûrkirî', 'نیسکی هەڵکوتراوە', 20.00, 6, 0, true, true, true, true, 120, 'Lebanon', true),
('Baba Gannuş', 'Baba Ganoush', 'بابا غنوش', 'Baba Gannûş', 'بابا غەنووش', 'Patlıcan ezmesi', 'Eggplant paste', 'عجينة باذنجان', 'Bacanaşê hûrkirî', 'باژەنگ هەڵکوتراوە', 22.00, 6, 1, true, true, true, true, 100, 'Lebanon', true),
('Cacık', 'Cacik', 'جاجيك', 'Cacîk', 'جاجیک', 'Yoğurtlu salatalık', 'Yogurt with cucumber', 'زبادي مع خيار', 'Mast bi xiyar', 'مەست بە خەیار', 18.00, 6, 0, true, true, true, true, 80, 'Turkey', true),
('Haydari', 'Haydari', 'حيدري', 'Haydarî', 'حەیدەری', 'Yoğurtlu ot', 'Yogurt with herbs', 'زبادي مع أعشاب', 'Mast bi giya', 'مەست بە گیاو', 20.00, 6, 0, true, true, true, true, 90, 'Turkey', true),
('Ezme', 'Ezme', 'عزمة', 'Ezme', 'عەزمە', 'Acılı domates ezmesi', 'Spicy tomato paste', 'عجينة طماطم حارة', 'Bacanaşê hûrkirî ya tûj', 'باژەنگ هەڵکوتراوەی تۆژ', 18.00, 6, 2, true, true, true, true, 70, 'Turkey', true),
('Zeytinyağlı Enginar', 'Artichoke with Olive Oil', 'خرشوف بزيت الزيتون', 'Enginar bi Rûnê Zeytûn', 'ئەنگەر بە ڕوونی زەیتون', 'Enginar mezeleri', 'Artichoke appetizers', 'مقبلات خرشوف', 'Mezeyên enginar', 'مەزەی ئەنگەر', 25.00, 6, 0, true, true, true, true, 110, 'Turkey', true),
('Fasulye Piyazı', 'Bean Salad', 'سلطة فاصوليا', 'Piyaza Fasûlye', 'پیازەی فاسۆلیە', 'Beyaz fasulye salatası', 'White bean salad', 'سلطة فاصوليا بيضاء', 'Salataya fasûlyeya spî', 'سەلاتەی فاسۆلیەی سپی', 20.00, 6, 0, true, true, true, true, 130, 'Turkey', true),
('Patlıcan Közleme', 'Grilled Eggplant', 'باذنجان مشوي', 'Bacanaşê Biraştî', 'باژەنگی براژت', 'Közlenmiş patlıcan', 'Grilled eggplant', 'باذنجان مشوي', 'Bacanaşê biraştî', 'باژەنگی براژت', 22.00, 6, 0, true, true, true, true, 85, 'Turkey', true);

-- Türk Mutfağı (Kategori 7) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular) VALUES
('İskender Kebap', 'Iskender Kebab', 'إسكندر كباب', 'Îskender Kebab', 'ئیسکەندەر کەباب', 'Döner et, yoğurt, domates sosu', 'Doner meat, yogurt, tomato sauce', 'لحم دوينر وزبادي وصلصة طماطم', 'Goştê doner, mast, sosa bacanaş', 'گۆشتی دۆنەر، مەست، سۆسای باژەنگ', 45.00, 7, 1, false, false, true, true, 350, 'Turkey', true),
('Adana Kebap', 'Adana Kebab', 'أضنة كباب', 'Adana Kebab', 'ئەدانە کەباب', 'Acılı kıyma kebap', 'Spicy minced meat kebab', 'كباب لحم مفروم حار', 'Kebabê goştê hûrkirî ya tûj', 'کەبابی گۆشتی هەڵکوتراوەی تۆژ', 42.00, 7, 3, false, false, true, true, 380, 'Turkey', true),
('Urfa Kebap', 'Urfa Kebab', 'أورفا كباب', 'Riha Kebab', 'ئورفە کەباب', 'Az acılı kıyma kebap', 'Mild minced meat kebab', 'كباب لحم مفروم معتدل', 'Kebabê goştê hûrkirî ya nerm', 'کەبابی گۆشتی هەڵکوتراوەی نەرم', 40.00, 7, 1, false, false, true, true, 360, 'Turkey', true),
('Pide', 'Pide', 'بيضة', 'Pîde', 'پیدە', 'Türk pizzası', 'Turkish pizza', 'بيتزا تركية', 'Pîzzaya Tirkî', 'پیتزای تورکی', 35.00, 7, 0, false, false, false, true, 280, 'Turkey', true),
('Lahmacun', 'Lahmacun', 'لحم بعجين', 'Lahmacûn', 'لەحمەجون', 'İnce hamur üzerine kıyma', 'Minced meat on thin dough', 'لحم مفروم على عجين رقيق', 'Goştê hûrkirî li ser hevîrê tenik', 'گۆشتی هەڵکوتراوە لەسەر هەویری تەنک', 25.00, 7, 1, false, false, false, true, 220, 'Turkey', true),
('Mantı', 'Manti', 'منتو', 'Mantî', 'مەنتی', 'Küçük hamur parçaları', 'Small dough pieces', 'قطع عجين صغيرة', 'Parçeyên hevîrê biçûk', 'پارچەکانی هەویری بچووک', 30.00, 7, 0, false, false, false, true, 250, 'Turkey', true),
('Karnıyarık', 'Karniyarik', 'كرني يرك', 'Karnîyarik', 'کەرنی یەریک', 'Patlıcan dolması', 'Stuffed eggplant', 'باذنجان محشي', 'Bacanaşê dagirtî', 'باژەنگی دەگرت', 28.00, 7, 1, true, false, true, true, 200, 'Turkey', true),
('İmambayıldı', 'Imam Bayildi', 'إمام بايلدي', 'Îmam Bayildî', 'ئیمام بەیڵدی', 'Patlıcan yemeği', 'Eggplant dish', 'طبق باذنجان', 'Xwarina bacanaş', 'خواردنی باژەنگ', 26.00, 7, 0, true, true, true, true, 180, 'Turkey', true);

-- İtalyan Mutfağı (Kategori 8) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular) VALUES
('Spaghetti Carbonara', 'Spaghetti Carbonara', 'سباغيتي كاربونارا', 'Spaghetti Carbonara', 'سپاگەتی کاربۆنارا', 'Yumurta, peynir, pastırma', 'Egg, cheese, bacon', 'بيض وجبن وبيكون', 'Hêlke, penîr, pastirma', 'هێلکە، پەنیر، پاسترما', 38.00, 8, 0, false, false, false, true, 420, 'Italy', true),
('Penne Arrabbiata', 'Penne Arrabbiata', 'بيني أرابياتا', 'Penne Arrabbiata', 'پێنەی ئەرەبیاتا', 'Acılı domates sosu', 'Spicy tomato sauce', 'صلصة طماطم حارة', 'Sosa bacanaş ya tûj', 'سۆسای باژەنگ تۆژ', 32.00, 8, 2, true, true, false, true, 350, 'Italy', true),
('Risotto ai Funghi', 'Mushroom Risotto', 'ريسوتو بالفطر', 'Risotto bi Kûvark', 'ریسۆتۆ بە کەوەرک', 'Mantar risottosu', 'Mushroom risotto', 'ريسوتو بالفطر', 'Risotto bi kûvark', 'ریسۆتۆ بە کەوەرک', 36.00, 8, 0, true, false, false, true, 380, 'Italy', true),
('Lasagna', 'Lasagna', 'لازانيا', 'Lasagna', 'لازانیا', 'Katmanlı makarna', 'Layered pasta', 'معكرونة مطبقة', 'Makarnaya tewşî', 'ماکارۆنی تەوشی', 42.00, 8, 0, false, false, false, true, 450, 'Italy', true),
('Osso Buco', 'Osso Buco', 'أوسو بوكو', 'Osso Buco', 'ئۆسۆ بۆکۆ', 'Dana incik yemeği', 'Veal shank dish', 'طبق عجل', 'Xwarina goştê golikê', 'خواردنی گۆشتی گۆلک', 48.00, 8, 1, false, false, true, true, 520, 'Italy', true),
('Tiramisu', 'Tiramisu', 'تيراميسو', 'Tiramisu', 'تیڕامیسو', 'İtalyan tatlısı', 'Italian dessert', 'حلويات إيطالية', 'Şîrînîya Îtalî', 'شیرینی ئیتاڵی', 25.00, 8, 0, true, false, false, false, 280, 'Italy', true),
('Bruschetta', 'Bruschetta', 'بروشيتا', 'Bruschetta', 'بڕۆشێتا', 'Tost ekmek üzerine domates', 'Tomato on toasted bread', 'طماطم على خبز محمص', 'Bacanaş li ser nanê biraştî', 'باژەنگ لەسەر نانی براژت', 18.00, 8, 0, true, true, false, false, 120, 'Italy', true),
('Minestrone', 'Minestrone', 'مينسترون', 'Minestrone', 'مینەسترۆنە', 'Sebze çorbası', 'Vegetable soup', 'حساء خضار', 'Şorbaya sebzeyan', 'شۆربای سەوزەوات', 28.00, 8, 0, true, true, true, true, 200, 'Italy', true);

-- Çin Mutfağı (Kategori 9) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular) VALUES
('Kung Pao Tavuk', 'Kung Pao Chicken', 'دجاج كونغ باو', 'Mirîşka Kung Pao', 'مریشکی کۆنگ پاو', 'Acılı tavuk yemeği', 'Spicy chicken dish', 'طبق دجاج حار', 'Xwarina mirîşk ya tûj', 'خواردنی مریشک تۆژ', 42.00, 9, 3, false, false, true, true, 380, 'China', true),
('Tavuklu Noodle', 'Chicken Noodles', 'نودلز دجاج', 'Noodle bi Mirîşk', 'نۆدڵ بە مریشک', 'Tavuklu erişte', 'Chicken noodles', 'نودلز دجاج', 'Noodle bi mirîşk', 'نۆدڵ بە مریشک', 35.00, 9, 1, false, false, false, true, 320, 'China', true),
('Sebzeli Noodle', 'Vegetable Noodles', 'نودلز خضار', 'Noodle bi Sebzeyan', 'نۆدڵ بە سەوزەوات', 'Sebzeli erişte', 'Vegetable noodles', 'نودلز خضار', 'Noodle bi sebzeyan', 'نۆدڵ بە سەوزەوات', 28.00, 9, 0, true, true, false, true, 280, 'China', true),
('Peking Ördeği', 'Peking Duck', 'بطة بكين', 'Mîra Pekîng', 'میرای پەکینگ', 'Pekin ördeği', 'Peking duck', 'بطة بكين', 'Mîra Pekîng', 'میرای پەکینگ', 65.00, 9, 0, false, false, true, true, 450, 'China', true),
('Dim Sum', 'Dim Sum', 'ديم سوم', 'Dim Sum', 'دیم سۆم', 'Buharda pişmiş hamur işi', 'Steamed dumplings', 'زلابية مطبوخة بالبخار', 'Xwarina hevîrê biharî', 'خواردنی هەویری بەهار', 25.00, 9, 0, false, false, false, true, 200, 'China', true),
('Wonton Çorbası', 'Wonton Soup', 'حساء وونتون', 'Şorbaya Wonton', 'شۆربای ۆنتۆن', 'Wonton çorbası', 'Wonton soup', 'حساء وونتون', 'Şorbaya wonton', 'شۆربای ۆنتۆن', 30.00, 9, 0, false, false, false, true, 180, 'China', true),
('Kızarmış Pirinç', 'Fried Rice', 'أرز مقلي', 'Birincê Sorkirî', 'برنجی سۆرکر', 'Kızarmış pirinç', 'Fried rice', 'أرز مقلي', 'Birincê sorkirî', 'برنجی سۆرکر', 22.00, 9, 0, true, true, true, true, 250, 'China', true),
('Mapo Tofu', 'Mapo Tofu', 'ماپو توفو', 'Mapo Tofu', 'ماپۆ تۆفو', 'Acılı tofu yemeği', 'Spicy tofu dish', 'طبق توفو حار', 'Xwarina tofu ya tûj', 'خواردنی تۆفو تۆژ', 32.00, 9, 3, true, true, true, true, 220, 'China', true);

-- Hint Mutfağı (Kategori 10) - 8 ürün
INSERT INTO products (name, name_en, name_ar, name_ku, name_sr, description, description_en, description_ar, description_ku, description_sr, price, category_id, spice_level, is_vegetarian, is_vegan, is_gluten_free, is_hot, calories, origin_country, popular) VALUES
('Butter Chicken', 'Butter Chicken', 'دجاج بالزبدة', 'Mirîşka Rûnê', 'مریشکی ڕوون', 'Tereyağlı tavuk', 'Butter chicken', 'دجاج بالزبدة', 'Mirîşka rûnê', 'مریشکی ڕوون', 45.00, 10, 2, false, false, true, true, 420, 'India', true),
('Tandoori Tavuk', 'Tandoori Chicken', 'دجاج تندوري', 'Mirîşka Tandoorî', 'مریشکی تەندۆری', 'Tandoor fırınında tavuk', 'Tandoor oven chicken', 'دجاج تندوري', 'Mirîşka firûnê tandoor', 'مریشکی فیرۆنی تەندۆر', 48.00, 10, 2, false, false, true, true, 380, 'India', true),
('Biryani', 'Biryani', 'برياني', 'Biryani', 'بیرانی', 'Baharatlı pirinç yemeği', 'Spiced rice dish', 'أرز بالبهارات', 'Xwarina birincê biharat', 'خواردنی برنج بەهارات', 38.00, 10, 2, false, false, true, true, 450, 'India', true),
('Palak Paneer', 'Palak Paneer', 'بالاك بانير', 'Palak Paneer', 'پاڵاک پانێر', 'Ispanaklı peynir', 'Spinach with cheese', 'سبانخ بالجبن', 'Sipînaş bi penîr', 'سپیناش بە پەنیر', 32.00, 10, 1, true, false, true, true, 280, 'India', true),
('Dal Makhani', 'Dal Makhani', 'دال مخاني', 'Dal Makhani', 'داڵ مەخانی', 'Mercimek yemeği', 'Lentil dish', 'طبق عدس', 'Xwarina nîsk', 'خواردنی نیسک', 28.00, 10, 1, true, true, true, true, 250, 'India', true),
('Naan', 'Naan', 'نان', 'Naan', 'نان', 'Hint ekmeği', 'Indian bread', 'خبز هندي', 'Nana Hindî', 'نانی هیندی', 8.00, 10, 0, true, true, false, true, 120, 'India', true),
('Raita', 'Raita', 'رايتا', 'Raita', 'ڕایەتا', 'Yoğurtlu sos', 'Yogurt sauce', 'صلصة زبادي', 'Sosa mast', 'سۆسای مەست', 12.00, 10, 0, true, true, true, false, 80, 'India', true),
('Gulab Jamun', 'Gulab Jamun', 'غولاب جامون', 'Gulab Jamun', 'گوڵاب جامون', 'Hint tatlısı', 'Indian dessert', 'حلويات هندية', 'Şîrînîya Hindî', 'شیرینی هیندی', 18.00, 10, 0, true, true, false, false, 200, 'India', true); 