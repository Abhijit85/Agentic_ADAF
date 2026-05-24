DEMO_QA_SKETCH_PLANNER = """Generate QA-Sketch given the statement and table to deduce whether the statement is True or False.

If some columns need to be transformed before executing the QA-Sketch, you can use a UDF function MAP() to generate new columns from existing columns. The grammar of MAP() is MAP([source_columns], "target_column_name"). 

Do not use KEYWORD STRFTIME, SUBSTRING, SUBSTR, SUBSTRING_INDEX, SPLIT_PART, SPLIT, EXTRACT. Use MAP() grammer to generate new columns INSTEAD.


Title: cultural interest fraternities and sororities
Columns: "letters", "organization", "nickname", "founding_time", "founding_university", "type"
Values of each Column:
/*
"letters": "αεπ" | "αεφ" | "σαεπ"
"organization": "alpha epsilon pi 1" | "alpha epsilon phi 2" | "sigma alpha epsilon pi 3"
"nickname": "aepi" | "aephi" | "sigma"
"founding_time": "1913-11-07" | "1909-10-24" | "1998-10-01"
"founding_university": "new york university" | "barnard college" | "university of california , davis"
"type": "fraternity" | "sorority" | "sorority"
*/
Statement: 4 of the cultural interest fraternity and sorority be fraternity while 3 be a sorority
QA-Sketch: ```SELECT (SELECT (SELECT COUNT(*) FROM w WHERE type = 'fraternity') = 4) AND (SELECT (SELECT COUNT(*) FROM w WHERE type = 'sorority') = 3)```


Title: british records in athletics
Columns: "row_id", "event", "data", "athlete", "date", "place"
Values of each Column:
/*
"row_id": 1 | 2 | 3
"event": "5 km" | "5 miles" | "10 km"
"data": "t19:29" | "32:38 +" | "40:17"
"athlete": "andi drake" | "ian mccombie" | "chris maddocks"
"date": "1990-05-27" | "1985-03-23" | "1989-04-30"
"place": "søfteland , norway" | "york , united kingdom" | "burrator , united kingdom"
*/
Statement: there be 8 different event that take place within the united kingdom
QA-Sketch: ```SELECT (SELECT COUNT(place) FROM w WHERE MAP(["place"], "country") = 'united kingdom') = 8```
Explanation for MAP function above: We need to check whether the place is in the United Kingdom. The MAP() function is used to generate a new column recording the country of each place.


Title: jeev milkha singh
Columns: "tournament", "wins", "top_10", "top_25", "events", "cuts_made"
Values of each Column:
/*
"tournament": "masters tournament" | "us open" | "the open championship"
"wins": 0 | 0 | 0
"top_10": 0 | 0 | 0
"top_25": 1 | 0 | 0
"events": 3 | 4 | 2
"cuts_made": 2 | 3 | 1
*/
Statement: the number of cut made in the pga championship tournament be smaller than the number of event
QA-Sketch: ```SELECT (SELECT `cuts made` FROM w WHERE tournament = 'pga championship') < (SELECT events FROM w WHERE tournament = 'pga championship')```


Title: 2008 women 's british open
Columns: "row_id", "place", "player", "country", "score", "to_par"
Values of each Column:
/*
"row_id": 1 | 2 | 3
"place": "t1" | "t2" | "3"
"player": "yuri fudoh" | "jiyai shin" | "juli inkster"
"country": "japan" | "south korea" | "united states"
"score": "66 + 68 = 134" | "69 + 66 = 135" | "69 + 67 = 136"
"to_par": 10 | 9 | 8
*/
Statement: kristie kerr , tie for 4th place , finish the round 1 stroke under lorena ochoa of mexico
QA-Sketch: ```SELECT (SELECT MAP(["score"], "total_score") FROM w WHERE player = 'kristie kerr') = (SELECT MAP(["score"], "total_score") FROM w WHERE player = 'lorena ochoa' AND country = 'mexico') - 1) AND ((SELECT place FROM w WHERE player = 'kristie kerr') = 't4' )```
Explanation for MAP function above: We need to calculate the total score of each player. The MAP() function is used to generate a new column recording the total score of each player.


Title: connecticut public radio
Columns: "call_sign", "frequency", "city_of_license", "facility_id", "erp_power_w", "height_m_ft", "class"
Values of each Column:
/*
"call_sign": "waic" | "wedw - fm" | "wnpr"
"frequency": "91.9 mhz" | "88.5 mhz" | "90.5 mhz"
"city_of_license": "springfield , massachusetts" | "stamford , connecticut" | "norwich , connecticut"
"facility_id": "1749" | "13619" | "13627"
"erp_power_w": "230" | "2000" | "18500"
"height_m_ft": "nan" | "nan" | "nan"
"class": "b1" | "a" | "b"
*/
Statement: there be 3 station with a call sign number in the 90s
QA-Sketch: ```SELECT (SELECT COUNT(*) FROM w WHERE MAP(["facility_id"], "is_frequence_in_90s") = 'yes' GROUP BY `call sign`) = 3```

row_id	place	player	country	score	to par	money
0	t1	larry mize	united states	70 + 72 + 72 + 71 = 285	-3	playoff
1	t1	bernhard langer	spain	73 + 71 + 70 + 71 = 285	-3	playoff
2	t1	greg norman	australia	73 + 74 + 66 + 72 = 285	-3	playoff

Title:1987 masters tournament
Columns: "place", "player", "country", "score", "to_par", "money"
Values of each Column:
/*
"place": "t1" | "t1" | "t1"
"player": "larry mize" | "bernhard langer" | "greg norman"
"country": "united states" | "spain" | "australia"
"score": "70 + 72 + 72 + 71 = 285" | "73 + 71 + 70 + 71 = 285" | "73 + 74 + 66 + 72 = 285"
"to_par": "-3" | "-3" | "-3"
"money": "playoff" | "playoff" | "playoff"
*/
Statement: bernhard m. langer have more point than roger maltbie during the 1987 master tournament
QA-Sketch: ```SELECT (SELECT MAP(["score"], "total_score_int") FROM w WHERE player = 'bernhard langer') > (SELECT total_score_int FROM w WHERE player = 'roger maltbie')```


Title: 1976 world junior figure skating championships
Columns: "rank", "name", "nation", "points", "places"
Values of each Column:
/*
"rank": 1 | 2 | 3
"name": "sherri baier / robin cowan" | "lorene mitchell / donald mitchell" | "elizabeth cain / peter cain"
"nation": "canada" | "united states" | "australia"
"points": 128.39 | 124.94 | 116.67
"places": 9 | 16 | 33
*/
Statement: 2 of the 7 top - ranked figure skate team be from france
QA-Sketch: ```SELECT (SELECT (SELECT COUNT(*) FROM w) = 7) AND (SELECT (SELECT COUNT(*) FROM w WHERE nation = 'france') = 2)```


Title: jason chambers
Columns: "row_id", "res", "record", "opponent", "method", "event", "round"
Values of each Column:
/*
"row_id": 1 | 2 | 3
"res": "win" | "win" | "loss"
"record": "18 - 5 - 2" | "17 - 5 - 2" | "16 - 5 - 2"
"opponent": "dan new" | "rene gonzalez" | "tristan yunker"
"method": "submission (rear naked choke)" | "decision (split)" | "submission ( armbar )"
"event": "tfc - power fights" | "mainstream mma - cold war" | "tfc 7 - total fight challenge 7"
"round": 1 | "n / a" | 1
*/
Statement: in mac - midwest absolute challenge , the player be defeat by dan spychalski in 1 round
QA-Sketch: ```SELECT (SELECT opponent, (CAST round AS INT) FROM w WHERE event = "mac - midwest absolute challenge")=("dan spychalski", 1)```"""



