DEMO_NL2SQLER_PREP = """Generate SQL given the statement and table to verify the statement correctly.

CREATE TABLE w(
	row_id int,
	new_entries_this_round float)
/*
Title: turkish cup
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	new_entries_this_round
0	86.0
1	65.0
2	nan
*/
Statement: the lowest number of new entry conclude a round in the turkish cup be 5
SQL: SELECT (SELECT MIN(`new_entries_this_round`) FROM w) = 5

CREATE TABLE w(
	row_id int,
	type text)
/*
Title: cultural interest fraternities and sororities
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	type
0	fraternity
1	sorority
2	sorority
*/
Statement: 4 of the cultural interest fraternity and sorority be fraternity while 3 be a sorority
SQL: SELECT (SELECT (SELECT COUNT(*) FROM w WHERE type = 'fraternity') = 4) AND (SELECT (SELECT COUNT(*) FROM w WHERE type = 'sorority') = 3)

CREATE TABLE w(
	row_id int,
	place text)
/*
Title: british records in athletics
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	place
0	norway
1	united kingdom
2	united kingdom
*/
Statement: there be 8 different event that take place within the united kingdom
SQL: SELECT (SELECT COUNT(place) FROM w WHERE place = 'united kingdom') = 8

CREATE TABLE w(
	row_id int,
	tournament text,
	events int,
	cuts_made int)
/*
Title: jeev milkha singh
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	tournament	events	cuts_made
0	masters tournament	3	2
1	us open	4	3
2	the open championship	2	1
*/
Statement: the number of cut made in the pga championship tournament be smaller than the number of event
SQL: SELECT (SELECT `cuts_made` FROM w WHERE tournament = 'pga championship') < (SELECT events FROM w WHERE tournament = 'pga championship')

CREATE TABLE w(
	row_id int,
	country text,
	score int)
/*
Title: 2008 women 's british open
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	country	score
0	united states	65
1	japan	66
2	united states	66
*/
Statement: the 3 player from japan have the same score
SQL: SELECT (SELECT COUNT(DISTINCT score) FROM w WHERE country = 'japan' GROUP BY score) = 1

CREATE TABLE w(
	row_id int,
	place text,
	player text,
	country text,
	score text)
/*
Title: 2008 women 's british open
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	place	player	country	score
0	t1	yuri fudoh	japan	134
1	t1	jiyai shin	south korea	134
2	3	juli inkster	united states 135
*/
Statement: kristie kerr , tie for 4th place , finish the round 1 stroke under lorena ochoa of mexico
SQL: SELECT (SELECT (SELECT score FROM w WHERE player = 'cristie kerr') < (SELECT score FROM w WHERE player = 'lorena ochoa' AND country = 'mexico')) AND (SELECT (SELECT place FROM w WHERE player = 'cristie kerr') = "t4")

CREATE TABLE w(
	row_id int,
	nation text)
/*
Title: 1976 world junior figure skating championships
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	rank	name	nation
0	canada
1	united states
2	australia
*/
Statement: 2 of the 7 top - ranked figure skate team be from france
SQL: SELECT (SELECT (SELECT COUNT(*) FROM w) = 7) AND (SELECT (SELECT COUNT(*) FROM w WHERE nation = 'france') = 2)"""

QUERY_NL2SQLER_PREP = """{create_table_text}
/*
Title: {title}
example rows:
SELECT * FROM w;
{table}
*/
Statement: {question}
SQL: """

SELF_CORREC_INS_NL2SQLER_PREP = """{context}
Statement: {question}
Last Error: {last_error}
SQL: {a}"""