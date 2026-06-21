# file-document-photo-video-organizer

Minimal organizer logic for file/document/photo/video workflows focused on:

- injecting a photo stream
- analyzing photos and identifying product photos
- generating title/description/price (+ optional attributes)
- grouping similar photos
- storing shared characteristics for grouped photos
- nested groups (groups within groups), such as a watch collection where each watch has 4-10 photos

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
