DEMO_BINDER = """Generate SQL given the question and table to answer the question correctly.
If question-relevant column(s) contents are not suitable for SQL comparisons or calculations, map it to a new column with clean content by a new grammar MAP("").

CREATE TABLE w(
	row_id text,
	year text,
	gold text,
	silver text,
	bronze text,
	host_city_cities text)
/*
Title: Results of World U-17 Hockey Challenge
5 example rows:
SELECT * FROM w LIMIT 5;
row_id	year	gold	silver	bronze	host_city_cities
1	2019	-	-	-	alberta medicine hat and saskatchewan swift current
2	2018	russia	finland	sweden	new brunswick quispamsis and saint john
3	2017	united states	canada red	czech republic	british columbia dawson creek and fort st. john
4	2016	sweden	canada black	russia	ontario sault ste. marie
5	2015 (jan.)	canada white	russia	sweden	british columbia dawson creek and fort st. john
*/
Q: What countries did the World U-17 Hockey Challenge attract after 2016?
QA-Sketch: ```SELECT `year`, `gold`, `silver`, `bronze` FROM w WHERE `year` > 2016```


CREATE TABLE w(
	row_id text,
	party text,
	party_democratic text,
	candidate text,
	votes text,
	percent text)
/*
Title: Results of 1932 United States presidential election in North Dakota
5 example rows:
SELECT * FROM w LIMIT 5;
row_id	party	party_democratic	candidate	votes	percent
1	-	democratic	franklin d. roosevelt	178,350	69.59%
2	-	republican	herbert hoover (inc.)	71,772	28.00%
4	-	liberty	william hope harvey	1,817	0.71%
5	total votes	total votes	total votes	256,290	100%
*/
Q: Who won the 1932 United States presidential election in North Dakota and what was the vote breakdown?
QA-Sketch: ```SELECT `party_democratic`, `candidate`, `votes`, `percent` FROM w WHERE `percent` = '69.59%'```


CREATE TABLE w(
	row_id text,
	year text,
	competition text,
	venue text,
	position text,
	notes text)
/*
Title: Competition record of Luchia Yishak
5 example rows:
SELECT * FROM w LIMIT 5;
row_id	year	competition	venue	position	notes
1	1990	african championships	cairo, egypt	2nd	3000 metres
2	1991	world championships	tokyo, japan	10th	10,000 m
3	1991	all-africa games	cairo, egypt	2nd	3000 m
4	1992	world cross country championships	boston, united states	10th	long race
5	1992	world cross country championships	boston, united states	3rd	team race
*/
Q: Where did Luchia Yishak place in the 3000m in the 1991 All-Africa Games? 
QA-Sketch: ```SELECT `venue`, `position` FROM w WHERE `year` = 1991 AND `competition` = 'all-africa games' AND `position` = '2nd' AND `notes` = '3000 m'```


CREATE TABLE w(
	row_id text,
	date text,
	name text,
	from text,
	fee text,
	ref text)
/*
Title: In of 2002-03 Yeovil Town F.C. season
5 example rows:
SELECT * FROM w LIMIT 5;
row_id	date	name	from	fee	ref
1	10 may 2002	williams, gavingavin williams	hereford united	22,500	-
2	1 july 2002	demba, abdoulayeabdoulaye demba	oostende	free (released)	-
3	22 august 2002	forinton, howardhoward forinton	torquay united	free (released)	-
4	30 september 2002	el-kholti, abdouabdou el-kholti	raja casablanca	free (released)	-
5	28 november 2002	jackson, kirkkirk jackson	stevenage borough	20,000	-
6	28 november 2002	aggrey, jimmyjimmy aggrey	harrow borough	free (released)	-
7	4 february 2003	gall, kevinkevin gall	bristol rovers	free	-
8	14 february 2003	mustoe, neilneil mustoe	stevenage borough	free	-
*/
Q: Who were the first two players to join Yeovil Town F.C. in the 2002-03 season?
QA-Sketch: ```SELECT `name`, `from`, `fee` FROM w WHERE `date` = '10 may 2002' OR `date` = '1 july 2002'```


CREATE TABLE w(
	row_id text,
	constituency text,
	candidate text,
	votes text,
	percentage text,
	position text)
/*
Title: October 1974 UK general election of Revolutionary Communist Party of Britain (Marxist–Leninist)
5 example rows:
SELECT * FROM w LIMIT 5;
row_id	constituency	candidate	votes	percentage	position
1	battersea north	carole reakes	102	0.4	5
2	birmingham handsworth	j. l. hutchinson	103	0.3	5
3	brighton kemptown	john buckle	125	0.3	5
4	bristol south east	p. rowe	79	0.1	6
5	cardiff south east	b. c. d. harris	75	0.2	5
6	lambeth central	peter john bratton	88	0.3	5
7	leicester south	g. h. rousseau	136	0.3	5
8	portsmouth south	a. d. rifkin	612	1.2	4
*/
Q: What is Revolutionary Communist Party of Britain highest recorded vote?
QA-Sketch: ```SELECT MAX(`votes`) FROM w WHERE `candidate` = 'A. D. Rifkin'```
"""

QUERY_BINDER = """{create_table_text}
/*
Title: {title}
example rows:
SELECT * FROM w;
{table}
*/
Q: {question}
Output ```your_QA-Sketch_here``` with no other texts.
QA-Sketch:"""


SELF_CORREC_INS_BINDER = """{context}
Q: {question}
Last Error: {last_error}
QA-Sketch: {a}"""