# Partner Codex handoff — November 3, 2026

Paste the text below into Codex in your own course project folder.

---

Help me bring my FIN 67110 equity-research desk up to date and prepare the Week 3 COST verifier tests for Checkpoint 2. Work in my existing repository. Explain steps in plain English, about 80% of the way to ASD-STE100, keeping every number, condition, and qualification.

First inspect my AGENTS.md, README, Git status, Python version, dependencies, saved runs, and existing code. Preserve work in progress. Treat this handoff as context, not proof that files or features exist in my repository. My previously selected company was RTX; my partner's was NOC. Confirm the assignment from my files before changing a report.

## Skills

The reference project is https://github.com/IamAIman-sys/The-Boss-Trading-Desk . Its local history includes commit 93c6175, which adds a CrewAI skill pack under `.agents/skills/`. Check whether that commit or the skill pack is available remotely; do not assume local uncommitted files are on GitHub.

If my project lacks the pack, obtain it from that repository in a separate temporary checkout. Copy the relevant skill directories, their reference files, and `CREWAI-SKILLS-LICENSE.txt` into my project's `.agents/skills/`, without overwriting different existing skills. If the remote does not contain it, report exactly which files I need from my partner. Do not claim the skills were installed until you verify the files.

The eight skills are `check-crewai-api`, `build-flow`, `test-crewai-project`, `getting-started`, `design-agent`, `design-task`, `connect-tools-and-mcp`, and `ask-docs`. Read the applicable SKILL.md files before using them. Check the installed CrewAI version and follow the skills' version checks. Skills guide your coding work; they do not train models or automatically become the desk's runtime instructions.

## Existing design and reference-project status

The reference desk has:

- `equity_desk.py`: seven SEC steps: ticker-to-CIK lookup; latest 10-K, 10-Q, and Item 2.02 8-K selection with accession and EDGAR Accepted time; document and earnings-exhibit text downloads; current/prior annual XBRL facts; Python ratio calculations; quarterly revenue/EPS release lines; peer facts and operating margins.
- `research_desk.py`: Research Analyst, Financial Analyst, Investment Advisor, and Strategy Manager, with JSON handoffs and saved report evidence.
- `model_client.py`: Purdue GenAI Studio, using `gpt-oss:120b` in the reference project. This is a model identifier, not a separate API key for each role.
- `financial_datasets.py`: optional exact-date closing-price lookup and annual statement comparison. Options are `--fetch-price-date YYYY-MM-DD` and `--compare-financial-datasets`. SEC facts still drive the ratios. Manual `--price` remains supported.
- Financial Datasets evidence saved under ignored `runs/`: price, date, source, retrieval time, adjustment limitation, and statement comparisons. Missing values are not zero. Debt and capex need definition review. A numeric match is not a human audit.

The reference project's latest validation passed 38 offline tests and all seven data steps for NOC with RTX as a peer. The fetched NOC price was $510.65 for October 19, 2026. P/E used annual GAAP diluted EPS of $29.08, giving about 17.56x. Both companies had 12 numeric matches and 6 definition-review items across the current and prior years. These results do not prove that my repository passes.

Important: at handoff, the Financial Datasets changes were local and uncommitted. `flow_desk.py`, `test_flow_desk.py`, and `personas/research_analyst.md` were also untracked. The CrewAI flow was a partial Research Analyst implementation. It did not yet implement all four roles, the full Verifier, or `--verify-only`. Inspect current files before deciding what to reuse.

## Credentials and personal work

Use my own local `.env`. Never display, copy from my partner, commit, or put keys in model prompts. `API_KEY` is the Purdue key; `FINANCIAL_DATASETS_API_KEY` is a separate data-provider key. The reference settings are `API_BASE_URL=https://genai.rcac.purdue.edu/api` and `MODEL=gpt-oss:120b`; confirm my own provider access. Read `SEC_USER_AGENT` from `.env` and send it on requests. Keep `.env`, `.venv`, and local generated/vendor data out of Git.

Preserve completed Checkpoint 1 reports and audits. Do not copy another student's report, audit judgments, or persona as mine. Do not invent human or partner checks. Clearly distinguish automated verifier marks from human audit marks.

## Week 3 work

Read the current official requirements:

- https://cinderzhang.github.io/FIN67110-Fall2026/week-03/index.html
- https://cinderzhang.github.io/FIN67110-Fall2026/week-03/lab-04-the-team.html
- https://cinderzhang.github.io/FIN67110-Fall2026/week-03/lab-05-make-the-team-yours.html
- https://cinderzhang.github.io/FIN67110-Fall2026/grading.html
- https://cinderzhang.github.io/FIN67110-Fall2026/schedule.html

Use CrewAI Flows unless my existing project or instructions establish a different supported framework. Implement the fixed graph: seven data steps → Research Analyst → Financial Analyst → Investment Advisor → Strategy Manager → Verifier. Code controls order and the permitted retry. Keep role instructions in separate files under `roles/`. Each role receives only its assigned JSON input. The Manager checks the five required report sections and can send a failing part back once. No role runs more than twice.

The Verifier must run after the Manager on every full run, with no bypass flag. It receives only the compiled report, saved filing texts, and saved facts. It checks sourced numbers, exact XBRL tag/period values, filing lines, and ratio arithmetic in code, then uses a model to check period and definition meaning. It skips the Investment Advisor's thesis. Missing sources and ambiguous ratio definitions are unsupported. Save marks, supported corrections, and real citations. Never invent a correction when evidence is absent.

Support `--verify-only PATH` to run only the Verifier on a saved run. Save each run's inputs, outputs, original report, verified report, and marks in a new company/date/time folder. Keep the filings line first and the marks table immediately below it. Print every node as it starts. Runtime code must not hardcode company names.

Run COST twice with peers WMT, TGT, BJ and the same price used in my Lab 03 run. Recover that price from my evidence; do not substitute NOC's price or a current quote. Confirm identical node order and separate folders. Then prepare separate test copies:

1. Raise diluted EPS by $1 in a copied report and alter its quoted source line to match; leave the underlying filing evidence intact. The Verifier must mark it wrong and restore the actual 10-K figure with its real line.
2. Add annual revenue growth 4 percentage points above the rate computed from the two quoted annual revenues. Expect wrong or unsupported, with the correct arithmetic.
3. Verify a clean report whose 11 core claims I have personally checked and corrected. Expect all 11 correct. If that human audit is missing, tell me which checks remain; do not claim it exists.
4. Confirm no full-run path skips the Verifier. My partner must check the seeded EPS marks against the 10-K; leave that human check pending until supplied.

Checkpoint 2 requires a permanent commit link containing the agent team and the seeded-error verifier marks. The published deadline at handoff was November 5, 2026, at 11:59 PM Eastern; verify the current schedule and any extension I provide.

Lab 05 also requires three student-written personas, sourced Insight lines, a partner-selected company run, and a UI. I must write the personas myself. You may explain the six-part structure and connect my text to the code, but do not write the personas for me.

Start with a short gap assessment of my actual repository. Then complete the authorized code and automated tests for Lab 04, preserving existing work. Ask for only the missing personal inputs or human checks. Finish with the exact install, COST run, and verify-only commands for my operating system, saved evidence paths, test results, and remaining human tasks. Distinguish local work from committed, pushed, and submitted work.
