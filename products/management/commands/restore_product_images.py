"""Reconnect product image records to matching files in local media storage."""

import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = (
        "Reconnect product image records to matching files in MEDIA_ROOT/products "
        "without uploading them to Cloudinary."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report matching local files without changing product records.",
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT).resolve()
        products_dir = media_root / "products"
        products = (
            Product.objects.exclude(image__isnull=True)
            .exclude(image="")
            .order_by("pk")
        )
        restored = already_local = missing = ambiguous = 0

        for product in products:
            stored_name = Path(product.image.name).name
            current_path = (media_root / product.image.name).resolve()
            if media_root in current_path.parents and current_path.is_file():
                already_local += 1
                continue

            stem = Path(stored_name).stem
            original_stem = re.sub(r"_[a-z0-9]{6}$", "", stem)
            matches = (
                sorted(
                    path
                    for path in products_dir.iterdir()
                    if path.is_file() and path.stem == original_stem
                )
                if products_dir.is_dir()
                else []
            )
            if len(matches) != 1:
                if matches:
                    ambiguous += 1
                    self.stderr.write(
                        self.style.WARNING(
                            f"{product.name}: multiple local images match {stored_name}"
                        )
                    )
                else:
                    missing += 1
                    self.stderr.write(
                        self.style.WARNING(
                            f"{product.name}: no local image matches {stored_name}"
                        )
                    )
                continue

            image_name = f"products/{matches[0].name}"
            if not options["dry_run"]:
                product.image.name = image_name
                product.save(update_fields=["image"])
            restored += 1
            self.stdout.write(f"{product.name}: {image_name}")

        summary = (
            f"Finished: {restored} {'would be restored' if options['dry_run'] else 'restored'}, "
            f"{already_local} already local, {missing} missing, {ambiguous} ambiguous."
        )
        if missing or ambiguous:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
