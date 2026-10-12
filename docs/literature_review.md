# Literature Review and Design Rationale

## 1. Scope and method

This review supports ResumeLens, an educational and deterministic résumé-processing pipeline in which each stage is a formal model: regular expressions (Stage 1), finite-state transducers (Stage 2), deterministic finite automata (Stage 3) and a context-free grammar implemented with textX (Stage 4). Its purpose, as the assignment states, is to guide the project, avoid reinventing existing work and justify the design decisions. It is a **focused** review, not a systematic one: it does not evaluate commercial applicant-tracking systems and does not compare ranking algorithms, because ResumeLens deliberately neither ranks candidates nor makes hiring decisions.

**Questions.**

- **RQ1.** How has prior work extracted information from résumés, and what are the trade-offs between rule-based and statistical approaches?
- **RQ2.** Which formal models support normalizing variants of the same term into a canonical form?
- **RQ3.** How can the satisfaction of a qualification pattern be decided in an explainable way?
- **RQ4.** How should a structured candidate representation be specified, validated and visualized?
- **RQ5.** What risks and limits does automated screening carry, and how should a system like this be tested?

**Search.** ACM Digital Library, ACL Anthology, IEEE Xplore, arXiv and Google Scholar, plus the official documentation of the libraries used (Python `re`, pyformlang, textX/Arpeggio) and the course material. Keywords: *resume parsing*, *résumé information extraction*, *skill extraction*, *e-recruitment*, *rule-based information extraction*, *finite-state transducer normalization*, *text normalization*, *deterministic finite automata*, *domain-specific language*, *EBNF*, *parsing expression grammar*, *textX*, *algorithmic hiring bias*, *grammar-based testing*, *mutation testing*. Sources were last consulted on 11 October 2026.

**Inclusion criteria.** Peer-reviewed papers, standard textbooks and standards that either (a) address résumé/job-posting information extraction, (b) define or analyze one of the four formal models we use, or (c) address validation, testing or fairness of such systems. Classic foundational papers are included when the project relies directly on their results (e.g. the theorem that a non-self-embedding grammar generates a regular language).

## 2. Résumé processing: context and related work (RQ1)

**Hybrid statistical extraction.** Yu, Guan and Zhou (2005) treat résumé information extraction as a *cascade*: first segment the résumé into general blocks (personal data, education, experience) with a hidden Markov model, then extract fields inside each block with an HMM or an SVM. Their key observation — that fields are easier to recognise once the section is known — is the same one that motivates Stage 1's section tracking (`sections.py`): a technology mentioned inside an e-mail address or in a "soft skills" heading must not become a technical skill. The difference is that we implement the cascade with explicit regular expressions and section boundaries, so every extraction can be traced to a pattern, at the cost of lower recall on unseen formats.

**Rule-based screening systems.** PROSPECT (Singh et al., 2010) extracts skills, experience and education from résumés to help recruiters shortlist candidates, combining information extraction with lexicons. Kopparapu (2010) extracts usable fields from unstructured résumés mainly with rules and keyword lists. Faliagka, Tsakalidis and Tzimas (2012) go further and *rank* applicants, combining extracted qualifications with personality traits mined from text. ResumeLens keeps the first half of this line of work (structured extraction) and explicitly rejects the second (ranking): its output is a membership decision for formally stated patterns, which can be inspected and contested.

**Skill extraction as a learning task.** Recent work frames skill extraction as span labelling on job postings: SkillSpan (Zhang et al., 2022) provides an annotated corpus of hard and soft skills and shows that domain-adapted language models improve extraction. Such models generalize better to unseen wording than a fixed vocabulary, but they require annotated data and produce decisions that are harder to explain. Large language models have also been proposed as screening agents (Gan, Zhang & Mori, 2024); they summarize and grade résumés flexibly, but their outputs are not guaranteed to be reproducible or traceable to an explicit rule.

**Why rules here.** Chiticariu, Li and Reiss (2013) document a gap between academia, where statistical extraction dominates publications, and industry, where rule-based extraction remains widespread because rules are *explainable, debuggable and easy to adapt* without retraining. That is exactly the requirement of this project: every decision must be justified by a formal model. We therefore adopt explicit rules and accept their known weakness (coverage) as a documented limitation (§8).

**Skill taxonomies.** Public taxonomies such as ESCO (European Commission) and O\*NET (U.S. Department of Labor) organize thousands of skills and occupations with preferred labels and alternative labels. Stage 2's canonical vocabulary (79 tokens grouped in families) follows the same *preferred label + aliases* idea at a much smaller scale; mapping our tokens to ESCO identifiers would be the natural way to scale the vocabulary.

