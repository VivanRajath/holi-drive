#!/usr/bin/env node
import { put } from "@vercel/blob";
import fs from "fs";

// Usage: node upload_blob.js <localPath> <destPath> [access]
// destPath is e.g. "certificates/12345.png" or "certificate/12345.html"
// access defaults to 'public' but can be 'private' etc.

const [,, localPath, destPath] = process.argv;
// access default comes from env var or argument
let access = process.argv[4] || process.env.BLOB_STORE_ACCESS || 'public';
if (!localPath || !destPath) {
  console.error('Usage: upload_blob.js <localPath> <destPath> [access]');
  process.exit(1);
}

async function main() {
  const data = fs.readFileSync(localPath);
  const { url } = await put(destPath, data, { access });
  process.stdout.write(url);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});