import unittest

from organizer import Organizer, Photo


class OrganizerTests(unittest.TestCase):
    def test_analyzes_product_photo_and_generates_listing_fields(self) -> None:
        organizer = Organizer()
        organizer.inject_photostream(
            [
                Photo(
                    id="p1",
                    path="stream/watch_alpha_01.jpg",
                    tags=("watch", "product"),
                    metadata={
                        "product_id": "watch-alpha",
                        "category": "watch",
                        "price": "499.99",
                        "brand": "Arcadia",
                    },
                )
            ]
        )

        analysis = organizer.analyze_photos()["p1"]

        self.assertTrue(analysis.is_product_photo)
        self.assertEqual(analysis.title, "Watch Alpha 01")
        self.assertEqual(analysis.description, "watch photo: Watch Alpha 01")
        self.assertEqual(analysis.price, 499.99)
        self.assertEqual(analysis.attributes["brand"], "Arcadia")

    def test_zero_price_is_preserved(self) -> None:
        organizer = Organizer()
        organizer.inject_photostream(
            [
                Photo(
                    id="p0",
                    path="stream/free_sample.jpg",
                    tags=("product",),
                    metadata={"price": 0, "product_id": "free-sample"},
                )
            ]
        )

        analysis = organizer.analyze_photos()["p0"]
        self.assertEqual(analysis.price, 0.0)
        self.assertTrue(analysis.is_product_photo)

    def test_float_zero_price_is_preserved(self) -> None:
        organizer = Organizer()
        organizer.inject_photostream(
            [Photo(id="p0f", path="stream/free_float.jpg", metadata={"price": 0.0})]
        )
        analysis = organizer.analyze_photos()["p0f"]
        self.assertEqual(analysis.price, 0.0)
        self.assertTrue(analysis.is_product_photo)

    def test_invalid_price_string_falls_back_to_none(self) -> None:
        organizer = Organizer()
        organizer.inject_photostream(
            [
                Photo(
                    id="p-bad",
                    path="stream/item_bad_price.jpg",
                    tags=("product",),
                    metadata={"price": "not-a-number"},
                )
            ]
        )
        analysis = organizer.analyze_photos()["p-bad"]
        self.assertIsNone(analysis.price)

    def test_groups_multiple_images_and_keeps_common_characteristics(self) -> None:
        organizer = Organizer()
        organizer.inject_photostream(
            [
                Photo(
                    id="a1",
                    path="watches/watch_alpha_01.jpg",
                    metadata={
                        "product_id": "watch-alpha",
                        "brand": "Arcadia",
                        "color": "black",
                    },
                ),
                Photo(
                    id="a2",
                    path="watches/watch_alpha_02.jpg",
                    metadata={
                        "product_id": "watch-alpha",
                        "brand": "Arcadia",
                        "color": "black",
                    },
                ),
            ]
        )

        groups = organizer.group_alike_photos()
        alpha_group = next(group for group in groups if group.name == "watch-alpha")

        self.assertEqual(set(alpha_group.image_ids), {"a1", "a2"})
        self.assertEqual(alpha_group.common_attributes["brand"], "Arcadia")
        self.assertEqual(alpha_group.common_attributes["color"], "black")

    def test_nested_watch_collection_with_4_to_10_photos_per_watch(self) -> None:
        organizer = Organizer()
        photos = []
        for i in range(1, 5):
            photos.append(
                Photo(
                    id=f"a{i}",
                    path=f"collection/watch_alpha_{i:02d}.jpg",
                    tags=("product", "watch"),
                    metadata={"product_id": "watch-alpha", "collection": "watches"},
                )
            )
        for i in range(1, 11):
            photos.append(
                Photo(
                    id=f"b{i}",
                    path=f"collection/watch_beta_{i:02d}.jpg",
                    tags=("product", "watch"),
                    metadata={"product_id": "watch-beta", "collection": "watches"},
                )
            )
        organizer.inject_photostream(photos)

        collection = organizer.create_product_groups("watches", min_images=4, max_images=10)

        self.assertEqual(collection.name, "watches")
        self.assertEqual(len(collection.children), 2)
        group_sizes = {child.name: len(child.image_ids) for child in collection.children}
        self.assertEqual(group_sizes["watch-alpha"], 4)
        self.assertEqual(group_sizes["watch-beta"], 10)

    def test_numeric_suffix_without_separator_is_not_trimmed(self) -> None:
        organizer = Organizer()
        organizer.inject_photostream(
            [
                Photo(id="m1", path="models/model2000.jpg", tags=("product",)),
                Photo(id="m2", path="models/model2000_variant.jpg", tags=("product",)),
            ]
        )
        groups = organizer.group_alike_photos()
        names_to_ids = {group.name: set(group.image_ids) for group in groups}
        self.assertEqual(names_to_ids["model2000"], {"m1"})
        self.assertEqual(names_to_ids["model2000_variant"], {"m2"})

    def test_custom_product_keywords_are_supported(self) -> None:
        organizer = Organizer(product_keywords={"shoe"})
        organizer.inject_photostream(
            [Photo(id="s1", path="stream/shoe_01.jpg", tags=(), metadata={"product_id": "shoe-01"})]
        )
        analysis = organizer.analyze_photos()["s1"]
        self.assertTrue(analysis.is_product_photo)


if __name__ == "__main__":
    unittest.main()
