# archivesspace-top-containers
This application is used by staff on their local machines to create new top containers in ArchivesSpace via the REST API.  The application accepts a CSV file as input and transforms the data into a JSON payload that is posted to create a new top container. That top container is then linked as an instance to the accession record specified in the CSV file.

The application allows for easy toggling between the `dev` and `prod` ArchiveSpace instances. Also, a `modify_data` flag must be included to overwrite data in ArchivesSpace, otherwise the application only produces a CSV file of the changes that would be made once `modify_data` is included.

# Installing the application
The following steps are needed to setup the application and only needed to be performed once.

* Clone this repo via `Download Zip` from the green `Code` button and extracting the files or via the provided `git` commands
* If running on a PC with Windows 10 or 11, setup Windows Subsystem for Linux.
  * Open Windows PowerShell.
  * Run `wsl --install`.
  * Click yes that you want to allow this app to make changes.
  * Reboot your PC.
  * Open another Windows PowerShell session and select `Ubuntu` from dropdown menu next to the `+`.
  * If you get an error related to virtualization, find instructions on enabling virtualization for your type of PC.
  * Create Unix username, this will be used later for assigning the `PATH` environmental variable.
  * Create unix password, this will be used for `sudo` commands.
  * Run `sudo add-apt-repository ppa:deadsnakes/ppa`. Press enter to continue when prompted.
  * Run `sudo apt install python3.11`.
  * Run `sudo apt install python3-pip`. Press `y` to continue when prompted.
* Change the working directory to the folder containing the application, 
e.g. 
  * If running on PC, use the following format, `cd /mnt/c/archivesspace-top-containers/` where the application is in `C:\archivesspace-top-containers\`
* Run `pip install pipenv --user`
  * If running on PC, run `export PATH=/home/<Unix_username>/.local/bin:$PATH` to assign the `PATH` variable.
* Run `make install`
* Create `.env` file in folder with:
    ```
    DEV_USER="username"
    DEV_PASSWORD="password"
    DEV_URL="<The dev API URL, typically ends with /staff/api>"
    PROD_USER="username"
    PROD_PASSWORD="password"
    PROD_URL="<The prod API URL, typically ends with /staff/api>"
    ``````

## Running the application
* Change the working directory to the folder containing the application, 
e.g. 
  * If running on PC, use the following format, `cd /mnt/c/archivesspace-top-containers/` where the application is in `C:\archivesspace-top-containers\`
* Prepare `<your file name>.csv` file with these columns and place it in a folder named `data`:
    | Column | Example value|      
    |-----------------|-----------------|
    | accession_uri |/repositories/0/accessions/000|
    | instance_type|mixed_materials|
    | container_type|DigitalStorage|
    | indicator|1234abcd|
    | location_uri|/locations/000|
* Open a Windows PowerShell session and select `Ubuntu` from dropdown menu next to the `+`.
* *MIT-specific instructions*: If running this application away from the campus Wi-Fi, be sure to connect to the VPN in order to access the ArchivesSpace staff API as it is IP-restricted.
* To ensure that data is updated as you expect, the application should first be run without the `modify_data` flag, which will only produce a CSV file of the data that would be posted. It is recommended to execute each of the following commands and review the output before proceeding to the next command.
    * Run without modify_data flag on dev
	```
    pipenv run containers --metadata_csv <your file name>.csv --as_instance dev
    ```
    * Run with modify_data flag on dev
    ```
	pipenv run containers --metadata_csv <your file name>.csv --as_instance dev --modify_data
    ```
    * Run without modify_data flag on prod
	```
    pipenv run containers --metadata_csv <your file name>.csv --as_instance prod
    ```
    * Run with modify_data flag on prod
    ```
    pipenv run containers --metadata_csv <your file name>.csv --as_instance prod --modify_data
    ```
* To verify that top containers posted and linked correctly in the ArchivesSpace UI, search for the accession record specified in the `accession_uri` column and open it. Select `Instances` on the left sidebar to see the instances attached to the accession, which should include all of the top containers that were just posted.

## Additional parameters
The application defaults to `data` as the folder for input and output files but you can specify a different folder with the `--directory` option.
  ```
  pipenv run containers --metadata_csv <your file name>.csv --as_instance dev --directory test_data
  ```

Similarly, the application defaults to repository `2` in ArchivesSpace but you can specify a different repository with the `--repository_id` option.
  ```
  pipenv run containers --metadata_csv <your file name>.csv --as_instance dev --repository_id 3
  ```
