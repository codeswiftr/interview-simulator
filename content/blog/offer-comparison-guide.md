# How to Compare and Evaluate Software Engineering Job Offers

You got multiple offers. Congratulations — now comes the part nobody prepares you for. Comparing software engineering compensation packages is a discipline in itself, and most candidates do it badly. They anchor on base salary, ignore equity complexity, and overlook the compounding effect of benefits over a four-year vesting window. This guide gives you a financial framework to compare offers on equal footing, handle pressure tactics professionally, and make a decision grounded in data rather than anxiety.

---

## Step 1: Build a Total Compensation Spreadsheet

Never compare offers by base salary alone. The actual delta between two packages over four years can swing by $200,000 or more once you account for equity, bonus, benefits, and cost-of-living adjustments.

Here is the comparison table template to fill out for each offer:

| Field | Company A | Company B | Company C |
|---|---|---|---|
| **Base Salary (annual)** | | | |
| **Annual Bonus (target %)** | | | |
| **Signing Bonus (total)** | | | |
| **Signing Bonus (clawback period)** | | | |
| **RSU Grant (total value at grant)** | | | |
| **RSU Vesting Schedule** | | | |
| **RSU Cliff** | | | |
| **Options (strike price)** | | | |
| **Options (current FMV)** | | | |
| **Options (exercise window post-departure)** | | | |
| **Refresher Grant Policy** | | | |
| **Health Insurance (employee premium/month)** | | | |
| **Health Insurance (family premium/month)** | | | |
| **Dental + Vision** | | | |
| **401k Match (% and cap)** | | | |
| **HSA Contribution** | | | |
| **Remote Stipend (annual)** | | | |
| **Learning & Development Budget** | | | |
| **Parental Leave (weeks)** | | | |
| **PTO Policy (unlimited vs. accrued)** | | | |
| **COLA-Adjusted Base (if relocating)** | | | |
| **Effective Year 1 TC** | | | |
| **Effective Year 4 TC (cumulative)** | | | |

For Year 4 cumulative, add: `(base × 4) + (bonus × 4) + signing bonus + RSU grant value + (401k match × 4) + benefits value`. This single number lets you compare packages on the same timeline as the standard vesting cliff.

---

## Step 2: Equity Valuation — Not All Stock Is Equal

This is where most engineers lose thousands to millions of dollars in expected value. Equity comes in three fundamentally different forms, and each requires a different valuation approach.

### Public Company RSUs

RSUs at public companies (Google, Meta, Amazon, etc.) are the simplest. Each vesting event converts directly to shares you can sell. Calculate value as:

```
Annual RSU value = (total grant / vesting period in years) × current stock price
```

But apply a discount. A four-year grant priced today at $300K assumes the stock stays flat. Run three scenarios — flat, 20% annual appreciation, 20% annual decline — and use the flat case as your conservative baseline.

Watch for double-trigger RSUs, common at pre-IPO companies that recently went public. These require both a time condition and a liquidity event (IPO or acquisition) before shares vest. They are worth less than standard single-trigger RSUs at a comparable dollar amount.

### Pre-IPO Company: Preferred Shares vs. Common Stock

When a startup offers equity, you almost certainly receive stock options or RSUs tied to common stock. Investors hold preferred shares. This distinction is critical during an acquisition or down-round liquidation.

Preferred shareholders have liquidation preference, which means they get paid first — often 1x to 2x their investment — before common stockholders receive anything. In an acquisition at or below the last round's valuation, common stockholders can receive zero even if the company sells for hundreds of millions of dollars.

To estimate actual common stock value, use this framework:

1. Identify the last funding round valuation (often disclosed publicly or in your offer letter)
2. Identify the total liquidation preference stack (ask the recruiter for the cap table summary — reputable companies provide this)
3. Calculate: `(acquisition price - total preference stack) / total diluted share count × your shares`

If a company was last valued at $2B with $500M in preference overhang and is likely to exit at $1.5B, your common shares are worth zero at exit. Conversely, if the same company exits at $4B, the math works in your favor.

### Stock Options: ISOs and NSOs

Stock options give you the right to purchase shares at the strike price set at grant. The key numbers are:

```
Paper gain per option = current FMV - strike price
Tax on exercise (ISOs) = $0 at exercise (but AMT trigger risk)
Tax on exercise (NSOs) = ordinary income tax on spread at exercise
```

An ISO with a $1.00 strike price and $10.00 FMV at exercise has a $9.00 spread per option. If you hold 10,000 options, that is $90,000 of ordinary income (for NSOs) recognized at exercise even if you cannot sell the shares. This is how engineers end up with unexpected six-figure tax bills.

The post-termination exercise window is equally important. Standard option agreements give you 90 days to exercise after leaving the company. If you cannot afford to exercise (or the tax bill is prohibitive), you forfeit the options. Some engineer-friendly companies offer 5- to 10-year exercise windows. This is worth asking about explicitly.