## 3. Regular expressions for explicit evidence (Stage 1, RQ1)

Kleene (1956) introduced regular events, and Thompson (1968) showed how to compile a regular expression into a nondeterministic automaton and simulate it in time linear in the text. Python's `re` module is a backtracking engine whose syntax goes beyond regular expressions in the formal sense (look-around, back-references); Friedl (2006) explains the practical consequences, including catastrophic backtracking and the importance of anchoring and boundaries. The Stage 1 documentation therefore (a) restricts itself to constructs whose formal meaning is clear, (b) explains each look-around as a *boundary* condition (e.g. `Node.js` must not match inside `main.js`), and (c) provides, for each expression, its equivalent automaton and negative examples. The Python documentation's distinction between *searching* and *full matching* is used deliberately: extraction uses `finditer`, while Stage 4 reuses the same contact expressions with full matching to validate DSL values.

A regular expression only establishes that a mention exists. It does not establish proficiency, recency or real experience, and it cannot interpret negation ("no experience with Java"). These limits are inherent to the model, not to our implementation, and are stated wherever results are reported.

## 4. Finite-state transducers for normalization (Stage 2, RQ2)

Finite-state transducers (FSTs) are the classical model for rewriting text in language technology. Kaplan and Kay (1994) showed that the rewrite rules used in phonology can be compiled into regular relations and composed into a single transducer; Mohri (1997) surveys weighted and unweighted transducers, their composition and determinization, and their use in speech and language processing; Roche and Schabes (1997) and Beesley and Karttunen (2003) present finite-state methods as practical engineering tools. Text normalization for speech synthesis — turning "Dr." into "doctor" or "2 kg" into "two kilograms" — is a close analogue of our problem: Sproat et al. (2001) classify such *non-standard words* and normalize them with a cascade of rules and models, and the Kestrel system (Ebden & Sproat, 2015) does it with weighted grammars compiled to FSTs.

ResumeLens applies the same idea at a smaller scale: `JS`, `Javascript` and `java script` become `JAVASCRIPT`; `sklearn` and `scikit learn` become `SCIKIT_LEARN`. We use a **cascade** CLEAN ∘ ALIAS ∘ EXPERIENCE ∘ FILTER, as recommended in this literature, because each small transducer can be specified (7-tuple), drawn and tested separately, while composition preserves the overall regular-relation semantics. A dictionary lookup would normalize the same aliases more simply, but it would not show the transduction model the assignment asks for, nor the tokenization and case-folding steps that the CLEAN transducer makes explicit.

## 5. Deterministic finite automata for qualification patterns (Stage 3, RQ3)

Rabin and Scott (1959) defined finite automata and proved the equivalence of deterministic and nondeterministic automata; Hopcroft (1971) gave the efficient minimization algorithm, and Hopcroft, Motwani and Ullman (2006) present the standard theory (closure properties, decision procedures, Myhill–Nerode). These results justify three choices of Stage 3: (a) each professional profile is a regular pattern over category symbols, so a DFA is sufficient; (b) we use a **total** transition function with an explicit trap state, which makes every rejection explainable by the step where the trap was entered; and (c) we can *prove* properties such as totality, absence of useless states and minimality (three of the four automata are minimal; in Full Stack two states are equivalent, which the document shows), which the Stage 3 document does and the export script machine-checks.

pyformlang (Romero, 2021) is an educational Python library that implements regular expressions, automata, transducers and grammars with their classical algorithms. Using it means that the formal objects in the documents (5-tuples, 7-tuples) are the same objects executed by the program, which is the educational point of the project; the paper supports this choice of tool, not any claim about hiring accuracy.

## 6. Context-free grammars, DSLs and textX (Stage 4, RQ4)

**Grammars and notation.** Chomsky (1956, 1959) introduced phrase-structure grammars and proved, among other results, that a context-free grammar that is not *self-embedding* generates a regular language — the result we use to state precisely that our document language, with its bounded nesting, is regular at token level (Stage 4, Theorem 2). BNF was introduced to define ALGOL 60 (Backus et al., 1963); Wirth (1977) proposed the extended notation with `[ ]` and `{ }` for options and repetition that later became ISO/IEC 14977 (EBNF), the notation required by the assignment. Knuth (1968) defined attribute grammars, which give meaning to a grammar by computing attributes on the parse tree; the construction of the `CandidateProfile` from a parse tree is an S-attributed definition in this sense.

