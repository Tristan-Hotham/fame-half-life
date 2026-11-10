# Reddit post

**Title:** [OC] When a notable person dies, their Wikipedia article is read about 15 times as much as usual that month. Two to three years later it is back to 0.98 of its old level (16,397 people, 2016 to 2023)

**Image:** fame_half_life_collage.png (or the GIF, fame-half-life.gif)

**Body:**

I followed the English Wikipedia articles of 16,397 people who died between 2016 and 2023 (a fixed pseudo-random 30% of everyone Wikidata lists with an English article), month by month from a year before their death to as much as five years after it. Attention is each month's share of all English Wikipedia reading, compared with the person's own average in the year before they died.

- Month of death: median 14.9x the usual level. Month after: 2.77x. A year on: 1.07x.
- The rush fades with a half-life of about 11 days; what is left fades with a half-life of about 6.9 months.
- Two to three years on, the typical person is at 0.98 of their old level; 48% end above it.
- People who died under 50 settle at 1.47; people who died at 90 or over at 0.89.
- Performers (actors, musicians, directors) are the only occupation group whose typical attention ends above where it started (1.10). Part of the gaps between occupations was already there before the deaths.
- Differences between women and men, and between English-speaking and other countries, depend on how you model them, so I don't read anything into them.

Interactive version (pick groups, hover for values, map by citizenship): https://maps.tristanhotham.com/fame-half-life/

**Source comment:**

Data: English Wikipedia user pageviews from the Wikimedia pageviews API (CC0), monthly, 2015 to 2026; people, dates, occupations and citizenships from Wikidata (CC0); country shapes from Natural Earth. Tools: Python (pandas, statsmodels, matplotlib). The analysis plan was written before any after-death numbers were computed; the paper, data and code are linked from the page. Medians across people, so a few very famous names do not drive the curve. Pageviews measure looking someone up, not remembering or valuing them, and English Wikipedia is one audience.
