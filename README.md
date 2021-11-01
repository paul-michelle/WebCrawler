# REDDIT SCRAPER
## You may scrape but don't you rape!    
#### ABOUT
This Reddit scraper collects info on posts and their author from a given reddit web-page.
As it is written now, the collected info is saved to a txt-file, while the logging info to 
a log file. 
#### INSTALLATION 
1. `Mkdir` on  your machine and create a virtual environment down there with Python >= 3.9.
2. Download files from this repo and place them next to the folder with your newly created virtenv.
3. Install the packages from *requirements.txt* file into your virtenv folder
(either with `$ pip install -r requirements.txt` or with the package-manager you'd normally do this).
4. To run the scraper you'll need [Chrome browser](https://www.google.com/chrome/)
on your machine as well as [ChromeDriver](https://chromedriver.chromium.org/) of a corresponding version.
To find out which version of ChromeDriver you need, open your Chrome browser, hit *Customize and control Google
Chrome -> Settings -> About Chrome* 
5. Being in the folder with the downloaded files from this repo, open the terminal and run `python manin.py --help`
You will see arguments you'll need to provide with dash-dash flags to run the program. Here's the demo.
> $ python main.py --help
> 
> usage: main.py [-h] [--chromedriver-path CHROMEDRIVER_PATH] [--target-dir-path TARGET_DIR_PATH] [--url URL] [--number NUMBER]

Thus, your command should follow this pattern...
> $ python main.py --chromedriver-path `/path/to/folder/with/chromedriver`
> --target-dir-path `/path/to/folder/to/load/scraping/results/and/logs` --url `https://www.reddit.com/`
> --number `quantity of posts you'd like to scrape`

As is, the last two arguments are optional for you and by default they are: `https://www.reddit.com/top/?t=month`
and `100` respectively. 

To make the first two commandline arguments fully optional as well, i.e. to hardcode them, open the
`settings.py` file and overwrite your `--chromedriver-path` and ` --target-dir-path`. 
In the corresponding constants. If you wish to, there you can
also change `--url` of the reddit-page to be scrape and `--number` of posts to be scraped.
If you do this, you will this way change the default values of dash-dash flags and can just run
> $ python main.py
> 
Go try reddit scraper!
#### DISCLAIMER
You are strongly discouraged to abuse the program and run massive and frequent requests
to the Reddit servers. Remember, you may scrape but don't you rape!