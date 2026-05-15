# Forced Benchmark: GLM-OCR + DeepSeek V4 Pro

## Summary

- Source PDF: `TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL/Test_1_digital_sec01_mod01.pdf`
- Forced path: rendered PDF pages -> `glm-ocr:latest` via Ollama -> `deepseek-v4-pro:cloud` via Ollama
- Normal PyMuPDF text path: intentionally bypassed for question extraction
- DeepSeek extraction mode: page chunks with `thinking=false`
- Pages rendered/OCRed: 14
- GLM OCR characters: 24548
- GLM OCR total latency: 26009 ms
- DeepSeek chunk total latency: 187641 ms
- Questions extracted by forced path: 32 / 33
- Questions with complete A-D options: 32 / 32
- Missing question numbers: [11]

## Benchmark Finding

This forced path exposed a layout/OCR miss: `glm-ocr:latest` did not extract Question 11 from the rendered page image, even after rerendering the page at higher resolution and OCRing the lower page crop. DeepSeek V4 therefore could not extract Question 11 from the GLM OCR text. This supports the README note that robust ingestion needs page diagnostics, selective crops/regions, and provenance instead of treating one full-page OCR pass as authoritative.

## Per-Page Results

| Page | Expected | Extracted | Status | Latency ms |
|---:|---:|---:|---|---:|
| 2 | 2 | 2 | ok | 22989 |
| 3 | 4 | 4 | ok | 11555 |
| 4 | 2 | 2 | ok | 5238 |
| 5 | 3 | 2 | ok | 5397 |
| 6 | 2 | 2 | ok | 5712 |
| 7 | 1 | 1 | ok | 8756 |
| 8 | 1 | 1 | ok | 7329 |
| 9 | 2 | 2 | ok | 21930 |
| 10 | 4 | 4 | ok | 9691 |
| 11 | 4 | 4 | ok | 11670 |
| 12 | 4 | 4 | ok | 10078 |
| 13 | 2 | 2 | ok | 3408 |
| 14 | 2 | 2 | ok | 63888 |

## Extracted Questions And Options

### Question 1

Former astronaut Ellen Ochoa says that although she doesn’t have a definite idea of when it might happen, she ____ that humans will someday need to be able to live in other environments than those found on Earth. This conjecture informs her interest in future research missions to the moon.

- **A)** demands
- **B)** speculates
- **C)** doubts
- **D)** establishes

### Question 2

Beginning in the 1950s, Navajo Nation legislator Annie Dodge Wauneka continuously worked to promote public health; this ____ effort involved traveling throughout the vast Navajo homeland and writing a medical dictionary for speakers of Diné bizaad, the Navajo language.

- **A)** impartial
- **B)** offhand
- **C)** persistent
- **D)** mandatory

### Question 3

Following the principles of community-based participatory research, tribal nations and research institutions are equal partners in health studies conducted on reservations. A collaboration between the Crow Tribe and Montana State University ____ this model: tribal citizens worked alongside scientists to design the methodology and continue to assist in data collection. Which choice completes the text with the most logical and precise word or phrase?

- **A)** circumvents
- **B)** eclipses
- **C)** fabricates
- **D)** exemplifies

### Question 4

The parasitic dodder plant increases its reproductive success by flowering at the same time as the host plant it has latched onto. In 2020, Jianqiang Wu and his colleagues determined that the tiny dodder achieves this ____ with its host by absorbing and utilizing a protein the host produces when it is about to flower. Which choice completes the text with the most logical and precise word or phrase?

- **A)** synchronization
- **B)** hibernation
- **C)** prediction
- **D)** moderation

### Question 5

Given that the conditions in binary star systems should make planetary formation nearly impossible, it’s not surprising that the existence of planets in such systems has lacked ____ explanation. Roman Rafikov and Kedron Silsbee shed light on the subject when they used modeling to determine a complex set of factors that could support planets’ development. Which choice completes the text with the most logical and precise word or phrase?

- **A)** a discernible
- **B)** a straightforward
- **C)** an inconclusive
- **D)** an unbiased

### Question 6

Seminole/Muscogee director Sterlin Harjo ____ television’s tendency to situate Native characters in the distant past: this rejection is evident in his series *Reservation Dogs*, which revolves around teenagers who dress in contemporary styles and whose dialogue is laced with current slang. Which choice completes the text with the most logical and precise word or phrase?

- **A)** repudiates
- **B)** proclaims
- **C)** foretells
- **D)** recants

