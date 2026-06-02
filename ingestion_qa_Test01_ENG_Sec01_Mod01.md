# Ingestion QA Report — Test01_ENG_Sec01_Mod01

| Field | Value |
|---|---|
| **Job ID** | `bd072449-02b7-4337-a71e-1aff5a6cb6f2` |
| **Status** | `approved` |
| **Extracted / Created** | 27 / 27 |
| **Phase 1** | ~6 min |
| **Phase 2 (annotation)** | ~14 min |
| **Rules version** | `rules_agent_dsat_grammar_ingestion_generation_v8` |
| **Source** | `TESTS/DATA_SRC/2024-2025 Tests Answers/Test01_ENG_Sec01_Mod01.pdf` |

## ⚠️ Warnings (non-blocking)

- **Q? — amendment_proposal:** LLM submitted amendment with `affected_vocab = "grammar_focus_key"` — not a valid ontology constant, proposal dropped silently. Job still approved.

---

## Summary Table

| Q# | Stem type | Family | Focus key | Difficulty | Correct |
|---|---|---|---|---|---|
| 1 | choose_words_in_context | craft_and_structure | contextual_meaning | low | A |
| 2 | choose_words_in_context | craft_and_structure | polarity_fit | medium | C |
| 3 | choose_sentence_function | craft_and_structure | sentence_function | medium | C |
| 4 | choose_sentence_function | — | — | — | B |
| 5 | choose_text_relationship | — | — | — | C |
| 6 | choose_detail | information_and_ideas | supporting_detail | low | D |
| 7 | choose_detail | — | — | — | D |
| 8 | choose_main_idea | — | — | — | D |
| 9 | choose_best_support | information_and_ideas | evidence_supports_claim | medium | B |
| 10 | choose_best_completion_from_data | — | — | — | C |
| 11 | choose_best_completion_from_data | — | — | — | A |
| 12 | choose_best_support | — | — | — | C |
| 13 | choose_best_completion_from_data | — | — | — | C |
| 14 | most_logically_completes | information_and_ideas | causal_inference | low | D |
| 15 | conform_to_standard_english | conventions_grammar | unnecessary_internal_punctuation | low | B |
| 16 | conform_to_standard_english | conventions_grammar | pronoun_antecedent_agreement | low | B |
| 17 | conform_to_standard_english | — | punctuation_comma | — | A |
| 18 | conform_to_standard_english | conventions_grammar | verb_form | medium | A |
| 19 | conform_to_standard_english | — | unnecessary_internal_punctuation | — | C |
| 20 | conform_to_standard_english | conventions_grammar | pronoun_antecedent_agreement | low | D |
| 21 | conform_to_standard_english | conventions_grammar | conjunctive_adverb_usage | medium | D |
| 22 | complete_the_text | — | transition_logic | — | D |
| 23 | choose_best_transition | — | transition_logic | — | A |
| 24 | choose_best_transition | — | transition_logic | — | D |
| 25 | complete_the_text | — | transition_logic | — | C |
| 26 | choose_best_notes_synthesis | — | data_interpretation_claims | — | B |
| 27 | choose_best_notes_synthesis | expression_of_ideas | emphasis_meaning_shifts | medium | A |

---

## Full Question Detail

### Q1

**Classification:** `craft_and_structure` · `choose_words_in_context` · `passage_excerpt` · `contextual_meaning` · difficulty: `low`

**Passage:**

> Researchers and conservationists stress that biodiversity loss due to invasive species is ____. For example, people can take simple steps such as washing their footwear after travel to avoid introducing potentially invasive organisms into new environments.

**Stem:** Which choice completes the text with the most logical and precise word or phrase?

✅ **A.** preventable
○ **B.** undeniable
○ **C.** common
○ **D.** concerning

---

### Q2

**Classification:** `craft_and_structure` · `choose_words_in_context` · `passage_excerpt` · `polarity_fit` · difficulty: `medium`

**Passage:**

> It is by no means ____ to recognize the influence of Dutch painter Hieronymus Bosch on Ali Banisadr’s paintings; indeed, Banisadr himself cites Bosch as an inspiration. However, some scholars have suggested that the ancient Mesopotamian poem Epic of Gilgamesh may have had a far greater impact on Banisadr’s work.

**Stem:** Which choice completes the text with the most logical and precise word or phrase?

