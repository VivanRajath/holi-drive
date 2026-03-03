import requests
url = 'https://10iup8m7n5u4jshd.public.blob.vercel-storage.com/'
headers={'Authorization':'Bearer vercel_blob_rw_10iup8m7n5U4jshD_lpZ3Kd7nRmabRMvjnn6ASt9aCxCHyv'}
params={'pathname':'certificates/python_test.png'}
resp = requests.put(url, headers=headers, params=params, data=b'hello')
print(resp.status_code, resp.text)