### Question 7

Which choice best states the main purpose of the text?

- **A)** To discuss von Ahn’s invention of reCAPTCHA
- **B)** To explain how digital scanners work
- **C)** To call attention to von Ahn’s book-digitizing project
- **D)** To indicate how popular reCAPTCHA is

### Question 8

Which choice best describes the function of the underlined sentence in the text as a whole?

- **A)** It creates a detailed image of the physical setting of the scene.
- **B)** It establishes that a character is experiencing an internal conflict.
- **C)** It makes an assertion that the next sentence then expands on.
- **D)** It illustrates an idea that is introduced in the previous sentence.

### Question 9

A study by a team including finance professor Madhu Veeraraghavan suggests that exposure to sunshine during the workday can lead to overly optimistic behavior. Using data spanning from 1994 to 2010 for a set of US companies, the team compared over 29,000 annual earnings forecasts to the actual earnings later reported by those companies. The team found that the greater the exposure to sunshine at work in the two weeks before a manager submitted an earnings forecast, the more the manager’s forecast exceeded what the company actually earned that year.

Which choice best states the function of the underlined sentence in the overall structure of the text?

- **A)** To summarize the results of the team’s analysis
- **B)** To present a specific example that illustrates the study’s findings
- **C)** To explain part of the methodology used in the team’s study
- **D)** To call out a challenge the team faced in conducting its analysis

### Question 10

The following text is adapted from Edith Nesbit’s 1906 novel The Railway Children.

Mother did not spend all her time in paying dull [visits] to dull ladies, and sitting dully at home waiting for dull ladies to pay [visits] to her. She was almost always there, ready to play with the children, and read to them, and help them to do their home-lessons. Besides this she used to write stories for them while they were at school, and read them aloud after tea, and she always made up funny pieces of poetry for their birthdays and for other great occasions.

According to the text, what is true about Mother?

- **A)** She wishes that more ladies would visit her.
- **B)** Birthdays are her favorite special occasion.
- **C)** She creates stories and poems for her children.
- **D)** Reading to her children is her favorite activity.

### Question 12

“To You” is an 1856 poem by Walt Whitman. In the poem, Whitman suggests that readers, whom he addresses directly, have not fully understood themselves, writing, _____

Which quotation from “To You” most effectively illustrates the claim?

- **A)** “You have not known what you are, you have slumber’d upon yourself / all your life, / Your eyelids have been the same as closed most of the time.”
- **B)** “These immense meadows, these interminable rivers, you are immense / and interminable as they.”
- **C)** “I should have made my way straight to you long ago, / I should have blabb’d nothing but you, I should have chanted nothing / but you.”
- **D)** “I will leave all and come and make the hymns of you, / None has understood you, but I understand you.”

### Question 13

Born in 1891 to a Quechua-speaking family in the Andes Mountains of Peru, Martín Chambi is today considered to be one of the most renowned figures of Latin American photography. In a paper for an art history class, a student claims that Chambi’s photographs have considerable ethnographic value—in his work, Chambi was able to capture diverse elements of Peruvian society, representing his subjects with both dignity and authenticity.

Which finding, if true, would most directly support the student’s claim?

- **A)** Chambi took many commissioned portraits of wealthy Peruvians, but he also produced hundreds of images carefully documenting the peoples, sites, and customs of Indigenous communities of the Andes.
- **B)** Chambi’s photographs demonstrate a high level of technical skill, as seen in his strategic use of illumination to create dramatic light and shadow contrasts.
- **C)** During his lifetime, Chambi was known and celebrated both within and outside his native Peru, as his work was published in places like Argentina, Spain, and Mexico.
- **D)** Some of the peoples and places Chambi photographed had long been popular subjects for Peruvian photographers.

### Question 14

Credited Film Output of James Young Deer, Dark Cloud, Edwin Carewe, and Lillian St. Cyr

| Individual | Years active | Number of films known and commonly credited |
| :--- | :--- | :--- |
| James Young Deer | 1909–1924 | 33 (actor), 35 (director), 10 (writer) |
| Dark Cloud | 1910–1920 | 35 (actor), 1 (writer) |
| Edwin Carewe | 1912–1934 | 47 (actor), 58 (director), 20 (producer), 4 (writer) |
| Lillian St. Cyr (Red Wing) | 1908–1921 | 66 (actor) |

