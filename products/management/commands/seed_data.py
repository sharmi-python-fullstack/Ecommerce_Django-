from django.core.management.base import BaseCommand
from products.models import Category, Product
from orders.models import Coupon


class Command(BaseCommand):
    help = 'Seed categories, products and coupons'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        categories_data = [
            {'name': 'Fresh Vegetables', 'slug': 'fresh-vegetables'},
            {'name': 'Fresh Fruits', 'slug': 'fresh-fruits'},
            {'name': 'Exotics', 'slug': 'exotics'},
            {'name': 'Green Leafy Veggies', 'slug': 'green-leafy-veggies'},
            {'name': 'Sprouts', 'slug': 'sprouts'},
            {'name': 'Organics', 'slug': 'organics'},
            {'name': 'Seasonal', 'slug': 'seasonal'},
            {'name': 'Frozen Veggies', 'slug': 'frozen-veggies'},
        ]

        categories = {}
        for cat in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat['slug'], defaults={'name': cat['name']}
            )
            categories[cat['slug']] = category
            if created:
                self.stdout.write(f'Created category: {cat["name"]}')

        products_data = [
            # Fresh Vegetables
            ('Tomato', 'fresh-vegetables', 40.00, 'kg', 'Farm fresh red tomatoes, juicy and ripe.', False),
            ('Onion', 'fresh-vegetables', 35.00, 'kg', 'Fresh pink onions, essential for every kitchen.', False),
            ('Potato', 'fresh-vegetables', 30.00, 'kg', 'High quality potatoes, perfect for all dishes.', False),
            ('Carrot', 'fresh-vegetables', 45.00, 'kg', 'Crunchy orange carrots rich in vitamin A.', False),
            ('Capsicum', 'fresh-vegetables', 60.00, 'kg', 'Fresh green capsicums, crisp and flavorful.', False),
            ('Cucumber', 'fresh-vegetables', 25.00, 'kg', 'Cool and refreshing cucumbers.', False),
            ('Lady Finger (Okra)', 'fresh-vegetables', 50.00, 'kg', 'Tender okra, great for curries and fries.', False),
            ('Cauliflower', 'fresh-vegetables', 55.00, 'pc', 'Fresh white cauliflower, firm and clean.', False),

            # Fresh Fruits
            ('Apple', 'fresh-fruits', 180.00, 'kg', 'Crispy red apples, sweet and juicy.', False),
            ('Banana', 'fresh-fruits', 50.00, 'dozen', 'Fresh ripe bananas, rich in potassium.', False),
            ('Orange', 'fresh-fruits', 80.00, 'kg', 'Juicy oranges loaded with vitamin C.', False),
            ('Mango', 'fresh-fruits', 120.00, 'kg', 'Sweet and fragrant mangoes, king of fruits.', False),
            ('Grapes', 'fresh-fruits', 90.00, 'kg', 'Seedless green grapes, sweet and tangy.', False),
            ('Pomegranate', 'fresh-fruits', 150.00, 'kg', 'Fresh pomegranates with juicy red seeds.', False),
            ('Papaya', 'fresh-fruits', 60.00, 'pc', 'Ripe papaya, rich in antioxidants.', False),
            ('Watermelon', 'fresh-fruits', 40.00, 'kg', 'Refreshing watermelon, perfect for summer.', False),

            # Exotics
            ('Avocado', 'exotics', 200.00, 'pc', 'Creamy and nutritious avocado.', False),
            ('Blueberries', 'exotics', 600.00, '250g', 'Antioxidant-rich fresh blueberries.', False),
            ('Dragon Fruit', 'exotics', 180.00, 'pc', 'Exotic dragon fruit with sweet mild flavor.', False),
            ('Kiwi', 'exotics', 160.00, 'kg', 'Tangy and vitamin-rich kiwis.', False),
            ('Cherries', 'exotics', 500.00, '500g', 'Sweet and juicy red cherries.', False),
            ('Litchi', 'exotics', 120.00, 'kg', 'Sweet and fragrant litchis.', False),

            # Green Leafy Veggies
            ('Spinach (Palak)', 'green-leafy-veggies', 30.00, 'bunch', 'Fresh spinach leaves, rich in iron.', False),
            ('Coriander', 'green-leafy-veggies', 25.00, 'bunch', 'Aromatic fresh coriander leaves.', False),
            ('Mint (Pudina)', 'green-leafy-veggies', 30.00, 'bunch', 'Refreshing fresh mint leaves.', False),
            ('Lettuce', 'green-leafy-veggies', 70.00, 'pc', 'Crispy lettuce for salads.', False),
            ('Fenugreek (Methi)', 'green-leafy-veggies', 35.00, 'bunch', 'Fresh fenugreek leaves, slightly bitter.', False),
            ('Amaranth (Chaulai)', 'green-leafy-veggies', 30.00, 'bunch', 'Nutritious amaranth greens.', False),

            # Sprouts
            ('Moong Sprouts', 'sprouts', 60.00, '500g', 'Fresh and crunchy moong sprouts.', False),
            ('Chana Sprouts', 'sprouts', 55.00, '500g', 'Protein-rich chickpea sprouts.', False),
            ('Mixed Sprouts', 'sprouts', 70.00, '500g', 'Nutritious mix of various sprouts.', False),
            ('Alfalfa Sprouts', 'sprouts', 80.00, '200g', 'Delicate and healthy alfalfa sprouts.', False),

            # Organics
            ('Organic Tomato', 'organics', 70.00, 'kg', '100% organic tomatoes, no chemicals.', True),
            ('Organic Onion', 'organics', 60.00, 'kg', 'Certified organic onions.', True),
            ('Organic Potato', 'organics', 55.00, 'kg', 'Organically grown potatoes.', True),
            ('Organic Spinach', 'organics', 50.00, 'bunch', 'Pesticide-free organic spinach.', True),
            ('Organic Carrot', 'organics', 80.00, 'kg', 'Organic carrots, naturally sweet.', True),
            ('Organic Apple', 'organics', 280.00, 'kg', 'Fresh organic apples.', True),

            # Seasonal
            ('Guava', 'seasonal', 60.00, 'kg', 'Seasonal sweet guavas.', False),
            ('Sapota (Chikoo)', 'seasonal', 70.00, 'kg', 'Sweet and soft seasonal sapota.', False),
            ('Pear', 'seasonal', 140.00, 'kg', 'Juicy seasonal pears.', False),
            ('Plum', 'seasonal', 100.00, 'kg', 'Tangy seasonal plums.', False),
            ('Jackfruit', 'seasonal', 50.00, 'kg', 'Fresh seasonal jackfruit pieces.', False),
            ('Custard Apple', 'seasonal', 150.00, 'kg', 'Sweet and creamy custard apples.', False),

            # Frozen Veggies
            ('Frozen Peas', 'frozen-veggies', 90.00, '500g', 'Quick-frozen sweet green peas.', False),
            ('Frozen Corn', 'frozen-veggies', 85.00, '500g', 'Frozen sweet corn kernels.', False),
            ('Frozen Mixed Veggies', 'frozen-veggies', 120.00, '500g', 'Mix of carrots, beans, peas and corn.', False),
            ('Frozen Baby Corn', 'frozen-veggies', 110.00, '500g', 'Tender frozen baby corn.', False),
            ('Frozen French Fries', 'frozen-veggies', 100.00, '500g', 'Crispy frozen french fries.', False),
            ('Frozen Spinach', 'frozen-veggies', 80.00, '500g', 'Flash-frozen spinach blocks.', False),
        ]

        for name, cat_slug, price, unit, desc, is_organic in products_data:
            slug = name.lower().replace('(', '').replace(')', '').replace(' ', '-').replace('/', '-')
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': categories[cat_slug],
                    'price': price,
                    'unit': unit,
                    'description': desc,
                    'is_organic': is_organic,
                    'in_stock': True,
                    'stock_quantity': 100,
                }
            )
            if created:
                self.stdout.write(f'Created product: {name}')

        # Coupons
        coupons_data = [
            {'code': 'WELCOME10', 'description': '10% off on your first order', 'discount_percent': 10, 'min_order_amount': 0},
            {'code': 'SAVE50', 'description': 'Flat ₹50 off', 'discount_amount': 50, 'min_order_amount': 300},
            {'code': 'FRESH20', 'description': '20% off above ₹500', 'discount_percent': 20, 'min_order_amount': 500},
            {'code': 'VEGGIE100', 'description': 'Flat ₹100 off above ₹700', 'discount_amount': 100, 'min_order_amount': 700},
        ]
        for coupon_data in coupons_data:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )
            if created:
                self.stdout.write(f'Created coupon: {coupon_data["code"]}')

        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))
