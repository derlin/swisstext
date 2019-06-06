Sentence Filtering
-------------------

We would need more rules to enhance the sentences' quality. Here are some ideas:

* Exclude sentences with the world *Wikipedia* (or *Alemannische Wikipedia*) DONE;
* Exclude short sentences with the character *:* or with parentheses;
* Exclude long sentences with no punctuation ? This would remove poems...;

URL Filtering
--------------

Right now, the :mod:`swisstext.cmd.link_util` package is rather simple. Having a better way of filtering
links beforehand (i.e. without the need to scrape them) could help us improve the performances by
(1) avoiding unnecessary scaping, (2) prevent sentences to be wrongly scraped (example: sentences from
wikipedia URLs containing *ISBN* are often miscategorized as Swiss German and of poor quality).

**Idea**: use exactly the same principle as in :mod:`swisstext.cmd.tools.pettern_sentence_filter`.
This would make URL filtering very flexible and powerful (and the code is already here)!
On the other hand, switching from dictionary lookup to regexes will impact performances...
