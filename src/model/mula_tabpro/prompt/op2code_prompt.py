DEMO_OP2CODE = """You are a agent to generate code for specific data preparation. Given a column or several columns of data, please generate code to augment or normalize the data. The data is stored in a pandas DataFrame object `df` so you DO NOT need to load the data. Process the object `df` and return the processed object `df`.

/*
"career_win_loss": "22-88" | "nan" | "17-20" | "11-14"
*/
Requirement: please process the column `career_win_loss` to satisfy: Extract the win number from the column 'career\nwin-loss'. If missing some records, fill in the missing records with `MIN_VALUE` since the question is asking for a larger win number.
Code: ```MIN_VALUE = -9999
added_col = 'win_number_team_a'
added_val = []
for value in df['career_win_loss']:
    if pd.isna(value) or value.strip().lower() == 'nan':  # Check for missing or NaN values
        added_val.append(MIN_VALUE)
    else:
        try:
            # Extract the win number by splitting the string on '-'
            win_number = int(value.split('-')[0].strip())
            added_val.append(win_number)
        except (ValueError, IndexError):
            # Handle unexpected formats by assigning MIN_VALUE
            added_val.append(MIN_VALUE)
df[added_col] = added_val```


/*
"enter_office": "1996-99" | "1998-2002" | "2000-04" | "2002-06" | "2004-08"
*/
Requirement: please process the column `enter_office` to satisfy: Calculate the duration of the term. First split the term into two parts, then calculate the abs difference between the two parts.
Code: ```added_col = 'term_duration'
added_val = []
for value in df['enter_office']:
    if pd.isna(value) or value.strip().lower() == 'nan':  # Check for missing or NaN values
        added_val.append(0)  # Assign a default duration of 0 for missing values
    else:
        try:
            # Split the term into two parts
            start, end = value.split('-')
            
            # Convert both parts to integers
            start_year = int(start.strip())
            end_year = int(end.strip())
            
            # Calculate the absolute difference between the two parts
            duration = abs(end_year - start_year)
            added_val.append(duration)
        except (ValueError, IndexError):
            # Handle unexpected formats by assigning a default duration of 0
            added_val.append(0)
df[added_col] = added_val```


/*
"year": 2005 | 2010 | 2007 | 2009
"month": 5 | 5 | [n.a.] | 12
"day": 4 | 22 | 1 | 31
*/
Requirement: please process the column `year`, `month`, `day` to satisfy: what is the date? if '[n.a.]' then return assume the value to be 00.
Code: ```added_col = 'formatted_date'
added_val = []
for index, row in df.iterrows():
    year = row['year']
    month = row['month']
    day = row['day']
    
    try:
        if pd.isna(month) or str(month).strip().lower() == '[n.a.]':
            month = '00'
        else:
            month = str(int(month)).zfill(2)  # Ensure two-digit format
        
        if pd.isna(day) or str(day).strip().lower() == '[n.a.]':
            day = '00'
        else:
            day = str(int(day)).zfill(2)  # Ensure two-digit format
        
        formatted_date = f"{year}-{month}-{day}"
        added_val.append(formatted_date)
    except (ValueError, TypeError):
        added_val.append(f"{year}-00-00")
df[added_col] = added_val```


/*
"notes": 1 episode | 1 episode | 119 episodes | 13 episodes | voice<br>3 episodes | episode: \drugs are bad | [n.a.] | season 3 episode 24 'to tell the truth'
*/
Requirement: please standardize the column `notes` to numerical format.
Code: ```import re

for index, value in enumerate(df['notes']):
    if pd.isna(value) or str(value).strip().lower() == '[n.a.]':  # Check for missing or NaN values
        df.at[index, 'notes'] = 0  # Normalize missing values to 0
    else:
        try:
            match = re.search(r'(\d+)\s*(?:episode|episodes)', str(value), re.IGNORECASE)
            if match:
                episode_count = int(match.group(1))  # Extract the numeric value
                df.at[index, 'notes'] = episode_count  # Replace with the numeric value
            else:
                # If no match is found, normalize to 0
                df.at[index, 'notes'] = 0
        except (ValueError, AttributeError):
            df.at[index, 'notes'] = 0```


/*
"date": "may 23, 1958" | "july 20, 1953" | "february 14, 1953" | "january 1, 1953" | "may 1, 1953"
*/
Requirement: please standardize the column `date` to datetime format.
Code: ```df['date'] = pd.to_datetime(df['date'], errors='coerce')
default_date = pd.Timestamp('1900-01-01')
df['date'] = df['date'].fillna(default_date)
df['date'] = df['date'].dt.strftime('%Y-%m-%d')```"""

QUERY_OP2CODE = """Please complete the prompt following the format above.
/*
{table}
*/
Requirement: please process the column {col} to satisfy: {question}
Output ```your_code_here``` with no other texts.
Code:"""


SELF_CORREC_INS_OP2CODE = """{context}
Q: {question}
Last Error: {last_error}
Code: {a}"""