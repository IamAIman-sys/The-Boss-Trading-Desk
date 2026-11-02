# SEC equity-research data desk

Build the data side of an equity-research desk in Python, modeled on Section 3.1 of Francis & Zhang (2026); the model roles come later. Read my SEC User-Agent as SEC_USER_AGENT from the .env file in this folder and send it on every request. The program takes a ticker as its argument, an optional --peers list of tickers, an optional --price number, and an optional --step number to run one step only. Nothing in the code names a company.

Seven steps, each printed as it runs:

1. Resolve the ticker to its CIK from SEC's company_tickers.json.
2. List the company's filings from the EDGAR submissions API and pick the latest 10-K, the latest 10-Q, and the latest 8-K whose document reports Item 2.02, the earnings release, printing each one's accession number and the "Accepted" time shown on its EDGAR index page.
3. Download the three documents, the 8-K's Exhibit 99.1 for the release, convert each to plain text and save them in a folder named by company, date and time of the run.
4. Fetch the XBRL company facts and, for the latest fiscal year, print total revenue, operating income, net income, diluted EPS, stockholders' equity, long-term debt and its current portion, cash from operations and additions to property and equipment, each with its tag, period end and filing, choosing among a concept's candidate tags the one whose latest year is newest and reading every concept for the same fiscal year as revenue, with the prior year beside it.
5. A calculator, in code, that prints with its arithmetic revenue growth, operating margin, return on average equity, debt to equity with the current portion included, free cash flow as cash from operations minus additions to property and equipment, and P/E from --price.
6. From the release text, print the lines that state the quarter's total revenue and diluted EPS.
7. For each peer, the same facts and the operating margin on the same definition.

Save the facts beside the texts. When you finish, tell me the exact command to install any packages it needs and the exact command to run it on a ticker with peers and a price.

The paper is in my git repository: `FRL-CanAIReplaceAnalyst.pdf`.

## Inputs and sources

| Input | Where |
| --- | --- |
| The seven steps | The instructor's demo on the screen, one step at a time. |
| The filings and the data | SEC EDGAR: the ticker file, the submissions API, the documents, the XBRL company facts (the data page and the Week 2 page link Costco's). |
| SEC access | EDGAR asks every program for a User-Agent with your name and email, in your `.env`. Read it as `SEC_USER_AGENT`. |
| The known answers | The instructor's run on the screen, read from what Costco filed last; each number judged by its filing (V below). |

Costco is the instructor's reference case. Keep the program ticker-driven; do not hard-code Costco or its answers.

The reference to "V below" comes from the course instructions. That section and the instructor's displayed answers have not been supplied here.
