# README

## Overview
This task has been done as a task assignment for a Junior Python Developer in Scripting team in 17/03/2025. 

Task: Create a Python script that uses Selenium to perform a Google search and extracts the first page’s search results. 
Requirements: 
- The search query can be hard-coded in your script, or accepted as a command-line argument. 
- User should be able to provide multple queries. 
- The script should work with both Mimic and SF (no need for mobile this time).
- After performing the search, extract for each result:
-- Result title
-- URL
Output: Save the results in a CSV file with appropriate headers.

And of course, logging and proper error handling.

## Requeriments
- Python 3.11 or later
- Required libraries: `csv`, `hashlib`, `requests`, `os`, `json`, `random`, `logging`, `pytz`, `sys`, `datetime`, `time`, `dotenv`, and `selenium`


## Setup
1. Clone or download the repository containing the script.
2. Make sure you have Python 3.11+ installed.
3. You can create a virtual enviroment before install requirements.
4. Install script requirements:
    ```bash
    pip install -r requirements.txt
    ```
5. Update the following variables in ```**.env**``` file:
   - `EMAIL`: Your Multilogin account email.
    - `PASSWORD`: Your Multilogin account password.
    - `TOKEN`: If you already have an automation token, you can include it here, instead to pass your email and password.
6. Update the following variables in ```***config.json***``` file.
    - `COUNTRY`: Obrigatory. Define the country from the proxy. It requires a ISO 3166 alpha-2 for country codes with 2 digits. Per default it uses "US" - the United States.
    - `REGION`: Optional. Defines the region or state from the defined country, it uses snake case: "region_name".
    - `CITY`: Optional. Defines the city from the region/country that you defined, it uses snake case: "city_name".
    - `PROTOCOL`: Mandatory. DEfines the proxy protocol. Choose between **HTTP** or **Socks5**.
    - `SESSION_TYPE`: Mandatory. It defines if the IP will last up to 24 hours or will be set a custom time for rotation. Recommended to keep the default: "sticky".
    - `BROWSER_TYPE`: Mandatory. Choose the prefered browser: Mimic or Stealthfox.
    - `OPERATIONAL_SYSTEM`: Mandatory. Choose a OS that matches with your native device. Default: "windows".
  

## How to Use
1. Connect Multilogin Agent.

2. Run the script:

   ```bash
   python google_scrapping.py query1 "query2 with spaces" query3 query 4 "query5 with spaces"
   ```
   Use ```python3``` in macOS and Linux enviroments.

3. Keep the browser window opened in foreground to allow the automation run smoothly.
3. Arguments/Queries:
    The arguments via command lind are **required** in order to allow the script run.

    You can send it as a single work, e.g.: `japan`, `spain`, `multilogin`. 

    Or if your query has spaces, you must to use quotation marks, e.g.: `"united kingdom"`, `"facebook ads"`, `"how to use create a bot with python"`.

    To facilitate, you can also use quotaion marks for single-work queries.

4. The script will:
   - Retrieve a proxy string with Multilogin Proxy, using proxy configurations in `config.json`.
   - Start a quick browser profile with Multilogin API.
   - Navigate to Google
   - Type as an human behavior and do the search
   - Collect all results titles and urls.
   - Record information collected in a CSV file.

5. Upon completion:
   - The file will be stored in the script's folder. It will also record the date and time, alongside the query provided.
   - Logs are stored in /logs/main.log, however, it's possible to follow it on console during the script execution.

## Logs
For logs check, the user can consult it on console, while the code is running, or also consult it in /logs/main.log to check and record.

The log level is defined to "INFO", it required more specific information for debbuging, it may be changed to "DEBUG". Or also change to "WARNING" or "ERROR" to inform only it shows up.

## Functions
Here you can have a quick overview about this project's functions.

- **browser_to_google()**: Resposible to navigate to google.com and ensure the page is load and ready.
- **build_proxy_payload()**: It builds a payload for proxy settings, with protocol, host, port, username and password, that will be used in check_proxy and start_qbp.
- **build_qbp_payload()**: It defines all settings and flags for a Quick Profile.
- **check_captcha()**: It's responsible for checking if a captcha challenge is requested. It will provide some time to be solved, if not, it will close the profile and start a new one to do the query again.
- **check_proxy()**: It checks if the proxy string is valid and active.
- **find_elements()**: Responsible to find title and url elements in first's page search.
- **find_google_search()**: It locates Google's search box.
- **get_proxy()**: Retrieves a proxy string.
- **handling_args()**: It handles with arguments/queries provided by the user in the script call/start, returning a arg_list that will be used during the script.
- **human_typing()**: Emulates a human typing behavior, also includes a random error that will be added and correct after it, to emulate typo during the tying.
- **main()**: Main function and all logic behind the scrapping.
- **save_to_csv()**: Records all inform as date, time, query, titles and urls in a CSV files.
- **signin()**: If the user doesn't pass a TOKEN in .env file, it will use email and password from .env file to request a new token.
- **start_qbp()**: Start a quick profile.
- **stop_profile()**: Stops a profile.
- **update_headers()**: Update headers with authorization token.

## Future implementations
Some ideas showed up while I was doing this task:

1. A simple UI to assist the user to pass queries, and retrieve the CSV file. More user friendly.
2. Split the main script in modules, to keep the main script clean and more readable.
3. Implement a captcha solver using paid tools, or;
4. As I'm doing an undergraduate in Data Science, it could possible to train an LLM to quick reconize the Google's captcha challenge and solve it. The pro: it wil be really good to solve Google's captcha challenge. The cons: It may not be reusable for other use cases with differnt captcha puzzles, since it will be really good only in this captcha challenge.