"""One-time upload of existing local Product images to Cloudinary.

This command reads files from MEDIA_ROOT and uploads copies to Cloudinary.  It
never deletes local files.  Cloudinary returns a public ID, which is saved back
to Product.image so the deployed Cloudinary storage can resolve the image URL.
"""

from pathlib import Path

import cloudinary
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from products.models import Product


class Command(BaseCommand):
    help = "Upload existing local Product.image files to Cloudinary without deleting local files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List local files that would be uploaded without changing Cloudinary or the database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Upload at most this many images (use --limit 1 for a first test).",
        )

    def handle(self, *args, **options):
        if options["limit"] is not None and options["limit"] < 1:
            raise CommandError("--limit must be at least 1.")

        config = cloudinary.config()
        if not all((config.cloud_name, config.api_key, config.api_secret)):
            raise CommandError(
                "Cloudinary credentials are not configured. Add a real CLOUDINARY_URL to .env."
            )

        media_root = Path(settings.MEDIA_ROOT).resolve()
        products = Product.objects.exclude(image__isnull=True).exclude(image="").order_by("pk")
        if options["limit"]:
            products = products[: options["limit"]]

        total = products.count()
        if not total:
            self.stdout.write(self.style.SUCCESS("No product images to upload."))
            return

        storage = MediaCloudinaryStorage()
        uploaded = skipped = missing = failed = 0
        self.stdout.write(f"Processing {total} product image(s)...")

        for index, product in enumerate(products, start=1):
            original_name = product.image.name
            source_path = (media_root / original_name).resolve()

            # ImageField paths come from the database; do not allow a malformed
            # value to make the command read a file outside MEDIA_ROOT.
            if source_path != media_root and media_root not in source_path.parents:
                missing += 1
                self.stderr.write(
                    self.style.WARNING(f"[{index}/{total}] {product.name}: invalid image path")
                )
                continue

            if not source_path.is_file():
                # A previous test run stores Cloudinary's public ID in the
                # database. It no longer maps to a local path, so treat a
                # confirmed remote asset as already complete on reruns.
                try:
                    if storage.exists(original_name):
                        skipped += 1
                        self.stdout.write(
                            f"[{index}/{total}] {product.name}: already in Cloudinary"
                        )
                        continue
                except Exception:
                    pass
                missing += 1
                self.stderr.write(
                    self.style.WARNING(
                        f"[{index}/{total}] {product.name}: local file not found: {original_name}"
                    )
                )
                continue

            if options["dry_run"]:
                uploaded += 1
                self.stdout.write(f"[DRY RUN] {product.name}: {original_name}")
                continue

            try:
                with source_path.open("rb") as image_file:
                    cloud_name = storage.save(original_name, File(image_file))
                product.image.name = cloud_name
                product.save(update_fields=["image"])
                uploaded += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[{index}/{total}] {product.name}: {original_name} -> {cloud_name}"
                    )
                )
            except Exception as error:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(f"[{index}/{total}] {product.name}: {error}")
                )

        summary = (
            f"Finished: {uploaded} uploaded, {skipped} already present, "
            f"{missing} missing, {failed} failed."
        )
        if missing or failed:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