Some researchers studying Indigenous actors and filmmakers in the United States have turned their attention to the early days of cinema, particularly the 1910s and 1920s, when people like James Young Deer, Dark Cloud, Edwin Carewe, and Lillian St. Cyr (known professionally as Red Wing) were involved in one way or another with numerous films. In fact, so many films and associated records for this era have been lost that counts of those four figures’ output should be taken as bare minimums rather than totals; it’s entirely possible, for example, that _____

- **A)** Dark Cloud acted in significantly fewer films than did Lillian St. Cyr, who is credited with 66 performances.
- **B)** Edwin Carewe’s 47 credited acting roles includes only films made after 1934.
- **C)** Lillian St. Cyr acted in far more than 66 films and Edwin Carewe directed more than 58.
- **D)** James Young Deer actually directed 33 films and acted in only 10.

### Question 15

Juvenile Plants Found Growing on Bare Ground and in Patches of Vegetation for Five Species

| Species | Bare ground | Patches of vegetation | Total | Percent found in patches of vegetation |
| :--- | :--- | :--- | :--- | :--- |
| *T. moroderi* | 9 | 13 | 22 | 59.1% |
| *T. libanitis* | 83 | 120 | 203 | 59.1% |
| *H. syriacim* | 95 | 106 | 201 | 52.7% |
| *H. squamatum* | 218 | 321 | 539 | 59.6% |
| *H. stoechas* | 11 | 12 | 23 | 52.2% |

Alicia Montesinos-Navarro, Isabelle Storer, and Rocío Perez-Barrales recently examined several plots within a diverse plant community in southeast Spain. The researchers calculated that if individual plants were randomly distributed on this particular landscape, only about 15% would be with other plants in patches of vegetation. They counted the number of juvenile plants of five species growing in patches of vegetation and the number growing alone on bare ground and compared those numbers to what would be expected if the plants were randomly distributed. Based on these results, they claim that plants of these species that grow in close proximity to other plants gain an advantage at an early developmental stage.

Which choice best describes data from the table that support the researchers’ claim?

- **A)** For all five species, less than 75% of juvenile plants were growing in patches of vegetation.
- **B)** The species with the greatest number of juvenile plants growing in patches of vegetation was *H. stoechas*.
- **C)** For *T. libanitis* and *T. moroderi*, the percentage of juvenile plants growing in patches of vegetation was less than what would be expected if plants were randomly distributed.
- **D)** For each species, the percentage of juvenile plants growing in patches of vegetation was substantially higher than what would be expected if plants were randomly distributed.

### Question 16

In the mountains of Brazil, *Barbacenia tomentosa* and *Barbacenia macrantha*—two plants in the Velloziaceae family—establish themselves on soilless, nutrient-poor patches of quartzite rock. Plant ecologists Anna Abrahão and Patricia de Britto Costa used microscopic analysis to determine that the roots of *B. tomentosa* and *B. macrantha*, which grow directly into the quartzite, have clusters of fine hairs near the root tip; further analysis indicated that these hairs secrete both malic and citric acids. The researchers hypothesize that the plants depend on dissolving underlying rock with these acids, as the process not only creates channels for continued growth but also releases phosphates that provide the vital nutrient phosphorus.

Which finding, if true, would most directly support the researchers’ hypothesis?

- **A)** Other species in the Velloziaceae family are found in terrains with more soil but have root structures similar to those of *B. tomentosa* and *B. macrantha*.
- **B)** Though *B. tomentosa* and *B. macrantha* both secrete citric and malic acids, each species produces the acids in different proportions.
- **C)** The roots of *B. tomentosa* and *B. macrantha* carve new entry points into rocks even when cracks in the surface are readily available.
- **D)** *B. tomentosa* and *B. macrantha* thrive even when transferred to the surfaces of rocks that do not contain phosphates.

### Question 17

Herbivorous sauropod dinosaurs could grow more than 100 feet long and weigh up to 80 tons, and some researchers have attributed the evolution of sauropods to such massive sizes to increased plant production resulting from high levels of atmospheric carbon dioxide during the Mesozoic era. However, there is no evidence of significant spikes in carbon dioxide levels coinciding with relevant periods in sauropod evolution, such as when the first large sauropods appeared, when several sauropod lineages underwent further evolution toward gigantism, or when sauropods reached their maximum known sizes, suggesting that _____

Which choice most logically completes the text?

