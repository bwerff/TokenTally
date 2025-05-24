# Receipt Processor (archived)

This lightweight service performs OCR on uploaded receipt images. It was
originally used for matching lines against promotional offers but is no longer
maintained as part of the TokenTally gateway.

### Running the server

```bash
python3 -m receipt_processor.service
```

Receipts can be uploaded via `POST /upload` with a `multipart/form-data` body
containing the image field named `file`.