○ **A.** substantial
○ **B.** satisfying
✅ **C.** unimportant
○ **D.** appropriate

---

### Q3

**Classification:** `craft_and_structure` · `choose_sentence_function` · `passage_excerpt` · `sentence_function` · difficulty: `medium`

**Passage:**

> Astronomers are confident that the star Betelgeuse will eventually consume all the helium in its core and explode in a supernova. They are much less confident, however, about when this will happen, since that depends on internal characteristics of Betelgeuse that are largely unknown. Astrophysicist Sarafina El-Badry Nance and colleagues recently investigated whether acoustic waves in the star could be used to determine internal stellar states but concluded that this method could not sufficiently reveal Betelgeuse’s internal characteristics to allow its evolutionary state to be firmly fixed.

**Stem:** Which choice best describes the function of the second sentence in the overall structure of the text?

○ **A.** It describes a serious limitation of the method used by Nance and colleagues.
○ **B.** It presents the central finding reported by Nance and colleagues.
✅ **C.** It identifies the problem that Nance and colleagues attempted to solve but did not.
○ **D.** It explains how the work of Nance and colleagues was received by others in the field.

---

### Q4

**Classification:** `choose_sentence_function` · `passage_excerpt`

**Passage:**

> The mimosa tree evolved in East Asia, where the beetle Bruchidius terrenus preys on its seeds. In 1785, mimosa trees were introduced to North America, far from any B. terrenus. But evolutionary links between predators and their prey can persist across centuries and continents. Around 2001, B. terrenus was introduced in southeastern North America near where botanist Shu-Mei Chang and colleagues had been monitoring mimosa trees. Within a year, 93 percent of the trees had been attacked by the beetles.

**Stem:** Which choice best describes the function of the third sentence in the overall structure of the text?

○ **A.** It states the hypothesis that Chang and colleagues had set out to investigate using mimosa trees and B. terrenus.
✅ **B.** It presents a generalization that is exemplified by the discussion of the mimosa trees and B. terrenus.
○ **C.** It provides context that clarifies why the species mentioned spread to new locations.
○ **D.** It offers an alternative explanation for the findings of Chang and colleagues.

---

### Q5

**Classification:** `choose_text_relationship` · `prose_paired`

**Passage:**

> Text 1 When companies in the same industry propose merging with one another, they often claim that the merger will benefit consumers by increasing efficiency and therefore lowering prices. Economist Ying Fan investigated this notion in the context of the United States newspaper market. She modeled a hypothetical merger of Minneapolis-area newspapers and found that subscription prices would rise following a merger.  Text 2 Economists Dario Focarelli and Fabio Panetta have argued that research on the effect of mergers on prices has focused excessively on short-term effects, which tend to be adverse for consumers. Using the case of consumer banking in Italy, they show that over the long term (several years, in their study), the efficiency gains realized by merged companies do result in economic benefits for consumers.

**Stem:** Based on the texts, how would Focarelli and Panetta (Text 2) most likely respond to Fan’s findings (Text 1)?

○ **A.** They would recommend that Fan compare the near-term effect of a merger on subscription prices in the Minneapolis area with the effect of a merger in another newspaper market.
○ **B.** They would argue that over the long term the expenses incurred by the merged newspaper company will also increase.
✅ **C.** They would encourage Fan to investigate whether the projected effect on subscription prices persists over an extended period.
○ **D.** They would claim that mergers have a different effect on consumer prices in the newspaper industry than in most other industries.

---

### Q6

**Classification:** `information_and_ideas` · `choose_detail` · `passage_excerpt` · `supporting_detail` · difficulty: `low`

**Passage:**

> Elinor, this eldest daughter, whose advice was so effectual, possessed a strength of understanding, and coolness of judgment, which qualified her, though only nineteen, to be the counsellor of her mother, and enabled her frequently to counteract, to the advantage of them all, that eagerness of mind in Mrs. Dashwood which must generally have led to imprudence. She had an excellent heart;—her disposition was affectionate, and her feelings were strong; but she knew how to govern them: it was a knowledge which her mother had yet to learn; and which one of her sisters had resolved never to be taught.

**Stem:** According to the text, what is true about Elinor?

○ **A.** Elinor often argues with her mother but fails to change her mind.
○ **B.** Elinor can be overly sensitive with regard to family matters.
○ **C.** Elinor thinks her mother is a bad role model.
✅ **D.** Elinor is remarkably mature for her age.

