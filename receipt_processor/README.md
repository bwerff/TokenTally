# Receipt Processor Microservice

This service performs basic OCR on uploaded receipt images, matches line items to
known offers and stores redemption records. Any receipt lines that do not match
an offer are logged for manual review.

### Running the server

```bash
python3 -m receipt_processor.service
```

Receipts can be uploaded via `POST /upload` with a `multipart/form-data` body
containing the image field named `file`.
