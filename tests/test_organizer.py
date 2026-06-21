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
                    tags=("watch",),
                    metadata={"product_id": "watch-alpha", "collection": "watches"},
                )
            )
        for i in range(1, 11):
            photos.append(
                Photo(
                    id=f"b{i}",
                    path=f"collection/watch_beta_{i:02d}.jpg",
                    tags=("watch",),
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


if __name__ == "__main__":
    unittest.main()