### Phantom Equity / Profit Interest Units

Phantom equity and profit interest units (common in LLCs and partnership structures) do not represent actual ownership. They track equity-like gains for compensation purposes. Phantom equity pays out in cash at a liquidity event. Profit interest units typically vest and receive favorable capital gains treatment if held long enough, but come with complex K-1 tax implications. If you are evaluating an offer with either of these structures, consult a CPA before signing.

---

## Step 3: Vesting Schedules and Cliffs

The standard vesting schedule in tech is four years with a one-year cliff. This means:

- Year 1: 0% vests until the cliff date, then 25% vests at once
- Years 2-4: the remaining 75% vests monthly or quarterly

This structure means that if you leave at 11 months, you leave with nothing. At 13 months, you leave with 25% plus about two months of post-cliff vesting.

Variations to watch for:

**Back-weighted vesting** is common at some large companies (Microsoft historically used a 0/25/50/100 structure over four years, meaning 50% of the grant vests in year four alone). This structure is designed to retain employees but significantly reduces the value of the grant if you leave before year four.

**Accelerated vesting on acquisition** (single-trigger or double-trigger acceleration) is worth asking about, particularly at startups. Single-trigger acceleration means your unvested shares vest automatically on acquisition. Double-trigger requires both acquisition and involuntary termination. Single-trigger is rare and valuable; double-trigger is more common.

**Refresher grants** are recurring new grants issued each year to prevent compensation from decaying as the original grant runs out. Ask explicitly whether the company has a structured refresher program and what the typical annual grant value is relative to the initial offer. Without refreshers, your RSU income drops to zero in year five.

---

## Step 4: HCOL vs. LCOL Offer Comparison

A $180,000 base salary in San Francisco and a $160,000 base salary in Austin are not a $20,000 difference in real compensation. After adjusting for state income tax and cost of living, the Austin offer may net more take-home per dollar.

Use a consistent methodology: levels.fyi and MIT's Living Wage Calculator provide city-specific data, but the simplest adjustment is:

1. Calculate post-tax base salary in each location (account for state income tax — California is 9.3%-13.3% on this income band, Texas is 0%)
2. Apply a housing cost index adjustment (BLS or Numbeo data)
3. Compare the purchasing power-adjusted figures

A concrete example: $200K in San Francisco versus $170K in Austin. California taxes cost roughly $17,000 more annually. SF median one-bedroom rent runs $1,000-$1,500/month higher than Austin. Over four years, the Austin offer may represent equivalent or greater purchasing power despite the lower nominal number.

Remote roles add another layer. If the company is headquartered in a low-cost state but you live in a high-cost city, your effective compensation is lower. Confirm whether the company adjusts salaries to local cost-of-living or pays a single national rate.

---

## Step 5: Benefits Valuation

Benefits are often worth $10,000-$30,000 annually in real dollar terms. The categories that move the needle most:

**Health Insurance Premium Differential**: Employer-subsidized health insurance is pre-tax compensation. A company covering 100% of premiums for a family plan versus one covering 70% can represent a $6,000-$12,000 annual difference. Get the actual monthly premium numbers from each recruiter.

**401k Match**: A 4% match on a $180,000 salary is $7,200 per year, $28,800 over four years, not counting investment growth. Compare match percentages, vesting schedules on the match itself (some matches vest over 2-3 years), and whether the cap is a percentage of salary or a dollar amount.

**HSA Contributions**: Companies contributing $500-$1,500 annually to an HSA tied to a high-deductible health plan add real value if you are generally healthy. The HSA is triple-tax-advantaged: contributions are pre-tax, growth is tax-free, and withdrawals for medical expenses are tax-free.

**Remote Work Stipends**: Annual stipends of $1,000-$3,000 for home office equipment, internet, and coworking memberships are taxable income but still meaningful when converted to real purchasing power.

**Unlimited PTO**: This one is frequently worth less than accrual-based PTO. Most engineers at unlimited PTO companies take fewer vacation days than those with explicit accrual. In states like California, accrued PTO is a vested wage paid out at termination. Unlimited PTO has no payout. If you have 80 hours of accrued PTO at a $150,000 salary, that is approximately $5,700 in wages owed at termination under accrual policies.

---

## Step 6: Handling Exploding Offer Deadlines

Exploding deadlines — offers with 24-48 hour acceptance windows — are a pressure tactic, not a business requirement. No legitimate company loses operational capacity by waiting an additional week for a qualified candidate to complete due diligence.

Here is a script for requesting an extension:

> "Thank you for the offer — I'm genuinely excited about this role and the team. I want to make an informed decision and treat this seriously, which means I need a bit more time to complete my review. Would it be possible to extend the deadline to [specific date, 5-10 business days out]? I want to make sure I'm committing fully and not rushing a decision this significant."

