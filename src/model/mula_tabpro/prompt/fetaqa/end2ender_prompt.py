DEMO_END2ENDER = """Here is the table to answer this question. Please use one brief sentence to answer the question.

Title: Results of World U-17 Hockey Challenge
/*
col : year | gold | silver | bronze
row1 : 2019 | - | - | -
row2 : 2018 | russia | finland | sweden
row3 : 2017 | united states | canada red | czech republic
row4 : 2016 | sweden | canada black | russia
row5 : 2015 | canada white | russia | sweden
*/
Question: What countries did the World U-17 Hockey Challenge attract after 2016?
Answer: The World U-17 Hockey Challenge attracted U-17 teams from Russia, Finland, Sweden, the United States, Canada, and the Czech Republic after 2016.


Title: Flash Airlines of Flash Airlines
/*
col : aircraft | exited | fate
row1 : boeing 737-3q8 | 3 january 2004 | crashed as flash airlines flight 604
row2 : boeing 737-3q8 | 5 march 2004 | became n271lf with ilfc
*/
Question: When did Flash Airlines shut down?
Answer: Flash Airlines' last plane, a Boeing 737-3Q8, exited service in 5 March 2004 because it became N271LF with ILFC.


Title: Results of 1932 United States presidential election in North Dakota
/*
col : party_democratic | candidate | votes | percent
row1 : democratic | franklin d. roosevelt | 178,350 | 69.59%
row2 : republican | herbert hoover (inc.) | 71,772 | 28.00%
row3 : socialist | norman thomas | 3,521 | 1.37%
row4 : liberty | william hope harvey | 1,817 | 0.71%
row5 : total votes | total votes | 256,290 | 100%
*/
Question: Who won the 1932 United States presidential election in North Dakota and what was the vote breakdown?
Answer: In the 1932 United States presidential election in North Dakota, Franklin D. Roosevelt of the Democratic party won with 69.59% of the popular vote and Herbert Hoover of the Republican party achieved 28.00%.


Title: Competition record of Luchia Yishak
/*
col : year | competition | venue | position | notes
row1 : 1990 | african championships | cairo, egypt | 2nd | 3000 metres
row2 : 1991 | world cross country championships | antwerp, belgium | 4th | long race
row3 : 1991 | all-africa games | cairo, egypt | 2nd | 3000 m
row4 : 1992 | world cross country championships | boston, united states | 10th | long race
row5 : 1992 | world cross country championships | boston, united states | 3rd | team race
*/
Question: What was Luchia Yishak's position in the 1990 African Championships?
Answer: Luchia Yishak was the runner-up in the 3000 m at the 1991 All-Africa Games.

Title: In of 2002-03 Yeovil Town F.C. season
/*
col : date | name | from | fee
row1 : 10 may 2002 | williams, gavingavin williams | hereford united | 22,500
row2 : 1 july 2002 | demba, abdoulayeabdoulaye demba | oostende | free (released)
row3 : 22 august 2002 | forinton, howardhoward forinton | torquay united | free (released)
row4 : 30 september 2002 | el-kholti, abdouabdou el-kholti | raja casablanca | free (released)
row5 : 28 november 2002 | jackson, kirkkirk jackson | stevenage borough | 20,000
row6 : 28 november 2002 | aggrey, jimmyjimmy aggrey | harrow borough | free (released)
row7 : 4 february 2003 | gall, kevinkevin gall | bristol rovers | free
row8 : 14 february 2003 | mustoe, neilneil mustoe | stevenage borough | free
*/
Question: Who were the first two players to join Yeovil Town F.C. in the 2002-03 season?
Answer: In the 2002-03 season, Gavin Williams from Hereford United joined Yeovil Town F.C. for a fee of £22,500, and Abdoulaye Demba Oostende joined for free.

Title: Filmography of Mark Lewis (storyteller)
/*
col : year | title | role | other_notes
row1 : 1995 | northern exposure | rusty keyes | -
row2 : 1997 | american river journals | host | won 1997 telly award
row3 : - | the tonight show with jay leno | guest performer | -
row4 : 2011 | grimm | robin's grandfather | pilot (one episode)
row5 : 2012 | leverage | santa claus/jack | the ho ho ho job
*/
Question: Which TV series did Mark Lewis perform in the year 1995 and 2012?
Answer: Mark Lewis performed on the TV Northern Exposure in 1995 and The Ho Ho Ho Job's Leverage as Santa/Jack in 2012.
"""


QUERY_END2ENDER = """Here is the table to answer this question. Use one brief sentence to answer the question.
Title: {title}
/*
{table}
*/
Question: {question}
The answer is:"""