"""Commit-by-commit spec for the farm-trade-support Git history.

Read by ../build_history.py, which replays it into a fresh repository.

AUTHORS: key -> (name, email). All names and emails are made up.

COMMITS: in replay order. Each commit is a dict:
  id       short label, used by "from" and "merge"
  branch   branch the commit goes on
  from     only on the first commit of a new branch: id of the commit the
           branch starts from
  merge    only on merge commits: branch whose current head is merged in
           (the commit's tree is a three-way merge, so "files" is not used)
  author   key in AUTHORS (author and committer are the same person)
  date     ISO 8601 with the author's local UTC offset
  message  full commit message: subject, blank line, body saying why
  files    path -> source, applied on top of the first parent's tree:
             "project"        the file as it is in ../project/ (final state)
             "files/<name>"   a stored earlier version in files/
             "derive:<name>"  an earlier version computed by build_history.py
             None             delete the file
"""

AUTHORS = {
    "amina": ("Amina Haddad", "amina.haddad@example.org"),   # team lead, Brussels
    "tomas": ("Tomas Ferreira", "tomas.ferreira@example.org"),  # R analyst, Sao Paulo
    "grace": ("Grace Owusu", "grace.owusu@example.org"),     # Stata analyst, Washington
    "mei": ("Mei Lin Tan", "meilin.tan@example.org"),        # Python analyst, Singapore
}