---

### Q7

**Classification:** `choose_detail` · `passage_excerpt`

**Passage:**

> Mrs. Ochiltree was a woman of strong individuality, whose comments upon her acquaintance[s], present or absent, were marked by a frankness at times no less than startling. This characteristic caused her to be more or less avoided. Mrs. Ochiltree was aware of this sentiment on the part of her acquaintance[s], and rather exulted in it.

**Stem:** Based on the text, what is true about Mrs. Ochiltree’s acquaintances?

○ **A.** They try to refrain from discussing topics that would upset Mrs. Ochiltree.
○ **B.** They are unable to spend as much time with Mrs. Ochiltree as she would like.
○ **C.** They are too preoccupied with their own concerns to speak with Mrs. Ochiltree.
✅ **D.** They are likely offended by what Mrs. Ochiltree has said about them.

---

### Q8

**Classification:** `choose_main_idea` · `poem`

**Passage:**

> Weary with toil, I [hurry] to my bed, The dear repose for limbs with travel tired; But then begins a journey in my head To work my mind, when body’s work’s expired: For then my thoughts—from far where I abide— [Begin] a zealous pilgrimage to thee, And keep my drooping eyelids open wide,

**Stem:** What is the main idea of the text?

○ **A.** The speaker is asleep and dreaming about traveling to see the friend.
○ **B.** The speaker is planning an upcoming trip to the friend’s house.
○ **C.** The speaker is too fatigued to continue a discussion with the friend.
✅ **D.** The speaker is thinking about the friend instead of immediately falling asleep.

---

### Q9

**Classification:** `information_and_ideas` · `choose_best_support` · `passage_excerpt` · `evidence_supports_claim` · difficulty: `medium`

**Passage:**

> Black beans (Phaseolus vulgaris) are a nutritionally dense food, but they are difficult to digest in part because of their high levels of soluble fiber and compounds like raffinose. They also contain antinutrients like tannins and trypsin inhibitors, which interfere with the body’s ability to extract nutrients from foods. In a research article, Marisela Granito and Glenda Álvarez from Simón Bolívar University in Venezuela claim that inducing fermentation of black beans using lactic acid bacteria improves the digestibility of the beans and makes them more nutritious.

**Stem:** Which finding from Granito and Álvarez’s research, if true, would most directly support their claim?

○ **A.** When cooked, fermented beans contained significantly more trypsin inhibitors and tannins but significantly less soluble fiber and raffinose than nonfermented beans.
✅ **B.** Fermented beans contained significantly less soluble fiber and raffinose than nonfermented beans, and when cooked, the fermented beans also displayed a significant reduction in trypsin inhibitors and tannins.
○ **C.** When the fermented beans were analyzed, they were found to contain two microorganisms, Lactobacillus casei and Lactobacillus plantarum, that are theorized to increase the amount of nitrogen absorbed by the gut after eating beans.
○ **D.** Both fermented and nonfermented black beans contained significantly fewer trypsin inhibitors and tannins after being cooked at high pressure.

---

### Q10

**Classification:** `choose_best_completion_from_data` · `prose_plus_table`

**Passage:**

> Earth’s atmosphere is bombarded by cosmic dust originating from several sources: short-period comets (SPCs), particles from the asteroid belt (ASTs), Halley-type comets (HTCs), and Oort cloud comets (OCCs). Some of the dust’s material vaporizes in the atmosphere in a process called ablation, and the faster the particles move, the higher the rate of ablation. Astrophysicist Juan Diego Carrillo-Sánchez led a team that calculated average ablation rates for elements in the dust (such as iron and potassium) and showed that material in slower-moving SPC or AST dust has a lower rate than the same material in faster-moving HTC or OCC dust. For example, whereas the average ablation rate for iron from AST dust is 28%, the average rate for _____

**Stem:** Which choice most effectively uses data from the table to complete the example?

○ **A.** iron from SPC dust is 20%.
○ **B.** sodium from OCC dust is 100%.
✅ **C.** iron from HTC dust is 90%.
○ **D.** sodium from AST dust is 75%.

---

### Q11

**Classification:** `choose_best_completion_from_data` · `prose_plus_graph`

**Passage:**

