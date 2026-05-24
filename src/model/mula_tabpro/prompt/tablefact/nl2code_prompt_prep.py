DEMO_NL2CODE_PREP = """You are a agent to generate code for table fact verification tasks. Given a table along with its title and a statement, please generate code to deduce whether the statement is True or False. The code should process the table stored in a pandas.DataFrame Object `df` and the final result should be a boolean value stored in the variable `result`.

Title: cultural interest fraternities and sororities
/*
row_id	type
0	fraternity
1	sorority
2	sorority
*/
Statement: 4 of the cultural interest fraternity and sorority be fraternity while 3 be a sorority
Code: ```fraternity_count = df[df['type'] == 'fraternity'].shape[0]
sorority_count = df[df['type'] == 'sorority'].shape[0]

result = (fraternity_count == 4) and (sorority_count == 3)```

Title: british records in athletics
/*
row_id	event	place
0	5 km	søfteland , norway
1	5 miles	york , united kingdom
2	10 km	burrator , united kingdom
*/
Statement: there be 8 different event that take place within the united kingdom
Code: ```uk_events = df[df['place'].str.contains('united kingdom', case=False)]
unique_uk_events = uk_events['event'].unique()
unique_uk_events_count = len(unique_uk_events)
result = (unique_uk_events_count == 8)```

Title: jeev milkha singh
/*
row_id	tournament	events	cuts made
0	masters tournament	3	2
1	us open	4	3
2	the open championship	2	1
*/
Statement: the number of cut made in the pga championship tournament be smaller than the number of event
Code: ```pga_championship = df[df['tournament'] == 'pga championship']
if not pga_championship.empty:
    cuts_made = pga_championship['cuts made'].values[0]
    events = pga_championship['events'].values[0]
    result = (cuts_made < events)
else:
    result = False```

Title: 2008 women 's british open
/*
row_id	place	player	to par
0	t1	yuri fudoh	10
1	t1	jiyai shin	10
2	3	juli inkster	9
*/
Statement: kristie kerr , tie for 4th place , finish the round 1 stroke under lorena ochoa of mexico
Code: ```kerr_ochoa = df[df['player'].isin(['kristie kerr', 'lorena ochoa'])]

# Check if both players are present in the DataFrame
if len(kerr_ochoa) == 2:
    kerr_to_par = kerr_ochoa[kerr_ochoa['player'] == 'kristie kerr']['to par'].values[0]
    ochoa_to_par = kerr_ochoa[kerr_ochoa['player'] == 'lorena ochoa']['to par'].values[0]
    kerr_place = kerr_ochoa[kerr_ochoa['player'] == 'kristie kerr']['place'].values[0]
    is_kerr_tied_for_4th = 't4' in kerr_place
    result = is_kerr_tied_for_4th and (kerr_to_par == ochoa_to_par - 1)
else:
    result = False```

Title: connecticut public radio
/*
row_id-------frequency
0-------91.9 fm
1-------88.5 fm
2-------90.5 fm ( hd ) connecticut public radio
*/
Statement: there be 3 station with a call sign number in the 90s
Code: ```stations_in_90s = df[df['frequency'].str.contains(r'^[9][0-9]', na=False)]
num_stations_in_90s = stations_in_90s.shape[0]
expected_stations = 3
result = (num_stations_in_90s == expected_stations)```

Title: 1987 masters tournament
/*
row_id	player	score	
0	larry mize	70 + 72 + 72 + 71 = 285	
1	bernhard langer	73 + 71 + 70 + 71 = 285	
2	greg norman	73 + 74 + 66 + 72 = 285	
*/
Statement: bernhard m. langer have more point than roger maltbie during the 1987 master tournament
Code: ```langer_maltbie = df[df['player'].isin(['bernhard langer', 'roger maltbie'])]
if len(langer_maltbie) == 2:
    langer_score = langer_maltbie[langer_maltbie['player'] == 'bernhard langer']['score'].values[0]
    maltbie_score = langer_maltbie[langer_maltbie['player'] == 'roger maltbie']['score'].values[0]
    langer_total_points = sum([int(s) for s in langer_score.split(' + ')])
    maltbie_total_points = sum([int(s) for s in maltbie_score.split(' + ')])
    result = (langer_total_points > maltbie_total_points)
else:
    result = False```

Title: 1976 world junior figure skating championships
/*
row_id	rank	nation	
0	1	canada	
1	2	united states	
2	3	australia	
*/
Statement: 2 of the 7 top - ranked figure skate team be from france
Code: ```top_ranked_teams = df[df['rank'] <= 7]
french_teams = top_ranked_teams[top_ranked_teams['nation'].str.contains('france', case=False)]
num_french_teams = french_teams.shape[0]
result = (num_french_teams == 2)```

Title: jason chambers
/*
row_id	opponent	event	round
0	dan new	tfc - power fights	1
1	rene gonzalez	mainstream mma - cold war	n / a
2	tristan yunker	tfc 7 - total fight challenge 7	1
*/
Statement: in mac - midwest absolute challenge , the player be defeat by dan spychalski in 1 round
Code: ```mac_midwest_challenge = df[df['event'].str.contains('mac - midwest absolute challenge', case=False)]
spychalski_match = mac_midwest_challenge[mac_midwest_challenge['opponent'].str.contains('dan spychalski', case=False)]

if not spychalski_match.empty:
    spychalski_round = spychalski_match['round'].values[0]
    result = (spychalski_round == 1)
else:
    result = False```"""

QUERY_NL2CODE_PREP = """Please complete the prompt following the format above.
Title: {title}
/*
{table}
*/
Statement: {question}
Output ```your_code_here``` with no other texts.
Code:"""


SELF_CORREC_INS_NL2CODE_PREP = """{context}
Statement: {question}
Last Error: {last_error}
Code: {a}"""