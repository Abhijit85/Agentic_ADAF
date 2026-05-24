DEMO_ENGINEER = """Your are an engineer to use NL2SQL or NL2Code tools to process the table based on the Reasoning Plan. Output [FINISH] represents the end of the process. If you use NL2Code, save the processed result in the DataFrame variable `df`. If you use python to generate a new column, make sure the new column name is unique (for example, column 'Airline' and 'airline' will not be accepted). 

Demonstrations:

Title: 2008 Liège-Bastogne-Liège
/*
col : Rank | Cyclist | Team | Time | UCI ProTour; Points
row 1 : 1 | Alejandro Valverde (ESP) | Caisse d'Epargne | 5h 29' 10" | 40
row 2 : 2 | Alexandr Kolobnev (RUS) | Team CSC Saxo Bank | s.t. | 30
row 3 : 3 | Davide Rebellin (ITA) | Gerolsteiner | s.t. | 25
row 4 : 4 | Paolo Bettini (ITA) | Quick Step | s.t. | 20
row 5 : 5 | Franco Pellizotti (ITA) | Liquigas | s.t. | 15
row 6 : 6 | Denis Menchov (RUS) | Rabobank | s.t. | 11
row 7 : 7 | Samuel Sánchez (ESP) | Euskaltel-Euskadi | s.t. | 7
row 8 : 8 | Stéphane Goubert (FRA) | Ag2r-La Mondiale | + 2" | 5
row 9 : 9 | Haimar Zubeldia (ESP) | Euskaltel-Euskadi | + 2" | 3
row 10 : 10 | David Moncoutié (FRA) | Cofidis | + 2" | 1
*/
Statement: russia had the most cyclists within the top 10
Reasoning Plan: ```1. Select relevant records.
2. Extract the country information.
3. Count the cyclist occurrences of each country.
4. Determine the country with the highest count.
5. Determine if Russia had the most cyclists within the top 10.```
Engineering Plan: ```1. Select all cyclists who finished within the top 10. Suggested too invoke: Executor(NL2SQL)```
SQL: ```SELECT * FROM w WHERE Rank <= 10;```

Get new table after invoke the Executor(NL2SQL) tool:
/*
col : Rank | Cyclist | Team | Time | UCI ProTour; Points
row 1 : 1 | Alejandro Valverde (ESP) | Caisse d'Epargne | 5h 29' 10" | 40
row 2 : 2 | Alexandr Kolobnev (RUS) | Team CSC Saxo Bank | s.t. | 30
row 3 : 3 | Davide Rebellin (ITA) | Gerolsteiner | s.t. | 25
row 4 : 4 | Paolo Bettini (ITA) | Quick Step | s.t. | 20
row 5 : 5 | Franco Pellizotti (ITA) | Liquigas | s.t. | 15
row 6 : 6 | Denis Menchov (RUS) | Rabobank | s.t. | 11
row 7 : 7 | Samuel Sánchez (ESP) | Euskaltel-Euskadi | s.t. | 7
row 8 : 8 | Stéphane Goubert (FRA) | Ag2r-La Mondiale | + 2" | 5
row 9 : 9 | Haimar Zubeldia (ESP) | Euskaltel-Euskadi | + 2" | 3
row 10 : 10 | David Moncoutié (FRA) | Cofidis | + 2" | 1
*/
Statement: russia had the most cyclists within the top 10
Reasoning Plan: ```1. Select relevant records.
2. Extract the country information.
3. Count the cyclist occurrences of each country.
4. Determine the country with the highest count.
5. Determine if Russia had the most cyclists within the top 10.```
Engineering Plan: ```2. Extract the country information. Suggested too invoke: Executor(NL2Code)```
Python ```df['Country'] = df['Cyclist'].apply(
    lambda x: re.search(r'\((\w+)\)', x).group(1) if re.search(r'\((\w+)\)', x) else None
)```

Get new table after invoke the Executor(NL2Code) tool:
/*
col : Rank | Cyclist | Team | Time | UCI ProTour; Points | Country
row 1 : 1 | Alejandro Valverde (ESP) | Caisse d'Epargne | 5h 29' 10" | 40 | ESP
row 2 : 2 | Alexandr Kolobnev (RUS) | Team CSC Saxo Bank | s.t. | 30 | RUS
row 3 : 3 | Davide Rebellin (ITA) | Gerolsteiner | s.t. | 25 | ITA
row 4 : 4 | Paolo Bettini (ITA) | Quick Step | s.t. | 20 | ITA
row 5 : 5 | Franco Pellizotti (ITA) | Liquigas | s.t. | 15 | ITA
row 6 : 6 | Denis Menchov (RUS) | Rabobank | s.t. | 11 | RUS
row 7 : 7 | Samuel Sánchez (ESP) | Euskaltel-Euskadi | s.t. | 7 | ESP
row 8 : 8 | Stéphane Goubert (FRA) | Ag2r-La Mondiale | + 2" | 5 | FRA
row 9 : 9 | Haimar Zubeldia (ESP) | Euskaltel-Euskadi | + 2" | 3 | ESP
row 10 : 10 | David Moncoutié (FRA) | Cofidis | + 2" | 1 | FRA
*/
Statement: russia had the most cyclists within the top 10
Reasoning Plan: ```1. Select relevant records.
2. Extract the country information.
3. Count the cyclist occurrences of each country.
4. Determine the country with the highest count.
5. Determine if Russia had the most cyclists within the top 10.```
Engineering Plan: ```3. Count the cyclist occurrences of each country. Suggested too invoke: Executor(NL2SQL)```
SQL: ```SELECT Country, COUNT(Cyclist) AS Count FROM w GROUP BY Country;```

Get new table after invoke the Executor(NL2SQL) tool:
/*
col : Country | Count
row 1 : ESP | 3
row 2 : RUS | 2
row 3 : ITA | 3
row 4 : FRA | 2
*/
Statement: russia had the most cyclists within the top 10
Reasoning Plan: ```1. Select relevant records.
2. Extract the country information.
3. Count the cyclist occurrences of each country.
4. Determine the country with the highest count.
5. Determine if Russia had the most cyclists within the top 10.```
Engineering Plan: ```4. Determine the country with the highest count. Suggested too invoke: Executor(NL2SQL)```
SQL: ```SELECT Country FROM w where Count = (SELECT MAX(Count) FROM w);```

Get new table after invoke the Executor(NL2SQL) tool:
/*
col : Country | Count
row 1 : ESP | 3
row 2 : ITA | 3
*/
Statement: russia had the most cyclists within the top 10
Reasoning Plan: ```1. Select relevant records.
2. Extract the country information.
3. Count the cyclist occurrences of each country.
4. Determine the country with the highest count.
5. Determine if Russia had the most cyclists within the top 10.```
Engineering Plan: ```5. The country with the highest count is Spain or Italy, not Russia. Suggested too invoke: [FINISH]```"""

# QUERY_END2ENDER = """Here is the table to answer this question. Answer the question.'
# /*
# {table}
# */
# Statement: {question}
# Direct output the answer.
# The answer is:"""

QUERY_ENGINEER = """Here is the table, the question and the Reasoning Plan. Please generate the Engineering Plan.'
Title: {title}
/*
{table}
*/
Statement: {question}
Reasoning Plan: ```{reasoning_plan}```
Last Error: {error}
Engineering Plan:"""

QUERY_REACT_ENGINEER = """Get new table after invoke the Executor({agent}) tool:
/*
{table}
*/
Statement: {question}
Reasoning Plan: ```{reasoning_plan}```
Last Error: {error}
Engineering Plan:"""