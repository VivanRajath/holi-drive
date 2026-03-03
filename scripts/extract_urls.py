import re, pathlib
text = pathlib.Path('node_modules/@vercel/blob/dist/chunk-Z56QURM6.js').read_text()
for m in re.finditer(r'https?://[^"\']+', text):
    if 'vercel' in m.group(0):
        print(m.group(0))