> High levels of public uncertainty about which economic policies a country will adopt can make planning difficult for businesses, but measures of such uncertainty have not tended to be very detailed. Recently, however, economist Sandile Hlatshwayo analyzed trends in news reports to derive measures not only for general economic policy uncertainty but also for uncertainty related to specific areas of economic policy, like tax or trade policy. One revelation of her work is that a general measure may not fully reflect uncertainty about specific areas of policy, as in the case of the United Kingdom, where general economic policy uncertainty ____

**Stem:** Which choice most effectively uses data from the graph to illustrate the claim?

✅ **A.** aligned closely with uncertainty about tax and public spending policy in 2005 but differed from uncertainty about tax and public spending policy by a large amount in 2009.
○ **B.** was substantially lower than uncertainty about tax and public spending policy each year from 2005 to 2010.
○ **C.** reached its highest level between 2005 and 2010 in the same year that uncertainty about trade policy and tax and public spending policy reached their lowest levels.
○ **D.** was substantially lower than uncertainty about trade policy in 2005 and substantially higher than uncertainty about trade policy in 2010.

---

### Q12

**Classification:** `choose_best_support` · `prose_plus_table`

**Passage:**

> When hibernating, Alaska marmots and Arctic ground squirrels enter a state called torpor, which minimizes the energy their bodies need to function. Often a hibernating animal will temporarily come out of torpor (called an arousal episode) and its metabolic rate will rise, burning more of the precious energy the animal needs to survive the winter. Alaska marmots hibernate in groups and therefore burn less energy keeping warm during these episodes than they would if they were alone. A researcher hypothesized that because Arctic ground squirrels hibernate alone, they would likely exhibit longer bouts of torpor and shorter arousal episodes than Alaska marmots.

**Stem:** Which choice best describes data from the table that support the researcher’s hypothesis?

○ **A.** The Alaska marmots’ arousal episodes lasted for days, while the Arctic ground squirrels’ arousal episodes lasted less than a day.
○ **B.** The Alaska marmots and the Arctic ground squirrels both maintained torpor for several consecutive days per bout, on average.
✅ **C.** The Alaska marmots had shorter torpor bouts and longer arousal episodes than the Arctic ground squirrels did.
○ **D.** The Alaska marmots had more torpor bouts than arousal episodes, but their arousal episodes were much shorter than their torpor bouts.

---

### Q13

**Classification:** `choose_best_completion_from_data` · `prose_plus_table`

**Passage:**

> Over the past two hundred years, the percentage of the population employed in the agricultural sector has declined in both France and the United States, while employment in the service sector (which includes jobs in retail, consulting, real estate, etc.) has risen. However, this transition happened at very different rates in the two countries. This can be seen most clearly by comparing the employment by sector in both countries in ____

**Stem:** Which choice most effectively uses data from the table to complete the text?

○ **A.** 1800
○ **B.** 1900
✅ **C.** 1950
○ **D.** 2012

---

### Q14

**Classification:** `information_and_ideas` · `most_logically_completes` · `passage_excerpt` · `causal_inference` · difficulty: `low`

**Passage:**

> Euphorbia esula (leafy spurge) is a Eurasian plant that has become invasive in North America, where it displaces native vegetation and sickens cattle. E. esula can be controlled with chemical herbicides, but that approach can also kill harmless plants nearby. Recent research on introducing engineered DNA into plant species to inhibit their reproduction may offer a path toward exclusively targeting E. esula, consequently ___

**Stem:** Which choice most logically completes the text?

○ **A.** making individual E. esula plants more susceptible to existing chemical herbicides.
○ **B.** enhancing the ecological benefits of E. esula in North America.
○ **C.** enabling cattle to consume E. esula without becoming sick.
✅ **D.** reducing invasive E. esula numbers without harming other organisms.

---

### Q15

**Classification:** `conventions_grammar` · `conform_to_standard_english` · `sentence_only` · role: `punctuation` · `unnecessary_internal_punctuation` · difficulty: `low`

**Passage:**

> Both Sona Charaipotra, an Indian American, and Dhonielle Clayton, an African American, grew up frustrated by the lack of diverse characters in books for young people. In 2011, these two writers joined forces to found CAKE Literary, a book packaging ____ specializes in the creation and promotion of stories told from diverse perspectives for children and young adults.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

○ **A.** company,
✅ **B.** company that
○ **C.** company
○ **D.** company, that

---

### Q16

**Classification:** `conventions_grammar` · `conform_to_standard_english` · `sentence_only` · role: `agreement` · `pronoun_antecedent_agreement` · difficulty: `low`