- **A)** fluctuations in atmospheric carbon dioxide affected different sauropod lineages differently.
- **B)** the evolution of larger body sizes in sauropods did not depend on increased atmospheric carbon dioxide.
- **C)** atmospheric carbon dioxide was higher when the largest known sauropods lived than it was when the first sauropods appeared.
- **D)** sauropods probably would not have evolved to such immense sizes if atmospheric carbon dioxide had been even slightly higher.

### Question 18

In documents called judicial opinions, judges explain the reasoning behind their legal rulings, and in those explanations they sometimes cite and discuss historical and contemporary philosophers. Legal scholar and philosopher Anita L. Allen argues that while judges are naturally inclined to mention philosophers whose views align with their own positions, the strongest judicial opinions consider and rebut potential objections; discussing philosophers whose views conflict with judges’ views could therefore _____

- **A)** allow judges to craft judicial opinions without needing to consult philosophical works.
- **B)** help judges improve the arguments they put forward in their judicial opinions.
- **C)** make judicial opinions more comprehensible to readers without legal or philosophical training.
- **D)** bring judicial opinions in line with views that are broadly held among philosophers.

### Question 19

Public-awareness campaigns about the need to reduce single-use plastics can be successful, says researcher Kim Borg of Monash University in Australia, when these campaigns give consumers a choice: for example, Japan achieved a 40 percent reduction in plastic-bag use after cashiers were instructed to ask customers whether _____ wanted a bag.

- **A)** they
- **B)** one
- **C)** you
- **D)** it

### Question 20

In ancient Greece, an Epicurean was a follower of Epicurus, a philosopher whose beliefs revolved around the pursuit of pleasure. Epicurus defined pleasure as “the absence of pain in the body and of trouble in the _____ that all life’s virtues derived from this absence.

- **A)** soul,” positing
- **B)** soul”: positing
- **C)** soul”; positing
- **D)** soul.” Positing

### Question 21

British scientists James Watson and Francis Crick won the Nobel Prize in part for their 1953 paper announcing the double helix structure of DNA, but it is misleading to say that Watson and Crick discovered the double helix. _____ findings were based on a famous X-ray image of DNA fibers, “Photo 51,” developed by X-ray crystallographer Rosalind Franklin and her graduate student Raymond Gosling.

- **A)** They’re
- **B)** It’s
- **C)** Their
- **D)** Its

### Question 22

In 1937, Chinese American screen actor Anna May Wong, who had portrayed numerous villains and secondary characters but never a heroine, finally got a starring role in Paramount Pictures’ Daughter of Shanghai, a film that ____ “expanded the range of possibilities for Asian images on screen.”

- **A)** critic, Stina Chyn, claims
- **B)** critic, Stina Chyn, claims,
- **C)** critic Stina Chyn claims
- **D)** critic Stina Chyn, claims,

### Question 23

In 1637, the price of tulips skyrocketed in Amsterdam, with single bulbs of rare varieties selling for up to the equivalent of $200,000 in today’s US dollars. Some historians ____ that this “tulip mania” was the first historical instance of an asset bubble, which occurs when investors drive prices to highs not supported by actual demand.

- **A)** claiming
- **B)** claim
- **C)** having claimed
- **D)** to claim

### Question 24

Researchers studying magnetosensation have determined why some soil-dwelling roundworms in the Southern Hemisphere move in the opposite direction of Earth’s magnetic field when searching for ____ in the Northern Hemisphere, the magnetic field points down, into the ground, but in the Southern Hemisphere, it points up, toward the surface and away from worms’ food sources.

- **A)** food:
- **B)** food,
- **C)** food while
- **D)** food

### Question 25

Scientists believe that, unlike most other species of barnacle, turtle barnacles (Chelonibia testudinari) can dissolve the cement-like secretions they use to attach ____ to a sea turtle shell, enabling the barnacles to move short distances across the shell’s surface.

- **A)** it
- **B)** themselves
- **C)** them
- **D)** itself

### Question 26

The classic children’s board game Chutes and Ladders is a version of an ancient Nepalese game, Paramapada Sopanapata. In both games, players encounter “good” or “bad” spaces while traveling along a path; landing on one of the good spaces ____ a player to skip ahead and arrive closer to the end goal. Which choice completes the text so that it conforms to the conventions of Standard English?

- **A)** allows
- **B)** are allowing
- **C)** have allowed
- **D)** allow

### Question 27

In 1943, in the midst of World War II, mathematics professor Grace Hopper was recruited by the US military to help the war effort by solving complex equations. Hopper’s subsequent career would involve more than just ____ as a pioneering computer programmer, Hopper would help usher in the digital age. Which choice completes the text so that it conforms to the conventions of Standard English?