QUERY_QA_SKETCH_PLANNER = """Title: {title}
Columns: {columns}
Values of each Column:
/*
{table}
*/
Statement: {question}
Output ```your_QA-Sketch_here``` with no other texts.
QA-Sketch:"""


SELF_CORREC_INS_QA_SKETCH_PLANNER = """{context}
Statement: {question}
Last Error: {last_error}
QA-Sketch: {a}"""



DEMO_AUG_OP_GEN_PLANNER = """Output the requirement about adding a new column based on the existing columns in the table.

Title: Fabrice Santoro
/*
"career\nwin-loss": "22-18" | "??" | "17-20" | "11-14"
*/
Statement: he win more at the australian open than indian wells
QA-Sketch: ```SELECT (SELECT MAP(["career\nwin-loss"], "win_number_team_a") FROM w WHERE `game_site` = 'australian open') > (SELECT `win_number_team_a` FROM w WHERE `game_site` = 'indian wells')```
New Column: `win_number_team_a`
Requirement: ```To deduce whether the statement is True or False, we need to know the number of wins at the Australian Open and Indian Wells. Thus, extract the win number which is the first number from the column 'career\nwin-loss'.```


Title: 2007 New Orleans Saints season
/*
"result/score": "l 41 - 10" | "l 31 - 14" | "l 31 - 14"
*/
Statement: 3 games were lost at home?
QA-Sketch: ```SELECT (SELECT COUNT(*) FROM w WHERE MAP(["result/score"], "is_loss") = 'yes' AND MAP(["game site"], "is_home_game") = 'yes') = 3```
New Column: `is_loss`
Requirement: ```Extract the result of the game from the column 'result/score' where "l" means lost and "w" means win.```


Title: 2007-08 NHL season
/*
"team_a": 1 | 1 | 1 | "[n.a.]"
"team_b": 2 | 3 | 4 | "[n.a.]"
*/
Statement: game in 2009 have the smallest score difference?
QA-Sketch: ```SELECT (SELECT year FROM w WHERE MAP(["score_a", "score_b"], "score_difference") = (SELECT MIN(MAP(["score_a", "score_b"], "score_difference")) FROM w WHERE year = 2009)) = 2009```
New Column: `abs_score_difference`
Requirement: ```Calculate the score difference between team_a and team_b. If missing some records, the score difference should be `MAX_VALUE` since the statement is about the smallest score difference.```


Title: 1987 masters tournament
/*
"score": "70 + 72 + 72 + 71 = 285" | "73 + 71 + 70 + 71 = 285" | "73 + 74 + 66 + 72 = 285"
*/
Statement: bernhard m. langer have more point than roger maltbie during the 1987 master tournament
QA-Sketch: ```SELECT (SELECT MAP(["score"], "total_score_int") FROM w WHERE player = 'bernhard langer') > (SELECT total_score_int FROM w WHERE player = 'roger maltbie')```
New Column: `total_score_int`
Requirement: ```Calculate the total score of each player.```

#!!!!!!!!!!!!!!!!!!!
Title: british records in athletics
/*
"place": "søfteland , norway" | "york , united kingdom" | "burrator , united kingdom"
*/
Statement: there be 8 different event that take place within the united kingdom
QA-Sketch: ```SELECT (SELECT COUNT(place) FROM w WHERE MAP(["place"], "is_city_in_uk") = 'united kingdom') = 8```
New Column: `is_city_in_uk`
Requirement: ```Generate a new column to record the country of each place. Specifically, extract the country from the column 'place'.```"""

