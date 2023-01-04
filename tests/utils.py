import fairly

# delete all archived files
# fairly get all account datasets
def delete_account_datasets(client_name: str):
    client = fairly.client(client_name)
    datasets = client.get_account_datasets()
    for d in datasets: client.delete_dataset(d.id["id"])
    datasets = client.get_account_datasets()
    while datasets is not None:
        delete_account_datasets(client_name)

# write main function
if __name__ == "__main__":
    delete_account_datasets("zenodo")

