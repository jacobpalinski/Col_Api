## Overview
The Cost of Living API provides financial data regarding property purchase, rent, utilities, childcare, transportation, food and beverage, leisure and apparel items for 265 cities. 
The inspiration for this project was my interest in how the cost of various items vary around the world and the fact there are few cost of living APIs currently that both have data on a broad number of items and are free.
I wanted to create a free API that has these 2 features.

At the time of writing the API has information regarding major cities in Australia, New Zealand, Europe, United States as well as Singapore, China, Taiwan, Thailand, Malaysia, South Korea, Japan, Hong Kong and Macau.

A variety of tools and technologies were used for this project. Data for the API endpoints was generated from a data pipleline that scrapes data from both numbeo.com and livingcost.org. Scraped data is loaded into a S3 bucket as raw json 
and then is transformed using Pyspark to be loaded into data lake in json format. The API itself is written using Flask Restful framework using SQLAlchemy ORM.

All tools / technologies used: Python, Flask, S3, EC2, Pyspark, Airflow, Docker, SQLAlchemy, PostgreSQL, Swagger, Postman.

Documentation for the API can be found [here](http://52.221.221.11:8088/apidocs/#/)

## Data Pipeline
### Architecture
![image](https://github.com/jacobpalinski/Col_Api/assets/64313786/311045ed-4994-4ce0-9a51-0d69b0468426)
### Extraction
Extraction takes places via two sources numbeo.com and livingcost.org. For numbeo.com extract comes from two urls:
- Currency settings page: Contains the conversion rate of each currency from USD to local. URL: https://www.numbeo.com/common/currency_settings.jsp
- Cost of various items by city. Example: https://www.numbeo.com/cost-of-living/in/Perth

On the otherhand, for livingcost.org, individual items are retrieved in three-step process by going first to the relevant country, finding the link which matches relevant city and then extracting relevant items from city page.
For example: https://livingcost.org/cost/australia -> city link: https://livingcost.org/cost/australia/sydney -> Extract relevant items

Locations.json is used to filter list of cities to extract financial information from. Locations.json was not originally planned to be created, but a lack of consistent pattern between urls for livingcost.org countries 
and simplicity for filtering cities to extract from numbeo.com lead to its creation and inclusion.

Extraction code can be found in the `airflow/dags/scripts/extraction.py` file.

### Transformation + Loading
Once the raw data is extracted into the S3 Raw Bucket it is transformed using Pyspark. Data is transformed and exported into individual files into data lake. 
Transformations required creation of columns, string manipulation, type conversion, joins and removal of null values.

The following files were created for data lake:
- locations_with_currencies.json
- homepurchase.json
- rent.json
- foodbeverage.json
- utilities.json
- transportation.json
- childcare.json
- apparel.json
- leisure.json

Pyspark transformation code can be found in the `airflow/dags/scripts/pyspark.py` file.

### Orchestration
Apache Airflow in a dockerised enviroment was the tool of choice for orchestration. Pipeline runs batch process once per week.

DAG structure:

![image](https://github.com/jacobpalinski/Col_Api/assets/64313786/bd133fb7-489b-4d05-aaa0-5fbb27967bbc)

DAG code can be found in the `airflow/dags/col_api_etl.py` file.

## API
The Cost of Living API uses JWT authentication for get requests in each url endpoint. 
To get data from various endpoints user will first need submit a post request to endpoint /v1/auth/user and login at /v1/auth/login.
User can also view account information, logout and reset password. See [documentation](http://52.221.221.11:8088/apidocs/#/) in overview for more information.

Get requests for each of the item categories (home purchase, childcare, apparel, food and beverage, leisure, rent, transportation and utilities) can accept
three parameters: country, city and abbreviation. Country will filter item results for that specific country, and city will filter results for city. 
Prices will be sorted in ascending order for each request.
Example Request: `http://52.221.221.11:8088/v1/homepurchase?country=United States`

If more than 50 results are returned for an API call, output will be paginated with 50 results per page. Next and previous page url will be displayed at the end of page output.
Example end of page output:
- Previous: `http://52.221.221.11:8088/v1/transportation?country=United+States&page=1`
- Next: `http://52.221.221.11:8088/v1/transportation?country=United+States&page=3`

### Transactional Modelling
Backend for Flask API was built using SQLAlchemy ORM and PostgreSQL. Transactional model consists of the following tables:
- user
- blacklisttoken
- currency
- location
- homepurchase
- rent
- utilities
- transportation
- foodbeverage
- childcare
- apparel
- leisure

user + blacklisttoken tables:

![image](https://github.com/jacobpalinski/Col_Api/assets/64313786/2e7d1a26-a6b7-49e7-b63b-866d0cc6b61b)


remaining tables:

![image](https://github.com/jacobpalinski/Col_Api/assets/64313786/41cbd2c1-ae1e-4ffd-861d-c93cbc3d0708)










































