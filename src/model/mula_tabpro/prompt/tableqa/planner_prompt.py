DEMO_QA_SKETCH_PLANNER = """Generate QA-Sketch given the question and table to answer the question correctly. 

If some columns need to be transformed before executing the QA-Sketch, you can use a UDF function MAP() to generate new columns from existing columns. The grammar of MAP() is MAP([source_columns], "target_column_name"). 

Do not use KEYWORD STRFTIME, SUBSTRING, SUBSTR, SUBSTRING_INDEX, SPLIT_PART, SPLIT, EXTRACT. Use MAP() grammer to generate new columns INSTEAD.


Title: 72 equal temperament
Columns: "interval_name", "size_steps", "size_cents", "just_cents"
/*
"interval_name": "perfect fifth" | "septendecimal tritone" | "septimal tritone"
"size_steps": "42" | "36" | "35"
"just_cents": "701.96" | "603.0" | "582.51"
*/
Q: how many intervals have a step size that is less than ten steps?
QA-Sketch: ```SELECT COUNT(`interval_name`) FROM w WHERE CAST(`size_steps` AS INT) < 10```


Title: Fabrice Santoro
Columns: "row_id", "name", "2001", "2002", "2003", "2004", "career\nsr", "career\nwin-loss"
Values of each Column:
/*
"row_id": 0 | 1 | 2
"name": "australian open" | "french open" | "wimbledon"
"2001": "2r" | "4r" | "3r"
"2002": "1r" | "2r" | "2r"
"2003": "3r" | "2r" | "2r"
"2004": "2r" | "3r" | "2r"
"career\nsr": "0 / 18" | "0 / 20" | "0 / 14"
"career\nwin-loss": "22-18" | "17-20" | "11-14"
*/
Q: did he win more at the australian open or indian wells?
QA-Sketch: ```SELECT name FROM w WHERE name IN ('australian open', 'indian wells') ORDER BY MAP(["career\nwin-loss"], "win_number_of_he") DESC LIMIT 1```


Title: List of highest-grossing openings for films
Columns: "rank", "film", "year", "opening_weekend_three_day", "inflation_adjusted_2014_usd"
/*
"rank": "1" | "2" | "3" | "4"
"film": "shrek the third" | "man of steel" | "alice in wonderland" | "spider-man"
"year": "2007" | "2013" | "2010" | "2002"
"opening_weekend_three_day": "$121,629,270" | "$116,619,362" | "$116,101,023" | "$114,844,116"
"inflation_adjusted_2014_usd": "$138,338,411" | "$118,068,774" | "$125,562,025" | "$150,582,840"
*/
Q: name one that ranked after man of steel.
QA-Sketch: ```SELECT `film` FROM w WHERE CAST(`rank` AS INT) > (SELECT `rank` FROM w WHERE `film` = 'man of steel') LIMIT 1```


Title: 2007-08 NHL season
Columns: "date", "team_a", "team_b", "place"
Values of each Column:
/*
"date": "2007-10-4" | "2008-1-1" | "2013-5-1"
"team_a": 1 | 1 | 1
"team_b": 2 | 3 | 4
"place": "home" | "home" | "home"
*/
Q: which game have the largest score difference?
QA-Sketch: ```SELECT `date` FROM w ORDER BY MAP(["team_a", "team_b"], "abs_score_difference") DESC LIMIT 1```


Title: Electoral district of Lachlan
Columns: "row_id", "member", "party", "term"
Values of each Column:
/*
"row_id": 0 | 1 | 2
"member": "john ryan" | "james martin" | "james watson"
"party": "none" | "none" | "none"
"term": "1859-1864" | "1864-1869" | "1869-1880"
*/
Q: of the members of the third incarnation of the lachlan, who served the longest?
QA-Sketch: ```SELECT member FROM w ORDER BY MAP(["term"], "served_duration") DESC LIMIT 1```


Title: Henry J. Kaiser-class oiler
Columns: "row_id", "ship", "status", "years_active"
Values of each Column:
/*
"row_id": 1 | 2 | 3 | 4
"ship": "henry j. kaiser" | "joshua humphreys" | "john lenthall" | "andrew j. higgins"
"status": "activesouthern california duty oiler" | "inactivated 1996, returned to service 2005" | "active" | "inactivated may 1996. sold to the chilean navy may 2009. towed to atlantic marine alabama shipyard, mobile, alabama, september 2009 for three-month refit. commissioned in chilean navy on 10 february 2010 and renamed almirante montt.[1]"
"years_active": "1986-present" | "1987-1996; 2005-2006; 2010-present" | "1987-1996; 1998-present" | "1987-1996 (usa); 2010-present (chile)"
*/
Q: how many of these ships are inactive?
QA-Sketch: ```SELECT COUNT(ship) FROM w WHERE MAP(["status"], "ship_is_active") = 'False'```


Title: Płock Governorate
Columns: "row_id", "language", "number", "percentage (%)", "males", "females"
Values of each Column:
/*
"row_id": 0 | 1 | 2
"language": "polish" | "yiddish" | "german"
"number": 447685 | 51215 | 35931
"percentage (%)": 80.86 | 9.25 | 6.49
"male": 216,794 | 24,538 | 17,409
"females": 230,891 | 26,677 | 18,522
*/
Q: how many male and female german speakers are there?
QA-Sketch: ```SELECT SUM(CAST(`males` AS INT) + CAST(`females` AS INT)) FROM w WHERE `language` = 'german'```


Title: 2007 New Orleans Saints season
Columns: "row_id", "date", "winner"
/*
"row_id": 1 | 2 | 3 | 4
"date": "19-22 mar" | "4-7 sep" | "11-14 sep" | "18-21 sep"
"name": "new york giants" | "tampa bay buccaneers" | "denver broncos" | "san francisco 49ers"
*/
Q: who is the first to win a game?
QA-Sketch: ```SELECT `winner` FROM w ORDER BY MAP(["date"], "begining_date_mm_dd") LIMIT 1```


Title: 2008 Clásica de San Sebastián
Columns: "rank", "cyclist", "team"
/*
"rank": "1" | "2" | "3"
"cyclist": "alejandro valverde (esp)" | "alexandr kolobnev (rus)" | "davide rebellin (ita)"
"team": "caisse d'epargne" | "team csc saxo bank" | "gerolsteiner"x
*/
Q: which other cyclists in the top 10 hailed from the same country as the winner?
Last Error: The SQL contains unacceptable keywords: SUBSTRING_INDEX. DO NOT USE KEYWORD STRFTIME, SUBSTRING, SUBSTR, SUBSTRING_INDEX, SPLIT_PART, SPLIT, EXTRACT. USE MAP() grammer to generate new columns INSTEAD.
QA-Sketch: ```SELECT `cyclist` FROM w WHERE MAP(["cyclist"], "country_of_cyclist") = (SELECT `country` FROM w WHERE rank = 1) AND rank <= 10 AND cyclist != (SELECT cyclist FROM w WHERE rank = 1);```"""