**Passage:**

> In 1930, Japanese American artist Chiura Obata depicted the natural beauty of Yosemite National Park in two memorable woodcuts: Evening at Carl Inn and Lake Basin in the High Sierra. In 2019, ____ exhibited alongside 150 of Obata’s other works in a single-artist show at the Smithsonian American Art Museum.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

○ **A.** it was
✅ **B.** they were
○ **C.** this was
○ **D.** some were

---

### Q17

**Classification:** `conform_to_standard_english` · `sentence_only` · role: `punctuation` · `punctuation_comma`

**Passage:**

> American writer Edwidge Danticat, who emigrated from Haiti in 1981, has won acclaim for her powerful short stories, novels, and ____ her lyrical yet unflinching depictions of her native country’s turbulent history, writer Robert Antoni has compared Danticat to Nobel Prize–winning novelist Toni Morrison.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

✅ **A.** essays, praising
○ **B.** essays and praising
○ **C.** essays praising
○ **D.** essays. Praising

---

### Q18

**Classification:** `conventions_grammar` · `conform_to_standard_english` · `sentence_only` · role: `verb_form` · `verb_form` · difficulty: `medium`

**Passage:**

> In 1966, Emmett Ashford became the first African American to umpire a Major League Baseball game. His energetic gestures announcing when a player had struck out and his habit of barreling after a hit ball to see if it would land out of ____ transform the traditionally solemn umpire role into a dynamic one.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

✅ **A.** bounds helped
○ **B.** bounds, helping
○ **C.** bounds that helped
○ **D.** bounds to help

---

### Q19

**Classification:** `conform_to_standard_english` · `sentence_only` · role: `punctuation` · `unnecessary_internal_punctuation`

**Passage:**

> In crafting her fantasy fiction, Nigerian-born British author Helen Oyeyemi has drawn inspiration from the classic nineteenth-century fairy tales of the Brothers Grimm. Her 2014 novel Boy, Snow, Bird, for instance, is a complex retelling of the story of Snow White, while her 2019 novel ____ offers a delicious twist on the classic tale of Hansel and Gretel.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

○ **A.** Gingerbread—
○ **B.** Gingerbread,
✅ **C.** Gingerbread
○ **D.** Gingerbread:

---

### Q20

**Classification:** `conventions_grammar` · `conform_to_standard_english` · `sentence_only` · role: `agreement` · `pronoun_antecedent_agreement` · difficulty: `low`

**Passage:**

> The violins handmade in the seventeenth century by Italian craftsman Antonio Stradivari have been celebrated as some of the finest in the world. In close collaboration with musicians, Stradivari introduced changes to the shape of a traditional violin, flattening some of the instrument’s curves and making ____ lighter overall.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

○ **A.** those
○ **B.** one
○ **C.** them
✅ **D.** it

---

### Q21

**Classification:** `conventions_grammar` · `conform_to_standard_english` · `sentence_only` · role: `punctuation` · `conjunctive_adverb_usage` · difficulty: `medium`

**Passage:**

> During the English neoclassical period (1660–1789), many writers imitated the epic poetry and satires of ancient Greece and Rome. They were not the first in England to adopt the literary modes of classical ____ some of the most prominent figures of the earlier Renaissance period were also influenced by ancient Greek and Roman literature.

**Stem:** Which choice completes the text so that it conforms to the conventions of Standard English?

○ **A.** antiquity, however
○ **B.** antiquity, however,
○ **C.** antiquity, however;
✅ **D.** antiquity; however,

---

### Q22

**Classification:** `complete_the_text` · `sentence_only` · role: `expression_of_ideas` · `transition_logic`

**Passage:**

> One poll taken after the first 1960 presidential debate suggested that John Kennedy lost badly: only 21 percent of those who listened on the radio rated him the winner. ____ the debate was ultimately considered a victory for the telegenic young senator, who rated higher than his opponent, Vice President Richard Nixon, among those watching on the new medium of television.

**Stem:** Which choice completes the text with the most logical transition?

○ **A.** In other words,
○ **B.** Therefore,
○ **C.** Likewise,
✅ **D.** Nevertheless,

---

### Q23

**Classification:** `choose_best_transition` · `sentence_only` · role: `expression_of_ideas` · `transition_logic`

**Passage:**