- **A)** equations, though:
- **B)** equations, though,
- **C)** equations. Though,
- **D)** equations though

### Question 28

In 1453, English King Henry VI became unfit to rule after falling gravely ill. As a result, Parliament appointed Richard, Third Duke of York, who had a strong claim to the English throne, to rule as Lord Protector. Upon recovering two years later, ____ forcing an angered Richard from the royal court and precipitating a series of battles later known as the Wars of the Roses. Which choice completes the text so that it conforms to the conventions of Standard English?

- **A)** Henry resumed his reign,
- **B)** the reign of Henry resumed,
- **C)** Henry’s reign resumed,
- **D)** it was Henry who resumed his reign,

### Question 29

Although novels and poems are considered distinct literary forms, many authors have created hybrid works that incorporate elements of both. Bernardine Evaristo’s The Emperor’s Babe, ____ is a verse novel, a book-length narrative complete with characters and a plot but conveyed in short, crisp lines of poetry rather than prose. Which choice completes the text with the most logical transition?

- **A)** by contrast,
- **B)** consequently,
- **C)** secondly,
- **D)** for example,

### Question 30

At two weeks old, the time their critical socialization period begins, wolves can smell but cannot yet see or hear. Domesticated dogs, ____ can see, hear, and smell by the end of two weeks. This relative lack of sensory input may help explain why wolves behave so differently around humans than dogs do: from a very young age, wolves are more wary and less exploratory.

Which choice completes the text with the most logical transition?

- **A)** in other words,
- **B)** for instance,
- **C)** by contrast,
- **D)** accordingly,

### Question 31

Researchers Helena Mihaljević-Brandt, Lucía Santamaría, and Marco Tullney report that while mathematicians may have traditionally worked alone, evidence points to a shift in the opposite direction. ____ mathematicians are choosing to collaborate with their peers—a trend illustrated by a rise in the number of mathematics publications credited to multiple authors.

Which choice completes the text with the most logical transition?

- **A)** Similarly,
- **B)** For this reason,
- **C)** Furthermore,
- **D)** Increasingly,

### Question 32

While researching a topic, a student has taken the following notes:

• Pterosaurs were flying reptiles that existed millions of years ago.
• In a 2021 study, Anusuya Chinsamy-Turan analyzed fragments of pterosaur jawbones located in the Sahara Desert.
• She was initially unsure if the bones belonged to juvenile or adult pterosaurs.
• She used advanced microscope techniques to determine that the bones had few growth lines relative to the bones of fully grown pterosaurs.
• She concluded that the bones belonged to juveniles.

The student wants to present the study and its findings. Which choice most effectively uses relevant information from the notes to accomplish this goal?

- **A)** In 2021, Chinsamy-Turan studied pterosaur jawbones and was initially unsure if the bones belonged to juveniles or adults.
- **B)** Pterosaur jawbones located in the Sahara Desert were the focus of a 2021 study.
- **C)** In a 2021 study, Chinsamy-Turan used advanced microscope techniques to analyze the jawbones of pterosaurs, flying reptiles that existed millions of years ago.
- **D)** In a 2021 study, Chinsamy-Turan determined that pterosaur jawbones located in the Sahara Desert had few growth lines relative to the bones of fully grown pterosaurs and thus belonged to juveniles.

### Question 33

While researching a topic, a student has taken the following notes:

• African American women played prominent roles in the Civil Rights Movement, including at the famous 1963 March on Washington.
• Civil rights activist Anna Hedgeman, one of the march’s organizers, was a political adviser who had worked for President Truman.
• Civil rights activist Daisy Bates was a well-known journalist and advocate for school desegregation.
• Hedgeman worked behind the scenes to make sure a woman was included in the lineup of speakers at the march.
• Bates was the sole woman to speak, delivering a brief but memorable address to the cheering crowd.

The student wants to compare the two women’s contributions to the March on Washington. Which choice most effectively uses relevant information from the notes to accomplish this goal?

- **A)** Hedgeman and Bates contributed to the march in different ways; Bates, for example, delivered a brief but memorable address.
- **B)** Hedgeman worked in politics and helped organize the march, while Bates was a journalist and school desegregation advocate.
- **C)** Although Hedgeman worked behind the scenes to make sure a woman speaker was included, Bates was the sole woman to speak at the march.
- **D)** Many African American women, including Bates and Hedgeman, fought for civil rights, but only one spoke at the march.