**Domain-specific languages.** Mernik, Heering and Sloane (2005) analyse when developing a DSL pays off — notably when a domain has a stable vocabulary of concepts and the notation must be checked and processed by tools — and survey implementation patterns (interpreter, compiler, embedding, and *language workbenches* that generate parsers from grammars). Fowler (2010) distinguishes external DSLs (own syntax, own parser) from internal ones. Stage 4 is a small external DSL implemented with a language workbench: textX.

**textX and PEG.** textX (Dejanović et al., 2017) builds a parser *and* a metamodel from a single grammar: each rule becomes a class, each assignment an attribute, and parsing produces an object graph ready to use, which removes the usual step of writing a tree walker. It runs on Arpeggio (Dejanović, Milosavljević & Vaderna, 2016), a parser for *parsing expression grammars* (PEG). PEGs (Ford, 2004) use ordered choice and greedy repetition and are therefore unambiguous by construction, but in general a PEG and the CFG with the same rules may describe different languages. Mascarenhas, Medeiros and Ierusalimschy (2014) proved that for **LL(1)** grammars both interpretations define the same language. Our grammar is LL(1) (Stage 4, Theorem 1), which is why the EBNF in the design document and the textX implementation describe exactly the same set of documents — a claim we also check by differential testing. The textX documentation describes the two mechanisms we rely on beyond syntax: *object processors* (to decode JSON strings and integers) and *model processors* (to check vocabulary, contact formats and uniqueness after parsing).

**Static semantics.** Conditions such as "a skill appears at most once" are context conditions, traditionally checked after parsing (Aho et al., 2006, ch. 5–6) rather than encoded in the context-free syntax. Keeping them in a model processor also lets Stage 4 reuse the Stage 1 expressions and the Stage 2 vocabulary instead of copying them into the grammar.

**Existing structured résumé formats.** JSON Resume defines a community JSON schema for résumés, and HR Open Standards (formerly HR-XML) and the Europass CV define XML/JSON vocabularies for recruitment data. They solve interchange, not explanation: they have no grammar-based error messages and do not record the outcome of a formal classification. ResumeLens keeps JSON as the API format and uses its own small DSL as the *validated* representation required by the assignment; the DSL's string literals follow JSON escaping (RFC 8259) so that the two worlds convert without loss.

**Safe visualization.** Rendering text taken from a document into HTML is a classical injection risk. The OWASP Cross-Site Scripting Prevention Cheat Sheet recommends context-aware output encoding; Stage 4 places data only in element content, escapes `& < > " '`, and adds a restrictive Content-Security-Policy to the generated page.

## 7. Fairness, transparency and testing (RQ5)

**Risks of automated hiring.** Bogen and Rieke (2018) review how hiring algorithms can reproduce historical bias at every step of the pipeline, and Raghavan et al. (2020) analyse the claims of commercial vendors and find little public evidence of validation or bias mitigation. A widely reported case is the experimental Amazon recruiting tool, abandoned after it learned to penalize résumés that mentioned women's organizations (Dastin, 2018). These works motivate three decisions of ResumeLens: no learned ranking; no use of personal data (name, location, contact) in any decision — those fields are carried to the output but never read by the automata; and transparent, traceable decisions whose patterns are written down and can be criticized.

**Testing formal-language software.** Classic techniques — equivalence partitioning, boundary values and decision tables (Myers et al., 2011) — apply directly to extractors and validators. Grammar-based test generation goes back to Hanford (1970) and Purdom (1972), who generated sentences from a grammar to test parsers. Differential testing (McKeeman, 1998) compares two independent implementations; in Stage 3 the oracle is a regular expression over categories. Property-based testing (Claessen & Hughes, 2000) checks laws such as `parse(serialize(m)) = m` on random inputs. In Stage 4 the tests use partitions, boundaries, hand-made round trips (`parse(serialize(m)) = m`) and adversarial text, and their strength is measured by mutation analysis. Mutation analysis (Jia & Harman, 2011) measures whether the suite would detect injected faults; we report mutation scores per stage.

## 8. Synthesis: alternatives and decisions

