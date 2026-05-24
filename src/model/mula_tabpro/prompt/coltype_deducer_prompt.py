
HEAD_COLTYPE_DEDUCER = """This agent is designed to deduce the column type based on the SQL. The column type should be:

- numerical: if the column is used for numerical calculation, such as Sort, Comparison, Min, Max, Sum, Average, etc.
- datetime: if the column is used for time calculation, such as Sort, Comparision, etc.
- string: otherwise, if we just need to select, filter, or group by the column.

In general, only if a column is used for numerical calculation, it should be classified as `numerical` or `datetime`. Otherwise, it should be classified as `string`."""


DEMO_COLTYPE_DEDUCER = """Deduce the column type based on the QA-Sketch. The Column Type Should be one of the following: 'string', 'numerical', 'datetime'.

/*
"if_loss": yes | no
"is_home_court": yes | no
*/
SQL: SELECT COUNT(*) FROM w WHERE `if_loss` = 'yes' AND `is_home_court` = 'yes'
Related Columns: if_loss, is_home_court
Column Type Dict: {'if_loss': 'string', 'is_home_court': 'string'}
Explanation: The column `if_loss` and `is_home_court` are used for filtering, so they should be classified as `string`.

/*
"kick_off": 8:30am | 1:00pm | 8:30am
"game_site": away | home | away
*/
SQL: SELECT `kick_off` FROM w ORDER by `kick_off` LIMIT 1
Related Columns: kick_off, game_site
Column Type Dict: {'kick_off': 'datetime', 'game_site': 'string'}
Explanation: The column `kick_off` is used for sorting, so it should be classified as `datetime` to convert them to a sortable format.

/*
"2010": 1,382 | 1,390 | 45
"2012": 1,584 | 1,638 | 90
"filledcolumnname": hydro power | thermal | other renewable
*/
SQL: SELECT CASE WHEN (SELECT `2010` FROM w WHERE `filledcolumnname` = 'hydro power') < (SELECT `2012` FROM w WHERE `filledcolumnname` = 'hydro power') THEN 'increase' ELSE 'decrease' END
Related Columns: 2010, 2012, filledcolumnname
Column Type Dict: {'2010': 'numerical', '2012': 'numerical', 'filledcolumnname': 'string'}
Explanation: The column `2010` and `2012` are used for numerical comparison, so they should be classified as `numerical`.

/*
"time": 5:23.45 | 6:23.45 | 7:23.45
"date": 06-22 | 06-22 | 07-24
"name": Anna | Bob | Charlie
*/
SQL: SELECT `name` FROM w WHERE `date` = '06-22' ORDER by `time` LIMIT 1
Related Columns: time, date, name
Column Type Dict: {'time': 'datetime', 'date': 'string', 'name': 'string'}
Explanation: The column `time` are used for sorting, so they should be classified as `datetime` to convert them to a sortable format.

/*
party_name: new renaissance party | new party | new party
row_id: 1 | 2 | 3
*/
SQL: SELECT `party_name` FROM w WHERE `row_id` = (SELECT `row_id` FRO0M w WHERE `party_name` = 'new renaissance party') - 1
Related Columns: party_name, row_id
Column Type Dict: {'party_name': 'string', 'row_id': 'numerical'}
Explanation: The column `row_id` is used for numerical calculation in the SQL (row_id-1), so it should be classified as `numerical`.

/*
"artist": gonzaga coutinho | predro osorio | concha
"year": 1931 | Spring 1932 | 1935/36
*/
SQL: SELECT `artist` FROM w ORDER by `year` desc LIMIT 1
Related Columns: artist, year
Column Type Dict: {'artist': 'string', 'year': 'numerical'}
Explanation: The column `year` is used for sorting, so it should be classified as `numerical`. While the column `artist` is used for filtering, so it should be classified as `string`.

/*
"date": 6th June 1996 | 31th March 1999 | 29th July 2000
"wrestler": jonnie stewart | king kong bundy | the patriot; (danny dominion)
*/
SQL: SELECT `date` FROM w WHERE `wrestler` = 'steve corino' ORDER by `date` LIMIT 1
Related Columns: date, wrestler
Column Type Dict: {'date': 'datetime', 'wrestler': 'string'}
Explanation: In the SQL, we need to sort the column `date`, so it should be classified as `datetime` to convert it to a sortable format.

/*
"males": 216,794 | 24,538 | 17,409
"females": 230,891 | 16,677 | 18,522
"language": polish | yiddish | german
*/
SQL: SELECT `males` + `females` FROM w WHERE `language` = 'german'
Related Columns: males, females, language
Column Type Dict: {'male': 'numerical', 'female': 'numerical', 'language': 'string'}
Explanation: The column `males` and `females` are used for numerical calculation in the SQL, so they should be classified as `numerical`.

/*
"year": 1898 | 1893 | 1898
"ger_nos": #12 | #13 | #14
*/
SQL: SELECT `year` FROM w WHERE `year` IN ( '1898' , '1893' ) GROUP by `year` ORDER by SUM (`ger_nos`) desc LIMIT 1
Related Columns: year, ger_nos
Column Type Dict: ```{'year': 'numerical', 'ger_nos': 'numerical'}```
Explanation: The column `year` is already in numerical format, so it should be classified as `numerical`. The column `ger_nos` is used for numerical calculation in the SQL, so it should be classified as `numerical`.

/*
"year": 2001 | 2001 | 2001 | 2003 | 2003
"event": 400 m | medley relay | 4x400 m relay | 400 m | 4x400 m relay | 400 m
"notes": 47.12 | 1:50.46 | 3:06.12 | 46.69 | 3:08.62 | 46.62
*/
SQL: SELECT `notes` FROM w WHERE `year` = 2005 AND `event` = '4x400 m relay'
Related Columns: event, notes, year
Column Type Dict: ```{'year': 'numerical', 'event': 'string', 'notes': 'string'}```
Explanation: We do not need to conduct numerical computation on the column `year` and `notes`, so they should be classified as `string`. The year is already converted to numerical format in the SQL, so it should be classified as `numerical`.

/*
"season": 2000-01 | 2001-02 | 2002-03 | 2003-04 | 2004-05 | 2005-06 | 2006-07 | 2007-08 | 2008-09
"north": ehc regensburg | bts bayreuth | ec bayreuth | ehc ingolstadt ii | ver selb | ec bad kissingen | ehc bayreuth | ec amberg | erc ingolstadt
*/
SQL: SELECT `north` FROM w WHERE `season` < "2002-03" and `north` != "ec bayreuth" ORDER by `season` desc LIMIT 1
Related Columns: season, north
Column Type Dict: ```{'season': 'string', 'north': 'string'}```
Explanation: Although the column `season` is used for numerical comparison in the SQL, but it can not be converted to numerical nor datetime format. Moreover, it is already in a sortable format, so it should be classified as `string`.

/*
"name": ask a biologist | archimedes-lab.org | awesome library | bitesize by the bbc
"cost": free | free | from us$75/year | free
*/
SQL: SELECT `name` FROM w WHERE cast ( `cost` AS int ) > ( SELECT SUM ( cast ( `cost` AS int ) ) FROM w )
Related Columns: name, cost
Column Type Dict: ```{'name': 'string', 'cost': 'numerical'}```
Explanation: The column `cost` is used for numerical calculation in the SQL, so it should be classified as `numerical`."""

QUERY_COLTYPE_DEDUCER = """Please complete the following prompt.
/*
{table}
*/
SQL: {sql}
Related Columns: {columns}
Output ```your_TypeDict_here``` with no other texts.
Column Type Dict:"""

SELF_CORREC_INS_DEDUCER = """/*
{context}
*/
{question}
Last Error: {last_error}
Column Type Dict: {a}"""