QUERY_AUG_OP_GEN_PLANNER = """Title: {title}
/*
{table}
*/
Statement: {question}
QA-Sketch: ```{neural_sql}```
New Column: `{new_column}`
Output ```your_requirement_here``` with no other texts.
Requirement:"""

SELF_CORREC_INS_AUG_OP_GEN_PLANNER = """{context}
Statement: {question}
QA-Sketch: ```{neural_sql}```
New Column: `{new_column}`
Last Error: {last_error}
Requirement: {a}"""

#!!!!!!!!!!!!!!
DEMO_NOR_OP_GEN_PLANNER = """Output the requirement about normalizing the given column to the required format.

Title: 2007 New Orleans Saints season
/*
"date": "october 19" | "july 13 2009" | "september 23 governor's cup"
*/
Statement: japan has the most medals in February
QA-Sketch: ```SELECT CASE WHEN Country = 'Japan' THEN 'true' ELSE 'false' END AS StatementIsTrue FROM ( SELECT Country, SUM(Medal) AS Total FROM w WHERE Date LIKE '02-%' GROUP BY Country ORDER BY Total DESC LIMIT 1) AS TopCountry;```
Requirement for normalizing the column `kickoff`: ```Standard the column `date` to sortable string like 'YYYY-MM-DD'.```


Title: jason chambers
/*
"round": 1 | "n / a" | 1
*/
Statement: in mac - midwest absolute challenge , the player be defeat by dan spychalski in 1 round
QA-Sketch: ```SELECT (SELECT opponent, (CAST round AS INT) FROM w WHERE event = "mac - midwest absolute challenge")=("dan spychalski", 1)```
Requirement for normalizing the column `round`: ```Standard the column `round` to numerical format.```


Title: List of mayors of New York City
/*
"salary": "5000" | "5000" | "10,000" | "10,000"
*/
Statement: the average salary of the mayors of New York City is 7500
QA-Sketch: ```SELECT CASE WHEN AVG(`salary`) = 7500 THEN 'true' ELSE 'false' END AS StatementIsTrue FROM w;```
Requirement for normalizing the column `salary`: ```Standard the column `salary` to numerical format.```


Title: 2007 New Orleans Saints season
/*
"score": "25 pt" | "30 pt" | "20 pt" | "15 pt" | "not attended"
*/
Statement: 20 is the lowest score achieved in a single competition?
QA-Sketch: ```SELECT CASE WHEN MIN(score) = 20 THEN 'true' ELSE 'false' END AS StatementIsTrue FROM w WHERE score != 'not attended';```
Requirement for normalizing the column `score`: ```Standard the column `score` to numerical format. Notice that some records are missing("not attended"), fill in the missing records with 9999 since the statement is about the lowest score.```


Title: List of Episodes for a TV Show
/*
"notes": "1 episode" | "1 episode" | "119 episodes" | "13 episodes" | "voice" | "3 episodes" | "episode: \drugs are bad" | "[n.a.]" | "season 3 episode 24 'to tell the truth'"
*/
Statement: total number of episodes in the TV show is 150
QA-Sketch: ```SELECT (SELECT SUM(episodes) FROM w) = 150```
Requirement for normalizing the column `notes`: ```Standard the column notes to numerical format. You will need to extract the numerical value for the episodes from the notes column, handle special cases like [n.a.] or text-based descriptions.```"""

QUERY_NOR_OP_GEN_PLANNER = """Title: {title}
/*
{table}
*/
Statement: {question}
QA-Sketch: ```{neural_sql}```
Output ```your_requirement_here``` with no other texts.
Requirement for normalizing the column `{column}`:"""

SELF_CORREC_INS_NOR_OP_GEN_PLANNER = """{context}
Statement: {question}
QA-Sketch: ```{neural_sql}```
Last Error: {last_error}
Requirement for normalizing the column: {a}"""

