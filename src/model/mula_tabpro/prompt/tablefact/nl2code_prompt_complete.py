DEMO_NL2CODE_COMPLETE = """You are a agent to generate code for table fact verification tasks. Given a table along with its title and a statement, please generate code to deduce whether the statement is True or False. The code should process the table stored in a pandas.DataFrame Object `df` and the final result should be a boolean value stored in the variable `result`.

Title: cultural interest fraternities and sororities
/*
row_id	letters	organization	nickname	founding time	founding university	type
0	αεπ	alpha epsilon pi 1	aepi	1913-11-07 00:00:00	new york university	fraternity
1	αεφ	alpha epsilon phi 2	aephi	1909-10-24 00:00:00	barnard college	sorority
2	σαεπ	sigma alpha epsilon pi 3	sigma	1998-10-01 00:00:00	university of california , davis	sorority
*/
Statement: 4 of the cultural interest fraternity and sorority be fraternity while 3 be a sorority
Code: ```fraternity_count = df[df['type'] == 'fraternity'].shape[0]
sorority_count = df[df['type'] == 'sorority'].shape[0]

result = (fraternity_count == 4) and (sorority_count == 3)```

Title: british records in athletics
/*
row_id	event	data	athlete	date	place
0	5 km	t19:29	andi drake	1990-05-27 00:00:00	søfteland , norway
1	5 miles	32:38 +	ian mccombie	1985-03-23 00:00:00	york , united kingdom
2	10 km	40:17	chris maddocks	1989-04-30 00:00:00	burrator , united kingdom
*/
Statement: there be 8 different event that take place within the united kingdom
Code: ```uk_events = df[df['place'].str.contains('united kingdom', case=False)]
unique_uk_events = uk_events['event'].unique()
unique_uk_events_count = len(unique_uk_events)
result = (unique_uk_events_count == 8)```

Title: jeev milkha singh
/*
row_id	tournament	wins	top - 10	top - 25	events	cuts made
0	masters tournament	0	0	1	3	2
1	us open	0	0	0	4	3
2	the open championship	0	0	0	2	1
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
row_id	place	player	country	score	to par
0	t1	yuri fudoh	japan	66 + 68 = 134	10
1	t1	jiyai shin	south korea	66 + 68 = 134	10
2	3	juli inkster	united states	65 + 70 = 135	9
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
row_id	call sign	frequency	city of license	facility id	erp / power w	height m ( ft )	class
0	waic	91.9 fm	springfield , ma	1749	230	nan	b1
1	wedw - fm	88.5 fm	stamford , ct	13619	2000	nan	a
2	wnpr	90.5 fm ( hd ) connecticut public radio	meriden , ct	13627	18500	nan	b
*/
Statement: there be 3 station with a call sign number in the 90s
Code: ```stations_in_90s = df[df['frequency'].str.contains(r'^[9][0-9]', na=False)]
num_stations_in_90s = stations_in_90s.shape[0]
expected_stations = 3
result = (num_stations_in_90s == expected_stations)```

Title: 1987 masters tournament
/*
row_id	place	player	country	score	to par	money
0	t1	larry mize	united states	70 + 72 + 72 + 71 = 285	-3	playoff
1	t1	bernhard langer	spain	73 + 71 + 70 + 71 = 285	-3	playoff
2	t1	greg norman	australia	73 + 74 + 66 + 72 = 285	-3	playoff
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
row_id	rank	name	nation	points	places
0	1	sherri baier / robin cowan	canada	128.39	9
1	2	lorene mitchell / donald mitchell	united states	124.94	16
2	3	elizabeth cain / peter cain	australia	116.67	33
*/
Statement: 2 of the 7 top - ranked figure skate team be from france
Code: ```top_ranked_teams = df[df['rank'] <= 7]
french_teams = top_ranked_teams[top_ranked_teams['nation'].str.contains('france', case=False)]
num_french_teams = french_teams.shape[0]
result = (num_french_teams == 2)```

Title: jason chambers
/*
row_id	res	record	opponent	method	event	round
0	win	18 - 5 - 2	dan new	submission (rear naked choke)	tfc - power fights	1
1	win	17 - 5 - 2	rene gonzalez	decision (split)	mainstream mma - cold war	n / a
2	loss	16 - 5 - 2	tristan yunker	submission ( armbar )	tfc 7 - total fight challenge 7	1
*/
Statement: in mac - midwest absolute challenge , the player be defeat by dan spychalski in 1 round
Code: ```mac_midwest_challenge = df[df['event'].str.contains('mac - midwest absolute challenge', case=False)]
spychalski_match = mac_midwest_challenge[mac_midwest_challenge['opponent'].str.contains('dan spychalski', case=False)]

if not spychalski_match.empty:
    spychalski_round = spychalski_match['round'].values[0]
    result = (spychalski_round == 1)
else:
    result = False```"""

QUERY_NL2CODE_COMPLETE = """Please complete the prompt following the format above.
Title: {title}
/*
{table}
*/
Statement: {question}
Output ```your_code_here``` with no other texts.
Code:"""


SELF_CORREC_INS_NL2CODE_COMPLETE = """{context}
Statement: {question}
Last Error: {last_error}
Code: {a}"""