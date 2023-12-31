import sqlite3
import requests
import csv
import os
from datetime import datetime, timezone

WEBHOOK_URL = os.environ["WEBHOOK"]
file_name = os.environ['FILE_NAME']

# Connect to the database file
conn = sqlite3.connect("message.db")

# Create a cursor object
cur = conn.cursor()

# Check if the table exists
cur.execute("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='messages')")
table_exists = cur.fetchone()[0]

def main():
    response = breakpoints()
    
    if "_error" in response:
        code = response["_error"]["http_code"]
        msg = response["_error"]["message"]
        print(f'HTTP Code {code} | {msg}')
        return
    elif not response["breakpoint"]:
        print("No data")
        return

    name, payload = message(response)
    to_csv(response)
    process_sql(name, payload)

def breakpoints():
    response = requests.get("https://tt2.gamehivegames.com/holiday_event/breakpoint")
    json_data = response.json()
    return json_data

def to_csv(json):
    # Get the JSON data
    json_data = json

    # Extract the data from the JSON
    holiday_event_id = json_data["holiday_event_id"]
    percentile_data = json_data["breakpoint"]
    percentiles = [p["percentile"] for p in percentile_data]
    currencies = [p["currency"] for p in percentile_data]
    
    # Read the CSV file and create it if it doesn't exist
    with open("breakpoints.csv", "r+") as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Remove blank rows at the end of the file
        while not rows[-1]:  # Check if the last row is empty
            print(f'popped: {rows.pop()}')  # Remove the last row if it is empty

        # Obtain the last non-empty row
        last_row = rows[-1] if rows else None  # Get the last non-empty row if it exists
        
        # Check if the holiday event ID matches the one from breakpoints
        if last_row and last_row[0] == holiday_event_id:
            # Update the row with the new currencies
            last_row[1:] = currencies
        else:
            # Add a new row to the CSV with the new holiday event ID and currencies
            new_row = [holiday_event_id] + currencies
            rows.append(new_row) if new_row else None
        
        # Move the file pointer to the beginning of the file
        f.seek(0)
        
        # Write the updated CSV back to the file
        writer = csv.writer(f)
        writer.writerows(rows)

def message(message):

    now = datetime.now(timezone.utc)
    unix = str(int(now.timestamp()))
    dt_string = now.strftime("%b %d, %Y | %I:%M:%S %p %Z")

    name = message.get("holiday_event_id", "")
    vals = [i["currency"] for i in message.get("breakpoint", [])]
    # vals[0] = 80%
    # vals[1] = 30%
    # vals[2] = 10%


    payload = {
        "username": "rawrzcookie bot",
        "embeds": [
            {
                "title": name,
                "description": f'Last Updated: <t:{unix}:R>',
                "color": 102204,
                "fields": [
                    {
                        "name": 'Top 10%',
                        "value": vals[2]
                    },
                    {
                        "name": 'Top 30%',
                        "value": vals[1]
                    },
                    {
                        "name": 'Top 80%',
                        "value": vals[0]
                    }
                ],
                "footer": {"text": f'UTC+0 | {dt_string}'}
            }
        ]
    }

    return [name, payload]

def process_sql(name, payload):
    
    # if the table exists
    if table_exists:
        # Try to execute the query
        try:
            # Combine the two queries into one
            cur.execute("SELECT MessageId, EventName FROM messages ORDER BY Timestamp DESC LIMIT 1")
            # Get the result as a list of tuple
            result = cur.fetchall()
            # Get the previous message ID
            previous_message_id = result[0][0]
            # Get the previous event name
            previous_event_name = result[0][1]
        except sqlite3.Error as e:
            # Print the error message
            print(e)
            # Set the previous message ID to None
            previous_message_id = None
            # Set the previous event name to blank
            previous_event_name = ""

        
        # if current event name is different than previous
        if (name != previous_event_name):
            # insert new row to database
            toWebhook("post", payload, name)

        # else if previous message id is not None
        elif previous_message_id:
            # edit previous webhook's message with new payload       
            toWebhook("patch", payload, name, previous_message_id)
        
        # else do nothing
        else:
            pass

    # if table does not exist
    else:
        # post new message with payload and save response content to database 
        toWebhook("post", payload, name)


def toWebhook(method, payload, name="", messageid=0):
    if method == "patch":
        requests.patch(f"{WEBHOOK_URL}/messages/{messageid}", json=payload)
    elif method == "post":
        with requests.post(f'{WEBHOOK_URL}?wait=true', json=payload) as response:

                # Get the data from the response
                res = response.json()
                message_id = res["id"]
                channel_id = res["channel_id"]
                timestamp = res["timestamp"]

                # Create the table if it doesn't exist
                if not table_exists:
                    cur.execute("CREATE TABLE IF NOT EXISTS messages (MessageId TEXT, ChannelId TEXT, EventName TEXT, Timestamp TEXT)")
    
                # Store the message ID and other information in the database
                cur.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (message_id, channel_id, name, timestamp))

                # Commit the changes
                conn.commit()

if __name__ == "__main__":
    main()
    # Close the database connection after everything is done
    conn.close()