> In November 1934, Amrita Sher-Gil was living in what must have seemed like the ideal city for a young artist: Paris. She was studying firsthand the color-saturated style of France’s modernist masters and beginning to make a name for herself as a painter. ___ Sher-Gil longed to return to her childhood home of India; only there, she believed, could her art truly flourish.

**Stem:** Which choice completes the text with the most logical transition?

✅ **A.** Still,
○ **B.** Therefore,
○ **C.** Indeed,
○ **D.** Furthermore,

---

### Q24

**Classification:** `choose_best_transition` · `passage_excerpt` · role: `expression_of_ideas` · `transition_logic`

**Passage:**

> In his 1925 book The Morphology of Landscape, US geographer Carl Sauer challenged prevailing views about how natural landscapes influence human cultures. ____ Sauer argued that instead of being shaped entirely by their natural surroundings, cultures play an active role in their own development by virtue of their interactions with the environment.

**Stem:** Which choice completes the text with the most logical transition?

○ **A.** Similarly,
○ **B.** Finally,
○ **C.** Therefore,
✅ **D.** Specifically,

---

### Q25

**Classification:** `complete_the_text` · `sentence_only` · role: `expression_of_ideas` · `transition_logic`

**Passage:**

> Although those who migrated to California in 1849 dreamed of finding gold nuggets in streambeds, the state’s richest deposits were buried deeply in rock, beyond the reach of individual prospectors. ____ by 1852, many had given up their fortune-hunting dreams and gone to work for one of the large companies capable of managing California’s complex mining operations.

**Stem:** Which choice completes the text with the most logical transition?

○ **A.** Furthermore,
○ **B.** Still,
✅ **C.** Consequently,
○ **D.** Next,

---

### Q26

**Classification:** `choose_best_notes_synthesis` · `notes_bullets` · role: `expression_of_ideas` · `data_interpretation_claims`

**Passage:**

> While researching a topic, a student has taken the following notes: • In 2013, archaeologists studied cat bone fragments they had found in the ruins of Quanhucun, a Chinese farming village. • The fragments were estimated to be 5,300 years old. • A chemical analysis of the fragments revealed that the cats had consumed large amounts of grain. • The grain consumption is evidence that the Quanhucun cats may have been domesticated.

**Stem:** The student wants to present the Quanhucun study and its conclusions. Which choice most effectively uses relevant information from the notes to accomplish this goal?

○ **A.** As part of a 2013 study of cat domestication, a chemical analysis was conducted on cat bone fragments found in Quanhucun, China.
✅ **B.** A 2013 analysis of cat bone fragments found in Quanhucun, China, suggests that cats there may have been domesticated 5,300 years ago.
○ **C.** In 2013, archaeologists studied what cats in Quanhucun, China, had eaten more than 5,000 years ago.
○ **D.** Cat bone fragments estimated to be 5,300 years old were found in Quanhucun, China, in 2013.

---

### Q27

**Classification:** `expression_of_ideas` · `choose_best_notes_synthesis` · `notes_bullets` · role: `expression_of_ideas` · `emphasis_meaning_shifts` · difficulty: `medium`

**Passage:**

> While researching a topic, a student has taken the following notes: • Started in 1925, the Scripps National Spelling Bee is a US-based spelling competition. • The words used in the competition have diverse linguistic origins. • In 2008, Sameer Mishra won by correctly spelling the word “guerdon.” • “Guerdon” derives from the Anglo-French word “guerdun.” • In 2009, Kavya Shivashankar won by correctly spelling the word “Laodicean.” • “Laodicean” derives from the ancient Greek word “Laodíkeia.”

**Stem:** The student wants to emphasize a difference in the origins of the two words. Which choice most effectively uses relevant information from the notes to accomplish this goal?

✅ **A.** “Guerdon,” the final word of the 2008 Scripps National Spelling Bee, is of Anglo-French origin, while the following year’s final word, “Laodicean,” derives from ancient Greek.
○ **B.** In 2008, Sameer Mishra won the Scripps National Spelling Bee by correctly spelling the word “guerdon”; however, the following year, Kavya Shivashankar won based on spelling the word “Laodicean.”
○ **C.** Kavya Shivashankar won the 2009 Scripps National Spelling Bee by correctly spelling “Laodicean,” which derives from the ancient Greek word “Laodíkeia.”
○ **D.** The Scripps National Spelling Bee uses words from diverse linguistic origins, such as “guerdon” and “Laodicean.”

---
