# Preparation

Copy .env.sample -> .env and populate with all required data

## DB
For this project I used mongodb, to install mongo on your server follow this [guide](https://www.mongodb.com/docs/manual/installation/)

Then you must create two dbs. MONGO_INITDB_DATABASE will be using to save 
parsed channel and TG_ACCOUNTS_DB_NAME - auth telegram data.

MONGO_INITDB_DATABASE - create the 'main_channels' collection that will 
store the first channels to start parsing, add at least one document with
the required field 'url' what is the value of the channel's telegram

TG_ACCOUNTS_DB_NAME - create the 'accounts' collection that will store tg 
accounts data. Add at least one document with the required fields: 'session_data',
'phone_number'. Also if your phone number in tg has password you must add 'password'
field to the document. 'session_data' is the session string that using to authorize though Telethon.
If you don't have it, you can use my script and follow the instructions.

```shell
python create_tg_session_string.py
```
You must have api_id and api_hash to get session string otherwise follow this
[instructions](https://core.telegram.org/api/obtaining_api_id) to get them

## Google Spreadsheet
If you want the date to also be displayed in google speadsheet, you need to add the creds.json file to the project root
and add SPREADSHEET_ID to .env file. To get this file go to [google console](https://console.cloud.google.com) create 
new project or the exists one and go to [credentials](https://console.cloud.google.com/apis/credentials) 
and create new service account. After creating the service account, select the Keys tab on the service account page and 
add a new key in json format. Download this file, rename it to creds.json, and move it to the project root folder.

# Start

```shell
docker build -t tg-similar-channel-parser .
docker run -d -p 5900:5900 tg-similar-channel-parser
```

To check if the script is working, you can connect to the vnc server using any vnc client. 
Port to connect is 5900