QUERY_QA_SKETCH_PLANNER = """Title: {title}
Columns: {columns}
Values of each Column:
/*
{table}
*/
Q: {question}
Output ```your_QA-Sketch_here``` with no other texts.
QA-Sketch:"""


SELF_CORREC_INS_QA_SKETCH_PLANNER = """{context}
Q: {question}
Last Error: {last_error}
QA-Sketch: {a}"""



DEMO_AUG_OP_GEN_PLANNER = """Output the requirement about adding a new column based on the existing columns in the table.

Title: Fabrice Santoro
/*
"career\nwin-loss": "22-18" | "??" | "17-20" | "11-14"
*/
Q: did he win more at the australian open or indian wells?
QA-Sketch: ```SELECT name FROM w WHERE name IN ('australian open', 'indian wells') ORDER BY MAP(["career\nwin-loss"], "win_number_team_a") DESC LIMIT 1```
New Column: `win_number_team_a`
Requirement: ```Extract the win number which is the first number from the column 'career\nwin-loss'. If missing some records, fill in the missing records with `MIN_VALUE` since the question is asking for a larger win number.```


Title: 2007 New Orleans Saints season
/*
"result/score": "l 41 - 10" | "l 31 - 14" | "l 31 - 14"
*/
Q: what number of games were lost at home?
QA-Sketch: ```SELECT COUNT(*) FROM w WHERE MAP(["result/score"], "is_loss") = 'yes' AND MAP(["game site"], "is_home_of_new_orleans_stants") = 'yes'```
New Column: `is_loss`
Requirement: ```Extract the result of the game from the column 'result/score' where "l" means lost and "w" means win.```


Title: 2007-08 NHL season
/*
"team_a": 1 | 1 | 1 | "[n.a.]"
"team_b": 2 | 3 | 4 | "[n.a.]"
*/
Q: which game have the smallest score difference?
QA-Sketch: ```SELECT `date` FROM w ORDER BY MAP(["team_a", "team_b"], "abs_score_difference") ASC LIMIT 1```
New Column: `abs_score_difference`
Requirement: ```Calculate the score difference between team_a and team_b. If missing some records, the score difference should be `MAX_VALUE` since the question is asking for the smallest score difference.```


Title: Electoral district of Lachlan
/*
"term": "1859-1864" | "1878-1880" | "1864-1869" | "1869-1880"
*/
Q: of the members of the third incarnation of the lachlan, who served the longest?
QA-Sketch: ```SELECT member FROM w ORDER BY MAP(["term"], "served_year_duration") DESC LIMIT 1```
New Column: `served_year_duration`
Requirement: ```Calculate the duration of the term. First split the term into two parts, then calculate the abs difference between the two parts.```


Title: List of mayors of New York City
/*
"enter_office": "1996-99" | "1998-2002" | "2000-04" | "2002-06" | "2004-08"
*/
Q: which mayor served the longest?
QA-Sketch: ```SELECT mayor FROM w ORDER BY MAP(["enter_office"], "served_year_duration") DESC LIMIT 1```
New Column: `served_year_duration`
Requirement: ```Calculate the serving duration. For some records, the start year or the end year is not complete, your should complte the year before calculating the duration.```


Title: Comparison of American and British English
/*
"year": 2005 | 2010 | 2007 | 2009
"month": 5 | 5 | "[n.a.]" | 12
"day": 4 | 22 | 1 | 31
*/
Q: which competition was held first?
QA-Sketch: ```SELECT competition FROM w ORDER BY MAP(["year", "month", "day"], "date_yyyy_mm_dd") LIMIT 1```
New Column: `date_yyyy_mm_dd`
Requirement: ```Combine the year, month, and day to get the date. If some records are missing, fill in the missing records with 99 since the question is asking for the earliest date. Moreover, if some records only 1 number for the month or day, fill in the missing records with 0 in the front.```"""

