DEMO_NL2CODE_COMPLETE = """You are a agent to generate code for table question answering tasks. Given a table along with its title and a question, please generate code to generate the answer. The code should process the table stored in a pandas.DataFrame Object `df` and the final result should be a numerical value or a string or a list stored in the variable `result`.

Title: Fabrice Santoro
/*
row_id	name	2001	2002	2003	2004	2005	2006	2007	2008	2009	2010	career\nsr	career\nwin-loss
0	australian open	2r	1r	3r	2r	1r	qf	3r	2r	3r	1r	0 / 18	22-18
1	french open	4r	2r	2r	3r	1r	1r	1r	2r	1r	a	0 / 20	17-20
2	wimbledon	3r	2r	2r	2r	2r	2r	2r	1r	2r	a	0 / 14	11-14
*/
Q: did he win more at the australian open or french open?
Code: ```australian_open_win_loss = df.loc[df['name'] == 'australian open', 'career\nwin-loss'].values[0]
french_open_win_loss = df.loc[df['name'] == 'french open', 'career\nwin-loss'].values[0]

australian_open_wins = int(australian_open_win_loss.split('-')[0])
french_open_wins = int(french_open_win_loss.split('-')[0])

if australian_open_wins > french_open_wins:
    result = "australian open"
elif french_open_wins > australian_open_wins:
    result = "french open"
else:
    result = "equal"```

Title: Portugal in the Eurovision Song Contest 1979
/*
row_id	draw	artist	song	points	place
0	1	gonzaga coutinho	"tema para um homem só"	102	5th
1	2	pedro osório s.a.r.l.	"uma canção comercial"	123	3rd
2	3	concha	"qualquer dia, quem diria"	78	6th
*/
Q: who was the last draw?
Code: ```result = df.loc[df['draw'] == df['draw'].max(), 'artist'].values[0]```

Title: 2007 New Orleans Saints season
/*
row_id	week	date	opponent	time	game site	tv	result/score	record
0	1	2007-9-6	indianapolis colts	t20:30 edt	rca dome	nbc	l 41 - 10	0-1
1	2	2007-9-16	tampa bay buccaneers	t13:0 edt	raymond james stadium	fox	l 31 - 14	0-2
2	3	2007-9-24	tennessee titans	t20:30 edt	louisiana superdome	espn	l 31 - 14	0-3
*/
Q: what number of games were lost at home?
Code: ```home_losses = df[df['game site'] != 'away']
result = len(home_losses[home_losses['result/score'].str.startswith('l')])```


Title: 2007-08 NHL season
/*
3 example rows:
SELECT * FROM w LIMIT 3;
date	team_a	team_b	place
2007-10-4	1	2	home
2008-1-1	1	3	home
2013-5-1	1	4	home
*/
Q: which game have the largest score difference?
Code: ```df['score_difference'] = abs(df['score_a'] - df['score_b'])
max_difference_index = df['score_difference'].idxmax()
result = df.loc[max_difference_index, ['date', 'team_a', 'team_b', 'score_a', 'score_b']].tolist()```


Title: Płock Governorate
/*
row_id	language	number	percentage (%)	males	females
0	polish	447685	80.86	216,794	230,891
1	yiddish	51215	9.25	24,538	26,677
2	german	35931	6.49	17,409	18,522
*/
Q: how many male and female german speakers are there?
Code: ```male_german_speakers = df.loc[df['language'] == 'german', 'males'].values[0]
female_german_speakers = df.loc[df['language'] == 'german', 'females'].values[0]
result = [male_german_speakers, female_german_speakers]```


Title: Electoral district of Lachlan
/*
row_id	member	party	term
0	john ryan	none	1859-1864
1	james martin	none	1864-1869
2	james watson	none	1869-1880
*/
Q: of the members of the third incarnation of the lachlan, who served the longest?
Code: ```df['term_duration'] = df['term'].apply(lambda x: int(x.split('-')[1]) - int(x.split('-')[0]))
longest_term_member = df.loc[df['term_duration'].idxmax(), 'member']
result = longest_term_member```"""

QUERY_NL2CODE_COMPLETE = """Please complete the prompt following the format above.
Title: {title}
/*
{table}
*/
Q: {question}
Output ```your_code_here``` with no other texts.
Code:"""


SELF_CORREC_INS_NL2CODE_COMPLETE = """{context}
Q: {question}
Last Error: {last_error}
Code: {a}"""