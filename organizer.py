from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re


@dataclass(frozen=True)
class Photo:
    id: str
    path: str
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PhotoAnalysis:
    photo_id: str
    is_product_photo: bool
    title: str
    description: str
    price: float | None
    attributes: dict[str, Any]


@dataclass
class PhotoGroup:
    name: str
    image_ids: list[str] = field(default_factory=list)
    common_attributes: dict[str, Any] = field(default_factory=dict)
    children: list["PhotoGroup"] = field(default_factory=list)


class Organizer:
    DEFAULT_PRODUCT_KEYWORDS = {"product", "catalog", "listing", "item"}

    def __init__(self, product_keywords: set[str] | None = None) -> None:
        self._photos: list[Photo] = []
        self._product_keywords = {
            keyword.lower() for keyword in (product_keywords or self.DEFAULT_PRODUCT_KEYWORDS)
        }

    def inject_photostream(self, photos: list[Photo]) -> None:
        self._photos.extend(photos)

    def analyze_photos(self) -> dict[str, PhotoAnalysis]:
        return {photo.id: self._analyze_photo(photo) for photo in self._photos}

    def group_alike_photos(self) -> list[PhotoGroup]:
        grouped: dict[str, list[Photo]] = {}
        for photo in self._photos:
            key = self._group_key(photo)
            grouped.setdefault(key, []).append(photo)

        groups: list[PhotoGroup] = []
        for key, photos in grouped.items():
            groups.append(
                PhotoGroup(
                    name=key,
                    image_ids=[photo.id for photo in photos],
                    common_attributes=self._common_attributes(photos),
                )
            )
        return groups

    def create_product_groups(
        self, collection_name: str, min_images: int = 1, max_images: int = 10
    ) -> PhotoGroup:
        analysis_by_photo_id = self.analyze_photos()
        product_photos = [p for p in self._photos if analysis_by_photo_id[p.id].is_product_photo]
        per_product: dict[str, list[Photo]] = {}
        for photo in product_photos:
            per_product.setdefault(self._product_id(photo), []).append(photo)

        children: list[PhotoGroup] = []
        for product_id, photos in per_product.items():
            if min_images <= len(photos) <= max_images:
                children.append(
                    PhotoGroup(
                        name=product_id,
                        image_ids=[photo.id for photo in photos],
                        common_attributes=self._common_attributes(photos),
                    )
                )

        return PhotoGroup(
            name=collection_name,
            image_ids=[],
            common_attributes={"collection": collection_name},
            children=children,
        )

    def create_product_listings(
        self, min_images: int = 1, max_images: int = 10
    ) -> list[PhotoAnalysis]:
        analysis_by_photo_id = self.analyze_photos()
        collection = self.create_product_groups(
            collection_name="products", min_images=min_images, max_images=max_images
        )
        listings: list[PhotoAnalysis] = []
        for item_group in collection.children:
            if not item_group.image_ids:
                continue
            analyzed = analysis_by_photo_id[item_group.image_ids[0]]
            listings.append(
                PhotoAnalysis(
                    photo_id=analyzed.photo_id,
                    is_product_photo=True,
                    title=analyzed.title,
                    description=analyzed.description,
                    price=analyzed.price,
                    attributes={
                        **item_group.common_attributes,
                        "image_ids": item_group.image_ids,
                    },
                )
            )
        return listings

    def _analyze_photo(self, photo: Photo) -> PhotoAnalysis:
        parsed_price = self._parse_price(photo.metadata.get("price"))
        is_product = self._is_product_photo(photo, parsed_price=parsed_price)
        name = Path(photo.path).stem.replace("_", " ")
        title = str(photo.metadata.get("title") or name).strip().title()

        category = photo.metadata.get("category", "general")
        description = str(photo.metadata.get("description") or f"{category} photo: {title}")

        price = parsed_price

        optional_attrs = {
            key: value
            for key, value in photo.metadata.items()
            if key not in {"title", "description", "price"}
        }

        return PhotoAnalysis(
            photo_id=photo.id,
            is_product_photo=is_product,
            title=title,
            description=description,
            price=price,
            attributes=optional_attrs,
        )

    def _is_product_photo(self, photo: Photo, parsed_price: float | None = None) -> bool:
        tag_set = {tag.lower() for tag in photo.tags}
        price = parsed_price if parsed_price is not None else self._parse_price(photo.metadata.get("price"))
        has_price = price is not None
        filename = Path(photo.path).stem.lower()
        filename_tokens = {
            token for token in re.split(r"[^a-z0-9]+", filename) if token
        }
        has_keyword_tag = any(tag in self._product_keywords for tag in tag_set)
        has_keyword_filename = any(token in self._product_keywords for token in filename_tokens)
        return has_price or has_keyword_tag or has_keyword_filename

    def _group_key(self, photo: Photo) -> str:
        return str(photo.metadata.get("group") or self._product_id(photo))

    def _product_id(self, photo: Photo) -> str:
        if photo.metadata.get("product_id"):
            return str(photo.metadata["product_id"])
        stem = Path(photo.path).stem.lower()
        # Trim sequence suffixes like "_1" or "-12", but keep embedded numbers (e.g. "model2000").
        return re.sub(r"[_-]\d+$", "", stem)

    def _common_attributes(self, photos: list[Photo]) -> dict[str, Any]:
        if not photos:
            return {}
        common = dict(photos[0].metadata or {})
        for photo in photos[1:]:
            metadata = photo.metadata or {}
            common = {
                key: value
                for key, value in common.items()
                if key in metadata and metadata[key] == value
            }
        return common

    def _parse_price(self, raw_price: Any) -> float | None:
        if isinstance(raw_price, (int, float)):
            return float(raw_price)
        if isinstance(raw_price, str) and raw_price.strip() != "":
            try:
                return float(raw_price)
            except ValueError:
                return None
        return None