QUERY_AUG_OP_GEN_PLANNER = """Title: {title}
/*
{table}
*/
Q: {question}
QA-Sketch: ```{neural_sql}```
New Column: `{new_column}`
Output ```your_requirement_here``` with no other texts.
Requirement:"""

SELF_CORREC_INS_AUG_OP_GEN_PLANNER = """{context}
Q: {question}
QA-Sketch: ```{neural_sql}```
New Column: `{new_column}`
Last Error: {last_error}
Requirement: {a}"""


DEMO_NOR_OP_GEN_PLANNER = """Output the requirement about normalizing the given column to the required format.

Title: 2007 New Orleans Saints season
/*
"date": "october 19" | "july 13 2009" | "september 23 governor's cup"
*/
Q: which country has the most medals in February?
QA-Sketch: ```SELECT Country, SUM(Medal) AS Total FROM w WHERE Date LIKE '02-%' GROUP BY Country ORDER BY Total DESC LIMIT 1;```
Requirement for normalizing the column `date`: ```Standard the column `date` to sortable string like 'YYYY-MM-DD'.```


Title: NFL Season
/*
"kickoff": "7:05pm" | "13:05" | "7:35pm" | "7:05pm"
*/
Q: What is the most common kickoff time for events?
QA-Sketch: ```SELECT kickoff, COUNT(*) AS cnt FROM w GROUP BY kickoff ORDER BY cnt DESC LIMIT 1;```
Requirement for normalizing the column `kickoff`: ```Uniform the column `kickoff` to 24-hour format like '%I:%M%p'.```


Title: List of mayors of New York City
/*
"salary": "5000" | "5000" | "10,000" | "10,000"
*/
Q: What is the average salary of the mayors of New York City?
QA-Sketch: ```SELECT AVG(salary) FROM w;```
Requirement for normalizing the column `salary`: ```Standard the column `salary` to numerical format.```


Title: 2007 New Orleans Saints season
/*
"score": "25 pt" | "30 pt" | "20 pt" | "15 pt" | "not attended"
*/
Q: what is the lowest score achieved in a single competition?
QA-Sketch: ```SELECT MAX(score) FROM w;```
Requirement for normalizing the column `score`: ```Standard the column `score` to numerical format. Notice that some records are missing("not attended"), fill in the missing records with 9999 since the question is asking for the lowest score.```


Title: Płock Governorate
/*
"number": 447685 | 51215 | 35931
*/
Q: how many male and female german speakers are there?
QA-Sketch: ```SELECT SUM(CAST(`males` AS INT) + CAST(`females` AS INT)) FROM w WHERE `language` = 'german'```
Requirement for normalizing the column `number`: ```Standard the column `number` to numerical format.```


Title: List of Episodes for a TV Show
/*
"notes": "1 episode" | "1 episode" | "119 episodes" | "13 episodes" | "voice" | "3 episodes" | "episode: \drugs are bad" | "[n.a.]" | "season 3 episode 24 'to tell the truth'"
*/
Q: what is the total number of episodes in the TV show?
QA-Sketch: ```SELECT SUM(episodes) FROM w;```
Requirement for normalizing the column `notes`: ```Standard the column notes to numerical format. You will need to extract the numerical value for the episodes from the notes column, handle special cases like [n.a.] or text-based descriptions.```"""

QUERY_NOR_OP_GEN_PLANNER = """Title: {title}
/*
{table}
*/
Q: {question}
QA-Sketch: ```{neural_sql}```
Output ```your_requirement_here``` with no other texts.
Requirement for normalizing the column `{column}`:"""

SELF_CORREC_INS_NOR_OP_GEN_PLANNER = """{context}
Q: {question}
QA-Sketch: ```{neural_sql}```
Last Error: {last_error}
Requirement for normalizing the column: {a}"""

