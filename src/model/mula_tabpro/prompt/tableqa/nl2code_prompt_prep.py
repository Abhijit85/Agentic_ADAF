DEMO_NL2CODE_PREP = """You are a agent to generate code for table question answering tasks. Given a table along with its title and a question, please generate code to generate the answer. The code should process the table stored in a pandas.DataFrame Object `df` and the final result should be a numerical value or a string or a list stored in the variable `result`.

Title: Fabrice Santoro
/*
row_id	name	career\nwin-loss
0	australian open	22-18
1	french open	17-20
2	wimbledon	11-14
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
row_id	draw	artist	
0	1	gonzaga coutinho	
1	2	pedro osório s.a.r.l.	
2	3	concha	
*/
Q: who was the last draw?
Code: ```result = df.loc[df['draw'] == df['draw'].max(), 'artist'].values[0]```

Title: 2007 New Orleans Saints season
/*
row_id	game site	result/score	
0	rca dome	l 41 - 10	
1	raymond james stadium	l 31 - 14	
2	louisiana superdome	l 31 - 14	
*/
Q: what number of games were lost at home?
Code: ```home_losses = df[df['game site'] != 'away']
result = len(home_losses[home_losses['result/score'].str.startswith('l')])```

Title: Płock Governorate
/*
row_id	language	males	females
0	polish	216,794	230,891
1	yiddish	24,538	26,677
2	german	17,409	18,522
*/
Q: how many male and female german speakers are there?
Code: ```male_german_speakers = df.loc[df['language'] == 'german', 'males'].values[0]
female_german_speakers = df.loc[df['language'] == 'german', 'females'].values[0]
result = [male_german_speakers, female_german_speakers]```


Title: Electoral district of Lachlan
/*
row_id	member	term
0	john ryan	1859-1864
1	james martin	1864-1869
2	james watson	1869-1880
*/
Q: of the members of the third incarnation of the lachlan, who served the longest?
Code: ```df['term_duration'] = df['term'].apply(lambda x: int(x.split('-')[1]) - int(x.split('-')[0]))
longest_term_member = df.loc[df['term_duration'].idxmax(), 'member']
result = longest_term_member```"""

QUERY_NL2CODE_PREP = """Please complete the prompt following the format above.
Title: {title}
/*
{table}
*/
Q: {question}
Output ```your_code_here``` with no other texts.
Code:"""


SELF_CORREC_INS_NL2CODE_PREP = """{context}
Q: {question}
Last Error: {last_error}
Code: {a}"""