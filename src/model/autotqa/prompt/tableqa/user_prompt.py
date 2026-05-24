DEMO_USER = """# Role: User  

## Responsibility: Your responsibility is to extract the final answer for the question from the reacting records and the last Engineering Plan.

## Answer Type: the answer can be a string or a list. If the answer is a list, the elements should be separated by "|".

# Demonstrations

## Demo1

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
Question: which country had the most cyclists within the top 10?
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
Engineering Plan: ```4. Determine the country with the highest count. Suggested too invoke: Executor(NL2SQL)```
SQL: ```SELECT Country FROM w where Count = (SELECT MAX(Count) FROM w);```
Get new table after invoke the Executor(NL2SQL) tool:
/*
col : Country | Count
row 1 : ESP | 3
row 2 : ITA | 3
*/
Engineering Plan: ```5. The answer is: ESP|ITA. Suggested too invoke: [FINISH]```
Answer: ```ESP|ITA```

# Demo2

Title: 2022 FIFA World Cup Group Stage Results
/*
col : Team | Goals Scored | Goals Conceded | Points
row 1 : Argentina | 2 | 5 | 6
row 2 : Poland | 3 | 2 | 4
row 3 : Mexico | 2 | 3 | 4
row 4 : Saudi Arabia | 3 | 4 | 3
*/
Question: which team had the highest goal difference in the group stage?
Engineering Plan: ```1. Calculate the absolute goal difference for each team. Suggested too invoke: Executor(NL2Code)```
Python ```df['Goal Difference'] = df['Goals Scored'] - df['Goals Conceded']
df['Goal Difference'] = df['Goal Difference'].abs()```
Get new table after invoke the Executor(NL2Code) tool:
/*
col : Team | Goals Scored | Goals Conceded | Points | Goal Difference
row 1 : Argentina | 2 | 5 | 6 | 3
row 2 : Poland | 3 | 2 | 4 | 1
row 3 : Mexico | 2 | 3 | 4 | 1
row 4 : Saudi Arabia | 3 | 4 | 3 | 1
*/
Engineering Plan: ```2. Determine the team with the highest goal difference. Suggested too invoke: Executor(NL2SQL)```
SQL: ```SELECT Team FROM w where "Goal Difference" = (SELECT MAX("Goal Difference") FROM w);```
Get new table after invoke the Executor(NL2SQL) tool:
/*
col : Team | Goals Scored | Goals Conceded | Points | Goal Difference
row 1 : Argentina | 2 | 5 | 6 | 3
*/
Engineering Plan: ```3. The answer is: Argentina. Suggested too invoke: [FINISH]```
Answer: ```Argentina```"""

# QUERY_END2ENDER = """Here is the table to answer this question. Answer the question.'
# /*
# {table}
# */
# Question: {question}
# Direct output the answer.
# The answer is:"""

QUERY_USER = """Here is the table, question and the reacting records. Please extract the final answer.'
{react_records_str}
Last Error: {error}
Output ```only_brief_answer``` with no extra text.
Answer: """