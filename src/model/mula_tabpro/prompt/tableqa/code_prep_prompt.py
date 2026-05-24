DEMO_CODE_PREP = """You are a agent to generate code to prepare the table based on the original table and question. Given a table along with its title and a question, please generate code to address data quality issues from three aspects: (1) redundancy: the table have irrelevant columns that could be distracting information. This requires to select relevant columns. But do not select relevant rows. (2) inconsistency: the table have inconsistent data format that is not conducive to table analysis. (3) incompleteness: the table have missing columns to get the final result, which could be generated from the existing columns. The code should process the table stored in a pandas.DataFrame Object `df` and the final result should be a cleaned table stored in the variable `df`.

Title: Fabrice Santoro
/*
row_id	name	2001	2002	2003	2004	2005	2006	2007	2008	2009	2010	career\nsr	career\nwin-loss
0	australian open	2r	1r	3r	2r	1r	qf	3r	2r	3r	1r	0 / 18	[n.a.]
1	french open	4r	2r	2r	3r	1r	1r	1r	2r	1r	a	0 / 20	?-20
2	wimbledon	3r	2r	2r	2r	2r	2r	2r	1r	2r	a	0 / 14	11-14
*/
Q: where did he win most?
Requirements: (1) related columns: name, career\nwin-loss; (2) generate a column about the wins from the column career\nwin-loss
Code: ```# we have already input a pd.DataFrame object named `df`
df = df[['name', 'career\nwin-loss']]
df[['career_wins', 'career_losses']] = df['career\nwin-loss'].str.split('-', expand=True)
df['career_wins'] = pd.to_numeric(df['career_wins'].replace('?', '0'), errors='coerce')
df = df.drop(columns=['career\nwin-loss'])
df = df.rename(columns={'career_wins': 'wins'})```


Title: 2007 New Orleans Saints season
/*
row_id	week	date	opponent	time	game site	tv	result/score	record
0	1	2007-9-6	indianapolis colts	t20:30 edt	rca dome	nbc l 41 - 10	0-1
1	2	2007-9-16	tampa bay buccaneers	t13:0 edt	raymond james stadium	fox 31 - 14	0-2
2	3	2007-9-24	tennessee titans	t20:30 edt	louisiana superdome	espn	l 31 - 14	0-3
*/
Q: how many games were lost at home?
Requirements: (1) related columns: game site, result/score; (2) generate a column about the loss from the column result/score; generate a column describing whether it is the home court of New Orleans Saints; (3) please normalize the column result/score to int format
Code: ```# we have already input a pd.DataFrame object named `df`
df = df[['game site', 'result/score']]
df[['result', 'score']] = df['result/score'].str.split(' ', 1, expand=True)
df[['saints_score', 'opponent_score']] = df['score'].str.split(' - ', expand=True)
df['saints_score'] = pd.to_numeric(df['saints_score'])
df['opponent_score'] = pd.to_numeric(df['opponent_score'])```


Title: 2007-08 NHL season
/*
date	team_a	team_b	place
4th Oct 2007	1	2.	home
2008-1-1	1	3	home
2013/5/1	-	4	home
*/
Q: when is the game have the largest score difference?
Requirements: (1) related columns: team_a, team_b; (2) generate a column about the score difference from the columns team_a, team_b; (3) please normalize the columns team_a to int format; please normalize the columns team_b to int format; normalize the column date into unified format
Code: ```# we have already input a pd.DataFrame object named `df`
df = df[['date', 'team_a', 'team_b']]
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df['team_a'] = pd.to_numeric(df['team_a'].replace('-', '0'), errors='coerce')
df['team_b'] = pd.to_numeric(df['team_b'].replace('-', '0'), errors='coerce')
df['score_difference'] = abs(df['team_a'] - df['team_b'])
df = df.dropna(subset=['score_difference'])```


Title: Płock Governorate
/*
row_id	language	number	percentage (%)	males	females
0	polish	447685	80.86	216,794	230,891
1	yiddish	51215	9.25	24,538	26,677
2	german	35931	6.49	17,409	18,522
*/
Q: how many german speakers?
Requirements: (1) related columns: males, females; (2) please normalize the column males to int format; please normalize the column females to int format (3) please generate a new column total_speakers
Code: ```# we have already input a pd.DataFrame object named `df`
df = df[['males', 'females']]
df['males'] = pd.to_numeric(df['males'].str.replace(',', ''), errors='coerce')
df['females'] = pd.to_numeric(df['females'].str.replace(',', ''), errors='coerce')
df['total_speakers'] = df['males'] + df['females']```


Title: Electoral district of Lachlan
/*
row_id	member	party	term
0	john ryan	none	1859-1864
1	james martin	none	1864-69
2	james watson	none	1869-80
*/
Q: which the members of the third incarnation of the lachlan served the longest.
Requirements: (1) related columns: term; (2) generate a column about the duration from the column term
Code: ```# we have already input a pd.DataFrame object named `df`
df = df[['term']]
df['term'] = df['term'].replace(r'(\d{4})-(\d{2})$', r'\1-\2\1', regex=True)
df[['start_year', 'end_year']] = df['term'].str.split('-', expand=True)
df['start_year'] = pd.to_numeric(df['start_year'], errors='coerce')
df['end_year'] = pd.to_numeric(df['end_year'], errors='coerce')
df['duration'] = df['end_year'] - df['start_year']```"""

QUERY_CODE_PREP = """Please complete the prompt following the format above.
Title: {title}
/*
{table}
*/
Q: {question}
Do not define the object `df` in your code, because this object will be directly input. 
Code:"""


SELF_CORREC_INS_CODE_PREP = """{context}
Q: {question}
Last Error: {last_error}
Code: {a}"""