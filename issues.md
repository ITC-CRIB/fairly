
5. fighsare is not providing a url for a remote dataset in the webclient

7. Figshare not allowing to delete a dataset,raising raise `ValueError("Operation not permitted")` 

6. Not able to include files succesfully in the metadata for upload

----------------
bug
remote_dataset.url is not returning a url
how to reproduce error:
1. create a local dataset
```
import fairly
client = fairly.client("zenodo")
dataset = fairly.dataset(<path/to/dataset>)
```

2. create a remote dataset by uploading the local dataset
```
remote_dataset = dataset.upload(client.client_id)
```
3. get the url of the remote dataset
```
remote_dataset.url
output: None
```
When I check for published remote dataset, I see the url though
```
remote = fairly.dataset("https://zenodo.org/record/3929547#.Yw_SodJBxhF")
remote.url
output:
https://zenodo.org/record/3929547#.Yw_SodJBxhF
```