COMMITS = [
    # ---- Set-up on main ----------------------------------------------------
    {
        "id": "M1", "branch": "main", "author": "amina",
        "date": "2026-03-02T09:40:12+01:00",
        "message": """Start the farm trade project from the team template

Using the template gives every analyst the same folder layout and the
same rules for data, code and outputs, so we can read each other's work.
The master scripts are empty placeholders, one per language.
""",
        "files": {
            "README.md": "files/README.v1.md",
            "AGENTS.md": "files/AGENTS.v1.md",
            "CLAUDE.md": "project",
            ".gitignore": "files/gitignore.v1",
            ".gitattributes": "project",
            "code/README.md": "files/code-README.v1.md",
            "code/00_master.py": "derive:empty",
            "code/00_master.R": "derive:empty",
            "code/00_master.do": "derive:empty",
            "reports/.gitkeep": "derive:empty",
        },
    },
    {
        "id": "M2", "branch": "main", "author": "amina",
        "date": "2026-03-04T14:05:47+01:00",
        "message": """Document the raw sources before anyone downloads them

The FAOSTAT and CEPII files are over 600 MB zipped, too large to commit.
Recording the links, versions and licences means anyone can rebuild the
clean data later, and we cite the sources correctly from the start.
""",
        "files": {"data/raw/README.md": "derive:raw_readme_v1"},
    },
    {
        "id": "M3", "branch": "main", "author": "amina",
        "date": "2026-03-09T10:22:31+01:00",
        "message": """Add clean farm trade data for 27 countries in 6 blocs

One row per exporter, importer and year, 2000-2019, with the CEPII
gravity variables joined on. Everyone works from the same panel instead
of cleaning FAOSTAT on their own.

Clean data and outputs are now committed (.gitignore changed): not
everyone on the team has R or Stata, and they still need to see every
result without running the code.
""",
        "files": {
            "data/clean/countries.csv": "project",
            "data/clean/farm_trade.csv": "derive:farm_trade_v1",
            "data/clean/README.md": "derive:clean_readme_v1",
            ".gitignore": "derive:gitignore_v2",
        },
    },
    # ---- Python branch starts early, from the first clean data ------------
    {
        "id": "P1", "branch": "python/bloc-charts", "from": "M3", "author": "mei",
        "date": "2026-03-10T16:48:05+08:00",
        "message": """Add up farm trade by bloc pair and year

The bloc charts need trade between blocs, not between countries.
Writing the totals to outputs/data/ as a tidy file means the charts,
and later the other languages, read one small table instead of the
full country panel.
""",
        "files": {
            "code/00_master.py": "files/00_master.v1.py",
            "code/01_bloc_trade.py": "files/01_bloc_trade.v1.py",
        },
    },
    # ---- Main: synthetic subsidies and the plan ----------------------------
    {
        "id": "M4", "branch": "main", "author": "amina",
        "date": "2026-03-11T11:15:20+01:00",
        "message": """Add synthetic farm support data for the Stata part

We have no comparable subsidy data for all 27 countries yet. A simulated
panel with known elasticities (direct 0.10, indirect 0.24, total 0.34)
lets Grace build and test the path model now, and check that sem
recovers the true values. The file is flagged as synthetic in
data/clean/README.md so nobody quotes it as real.
""",
        "files": {
            "data/clean/farm_support.csv": "project",
            "data/clean/README.md": "derive:clean_readme_v2",
            "data/raw/README.md": "project",
        },
    },
    {
        "id": "M5", "branch": "main", "author": "amina",
        "date": "2026-03-12T15:30:44+01:00",
        "message": """Write the project purpose and split the work by language

Each analyst works in the tool they know best: Python for the bloc
charts, R for the gravity model, Stata for the subsidy path model.
Each part gets its own branch, so the parts can merge when they are
ready without waiting for each other.
""",
        "files": {"README.md": "derive:readme_v2"},
    },
    {
        "id": "P2", "branch": "python/bloc-charts", "author": "mei",
        "date": "2026-03-16T10:05:33+08:00",
        "message": """Chart farm trade between blocs over time

A first look at how bloc-to-bloc trade grew from 2000 to 2019, to see
which flows are worth a closer look before we model anything.
""",
        "files": {
            "code/00_master.py": "files/00_master.v2.py",
            "code/02_bloc_trend.py": "project",
        },
    },
    # ---- R branch -----------------------------------------------------------
    {
        "id": "R1", "branch": "r/gravity", "from": "M5", "author": "tomas",
        "date": "2026-03-17T10:42:18-03:00",
        "message": """Estimate a PPML gravity model of farm trade

PPML instead of OLS on log trade: it keeps the zero flows and stays
consistent when the errors are heteroskedastic, which log-linear OLS
does not. Exporter-year and importer-year fixed effects absorb GDP and
multilateral resistance, so GDP does not enter the formula.
""",
        "files": {
            "code/00_master.R": "files/00_master.v1.R",
            "code/01_gravity.R": "files/01_gravity.v1.R",
        },
    },
    {
        "id": "R2", "branch": "r/gravity", "author": "tomas",
        "date": "2026-03-23T15:20:09-03:00",
        "message": """save gravity table as txt and csv

console output is gone after each run, this way we can compare runs
""",
        "files": {"code/01_gravity.R": "files/01_gravity.v2.R"},
    },
    {
        "id": "P3", "branch": "python/bloc-charts", "author": "mei",
        "date": "2026-03-24T17:12:51+08:00",
        "message": """Add a 2000 vs 2019 summary table and commit the tidy bloc data

The table answers the first question people ask: which bloc flows grew
most. The tidy file goes in so Tomas can check the totals against his
gravity data in R without running Python.
""",
        "files": {
            "code/01_bloc_trade.py": "project",
            "outputs/data/bloc_trade.csv": "derive:bloc_trade_v1",
        },
    },
    # ---- Stata branch -------------------------------------------------------
    {
        "id": "S1", "branch": "stata/sem-passthrough", "from": "M5", "author": "grace",
        "date": "2026-03-25T09:55:40-04:00",
        "message": """Load the farm support data in Stata and take logs

The path model is in elasticities, so every variable enters in logs.
The assert stops the run if a zero or missing value would turn into a
missing log and silently drop rows. Stata log files are now ignored:
they change on every run and hold nothing the outputs do not.
""",
        "files": {
            "code/00_master.do": "files/00_master.v1.do",
            "code/01_prepare.do": "files/01_prepare.v1.do",
            ".gitignore": "project",
        },
    },
    {
        "id": "R3", "branch": "r/gravity", "author": "tomas",
        "date": "2026-03-31T11:08:27-03:00",
        "message": """Write tidy gravity coefficients to outputs/data

The readable table is hard to parse from other code. A tidy file with
term, estimate, std_error and p_value lets Mei and Grace reuse the
results in Python or Stata, for example in a dashboard.
""",
        "files": {"code/01_gravity.R": "derive:gravity_v3"},
    },
    {
        "id": "P4", "branch": "python/bloc-charts", "author": "mei",
        "date": "2026-04-01T14:36:02+08:00",
        "message": """Add a 2019 heatmap of trade between blocs

The trend chart shows growth but not the structure. A heatmap shows who
trades with whom in one year at a glance, including flows inside each
bloc.
""",
        "files": {
            "code/00_master.py": "files/00_master.v3.py",
            "code/03_bloc_heatmap.py": "files/03_bloc_heatmap.v1.py",
        },
    },
    {
        "id": "S2", "branch": "stata/sem-passthrough", "author": "grace",
        "date": "2026-04-01T16:20:15-04:00",
        "message": """Estimate the subsidy pass-through as a path model with sem

A single regression gives only the total effect of subsidy on output.
sem estimates both equations together, and estat teffects splits the
total into a direct effect and an indirect one through fertiliser use,
which is the question the ministry asked.
""",
        "files": {
            "code/00_master.do": "files/00_master.v2.do",
            "code/02_sem.do": "files/02_sem.v1.do",
        },
    },
    # ---- Unit bug found by Mei, fixed by Amina on a fix branch -------------
    {
        "id": "F1", "branch": "fix/trade-units", "from": "M5", "author": "amina",
        "date": "2026-04-06T10:12:36+02:00",
        "message": """Convert FAOSTAT trade values from thousand USD to USD

The colour bar on Mei's heatmap topped out at a fraction of a billion,
far too small for trade between whole blocs. FAOSTAT reports trade
values in thousand US dollars, and the clean file kept them as
they came while the README said US dollars. trade_usd is now multiplied
by 1,000, and the README says where the conversion happens.

PPML coefficients do not change with the scale of trade, but every
total and chart in USD does: rerun anything built on farm_trade.csv.
""",
        "files": {
            "data/clean/farm_trade.csv": "project",
            "data/clean/README.md": "project",
        },
    },
    {
        "id": "MF", "branch": "main", "merge": "fix/trade-units", "author": "amina",
        "date": "2026-04-07T09:30:03+02:00",
        "message": """Merge branch 'fix/trade-units'

Brings the corrected trade values to main so the R and Python branches
can pick them up before they write any outputs.
""",
    },
    {
        "id": "PM", "branch": "python/bloc-charts", "merge": "main", "author": "mei",
        "date": "2026-04-08T09:18:42+08:00",
        "message": """Merge branch 'main' into python/bloc-charts

Picks up the trade unit fix, so the bloc totals come out in US dollars.
""",
    },
    {
        "id": "R4", "branch": "r/gravity", "author": "tomas",
        "date": "2026-04-08T13:45:11-03:00",
        "message": """Cluster standard errors by country pair

Grace reviewed the table and pointed out that the t-statistics were in
the hundreds. Flows of one pair are correlated over time, so the default
IID standard errors are far too small. Clustering by pair gives honest
uncertainty; the coefficients do not change.
""",
        "files": {"code/01_gravity.R": "project"},
    },
    {
        "id": "P5", "branch": "python/bloc-charts", "author": "mei",
        "date": "2026-04-09T15:40:26+08:00",
        "message": """Write the value in each heatmap cell

With trade now in US dollars the cells hold readable billions. Printing
them saves readers from guessing values from the colour scale; white
text keeps the numbers readable on dark cells.
""",
        "files": {"code/03_bloc_heatmap.py": "project"},
    },
    {
        "id": "S3", "branch": "stata/sem-passthrough", "author": "grace",
        "date": "2026-04-09T11:02:58-04:00",
        "message": """Write the sem effects to Excel and to a tidy CSV

The ministry team reads Excel, so the effects go to a formatted sheet
with putexcel. The tidy CSV has the same rows in the agreed columns, so
the other languages can read it without Stata.
""",
        "files": {"code/02_sem.do": "derive:sem_v2_as_02"},
    },
    {
        "id": "P6", "branch": "python/bloc-charts", "author": "mei",
        "date": "2026-04-13T10:25:14+08:00",
        "message": """Regenerate the bloc outputs on the corrected trade data

The tidy file from March was in thousand USD. All Python outputs are
rebuilt from the fixed farm_trade.csv. The master script now creates
the output folders first, because a fresh checkout of main does not
have outputs/tables or outputs/figures yet.
""",
        "files": {
            "code/00_master.py": "project",
            "outputs/data/bloc_trade.csv": "project",
            "outputs/tables/bloc_trade.csv": "project",
            "outputs/figures/bloc_trend.png": "project",
            "outputs/figures/bloc_heatmap_2019.png": "project",
        },
    },
    {
        "id": "RM", "branch": "r/gravity", "merge": "main", "author": "tomas",
        "date": "2026-04-13T14:10:37-03:00",
        "message": """Merge branch 'main' into r/gravity

Picks up the trade unit fix before the R outputs are written, so the
saved table reports the model on trade in US dollars.
""",
    },
    {
        "id": "R5", "branch": "r/gravity", "author": "tomas",
        "date": "2026-04-14T16:30:50-03:00",
        "message": """Plot the gravity coefficients and commit the R outputs

A coefficient plot with 95% intervals shows at a glance which drivers
matter: distance cuts trade, a trade agreement raises it, a common
language adds nothing once the fixed effects are in. Base graphics only,
so nobody needs another package. Outputs are committed for readers
without R.
""",
        "files": {
            "code/00_master.R": "project",
            "code/02_coef_plot.R": "project",
            "outputs/tables/gravity.txt": "project",
            "outputs/tables/gravity.csv": "project",
            "outputs/data/gravity_coefs.csv": "project",
            "outputs/figures/gravity_coefs.png": "project",
        },
    },
    {
        "id": "MR", "branch": "main", "merge": "r/gravity", "author": "amina",
        "date": "2026-04-20T10:05:22+02:00",
        "message": """Merge branch 'r/gravity'

The gravity model is reviewed (clustered errors) and runs on the
corrected trade data. Merging it first, as the Python and Stata parts
are still in progress.
""",
    },
    {
        "id": "M6", "branch": "main", "author": "amina",
        "date": "2026-04-21T11:40:09+02:00",
        "message": """Document how to run the R part and what it produces

The R part is the first one on main. The README and code/README.md now
say how to run it and where its results are, so nobody has to read the
scripts to find them.
""",
        "files": {
            "README.md": "derive:readme_v3",
            "code/README.md": "derive:code_readme_v2",
        },
    },
    {
        "id": "S4", "branch": "stata/sem-passthrough", "author": "grace",
        "date": "2026-04-22T10:30:31-04:00",
        "message": """Add a scatter of output against subsidy before the path model

A plain scatter with a fitted line shows the total relation before sem
splits it, a quick check that the model result is plausible. The sem
do-file moves to 03 so the files still run in number order, and the
master creates the output folders it writes to.
""",
        "files": {
            "code/00_master.do": "derive:master_do_v3",
            "code/02_figure.do": "derive:figure_v1",
            "code/02_sem.do": None,
            "code/03_sem.do": "derive:sem_v2_as_03",
        },
    },
    {
        "id": "MP", "branch": "main", "merge": "python/bloc-charts", "author": "amina",
        "date": "2026-04-29T09:50:48+02:00",
        "message": """Merge branch 'python/bloc-charts'

The bloc charts and tables are rebuilt on the corrected trade data, so
every total on main is now in US dollars.
""",
    },
    {
        "id": "M7", "branch": "main", "author": "amina",
        "date": "2026-04-30T14:15:26+02:00",
        "message": """Document how to run the Python part and what it produces

Most readers have Python but not R or Stata, so this is the part they
will run themselves. The README lists the command and the two packages
it needs, and every Python output, so nobody has to guess.
""",
        "files": {
            "README.md": "derive:readme_v4",
            "code/README.md": "derive:code_readme_v3",
        },
    },
    {
        "id": "S5", "branch": "stata/sem-passthrough", "author": "grace",
        "date": "2026-05-05T15:05:19-04:00",
        "message": """Make the do-files fail early with a clear message

Tomas ran 03_sem.do on its own and got "variable ln_output not found",
which does not say what to do. 02 and 03 now check that the prepared
data are in memory and say to run 01 first. 01 also checks that every
country code joins countries.csv, so a typo cannot silently drop a
country from the model.
""",
        "files": {
            "code/01_prepare.do": "project",
            "code/02_figure.do": "project",
            "code/03_sem.do": "project",
        },
    },
    {
        "id": "S6", "branch": "stata/sem-passthrough", "author": "grace",
        "date": "2026-05-07T10:48:03-04:00",
        "message": """commit Stata outputs

sem gets the true elasticities back within 0.01 (direct 0.105, indirect
0.238, total 0.342). Committed so people without Stata can see them.
""",
        "files": {
            "outputs/tables/sem_elasticities.xlsx": "project",
            "outputs/figures/sem_scatter.png": "project",
            "outputs/data/sem_effects.csv": "project",
        },
    },
    {
        "id": "MS", "branch": "main", "merge": "stata/sem-passthrough", "author": "amina",
        "date": "2026-05-12T10:20:55+02:00",
        "message": """Merge branch 'stata/sem-passthrough'

The path model recovers the known elasticities, and the do-files stop
with clear messages when run out of order. All three parts are now on
main.
""",
    },
    {
        "id": "M8", "branch": "main", "author": "amina",
        "date": "2026-05-13T16:00:41+02:00",
        "message": """Document how to run the Stata part and what it produces

With all three parts merged, the README explains that the parts are
independent and that every output is committed, so a reader with only
Python still sees the R and Stata results.
""",
        "files": {
            "README.md": "derive:readme_v5",
            "code/README.md": "project",
        },
    },
    {
        "id": "M9", "branch": "main", "author": "amina",
        "date": "2026-06-03T09:35:17+02:00",
        "message": """Tell coding assistants about this project and how to help

New team members use coding assistants to find their way around. AGENTS.md
now describes the three parts, flags the synthetic data and fixes the
tidy output columns. It also asks the assistant to explain a change
before making it, so people learn the project instead of only getting
edits.
""",
        "files": {"AGENTS.md": "project"},
    },
    # ---- Second fix: found by Amina, fixed by Grace ------------------------
    {
        "id": "G1", "branch": "fix/stata-root-check", "from": "M9", "author": "grace",
        "date": "2026-06-16T11:20:08-04:00",
        "message": """Stop the Stata master early when not run from the project root

Amina ran the master from inside code/ and got "file
data/clean/farm_support.csv not found" deep inside 01_prepare.do. The
master now checks for the data first and says to run from the project
root, the folder that holds README.md.
""",
        "files": {"code/00_master.do": "project"},
    },
    {
        "id": "MG", "branch": "main", "merge": "fix/stata-root-check", "author": "amina",
        "date": "2026-06-18T10:00:30+02:00",
        "message": """Merge branch 'fix/stata-root-check'

Small fix: a clear message instead of a confusing error when the Stata
master is run from the wrong folder.
""",
    },
    {
        "id": "M10", "branch": "main", "author": "amina",
        "date": "2026-07-08T14:30:12+02:00",
        "message": """reports/: readme instead of .gitkeep

notes and write-ups go here, not in outputs/
""",
        "files": {"reports/.gitkeep": None, "reports/README.md": "project"},
    },
    {
        "id": "M11", "branch": "main", "author": "amina",
        "date": "2026-08-14T11:10:45+02:00",
        "message": """Name who works on each part in the README

Readers outside the team asked whom to contact about each part. The Git
history has the names too, but the README is where people look first.
""",
        "files": {"README.md": "project"},
    },
]
