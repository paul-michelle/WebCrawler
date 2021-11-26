# REDDIT SCRAPER
## You may scrape but don't you rape!    
#### ABOUT
This Reddit scraper collects info on posts and their authors from a given reddit web-page.
The collected info is saved to a txt-file/db-table/db-collection, while the logging info to 
a log file. CRUD-operations are performed via pretty simple RESTful API.
#### INSTALLATION 
1. `Mkdir` on  your machine and create a virtual environment down there with Python >= 3.9.
2. Download files from this repo and place them next to the folder with your newly created virtenv.
3. Install the packages from *requirements.txt* file into your virtenv folder
(either with `$ pip install -r requirements.txt` or with the package-manager you'd normally do this).
4. To run the scraper you'll need [Chrome browser](https://www.google.com/chrome/)
on your machine as well as [ChromeDriver](https://chromedriver.chromium.org/) of a corresponding version.
To find out which version of ChromeDriver you need, open your Chrome browser, hit *Customize and control Google
Chrome -> Settings -> About Chrome*.
5. To be able to perfrom CRUD operations within a database, make sure you've got
connection to [PostgreSQL](https://www.postgresql.org/) and [MongoDB](https://www.mongodb.com/). 
Both of the services are available for free in development purposes. 
6. To run CRUD-operations on the output file/table/collection you will either need your favourite command line
util, or a GUI app. [Postman](https://www.postman.com/downloads/) will come in handy.
It's also free of charge, at least to extend needed.

#### LAUNCHING AND USING
Move to the folder with the downloaded files from this repo, open the terminal and run `python manin.py --help`.
You will see arguments you'll need to provide with dash-dash flags to run the program. Here's the demo.
> $ python main.py --help
> 
> usage: main.py [-h] <br><br>
> [--chromedriver-path CHROMEDRIVER_PATH] <br> 
> [--target-dir-path TARGET_DIR_PATH] <br><br>
> [--url URL] <br>
> [--number NUMBER] <br>
> [--host HOST] <br>
> [--port PORT] <br>
> [--server SERVER] <br><br>
> [--postgres-host POSTGRES_HOST] <br>
> [--postgres-port POSTGRES_PORT] <br>
> [--postgres-db POSTGRES_DB] <br>
> [--postgres-user POSTGRES_USER] <br>
> [--postgres-pass POSTGRES_PASS] <br><br>
> [--mongo-host MONGO_HOST]<br>
> [--mongo-port MONGO_PORT] <br>
> [--mongo-db MONGO_DB]<br>


Open the `settings.py` file and overwrite your `--chromedriver-path` and `--target-dir-path`.
Also make sure to have your db instances launch (if on linux, use `service postgresql status` and `systemctl status
mongod`). Note, that you are to **obligatory** set your db credentials and details.

Before you launch the script move to the `main.py` module and set the type of `CRUD
executor` you would like to use: either `TXT`, or `SQL`(postgres), or `NoSQL`(mongo).
I.e. the info will be saved to `txt-file`, or  `tables`, or `collections` respectively.

After you launch the script, it will collect enough raw info from the webpage, process it and
temporarily place in into a collector-dict (so, it will be in the RAM). 

Open the `Postman` and use the following uris for the corresponding CRUD
operatons.

Here is the scheme: <br>

`http://localhost:8087/posts/` with `PUT`
--> to fetch first entry from the RAM and save it. <br>
`http://localhost:8087/posts/remaining/` with `PUT`
--> to fetch all remaining entries from the RAM and save them. <br>
`http://localhost:8087/posts/` with `GET`
--> to get all the entries already saved into file/database. <br>
`http://localhost:8087/posts/UNIQUE_ID/` with `GET`
--> to get a specific entry already saved file/database. <br>
`http://localhost:8087/posts/UNIQUE_ID/` with `PUT`
--> to update a specific entry from file/database. <br>
`http://localhost:8087/posts/UNIQUE_ID/` with `DELETE`
--> to get rid of a specific entry from file/database. <br>

Here are some API **demos**: <br>

`http://localhost:8087/posts/` with `PUT`
![demo](api_demos/api_demo_write_one_post.png) <br>

`http://localhost:8087/posts/` with `GET`
![demo](api_demos/api_demo_get_one_post.png) <br>

`http://localhost:8087/posts/UNIQUE_ID/` with `PUT`
![demo](api_demos/api_demo_update_one_post.png) <br>

Go try reddit scraper!

#### DISCLAIMER
You are strongly discouraged to abuse the program and run massive and frequent requests
to the Reddit servers. Remember, you may scrape but don't you rape!