"""Download Pixabay images for products that do not yet have an image.

The command deliberately uses Django's ``ImageField.save()`` instead of writing
files directly.  That keeps the file location in sync with the configured media
storage, including the default ``MEDIA_ROOT/products/`` location.
"""

import json
import mimetypes
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.text import slugify

from products.models import Product


PIXABAY_SEARCH_URL = "https://pixabay.com/api/"
MAX_IMAGE_BYTES = 20 * 1024 * 1024  # Do not accidentally save an oversized file.

# Preserve familiar store names while searching with terms that photo libraries
# are more likely to understand. Keys are case-insensitive.
SEARCH_ALIASES = {
    "amaranth (chaulai)": "amaranth leaves",
    "mint (pudina)": "mint leaves",
    "sapota (chikoo)": "sapodilla fruit",
    "spinach (palak)": "spinach leaves",
}


class Command(BaseCommand):
    help = (
        "Download a Pixabay image for every product whose image field is empty. "
        "Requires a PIXABAY_API_KEY environment variable or --api-key."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--api-key",
            help="Pixabay API key. Prefer setting the PIXABAY_API_KEY environment variable.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Replace images that are already set as well as empty image fields.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Process at most this many products (useful for a small test run).",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.30,
            help="Seconds to wait between products (default: 0.30).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Search Pixabay and report proposed matches without saving files or database changes.",
        )

    def handle(self, *args, **options):
        api_key = options["api_key"] or os.environ.get("PIXABAY_API_KEY")
        if not api_key:
            raise CommandError(
                "A Pixabay API key is required. Set PIXABAY_API_KEY or pass --api-key. "
                "Create a free key at https://pixabay.com/api/docs/."
            )

        if options["limit"] is not None and options["limit"] < 1:
            raise CommandError("--limit must be at least 1.")
        if options["delay"] < 0:
            raise CommandError("--delay cannot be negative.")

        products = Product.objects.all().order_by("pk")
        if not options["force"]:
            products = products.filter(Q(image__isnull=True) | Q(image=""))
        if options["limit"]:
            products = products[: options["limit"]]

        product_count = products.count()
        if not product_count:
            self.stdout.write(self.style.SUCCESS("No products need images."))
            return

        self.stdout.write(f"Processing {product_count} product(s)...")
        saved = failed = 0
        for index, product in enumerate(products, start=1):
            try:
                image = self.search_image(product.name, api_key)
                if image is None:
                    raise ValueError("Pixabay returned no matching images")

                image_url = self.image_url(image)
                if options["dry_run"]:
                    self.stdout.write(
                        f"[DRY RUN] {product.name}: Pixabay image {image['id']} — {image_url}"
                    )
                    saved += 1
                    continue

                content, extension = self.download_image(image_url)
                file_name = self.file_name(product, image["id"], extension)
                product.image.save(file_name, content, save=False)
                product.save(update_fields=["image"])
                saved += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{index}/{product_count}] {product.name} -> {product.image.name} "
                        f"(Pixabay image {image['id']})"
                    )
                )
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError, OSError) as error:
                failed += 1
                self.stderr.write(
                    self.style.WARNING(f"[{index}/{product_count}] {product.name}: {error}")
                )

            if index < product_count and options["delay"]:
                time.sleep(options["delay"])

        summary = f"Finished: {saved} saved, {failed} failed."
        if failed:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))

    def search_image(self, product_name, api_key):
        """Return the best Pixabay search result for a product name, if one exists."""
        search_term = SEARCH_ALIASES.get(product_name.casefold(), product_name)
        # Parenthetical local-language aliases make weak search terms. For names
        # without a dedicated mapping, search the primary product name instead.
        search_term = re.sub(r"\s*\([^)]*\)", "", search_term).strip()
        query = urlencode(
            {
                # The extra terms favor clean e-commerce-style food photography.
                "key": api_key,
                "q": f"{search_term} fresh food",
                "image_type": "photo",
                "safesearch": "true",
                "order": "popular",
                # Pixabay requires a value from 3 through 200.  We only use
                # the first result, but must request the minimum valid page.
                "per_page": 3,
            }
        )
        request = Request(
            f"{PIXABAY_SEARCH_URL}?{query}",
            headers={
                "Accept": "application/json",
                "User-Agent": "VegFruitStoreImageImporter/1.0",
            },
        )
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        images = payload.get("hits", [])
        return images[0] if images else None

    @staticmethod
    def image_url(image):
        # The standard API returns largeImageURL when available (roughly 1280 px)
        # and webformatURL otherwise (roughly 640 px), both ample for product cards.
        return image.get("largeImageURL") or image["webformatURL"]

    @staticmethod
    def download_image(image_url):
        request = Request(
            image_url,
            headers={
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "User-Agent": "VegFruitStoreImageImporter/1.0",
            },
        )
        with urlopen(request, timeout=60) as response:
            content_type = response.headers.get_content_type()
            if not content_type.startswith("image/"):
                raise ValueError(f"Expected an image, received {content_type}")
            data = response.read(MAX_IMAGE_BYTES + 1)

        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("Image is larger than 20 MB")

        extension = mimetypes.guess_extension(content_type) or ".jpg"
        # FileSystemStorage and browsers handle .jpg consistently for JPEGs.
        if extension == ".jpe":
            extension = ".jpg"
        return ContentFile(data), extension

    @staticmethod
    def file_name(product, image_id, extension):
        safe_name = slugify(product.name) or "product"
        return f"{safe_name}-{product.pk}-pixabay-{image_id}{extension}"
