DEMO_NL2SQLER_PREP = """Generate SQL given the question and table to answer the question correctly. 


CREATE TABLE w(
	row_id int,
	draw int,
	artist text)
Title: Portugal in the Eurovision Song Contest 1979
/*
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	draw	artist
0	1	gonzaga coutinho
1	2	pedro osório s.a.r.l.
2	3	concha
*/
Q: who was the last draw?
SQL: ```SELECT `artist` FROM w ORDER by `row_id` desc LIMIT 1```


CREATE TABLE w(
	row_id int,
	title text
    artist text)
Title: The Boys (comics)
/*
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	artist	title
0	garth ennis	the name of the game
1	carlos ezquerra	get some
2	darick robertson	good for the soul
*/
Q: what title appears before "the self-preservation society"?
SQL: ```SELECT `title` FROM w WHERE row_id = ( SELECT row_id FROM w WHERE `title` = 'the self-preservation society' ) - 1```


CREATE TABLE w(
        row_id int,
        season text,
        is_october text)
Title: List of Little People
/*
example rows:
SELECT * FROM w;
row_id  season  is_october
1       1       False
2       6       False
3       2       True
4       3       True
5       7       True
*/
Q: the number of consecutive seasons in october?
SQL: ```WITH true_rows AS (SELECT row_id, row_id - ROW_NUMBER() OVER (ORDER BY row_id) AS grp FROM w WHERE is_october = 'True') SELECT MAX(cnt) AS max_consecutive_seasons FROM (SELECT grp, COUNT(*) AS cnt FROM true_rows GROUP BY grp) t;````

CREATE TABLE w(
	row_id int,
	name text,
	wins int)
Title: Fabrice Santoro
/*
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	name	wins
0	at australian open	22
1	at french open	17
2	at wimbledon	11
*/
Q: did he win more at the australian open or indian wells?
SQL: ```SELECT CASE WHEN (SELECT wins FROM w WHERE name = 'at australian open') > (SELECT wins FROM w WHERE name = 'at indian wells') THEN 'australian open' ELSE 'indian wells' END AS result;```


CREATE TABLE w(
	row_id int,
	language text,
	males int,
	females int)
Title: Płock Governorate
/*
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	language	males	females
0	polish	216794	230891
1	yiddish	24538	26677
2	german	17409	18522
*/
Q: how many male and female german speakers are there?
SQL: ```SELECT `males` + `females` FROM w WHERE `language` = 'german'```


CREATE TABLE w(
	row_id int,
	administrative_area text,
    when text,
	area_km2 real)
Title: Saint Helena, Ascension and Tristan da Cunha
/*
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	administrative_area	when	area_km2
0	saint helena	4-12	122.0
1	ascension island	2-07	91.0
2	tristan da cunha	05-12	184.0
*/
Q: is the are of saint helena more than that of nightingale island?
SQL: ```SELECT CASE WHEN (SELECT area_km2 FROM w WHERE administrative_area = 'saint helena') > (SELECT area_km2 FROM w WHERE administrative_area = 'nightingale island') THEN 'yes' ELSE 'no' END AS result;```


CREATE TABLE w(
	id int,
	wrestler text,
	date text
    country text)
Title: WSL World Heavyweight Championship
/*
3 example rows:
SELECT * FROM w LIMIT 3;
id	wrestler	date	country
0	jonnie stewart	1996-6-6	usa
1	king kong bundy	1999-3-31	usa
2	the patriot; (danny dominion)	2000-7-29	usa
*/
Q: when did steve corino win his first wsl title?
SQL: ```SELECT `date` FROM w WHERE `wrestler` = 'steve corino' ORDER by `date` LIMIT 1```


CREATE TABLE w(
	row_id int,
	name text,
    position int,)
Title: Athletics at the 2001 Goodwill Games - Results
/*
3 example rows:
SELECT * FROM w LIMIT 4;
row_id	name	position
1	brahim boulami	2
2	reuben kosgei	4
3	stephen cherono	1
4	total	total([n.a.])
*/
Q: who has the highest rank?
SQL: ```SELECT `name` FROM w ORDER BY `position` ASC LIMIT 1 WHERE `position` != 'total([n.a.])';```


CREATE TABLE w(
	row_id int,
	year int,
	team text)
Title: 2009-10 FC Barcelona season
/*
3 example rows:
SELECT * FROM w LIMIT 5;
row_id	year	team
1	2009	barcelona
2	2010	chelsea
3	2011	chelsea
4	[n.a.]	skip
5 	totaal	all
*/
Q: how long in terms of years did the team play?
SQL: ```SELECT MAX(`year`) - MIN(`year`) + 1 AS `years_played` FROM w WHERE `year`!='[n.a.]' AND `year`!='totaal';```"""

QUERY_NL2SQLER_PREP = """{create_table_text}
Title: {title}
/*
example rows:
SELECT * FROM w;
{table}
*/
Q: {question}
Output ```your_sql_here``` with no other texts.
SQL:"""

SELF_CORREC_INS_NL2SQLER_PREP = """{context}
Q: {question}
Last Error: {last_error}
SQL: {a}"""