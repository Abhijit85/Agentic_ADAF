DEMO_NL2SQLER_PREP = """Generate SQL given the question and table to answer the question correctly.

CREATE TABLE w(
	row_id int,
	name text,
	wins int)
/*
Title: Fabrice Santoro
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	name	wins
0	australian open	22
1	french open	17
2	wimbledon	11
*/
Q: did he win more at the australian open or indian wells?
SQL: SELECT name FROM w WHERE name IN ('australian open', 'indian wells') ORDER BY wins DESC LIMIT 1


CREATE TABLE w(
	row_id int,
	game_site text,
	result text)
/*
Title: 2007 New Orleans Saints season
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	game_site	result
0	rca dome	l
1	raymond james stadium	l
2	louisiana superdome	l
*/
Q: what number of games were lost at home?
SQL: SELECT COUNT(*) FROM w WHERE result = 'l' AND `game_site` = 'louisiana superdome'


CREATE TABLE w(
	row_id int,
	game_site text,
	result_score text)
/*
Title: 2007 New Orleans Saints season
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	game_site	result_score
0	away	loss
1	home	win
2	away	loss
*/
Q: what number of games were lost at home?
SQL: SELECT COUNT(*) FROM w WHERE `result_score` = 'loss' AND `game_site` = 'home'


CREATE TABLE w(
	row_id int,
	filledcolumnname text)
/*
Title: Electricity in Sri Lanka
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	filledcolumnname
0	hydro power
1	thermal
2	other renewables
*/
Q: did the hydro power increase or decrease from 2010 to 2012?
SQL: SELECT CASE WHEN (SELECT `2010` FROM w WHERE filledcolumnname = 'hydro power') < (SELECT `2012` FROM w WHERE filledcolumnname = 'hydro power') THEN 'increase' ELSE 'decrease' END


CREATE TABLE w(
	row_id int,
	draw int,
	artist text)
/*
Title: Portugal in the Eurovision Song Contest 1979
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	draw	artist
0	1	gonzaga coutinho
1	2	pedro osório s.a.r.l.
2	3	concha
*/
Q: who was the last draw?
SQL: SELECT `artist` FROM w ORDER by `draw` desc LIMIT 1


CREATE TABLE w(
	row_id int,
	year int,
	ger_nos text)
/*
Title: GER Class N31
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	year	ger_nos
0	1893	999
1	1893	979
2	1894	989
*/
Q: which had more ger numbers, 1898 or 1893?
SQL: SELECT `year` FROM w WHERE `year` IN ( '1898' , '1893' ) GROUP by `year` ORDER by SUM (`ger_nos`) desc LIMIT 1


CREATE TABLE w(
	row_id int,
	tramway text,
	year_of_inauguration text)
/*
Title: List of spans
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	tramway	year_of_inauguration
0	peak 2 peak gondola	2008
1	hut of regensburg material transport aerial railway	?
2	vanoise express	2003
*/
Q: was the sandia peak tramway innagurate before or after the 3s aerial tramway?
SQL: SELECT ( SELECT `year_of_inauguration` FROM w WHERE `tramway` = 'sandia peak tramway' ) < ( SELECT `year_of_inauguration` FROM w WHERE `tramway` = '3s aerial tramway' )


CREATE TABLE w(
	id int,
	year int,
	location text)
/*
Title: World Artistic Gymnastics Championships - Women's floor
3 example rows:
SELECT * FROM w LIMIT 3;
id	year	location
0	1950	basel
1	1954	rome
2	1958	moscow
*/
Q: where were the championships held before the 1962 prague championships?
SQL: SELECT `location` FROM w WHERE `year` < 1962 ORDER by `year` desc LIMIT 1


CREATE TABLE w(
	id int,
	wrestler text,
	date text)
/*
Title: WSL World Heavyweight Championship
3 example rows:
SELECT * FROM w LIMIT 3;
id	wrestler	date
0	jonnie stewart	1996-6-6
1	king kong bundy	1999-3-31
2	the patriot; (danny dominion)	2000-7-29
*/
Q: when did steve corino win his first wsl title?
SQL: SELECT `date` FROM w WHERE `wrestler` = 'steve corino' ORDER by `date` LIMIT 1


CREATE TABLE w(
	row_id int,
	language text,
	males int,
	females int)
/*
Title: Płock Governorate
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	language	males	females
0	polish	216794	230891
1	yiddish	24538	26677
2	german	17409	18522
*/
Q: how many male and female german speakers are there?
SQL: SELECT `males` + `females` FROM w WHERE `language` = 'german'


CREATE TABLE w(
	row_id int,
	temple text,
	city_town_village text)
/*
Title: Shikoku Pilgrimage
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	temple	city_town_village
0	ryōzen-ji (霊山寺)	naruto
1	gokuraku-ji (極楽寺)	naruto
2	konsen-ji (金泉寺)	itano
*/
Q: what is the difference in the number of temples between imabari and matsuyama?
SQL: SELECT abs ( ( SELECT COUNT ( `temple` ) FROM w WHERE `city_town_village` = 'imabari' ) - ( SELECT COUNT ( `temple` ) FROM w WHERE `city_town_village` = 'matsuyama' ) )


CREATE TABLE w(
	row_id int,
	name text,
	nationality text)
/*
Title: Athletics at the 2001 Goodwill Games - Results
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	name	nationality
0	brahim boulami	morocco
1	reuben kosgei	kenya
2	stephen cherono	kenya
*/
Q: what counties had the least participants for the race?
SQL: SELECT `nationality` FROM w GROUP by `nationality` having COUNT ( `name` ) = ( SELECT COUNT ( `name` ) FROM w GROUP by `nationality` ORDER by COUNT ( `name` ) asc LIMIT 1 )

CREATE TABLE w(
	row_id int,
	administrative_area text,
	area_km2 real)
/*
Title: Saint Helena, Ascension and Tristan da Cunha
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	administrative_area	area_km2
0	saint helena	122.0
1	ascension island	91.0
2	tristan da cunha	184.0
*/
Q: is the are of saint helena more than that of nightingale island?
SQL: SELECT ( SELECT `area_km2` FROM w WHERE `administrative_area` = 'saint helena' ) > ( SELECT `area_km2` FROM w WHERE `administrative_area` = 'nightingale island' )


CREATE TABLE w(
	row_id int,
	title text)
/*
Title: The Boys (comics)
3 example rows:
SELECT * FROM w LIMIT 3;
row_id	title
0	the name of the game
1	get some
2	good for the soul
*/
Q: what title appears before "the self-preservation society"?
SQL: SELECT `title` FROM w WHERE row_id = ( SELECT row_id FROM w WHERE `title` = 'the self-preservation society' ) - 1"""

QUERY_NL2SQLER_PREP = """{create_table_text}
/*
Title: {title}
example rows:
SELECT * FROM w;
{table}
*/
Q: {question}
SQL:"""

SELF_CORREC_INS_NL2SQLER_PREP = """{context}
Q: {question}
Last Error: {last_error}
SQL: {a}"""