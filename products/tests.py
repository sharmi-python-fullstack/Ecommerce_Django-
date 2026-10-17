from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings

from products.models import Category, Product


class SeedDataCommandTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        products_dir = Path(self.media_dir.name) / "products"
        products_dir.mkdir()
        (products_dir / "apple-9-pixabay-2788599.jpg").write_bytes(b"image")

    def test_seeds_products_with_matching_local_images_idempotently(self):
        for _ in range(2):
            call_command("seed_data", stdout=StringIO(), stderr=StringIO())

        apple = Product.objects.get(slug="apple")
        self.assertEqual(apple.image.name, "products/apple-9-pixabay-2788599.jpg")
        self.assertEqual(Product.objects.count(), 50)


class RestoreProductImagesCommandTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

        self.category = Category.objects.create(name="Fruit", slug="fruit")
        products_dir = Path(self.media_dir.name) / "products"
        products_dir.mkdir()
        (products_dir / "apple-9-pixabay-2788599.jpg").write_bytes(b"image")
        self.product = Product.objects.create(
            name="Apple",
            slug="apple",
            category=self.category,
            price="1.00",
            image="media/products/apple-9-pixabay-2788599_gdujyo",
        )

    def test_restores_cloudinary_style_name_to_local_media_path(self):
        call_command("restore_product_images")

        self.product.refresh_from_db()
        self.assertEqual(
            self.product.image.name,
            "products/apple-9-pixabay-2788599.jpg",
        )

    def test_dry_run_does_not_change_product_image(self):
        call_command("restore_product_images", "--dry-run")

        self.product.refresh_from_db()
        self.assertEqual(
            self.product.image.name,
            "media/products/apple-9-pixabay-2788599_gdujyo",
        )
