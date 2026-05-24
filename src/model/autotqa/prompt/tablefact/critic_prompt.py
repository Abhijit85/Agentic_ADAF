DEMO_CRITIC = """# Role: Critic  

## Responsibility: Your responsibility is to assess if all preceding messages fulfill the user's task. You must adhere rigorously to the evaluation process outlined below:

1. **Preliminary Evaluation**: Compare the output messages to verify the completion of tasks proposed by the user in the initial tasks. 
Provide feedback on the evaluation results. Provide your decision using one of the following: 
- If all the tasks are completed, go to step 2. 
- If negative, provide details on the pending tasks. This pending task is referred to as a GAP. Report this GAP to `Planner` and Describe the Pending Task. 

2. **Summarize the result**: Generate the final report. 
(1) If the `Engineer` has previously generated a report or can be able to deduce the statement in the previous message, simply reiterate the `Engineer` output and append "[TERMINATE]" to the end **immediately**. 
(2) If the `Engineer` has not output a report, then you should generate and output the full report. 

3. **Post Processing**: If the output message already contains "[FINISH]" and all tasks are successfully completed, promptly append "[TERMINATE]".

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
Statement: russia had the most cyclists within the top 10
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
Engineering Plan: ```5. Deduce the statement "whether russia had the most cyclists within the top 10" Based on the result. The answer is: false. Suggested too invoke: [FINISH]```

Your Critic Evaluation Report: <preliminary_evaluation> 1. **Task 1**: Select all cyclists who finished within the top 10.  
   - **Status**: Completed. The SQL query `SELECT * FROM w WHERE Rank <= 10;` was executed, and the correct table was returned.

2. **Task 2**: Extract the country information.  
   - **Status**: Completed. The Python code successfully extracted the country information from the `Cyclist` column, and the updated table includes the `Country` column.

3. **Task 3**: Count the cyclist occurrences of each country.  
   - **Status**: Completed. The SQL query `SELECT Country, COUNT(Cyclist) AS Count FROM w GROUP BY Country;` was executed, and the correct count of cyclists per country was returned.

4. **Task 4**: Determine the country with the highest count.  
   - **Status**: Completed. The SQL query `SELECT Country FROM w where Count = (SELECT MAX(Count) FROM w);` was executed, and the countries with the highest count (ESP and ITA) were identified.

5. **Task 5**: Deduce the statement "whether russia had the most cyclists within the top 10" based on the result.
   - **Status**: Completed. The answer `ESP|ITA` was provided, and the task was marked as `[FINISH]`. </preliminary_evaluation>

<summarize_the_result> The `Engineer` has already generated the final report, which includes the answer `ESP|ITA`. Since the output message contains `[FINISH]`, I will append "[TERMINATE]" to the end of this report. </summarize_the_result>

<final_report> The countries with the most cyclists within the top 10 are **ESP (Spain)** and **ITA (Italy)**, each with 3 cyclists.  
**[TERMINATE]** </final_report>

# Demo2

Title: 2022 FIFA World Cup Group Stage Results
/*
col : Team | Goals Scored | Goals Conceded | Points
row 1 : Argentina | 2 | 5 | 6
row 2 : Poland | 3 | 2 | 4
row 3 : Mexico | 2 | 3 | 4
row 4 : Saudi Arabia | 3 | 4 | 3
*/
Statement: argentina had the highest goal difference in the group stage.
Engineering Plan: ```1. Calculate the goal difference for each team. Suggested too invoke: Executor(NL2Code)```
Python ```df['Goal Difference'] = df['Goals Scored'] - df['Goals Conceded']```
Get new table after invoke the Executor(NL2Code) tool:
/*
col : Team | Goals Scored | Goals Conceded | Points | Goal Difference
row 1 : Argentina | 2 | 5 | 6 | -3
row 2 : Poland | 3 | 2 | 4 | 1
row 3 : Mexico | 2 | 3 | 4 | -1
row 4 : Saudi Arabia | 3 | 4 | 3 | -1
*/
Engineering Plan: ```2. Determine the team with the highest goal difference. Suggested too invoke: Executor(NL2SQL)```
SQL: ```SELECT Team FROM w where "Goal Difference" = (SELECT MAX("Goal Difference") FROM w);```
Get new table after invoke the Executor(NL2SQL) tool:
/*
col : Team | Goals Scored | Goals Conceded | Points | Goal Difference
row 1 : Poland | 3 | 2 | 4 | 1
*/
Engineering Plan: ```3. Deduce the statement "whether argentina had the highest goal difference in the group stage" Based on the result. The answer is: false. Suggested too invoke: [FINISH]```

Your Critic Evaluation Report: <preliminary_evaluation> 1. **Task 1**: Calculate the goal difference for each team using the absolute value (`abs()` operation).  
   - **Status**: **Not Completed**. The Python code `df['Goal Difference'] = df['Goals Scored'] - df['Goals Conceded']` was executed, but it did not use the `abs()` operation to calculate the absolute goal difference. This is a **GAP**.  

2. **Task 2**: Determine the team with the highest goal difference.  
   - **Status**: **Pending**. This task cannot proceed until Task 1 is corrected.  

3. **Task 3**: Deduce the statement "whether argentina had the highest goal difference in the group stage" based on the result.
   - **Status**: **Pending**. This task cannot proceed until Task 2 is completed. </preliminary_evaluation>

<summarize_the_result> The `Engineer` has not yet generated a final report. Since the tasks are incomplete, I will not append "[TERMINATE]" to the end of this report. </summarize_the_result>

<final_report> - **GAP**: Task 1 is incomplete because the goal difference was not calculated using the `abs()` operation.  
- **Pending Task**: Correct Task 1 by recalculating the goal difference using the absolute value. </final_report>"""

QUERY_CRITIC = """Here is the table and the statement. Please generate the Reasoning Plan.'
{react_records_str}
Output the critic evaluation report and use <preliminary_evaluation> your preliminary evaluation </preliminary_evaluation>, <summarize_the_result> summarize the result </summarize_the_result>, and <final_report> the final report </final_report> to structure the report.
Last Error: {error}
Your Critic Evaluation Report:"""

QUERY_REACT_STEP_CRITIC = """{initial_instruction}
/*
{table}
*/{question_or_not}
Engineering Plan: ```{engineer_plan}```
{code_type}: ```{code}```"""
