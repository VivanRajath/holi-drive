# LCC Holi Drive

This project generates participation badges and allows users to share them.

## Setup

### Python

Install dependencies:
```powershell
python -m venv venv
& venv\Scripts\activate.ps1
pip install -r requirements.txt
```

### Node (for Vercel Blob storage)

The API optionally uses Vercel Blob for persistent storage. If you want to
store certificates in Vercel Blob, install the Node helper:

```bash
cd holi-drive
npm install          # or yarn install
```

If `USE_BLOB` is set in the environment the API will upload generated badge
images and certificate HTML pages to blob storage and return the blob URL.
Blob operations are handled by `upload_blob.js` using `@vercel/blob`.

By default the helper writes with `public` access so generated badges can be
shared. If your Vercel Blob store is configured as private set the environment
variable `BLOB_STORE_ACCESS=private` (or supply the access as the third
argument to `upload_blob.js`).

> **Note:** you must provide a Vercel Blob token in `BLOB_READ_WRITE_TOKEN` (the
> name expected by `@vercel/blob`) when running locally or in production.
> Without a token, the helper will fail during upload.
## Environment Variables

- `USE_BLOB` (any value) — enable blob uploads; requires Node dependencies.
- `STORAGE_DIR` — where to place files when not using blob (default `/tmp` on
  Vercel, `public` in local dev if writable).
- `SITE_ORIGIN` — absolute origin used when constructing share URLs (e.g.
  `https://your-domain.vercel.app`).
- SMTP env vars for email sending.

## Running Locally

```powershell
python dev_server.py
```

Submit the form at http://localhost:8000 to test badge generation; look in
`public/certificates` and `public/certificate` for files.

When `USE_BLOB` is enabled, the handler will call `node upload_blob.js` to
upload to Vercel Blob, so you must run `npm install` first.
