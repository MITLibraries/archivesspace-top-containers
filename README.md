# archivesspace-top-containers

## Running the application
* Clone repo
<!-- * Install Cygwin if necessary
    *	Download Cygwin from https://cygwin.com/setup-x86_64.exe
    *	Install Cygwin
        * Make sure “Category” is selected from the “View” dropdown menu
        * Expand “All”
        * Expand “Python”
        * Find “python3”
            * Under “New” column, select the latest version (as of writing, 3.9.10-1)
        * Find “python39-pip”
            * Under “New” column, select the latest version (as of writing, 23.0.1-1)
        * Click “Next” on the next few screens to finish the installation
* Open terminal and navigate to repo folder -->
install wsl
upgrade wsl
sudo apt install python3-pip
pip install pipenv --user
export PATH=/home/???/.local/bin:$PATH

sudo apt update && upgrade
sudo apt install python3 python3-pip

sudo apt install wget build-essential libncursesw5-dev libssl-dev \
libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11


* Run `pip install pipenv –user`
* Run `make install`
* Create `.env` file in folder with:
    ```
    DEV_USER="username "
    DEV_PASSWORD="password"
    DEV_URL="https://archivesspace-dev.url/staff/api"
    PROD_USER="username "
    PROD_PASSWORD="password"
    PROD_URL="https://archivesspace-prod.url/staff/api"
    ```
* Prepare `.csv` file with columns and place it in a folder named `data`:
    * accession_uri
    * instance_type
    * container_type
    * indicator
    * location_uri
	
* To ensure that data is updated as you expect, the application should first be run without the `modify_data` flag, which will only produce a CSV file of the data that would be posted. It is recommended to execute each of the following commands and review the output before proceeding to the next command:
    * Run without modify_data flag on dev
	```
    pipenv run containers --metadata_csv metadata.csv --as_instance dev
    ```
    * Run with modify_data flag on dev
    ```
	pipenv run containers --metadata_csv metadata.csv --as_instance dev --modify_data
    ```
    * Run without modify_data flag on prod
	```
    pipenv run containers --metadata_csv metadata.csv --as_instance prod
    ```
    * Run with modify_data flag on prod
    ```
    pipenv run containers --metadata_csv metadata.csv --as_instance prod --modify_data
    ```

* NOTE: The application defaults to `data` as the folder for input and output files but you can specify a different folder with the `--directory` option.
```
pipenv run containers --metadata_csv metadata.csv --as_instance dev --directory test_data
```

Similarly, the application defaults to repository `2` in ArchivesSpace but you can specify a different repository with the `--repository_id` option.
```
pipenv run containers --metadata_csv metadata.csv --as_instance dev --repository_id 3
```