| Problem | Alternatives in the literature | Choice in ResumeLens | Reason / trade-off |
|---|---|---|---|
| Extract candidate data and skill mentions | HMM/CRF cascades; neural span labelling (SkillSpan); LLM agents | explicit regular expressions with section boundaries | explainable and testable without annotated data; lower recall on unseen wording |
| Normalize aliases | dictionary lookup; embeddings; FST cascades | FST cascade with pyformlang | formal 7-tuples and composition; each step drawable and testable |
| Decide if a profile is satisfied | scoring/ranking; classifiers; rules | one DFA per profile with trap state | membership is decidable and traceable; totality, determinism and (non-)minimality are proven; no ranking |
| Represent the result | JSON Resume / HR Open / Europass; templates | textX DSL with EBNF, then JSON and HTML | grammar-based validation with located errors; LL(1) so PEG = CFG |
| Show the result | template engines; client-side rendering | self-contained HTML after validation, fully escaped, CSP | no injection; printable; works offline |
| Assure quality | example tests | partitions, boundaries, decision tables, differential tests (Stage 3), round trips, mutation analysis | evidence that tests detect faults, not only that code runs |

**Gap addressed.** Most published résumé systems optimize extraction accuracy or ranking quality with statistical models. ResumeLens addresses a different, educational and practical need: an end-to-end pipeline in which *every* step is a formal model with a written specification, a proof of its key properties and an executable implementation, so that a decision about a candidate can be explained from the text up to the HTML.

**Limits and future work.** The pipeline has no annotated corpus, so extraction precision and recall are unknown; negation and context ("used Java in 2010") are not interpreted; the vocabulary is small and English-centred; and acceptance of a pattern is not evidence of competence. Natural next steps are an annotated evaluation set, mapping the vocabulary to ESCO, and weighted transducers to handle uncertain aliases.

## Bibliography

1. Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006). *Compilers: Principles, Techniques, and Tools* (2nd ed.). Pearson.
2. Backus, J. W., et al. (1963). Revised report on the algorithmic language ALGOL 60 (P. Naur, Ed.). *Communications of the ACM, 6*(1), 1–17.
3. Beesley, K. R., & Karttunen, L. (2003). *Finite State Morphology*. CSLI Publications.
4. Bogen, M., & Rieke, A. (2018). *Help Wanted: An Examination of Hiring Algorithms, Equity, and Bias*. Upturn.
5. Bray, T. (Ed.). (2017). *The JavaScript Object Notation (JSON) Data Interchange Format* (RFC 8259). IETF.
6. Chiticariu, L., Li, Y., & Reiss, F. R. (2013). Rule-based information extraction is dead! Long live rule-based information extraction systems! *Proceedings of EMNLP 2013*. https://aclanthology.org/D13-1079/
7. Chomsky, N. (1956). Three models for the description of language. *IRE Transactions on Information Theory, 2*(3), 113–124.
8. Chomsky, N. (1959). On certain formal properties of grammars. *Information and Control, 2*(2), 137–167.
9. Claessen, K., & Hughes, J. (2000). QuickCheck: A lightweight tool for random testing of Haskell programs. *ICFP '00*, 268–279. https://doi.org/10.1145/351240.351266
10. Dastin, J. (2018, October 10). Amazon scraps secret AI recruiting tool that showed bias against women. *Reuters*.
11. Dejanović, I., Milosavljević, G., & Vaderna, R. (2016). Arpeggio: A flexible PEG parser for Python. *Knowledge-Based Systems, 95*, 71–74.
12. Dejanović, I., Vaderna, R., Milosavljević, G., & Vuković, Ž. (2017). TextX: A Python tool for Domain-Specific Languages implementation. *Knowledge-Based Systems, 115*, 1–4. https://doi.org/10.1016/j.knosys.2016.10.023
13. Ebden, P., & Sproat, R. (2015). The Kestrel TTS text normalization system. *Natural Language Engineering, 21*(3).
14. European Commission. *ESCO — European Skills, Competences, Qualifications and Occupations*. https://esco.ec.europa.eu/
15. Faliagka, E., Tsakalidis, A., & Tzimas, G. (2012). An integrated e-recruitment system for automated personality mining and applicant ranking. *Internet Research, 22*(5), 551–568.
16. Ford, B. (2004). Parsing expression grammars: A recognition-based syntactic foundation. *POPL '04*, 111–122. https://doi.org/10.1145/964001.964011
17. Fowler, M. (2010). *Domain-Specific Languages*. Addison-Wesley.
18. Friedl, J. E. F. (2006). *Mastering Regular Expressions* (3rd ed.). O'Reilly.
19. Gan, C., Zhang, Q., & Mori, T. (2024). Application of LLM agents in recruitment: A novel framework for resume screening. *Journal of Information Processing, 32*. https://arxiv.org/abs/2401.08315
20. Hanford, K. V. (1970). Automatic generation of test cases. *IBM Systems Journal, 9*(4), 242–257.
21. Hopcroft, J. E. (1971). An n log n algorithm for minimizing states in a finite automaton. In *Theory of Machines and Computations* (pp. 189–196). Academic Press.
22. Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2006). *Introduction to Automata Theory, Languages, and Computation* (3rd ed.). Pearson.
23. ISO/IEC 14977:1996. *Information technology — Syntactic metalanguage — Extended BNF*.
24. Jia, Y., & Harman, M. (2011). An analysis and survey of the development of mutation testing. *IEEE Transactions on Software Engineering, 37*(5), 649–678.
25. JSON Resume. *JSON Resume schema*. https://jsonresume.org/schema
26. Kaplan, R. M., & Kay, M. (1994). Regular models of phonological rule systems. *Computational Linguistics, 20*(3), 331–378.
27. Kleene, S. C. (1956). Representation of events in nerve nets and finite automata. In C. E. Shannon & J. McCarthy (Eds.), *Automata Studies* (pp. 3–41). Princeton University Press.
28. Knuth, D. E. (1968). Semantics of context-free languages. *Mathematical Systems Theory, 2*(2), 127–145.
29. Kopparapu, S. K. (2010). Automatic extraction of usable information from unstructured resumes to aid search. *IEEE International Conference on Progress in Informatics and Computing (PIC)*.
30. Mascarenhas, F., Medeiros, S., & Ierusalimschy, R. (2014). On the relation between context-free grammars and parsing expression grammars. *Science of Computer Programming, 89*, 235–250. https://arxiv.org/abs/1304.3177
31. McKeeman, W. M. (1998). Differential testing for software. *Digital Technical Journal, 10*(1), 100–107.
32. Mernik, M., Heering, J., & Sloane, A. M. (2005). When and how to develop domain-specific languages. *ACM Computing Surveys, 37*(4), 316–344. https://doi.org/10.1145/1118890.1118892
33. Mohri, M. (1997). Finite-state transducers in language and speech processing. *Computational Linguistics, 23*(2), 269–311.
34. Myers, G. J., Sandler, C., & Badgett, T. (2011). *The Art of Software Testing* (3rd ed.). Wiley.
35. OWASP Foundation. *Cross Site Scripting Prevention Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
36. Purdom, P. (1972). A sentence generator for testing parsers. *BIT Numerical Mathematics, 12*(3), 366–375.
37. Python Software Foundation. *re — Regular expression operations*. https://docs.python.org/3/library/re.html
38. Rabin, M. O., & Scott, D. (1959). Finite automata and their decision problems. *IBM Journal of Research and Development, 3*(2), 114–125.
39. Raghavan, M., Barocas, S., Kleinberg, J., & Levy, K. (2020). Mitigating bias in algorithmic hiring: Evaluating claims and practices. *Proceedings of FAT\* 2020*. https://arxiv.org/abs/1906.09208
40. Roche, E., & Schabes, Y. (Eds.). (1997). *Finite-State Language Processing*. MIT Press.
41. Romero, J. (2021). Pyformlang: An educational library for formal language manipulation. *SIGCSE '21*. https://doi.org/10.1145/3408877.3432464
42. Singh, A., Rose, C., Visweswariah, K., Chenthamarakshan, V., & Kambhatla, N. (2010). PROSPECT: A system for screening candidates for recruitment. *CIKM '10*.
43. Sproat, R., Black, A. W., Chen, S., Kumar, S., Ostendorf, M., & Richards, C. (2001). Normalization of non-standard words. *Computer Speech & Language, 15*(3), 287–333.
44. textX contributors. *textX documentation: Grammar, Metamodel, Error handling*. https://textx.github.io/textX/
45. Thompson, K. (1968). Regular expression search algorithm. *Communications of the ACM, 11*(6), 419–422.
46. U.S. Department of Labor. *O\*NET OnLine*. https://www.onetonline.org/
47. Wirth, N. (1977). What can we do about the unnecessary diversity of notation for syntactic definitions? *Communications of the ACM, 20*(11), 822–823.
48. Yu, K., Guan, G., & Zhou, M. (2005). Resume information extraction with cascaded hybrid model. *Proceedings of ACL 2005*. https://aclanthology.org/P05-1062/
49. Zhang, M., Jensen, K. N., Sonniks, S. D., & Plank, B. (2022). SkillSpan: Hard and soft skill extraction from English job postings. *Proceedings of NAACL 2022*. https://aclanthology.org/2022.naacl-main.366
50. Course material supplied with the task: *BNF*, *CFG*, *CyEDIIITransducers*, *mainRegexReviewRepaso*, *RG*, and *Integrative Task 1 (2026-2)* (`docs/Initial Doc.md`).
