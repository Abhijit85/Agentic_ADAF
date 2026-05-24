IMPUTATER_EVALUATOR_DEMO = """# Task Description

Given table with missing value to be `[n.a.]`, you are required to impute the missing values in the table.

# Demonstration

## Demonstration 1

Table:
/*
pos | rider | manufacturer | time_retired | points
---|---|---|---|---
1 | loris capirossi | honda | 38:04.730 | 25.0
2 | valentino rossi | aprilia | +0.180 | 20.0
3 | jeremy mcwilliams | aprilia | +0.534 | 16.0
4 | tohru ukawa | honda | +0.537 | 13.0
5 | shinya nakano | yamaha | +0.742 | 11.0
6 | ralf waldmann | aprilia | +7.019 | 10.0
7 | franco battaini | aprilia | +20.889 | 9.0
8 | stefano perugini | honda | +20.891 | 8.0
9 | jason vincent | honda | +21.310 | 7.0
10 | anthony west | tsr-honda | +26.816 | 6.0
11 | alex hofmann | tsr-honda | +26.933 | 5.0
12 | sebastian porto | yamaha | +27.054 | 4.0
13 | tomomi manako | yamaha | +27.903 | 3.0
14 | masaki tokudome | tsr-honda | +33.161 | 2.0
15 | jarno janssen | tsr-honda | +56.248 | 1.0
16 | luca boscoscuro | tsr-honda | +56.432 | [n.a.]
17 | johann stigefelt | yamaha | +1:07.433 | [n.a.]
18 | julien allemand | tsr-honda | +1:16.347 | [n.a.]
*/
Please imputate the missing values in the column `points`.
Output: ```[25.0, 20.0, 16.0, 13.0, 11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 0.0, 0.0]```

## Demonstration 2

Original Table:
/*
row_id | tour | report | venue | prize_money_usd | date_finish | official_title | city | date_start
---|---|---|---|---|---|---|---|---
1 | 1 | report | stadium badminton kuala lumpur | 200000 | january 21 | malaysia super series | kuala lumpur | january 16
2 | 2 | report | seoul national university gymnasium | 300000 | january 28 | korea open super series | seoul | january 23
3 | 3 | report | national indoor arena | 200000 | march 11 | all england super series | birmingham | march 6
4 | 4 | report | st. jakobshalle | 200000 | march 18 | swiss open super series | basel | march 12
5 | 5 | report | singapore indoor stadium | 200000 | may 6 | singapore super series | singapore | may 1
*/

Processed Table:
/*
row_id | tour | report | venue | prize_money_usd | date_finish | official_title | city | date_start | duration_days
---|---|---|---|---|---|---|---|---|---
1 | 1 | report | stadium badminton kuala lumpur | 200000 | january 21 | malaysia super series | kuala lumpur | january 16 | 5
2 | 2 | report | seoul national university gymnasium | 300000 | january 28 | korea open super series | seoul | january 23 | 5
3 | 3 | report | national indoor arena | 200000 | march 11 | all england super series | birmingham | march 6 | 5
4 | 4 | report | st. jakobshalle | 200000 | march 18 | swiss open super series | basel | march 12 | 6
5 | 5 | report | singapore indoor stadium | 200000 | may 6 | singapore super series | singapore | may 1 | 5
*/

Logical Operator: Augment(req="Calculate the duration in days between date_start and date_finish. If the event is marked as "cancelled", the duration should be 0.", cols=['date_start', 'date_finish'])

Output: ```Yes``` The duration is correctly calculated.

## Demonstration 3

Original Table:
/*
row_id | column_from | honours | to | nationality | comments | name
---|---|---|---|---|---|---
1 | 2012-07-01 | [n.a.] | present | denmark | [n.a.] | henrik jensen
2 | 2012-06-18 | [n.a.] | 23 june 2012 | denmark | caretaker for one league match | john 'tune' kristiansen
3 | 2012-01-01 | won promotion to the third tier | 18 june 2012 | denmark | [n.a.] | peer f. hansen
4 | 2010-07-27 | won promotion to the fourth tier | 30 december 2011 | denmark | originally had contract until summer 2012 | john 'tune' kristiansen
5 | 2010-07-17 | [n.a.] | 27 july 2010 | denmark | never coached the team in a match | rene heitmann
*/

Processed Table:
/*
row_id | column_from | honours | to | nationality | comments | name | standardized_to
---|---|---|---|---|---|---|---
1 | 2012-07-01 | [n.a.] | present | denmark | [n.a.] | henrik jensen | 9999-12-31
2 | 2012-06-18 | [n.a.] | 23 june 2012 | denmark | caretaker for one league match | john 'tune' kristiansen | 2012-06-23
3 | 2012-01-01 | won promotion to the third tier | 18 june 2012 | denmark | [n.a.] | peer f. hansen | 2012-06-18
4 | 2010-07-27 | won promotion to the fourth tier | 30 december 2011 | denmark | originally had contract until summer 2012 | john 'tune' kristiansen | 2011-12-30
5 | 2010-07-17 | [n.a.] | 27 july 2010 | denmark | never coached the team in a match | rene heitmann | 2010-07-27
*/

Logical Operator: Normalize(req="Standard the column `to` to sortable string like 'YYYY-MM-DD'. Handle special cases like 'present' by replacing them with a future date like '9999-12-31'.", cols=['to'])

Output: ```Yes``` The column `to` is correctly standardized."""

IMPUTATER_EVALUATOR_QUERY = """# Evaluation

Original Table:
/*
{in_tbl}
*/

Processed Table:
/*
{out_tbl}
*/

Logical Operator: {op}

Output ```yes_or_not``` with NO EXTRA Texts.
Output: """