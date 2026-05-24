DEMO_PLANNER = """Your are a agent to plan the reasoning process for answering questions based on a table.

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
Question: which country had the most cyclists within the top 10?
Reasoning Plan: ```1. Select relevant records.
2. Extract the country information.
3. Count the cyclist occurrences of each country.
4. Determine the country with the highest count.
5. Answer the question.```

Title: UCI ProTour Points
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
Question: how many players got less than 10 points?
Reasoning Plan: ```1.Select relevant records.
2.Extract the UCI ProTour Points for each cyclist.
3.Identify cyclists with less than 10 points.
4.Count the number of cyclists meeting the criteria.
5.Answer the question.```"""

QUERY_PLANNER = """Here is the table and the question. Please generate the Reasoning Plan.'
Title: {title}
/*
{table}
*/
Question: {question}
Last Error: {error}
Output ```your_reasoning_plan_here``` with no extra text.
Reasoning Plan:"""


















DEMO_MODIFY_PLANNER = """Your are a agent to plan the reasoning process for answering questions based on a table.

Demonstrations:

Title: 2022 FIFA World Cup Group Stage Results
/*
col : Team | Goals Scored | Goals Conceded | Points
row 1 : Argentina | 2 | 5 | 6
row 2 : Poland | 3 | 2 | 4
row 3 : Mexico | 2 | 3 | 4
row 4 : Saudi Arabia | 3 | 4 | 3
*/
Question: which team had the highest goal difference in the group stage?
Old Reasoning Plan: ```1. Select relevant records.
2. Calculate the goal difference for each team.
3. Identify the team with the highest goal difference.
4. Answer the question.```
Critic Report: ```**GAP**: Task 1 is incomplete because the goal difference was not calculated using the `abs()` operation.  
- **Pending Task**: Correct Task 1 by recalculating the goal difference using the absolute value.```
New Reasoning Plan: ```1. Select relevant records.
2. Calculate the absolute goal difference for each team.
3. Identify the team with the highest goal difference.
4. Answer the question.```

Title: UCI ProTour Points
/*
col : Rank | Cyclist | Team | Time | UCI ProTour; Points
row 1 : 1 | Alejandro Valverde (ESP) | Caisse d'Epargne | 5h 29' 10" | 15+5+20=40
row 2 : 2 | Alexandr Kolobnev (RUS) | Team CSC Saxo Bank | s.t. | 9+10+11=30
row 3 : 3 | Davide Rebellin (ITA) | Gerolsteiner | s.t. | 15+10=25
row 4 : 4 | Paolo Bettini (ITA) | Quick Step | s.t. | 3+17=20
row 5 : 5 | Franco Pellizotti (ITA) | Liquigas | s.t. | 11+4=15
row 6 : 6 | Denis Menchov (RUS) | Rabobank | s.t. | 9+2=11
row 7 : 7 | Samuel Sánchez (ESP) | Euskaltel-Euskadi | s.t. | 5+2=7
row 8 : 8 | Stéphane Goubert (FRA) | Ag2r-La Mondiale | + 2" | 1+4=5
row 9 : 9 | Haimar Zubeldia (ESP) | Euskaltel-Euskadi | + 2" | 0+3=3
row 10 : 10 | David Moncoutié (FRA) | Cofidis | + 2" | 1=1
*/
Question: how many players got less than 10 points?
Old Reasoning Plan: ```1.Select relevant records.
2.Extract the UCI ProTour Points for each cyclist.
3.Identify cyclists with less than 10 points.
4.Count the number of cyclists meeting the criteria.
5.Answer the question.```
Critic Report: ```**GAP**: Task 2 is incomplete because the it should conduct string extraction to get the numerical values of the UCI ProTour Points.
**Pending Task**: Conduct string extraction to extract the total UCI ProTour Points and convert it to numerical for each cyclist.```
New Reasoning Plan: ```1.Select relevant records.
2.Extract the UCI ProTour Points for each cyclist and convert it to numerical values.
3.Identify cyclists with less than 10 points.
4.Count the number of cyclists meeting the criteria.
5.Answer the question.```"""


QUERY_MODIFY_PLANNER = """Here is the table and the question. Please generate the Reasoning Plan.'
Title: {title}
/*
{table}
*/
Question: {question}
Old Reasoning Plan: ```{old_reasoning_plan}```
Critic Report: ```{critic_report}```
Last Error: {error}
New Reasoning Plan:"""