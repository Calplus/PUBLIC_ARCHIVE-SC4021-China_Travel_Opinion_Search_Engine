# Sourced from Calplus (https://github.com/Calplus)
# SC4021 — China Travel Opinion Search Engine

**Video Script**

**Target duration:** 5 minutes  |  **Format:** Screen recording with voiceover

## **\[0:00–0:30\] Opening — Team Introduction**

*Show the app on boot*

“Hi, we’re Group 17\. Today we’re presenting our China Travel Opinion Search Engine — a system that lets users search, filter, and analyse 2.4 million travel-related documents from Instagram and Pinterest.”

## **\[0:30–0:50\] Motivation — Why This Matters**

*\[Screen: Show a Google search for "China travel opinions" — fragmented results across platforms\]*

“Planning a trip to China means sifting through thousands of social media posts across multiple platforms. There’s no unified way to search travel opinions, filter by sentiment, or compare destinations side by side.”

“Our search engine solves this. We crawled over 2.4 million documents — 118,000 Instagram posts, 117,000 comments, and 2.1 million Pinterest pins — all tagged with sentiment labels, cities, categories, and languages.”

## **\[0:50–1:10\] System Architecture — What Powers It**

*\[Screen: Show architecture diagram or Elasticsearch dashboard\]*

“Under the hood, we use Elasticsearch 8.17 with BM25 ranking and a custom text analysis pipeline — standard tokenisation, lowercase normalisation, stop word removal, and Snowball stemming. This indexes all 2.4 million documents across three separate indices, enabling sub-100-millisecond search with full-text matching, fuzzy queries, and field-level boosting.”

## **\[1:10–2:25\] Live Demo — Core Search Experience**

*\[Screen: Switch to the live application\]*

“Let’s see the search in action. I’ll search for ‘great wall’”

***\[Type query, hit Enter\]***
# Sourced from Calplus (https://github.com/Calplus)

“We get over 6,000 results — each card shows the image thumbnail, the original post text with matched terms highlighted, the source platform, and a direct link to the original post.”

***\[Select Sentiment: Negative\]***

“Now we only see negative, or even neutral opinions about the Great Wall — You could possibly find complaints about crowds, overpricing, and long queues. This is incredibly useful for trip planning.”

***\[Select Category: Food, clear sentiment filter\]***

“Now, I can reset everything and switch to family and kids-related posts near the Great Wall area. These faceted filters work in combination — source, sentiment, category, city, language, and date range can all be applied simultaneously.”

***\[Click on Sort: Most Likes\]***

“Resetting once again and sorting by likes surfaces the most-engaged posts first — acting as a quality signal, similar to PageRank. The most-liked posts tend to be the most detailed travel experiences, or large organizations, in this case, national geographic”

***\[Click ‘Find Similar’ on a result\]***

“The ‘Find Similar’ button is our relevance feedback mechanism, inspired by the Rocchio algorithm. It uses the clicked document as a seed to find related content — effectively letting the user tell the system ‘more like this.’”

## **\[2:25–3:10\] Analytics Dashboard & Geo Map**

*\[Screen: Click on Analytics Dashboard tab\]*

“The Analytics tab transforms search results into visual insights. Here’s the sentiment-over-time chart — a stacked 100% bar chart overlaid with a total-posts line. I can click on any month to see that month’s top posts and a detailed pie chart breakdown.”

“Below that, the Cities panel shows a horizontal stacked bar for each city — Beijing, Changsha, Xi’an with positive, neutral, and negative proportions; though in this case its mostly positive. Which is normal, as people usually only post positive content\! At a glance, you can see which cities have the best sentiment.”

***\[Click on Geo Map tab\]***

“This is our geo-spatial sentiment map. Each circle marker represents a Chinese city, with colour coded sentiment — green for positive, red for negative, orange in between. The marker size shows document volume. I can toggle between absolute and relative scoring modes.”

Form this chart, we can instantly see across all 29 mapped cities and see that the coastal areas tend to receive the great wall more positively than western cities. This allows consumers, or even researchers, to delve deeper and understand why this happens.

## **\[3:10–3:55\] Classification Pipeline — Neurosymbolic Approach**
# Source: github.com/Calplus

*\[Screen: Show the pipeline architecture diagram from the report\]*

“Under the hood, our classification uses a neurosymbolic approach — combining deep learning with symbolic AI.”

“Stage 1 is a subjectivity detection gate — a regex-based filter that identifies whether text contains opinion signals like first-person pronouns, superlatives, or emojis., while the 2nd stage applies both RoBERTa and SenticNet, to detect and categorize our posts.”

“The ensemble weighs RoBERTa at 70% and SenticNet at 30%, combining the pattern recognition of neural networks with the interpretability of symbolic AI. 

## **\[3:55–4:30\] Evaluation & Ablation Study**

*\[Screen: Show confusion matrix and metrics from the report\]*

“We validated the pipeline against 1,403 human-annotated samples, labelled independently by two annotators. The human inter-annotator agreement is kappa 0.94 — almost perfect — which makes it reliable.”

“Against this gold standard, our pipeline achieves 88.3% accuracy, a Macro F1 of 86.2%, and a Cohen’s kappa of 0.79 — substantial agreement with human judgement. Negative recall is especially strong at 89%, despite negative being only 5.9% of the dataset.”

## **\[4:30–5:00\] Summary & Creative Highlights**

*\[Screen: Return to the application, show a final search\]*

“To wrap up, here are some things that set our project apart:”

“First, scale — 2.4 million documents from two platforms, processed with an 8-step cleaning pipeline including emoji-to-text conversion and MinHash deduplication.”

“Second, the neurosymbolic approach — combining RoBERTa and SenticNet in a way that’s directly grounded in NLU lecture theory on third-wave AI.”

“Third, 10 innovations across indexing and classification — 7 indexing innovations including multilingual search, geo-spatial sentiment mapping, analytics dashboards, and a destination intelligence briefing that ranks over 80 cities; plus 3 classification innovations including the SenticNet ensemble, aspect-based sentiment analysis, and the full neurosymbolic pipeline.”

“Thank you for watching.

*\[Screen: End slide with team name and thank you\]*

*Total estimated duration: \~5 minutes*

