import os
import urllib.request
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from products.models import Category, Product

class Command(BaseCommand):
    help = "Populate the database with sample categories and products, downloading images from the web"

    # Sample data; replace URLs with real images as needed
    CATEGORIES = [
        {
            "image_url": "https://picsum.photos/seed/fruits/400/400",
            "slug": "fruits",
            "name": "Fruits",
        },
        {
            "image_url": "https://picsum.photos/seed/vegetables/400/400",
            "slug": "vegetables",
            "name": "Vegetables",",
            "slug": "vegetables",
            "name": "Vegetables",
        },

    ]

    PRODUCTS = [
        {
            "name": "Apple",
            "slug": "apple",
            "category": "Fruits",
            "description": "Fresh red apples.",
            "price": "2.99",
            "unit": "kg",
            "image_url": "https://via.placeholder.com/400?text=Apple",
            "in_stock": True,
            "stock_quantity": 150,
            "is_organic": True,
        },
        {
            "name": "Carrot",
            "slug": "carrot",
            "category": "Vegetables",
            "description": "Crunchy orange carrots.",
            "price": "1.50",
            "unit": "kg",
            "image_url": "https://via.placeholder.com/400?text=Carrot",
            "in_stock": True,
            "stock_quantity": 200,
            "is_organic": False,
        },
    ]

    def download_image(self, url):
        """Download an image from the given URL.

        Returns a ContentFile if successful, otherwise None.
        """
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                return ContentFile(response.read())
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to download image from {url}: {e}"))
            return None

    def handle(self, *args, **options):
        # Populate categories
        for cat_data in self.CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"], defaults={"slug": cat_data["slug"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category {category.name}"))
            # Update/Set image for category if download succeeded
            img_content = self.download_image(cat_data["image_url"])
            if img_content:
                filename = os.path.basename(cat_data["image_url"]).split("?")[0]
                category.image.save(filename, img_content, save=True)
            else:
                self.stdout.write(self.style.WARNING(f"Skipping image for category {category.name}"))

        # Populate products
        for prod_data in self.PRODUCTS:
            try:
                category = Category.objects.get(name=prod_data["category"])
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Category {prod_data['category']} not found, skipping product {prod_data['name']}"
                    )
                )
                continue
            product, created = Product.objects.get_or_create(
                name=prod_data["name"],
                defaults={
                    "slug": prod_data["slug"],
                    "category": category,
                    "description": prod_data["description"],
                    "price": prod_data["price"],
                    "unit": prod_data["unit"],
                    "in_stock": prod_data["in_stock"],
                    "stock_quantity": prod_data["stock_quantity"],
                    "is_organic": prod_data["is_organic"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product {product.name}"))
            # Update/Set image
            img_content = self.download_image(prod_data["image_url"])
            filename = os.path.basename(prod_data["image_url"]).split("?")[0]
            product.image.save(filename, img_content, save=True)

        self.stdout.write(self.style.SUCCESS("Database population complete."))