Most companies grant extensions to candidates who ask professionally. If a company refuses to extend a 24-hour deadline, that is signal about the culture. Companies that respect employees do not engineer decisions under duress.

If you have a competing offer with a closer deadline, you can be direct:

> "I have another offer with a deadline of [date]. I'd like to resolve this by [date + 2 days] if at all possible. Can we schedule a call to discuss any remaining questions before then?"

---

## Step 7: The Counter-Offer Playbook

A competing offer is your most powerful negotiation lever. Use it explicitly, numerically, and without apology.

**Sample counter-offer email:**

---

Subject: Re: [Company] Offer — Follow-Up

Hi [Recruiter name],

Thank you again for the offer — I want to reiterate my genuine interest in the team and the role. I've been going through the details carefully and wanted to share where I've landed.

I currently have a competing offer at [Company B] that includes a base of $[X] with a [Y]% target bonus and a four-year RSU package valued at $[Z] at current prices. I'd like to join [Company A] over that option, but I need the total compensation to be in a comparable range to make that choice.

Specifically, I'm hoping we can get to a base of $[target base] and an RSU grant in the $[target equity] range. I believe this reflects the scope and impact of the role as we discussed.

I'm not trying to leverage this into a bidding war — I'd genuinely prefer to move forward with you. Can we get on a quick call to see if this is workable?

[Your name]

---

Key principles: give the competing number specifically (vague references to "another offer" carry much less weight), state your preferred outcome rather than leaving it open-ended, and keep the tone collaborative rather than ultimatum-driven.

---

## Step 8: When to Accept Lower TC for Better Growth

Total compensation is not the only rational optimization target. There are situations where accepting a meaningfully lower TC package is the correct financial decision over a three-to-five year horizon.

**Leveling arbitrage**: A senior engineer (L5 equivalent) at a company that values the role highly and promotes readily is worth more in two years than an L5 stuck in a promotion logjam at a higher-paying FAANG. If Company A offers $220K at L5 with a 12-month promotion cycle to L6 ($300K band) and Company B offers $260K at L5 with a 36-month average time-to-L6, the NPV of Company A may be higher despite lower initial TC.

**Equity upside in pre-IPO companies**: A genuinely differentiated startup with strong unit economics, a clear path to liquidity, and a compensation package that includes meaningful equity (not phantom equity, not a de minimis option pool percentage) is worth considering even if base salary is 15-20% below market. The key word is "meaningful." Run the cap table math from Step 2. If your equity represents 0.05% of a company valued at $500M with $200M in preference overhang and a realistic exit at $600M, that is approximately $200,000 at exit — roughly 10 RSU grants from a public company. That is a rational trade. If your equity represents 0.001% of a company already valued at $10B with heavy preference, it is not.

**Skill trajectory**: Some roles at lower-TC companies provide disproportionate breadth — owning infrastructure, shipping customer-facing systems, architecting at a scale you would not reach at a large company for five more years. The ability to demonstrate scope on your resume and in future interviews compounds. This is not a vague "growth opportunity" claim; model the specific skills, systems ownership, and scope you expect, and compare against what the higher-TC role actually involves.

---

## Step 9: Leveling Mismatches

Leveling discrepancies between companies are common and create real financial risk. If Company A levels you at Senior (L5) and Company B levels you at Staff (L6), you are not comparing equivalent offers even if base salaries are similar. The L6 role implies a higher compensation ceiling, more scope, and a higher starting point for future negotiations.

Before accepting, ask:

- What is the exact level title in your system?
- What is the compensation band for this level?
- What is the average tenure at this level before promotion consideration?
- Is this offer at the top, middle, or bottom of the band?

Being hired at the top of a band (common for strong negotiators) feels like a win but limits merit increase headroom. Being hired at the midpoint leaves room for growth without hitting the ceiling.

If you believe you are being leveled incorrectly, address it before signing:

> "Based on the scope of the role and my experience leading [specific work], I expected this to be leveled at [target level]. Can we discuss alignment on leveling, or is there flexibility to start at [target level] with the corresponding compensation range?"

---

## Making the Decision

Once your spreadsheet is complete and negotiations are concluded, you have a quantified picture of each offer. The financial comparison is not the decision — it is the foundation for the decision. Layer on top of it: team quality (speak with 3-5 potential colleagues before accepting), product trajectory, manager reputation (LinkedIn message the manager's previous reports), and your own assessment of the role's scope.

The goal is not to maximize the number on the spreadsheet at the expense of every other variable. It is to ensure you are making an informed choice with your eyes open to the full financial picture, so that whatever you choose, you chose it deliberately.

The offer that looks best on the spreadsheet after doing this work rigorously is usually worth taking. But when the numbers are close — within 10-15% over four years — the non-financial variables should decide it.
