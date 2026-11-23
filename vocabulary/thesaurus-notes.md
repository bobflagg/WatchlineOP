# Thesaurus notes

Records the cross-branch associations, label review and external mappings. Related links are written in both directions in `watchline.ttl`; each unordered pair appears once below. A related link earns its place only where the schema (`profiles/qNN.yaml`) does not already connect the two concepts. Stage 4 procedure: `specs/stage4-procedure.md`. Checked by `scripts/check_thesaurus.py` (`make thesaurus`).

## Related links

Association kinds:

- `identifier-of`: one concept is the identifier of the other.
- `contrasts-with`: look-alike concepts that must be kept apart in an answer.
- `reported-with`: an answer term that is reported only together with another.
- `output-of`: a result produced by an action on the other concept.
- `found-through`: one concept is located by means of the other.
- `same-subject-different-role`: the same thing, seen in a different role in an answer.
- `summary-of`: a flag or count on one concept that summarizes records held under the other.
- `input-to`: a stored value that is compared at answer time to produce the other concept.
- `part-of-sum`: one concept is a term added into the other.
- `source-of`: one concept is a cause or origin of the other as the answer reports it.
- `acts-on`: a recorded document type that is filed about a loan or lease assignment recorded by the other type. The record does not say which one, so the answer lists both and links neither.

| concept | concept | kind | justification |
| --- | --- | --- | --- |
| `address-party-count` | `address-document-count` | same-subject-different-role | Two hub counts for one address: distinct names and distinct documents. A reader needs both to see a hub. |
| `deed` | `document` | contrasts-with | A Deed is a deed-type document recorded against a lot in the graph; a Document is any type loaded by party names. Different nodes that share an id. |
| `document` | `document-id` | identifier-of | The id identifies the document. |
| `document` | `document-party` | summary-of | The document is the record; its parties are the people and companies recorded on it. |
| `document-party` | `has-party` | output-of | The link carries the party's role. |
| `document-party` | `party-name` | same-subject-different-role | The name is the label a reader quotes for the party. |
| `document-party` | `party-role` | same-subject-different-role | The role is recorded on the link, not on the party. |
| `grantee-name` | `party-name` | contrasts-with | A grantee name is on a loaded deed; a party name is on any loaded document in any role. |
| `mail-drop-address` | `set-aside` | source-of | A mail-drop list entry is one reason an address is set aside. |
| `network-masked-address` | `set-aside` | source-of | A network mask is one reason an address is set aside. |
| `portfolio-masked-address` | `set-aside` | source-of | A portfolio mask is one reason an address is set aside. |
| `bbl` | `tax-lot` | identifier-of | The BBL identifies the lot. Users ask for "the BBL of" an address, and the schema holds it only as a property name. |
| `bin` | `building` | identifier-of | The BIN identifies the building. Same reason as the BBL. |
| `building` | `pluto-building-count` | contrasts-with | HPD's list of buildings and PLUTO's count disagree on about 27% of lots. The answer reports both, labelled by source. |
| `address` | `address-resolution-outcome` | output-of | The outcome is the result of resolving a typed address. |
| `address-resolution-outcome` | `candidate-street-name` | reported-with | Candidate street names are returned only when the outcome is ambiguous. |
| `related-lot` | `bin` | found-through | Related lots are the other lots that share the resolved BIN. |
| `related-lot` | `tax-lot` | same-subject-different-role | A related lot is another tax lot, reported next to the resolved one. |
| `in-graph` | `tax-lot` | same-subject-different-role | In graph says whether the resolved lot is one the graph holds. |
| `registration-id` | `registration` | identifier-of | The id identifies the registration, not the building it covers. Users quote the id from a notice. |
| `hpd-registered` | `registration` | summary-of | The lot flag says some HPD registration exists on the lot. The registrations themselves are reached from the building, which the schema does not connect to the lot flag. |
| `last-registered-date` | `registration-end-date` | contrasts-with | Users read "registered" as "valid until". One is when HPD last received the filing; the other is when the period ends. The answer gives both and does not call the registration current. |
| `recorded-date` | `document-date` | contrasts-with | Users read "most recent" as the date on the document. The rule is the recorded date; the document date is often absent. The answer gives both. |
| `document-id` | `deed` | identifier-of | The id identifies the document, not a lot or a party. Users quote it from ACRIS. |
| `grantee` | `owner-contact` | contrasts-with | A deed party and an HPD contact are different roles. The comparison between them is made at answer time, so the schema holds no link; a name match is a lead, not a finding. |
| `grantee-name` | `name-agreement` | input-to | The agreement is computed from the names; it is not stored, so the schema cannot lead a reader to it. |
| `owner-name` | `name-agreement` | input-to | The other name compared. Same reason. |
| `mailing-address` | `address-agreement` | input-to | The street line is compared; the result is not stored. |
| `zip-code` | `address-agreement` | input-to | The first five digits are compared. Same reason. |
| `address-line-two` | `address-agreement` | reported-with | Reported next to the address agreement but never compared. |
| `name-agreement` | `comparison-rule` | reported-with | The rule (N1 or N2) is always stated with the result. |
| `address-agreement` | `comparison-rule` | reported-with | The rule (A1) is always stated with the result. |
| `name-agreement` | `address-agreement` | contrasts-with | Two separate fields. A name match does not imply an address match, nor the reverse; neither says the parties are the same. |
| `mailing-address` | `address` | contrasts-with | A party's mailing address is not the address of the property. |
| `role-contact` | `owner-contact` | contrasts-with | Both are HPD contacts on a registration, kept apart by type. Q2 reports owners, Q4 everyone else; the answer never merges them. |
| `agent` | `owner-contact` | contrasts-with | A managing agent is a management relationship, not ownership. Users ask "who is the owner" and get the agent. |
| `head-officer` | `contact-title` | contrasts-with | The role is the HPD type; the title is free text beside it. A title such as PRESIDENT never changes or sets the role. |
| `corporation-name` | `owner-name` | same-subject-different-role | The same entity can be the owner and the agent (anchor C). Reported once per role as recorded; a match is a lead, not a merge. |
| `dos-entity` | `dos-id` | identifier-of | The id identifies the filing, not a person. Users quote it from a DOS lookup. |
| `dos-entity` | `owner-contact` | contrasts-with | A DOS entity and an HPD owner contact are different records. The name match is made at answer time, so the schema holds no link; a match is a lead, not a finding. |
| `dos-entity-name` | `owner-name` | found-through | A DOS record is found by an owner's name. The comparison is computed, so the schema cannot lead a reader from one to the other. |
| `dos-entity-name` | `grantee-name` | found-through | The same, from a deed grantee's name. |
| `dos-entity-name` | `name-agreement` | input-to | The agreement is computed from the two names and not stored. |
| `dos-entity-name` | `comparison-rule` | reported-with | The rule (N1, N2 or N3) is always stated with the match. |
| `dos-process-address` | `process-address-entity-count` | summary-of | The count summarizes how many active DOS entities list the address, so a shared process address is read with its hub size. |
| `dos-process-name` | `dos-process-address` | reported-with | The name and address where the state forwards papers are reported together. |
| `registered-agent-name` | `registered-agent-address` | reported-with | The agent's name and address are reported together, when listed. |
| `dos-process-name` | `registered-agent-name` | contrasts-with | Two different recorded roles on one record. A process name is where service goes; an agent is a listed party. Neither runs the entity. |
| `registered-agent-name` | `agent` | contrasts-with | A DOS registered agent is not an HPD managing agent. Users say "agent" for both. |
| `abbreviation-match` | `normalization-match` | contrasts-with | A spelling normalization needs no table; an abbreviation expansion needs a named one (AB1). The answer keeps them apart. |
| `abbreviation-match` | `comparison-rule` | output-of | The match carries rule AB1. |
| `differs-by-numeral-or-word` | `normalization-match` | contrasts-with | Holdings and Holdings II look alike but are not a match; no spelling rule makes them one. |

| `landlord` | `operational-network` | found-through | A reader moves from landlord records to the network they sit in. The schema joins them only through lots (`COVERS`, `IN_NETWORK`). |
| `landlord` | `owner-contact` | contrasts-with | A landlord record is built from owner contacts but is not one, and is not an owner. |
| `operational-network` | `related-lot` | contrasts-with | Related lots share a BIN (Q1); network members connect through registration infrastructure (Q8). Different relations, kept apart. |
| `connected-by-name` | `connected-by-address` | contrasts-with | Two network link kinds with different evidence: a fuzzy name match and a shared business address. Each carries its own weight; the answer never merges them. |
| `connected-by-name` | `connected-by-identity` | contrasts-with | A name match is a lead; an identity link says two records are one party. Different strength, reported apart. |
| `connected-by-address` | `connected-by-identity` | contrasts-with | A shared address is a lead; an identity link says two records are one party. Reported apart. |
| `connected-by-deed` | `connected-by-identity` | contrasts-with | Both build the owner portfolio. A deed link shows buildings conveyed together; an identity link shows one party. Each cites its own evidence. |
| `connected-by-identity` | `ownership-signal` | found-through | A reader asks why two landlords are linked; the stage of the identity link is one of the signal values. |
| `connected-by-deed` | `ownership-signal` | found-through | Same reader, deed side: the stage is a deed signal value. |
| `mortgage` | `satisfaction` | acts-on | A satisfaction is filed about a mortgage, but the record does not say which. No satisfaction is not proof a loan is outstanding. |
| `mortgage` | `agreement` | acts-on | An agreement can be recorded the same day as a mortgage and may consolidate earlier loans; the record does not say so. |
| `assignment` | `termination` | acts-on | A termination (TL&R) ends an assignment of leases and rents (AL&R), not a loan. |
| `satisfaction` | `termination` | contrasts-with | Users read both as "the loan ended". A satisfaction concerns a mortgage and a termination an assignment of leases and rents; neither is proof of payment. |
| `has-deed` | `has-financing-document` | contrasts-with | Two lot-to-document links. A deed document says who took title, a financing document says who lent; the answer lists them apart. |
| `evidence-type` | `evidence-id` | same-subject-different-role | The kind of release record and its id, read together; the id means nothing without the kind. |
| `masked-address-edges` | `network-masked-address` | found-through | A reader asks how much a mask hid; the count sits on the masked address, the edges are not stored. |
| `landlord` | `landlord-name` | reported-with | The answer names a landlord record by its name; the schema holds the name on the record. |
| `landlord` | `business-address` | reported-with | The answer gives the business addresses filed for a landlord record next to its name. |
| `landlord` | `anchor-landlord` | same-subject-different-role | The anchor is one landlord record, singled out as the name a group is shown under. |
| `landlord-name` | `owner-name` | contrasts-with | An HPD owner contact's name and a landlord record's name are different roles. The landlord's name is Who Owns What's, not a registrant's, and the two are never merged. |
| `business-address` | `mailing-address` | contrasts-with | Both are addresses HPD contacts file. The mailing address belongs to one owner contact on one registration; the business address is the landlord record's, over its lots. Reported apart. |
| `anchor-landlord` | `owner-portfolio` | found-through | A reader asks what a portfolio is called; the answer is its anchor's name. |
| `anchor-landlord` | `operational-network` | found-through | Same, for a network. |
| `network-absence` | `in-network` | contrasts-with | The reason a lot is in no network answers the opposite of membership; a reader moves from one to the other. |
| `network-absence` | `network-absence-detail` | same-subject-different-role | The same reason at two levels; the answer gives both. |
| `owner-portfolio` | `operational-network` | contrasts-with | Two groupings of the same landlord records by different evidence; a lot can be in both. Q9.4 compares them and the answer never mixes them. |
| `owner-portfolio` | `landlord` | found-through | A reader moves from landlord records to the portfolio they sit in. The schema joins them only through lots (`COVERS`, `IN_PORTFOLIO`). |
| `owner-portfolio` | `related-lot` | contrasts-with | Related lots share a BIN (Q1); portfolio members share ownership signals (Q9). Different relations, kept apart. |
| `portfolio-absence` | `in-portfolio` | contrasts-with | The reason a lot is in no portfolio answers the opposite of membership. |
| `portfolio-absence` | `network-absence` | contrasts-with | The same lot can be absent from one layer and present in the other, for different reasons; the reasons are never merged. |
| `portfolio-absence` | `portfolio-absence-detail` | same-subject-different-role | The same reason at two levels; the answer gives both. |
| `portfolio-absence-detail` | `network-absence-detail` | contrasts-with | One shared scheme, different layers: each layer uses its own subset of codes. |
| `portfolio-masked-address` | `network-masked-address` | contrasts-with | Two methods' masks of an address, each its own decision and degree: the network mask leaves address links out, the portfolio mask gives identity address evidence no weight. The degrees differ for 28 of the 30 texts both masked. Reported apart; an address can be in either, both or neither. |
| `portfolio-masked-address` | `mail-drop-address` | contrasts-with | A method's mask and a project's curated list, different authorities. Reported apart. |
| `portfolio-masked-address` | `mailing-address` | found-through | A reader starts from the street line an HPD contact records and looks for a mask on that text. The schema joins them only by text (street line plus second line, ZIP ignored). |
| `network-masked-address` | `mail-drop-address` | contrasts-with | Two classifications of an address by different authorities: a method's mask in one run, and a curated, unreviewed project list. Reported apart; an address can be in one, both or neither. |
| `network-masked-address` | `mailing-address` | found-through | A reader starts from the street line an HPD contact records and looks for a mask on that text. The schema joins them only by text (street line plus second line, ZIP ignored). |
| `mail-drop-address` | `mailing-address` | found-through | A reader starts from an HPD contact's street line and looks for it on the list. The schema joins them only by text, and the list's spelling differs from HPD's. |
| `network-masked-address` | `aggregator-address-masked` | source-of | A masked address is why a lot can carry the absence reason aggregator address masked; a reader moves from the reason to the addresses behind it. |
| `ownership-affiliation` | `shareholder` | source-of | A reader moves from a recorded shareholder to the ownership-type item it supports. The shareholder's share is unstated and it is not a parent company. |
| `ownership-affiliation` | `owner-portfolio` | source-of | An Owner Portfolio is the derived origin of a hypothesized ownership lead about an entity's lots; the answer labels it hypothesized and never a legal finding. |
| `ownership-affiliation` | `parent-affiliation` | contrasts-with | Only a documented parent may be called one; an owner or shareholder record is ownership, not parenthood. |
| `management-affiliation` | `agent` | source-of | The disclosed managing agent role is what makes a management item; it is not ownership. |
| `management-affiliation` | `site-manager` | source-of | The site manager role is what makes a management item; it is not ownership. |
| `management-affiliation` | `ownership-affiliation` | contrasts-with | Shared management does not establish shared ownership. |
| `financing-affiliation` | `mortgage` | source-of | The recorded mortgage is the document behind a financing item. |
| `financing-affiliation` | `parent-affiliation` | contrasts-with | A lender is a financing relationship, not control or parenthood. |
| `other-affiliation` | `operational-network` | source-of | An Operational Network is the derived origin of an `other` lead: an infrastructure connection, not ownership. |
| `mortgage` | `document` | same-subject-different-role | A mortgage is a document of current type MTGE; the answer reads it with the document's date and amount but as financing evidence. |
| `mortgage` | `borrower` | same-subject-different-role | Borrower is the role a party plays on a mortgage (party type 1). |
| `mortgage` | `lender` | same-subject-different-role | Lender is the role a party plays on a mortgage (party type 2). |
| `borrower` | `lender` | contrasts-with | Opposite roles on one mortgage; several borrowers are a shared-borrower record, not a lender relationship. |
| `documented` | `hypothesized` | contrasts-with | A recorded assertion versus a derived lead; the answer never presents a lead as recorded. |
| `documented` | `reported` | contrasts-with | A reported claim is shown as reported, not as documented. |
| `hypothesized` | `reported` | contrasts-with | A method's conclusion versus a publication's statement; neither is verified. |
| `grantee` | `grantor` | contrasts-with | Opposite roles on one deed (ACRIS party types 2 and 1); the same name can be both on one deed, reported as recorded and not a sale. |
| `grantee-name` | `grantor-name` | contrasts-with | The name on each side of a deed; both are looked up by name key and never merged into one party. |
| `document-amount` | `not-a-sale` | input-to | The recorded amount (0 is common) is one of the two inputs to the not-a-sale flag; the other is the document type. 0 is never read as a gift. |
| `deed` | `not-a-sale` | summary-of | The flag and its count summarize deeds without a recorded amount or of a correction or confirmatory type; computed, not stored. |
| `deed` | `attributable-transfer` | summary-of | The flag marks a deed whose grantee or grantor name matches a registered owner; computed, not stored. |
| `corporate-owner` | `attributable-transfer` | input-to | The HPD corporate-owner name key is compared with the deed party name keys at answer time (rule N3); a lead, never a finding of the same party. |
| `supporting-deed` | `deed` | output-of | The supporting deed is the deed picked by date and basis at answer time; the schema holds only the Deed. |
| `supporting-deed` | `date-basis` | input-to | The basis (document or recorded date) decides which deeds support a date. |
| `date-basis` | `document-date` | input-to | The `document` basis reads the document date, else the recorded date. |
| `date-basis` | `recorded-date` | input-to | The `recorded` basis reads the recorded date; it shows what public record showed. |
| `registration-in-force` | `registration` | output-of | The status is computed for a registration at answer time; the schema holds only the registration. |
| `registration-in-force` | `last-registered-date` | input-to | A registration filed after the date is registered-later, not in force. |
| `registration-in-force` | `registration-end-date` | input-to | An end date before the date makes a registration ended. |
| `supporting-deed` | `title-registration-relation` | input-to | The grantees of the supporting deeds are one side of the comparison. |
| `registration-in-force` | `title-registration-relation` | input-to | The corporate owners of the registrations in force are the other side. |
| `attributable-transfer` | `title-registration-relation` | contrasts-with | Both are name leads between a deed and an HPD owner; one is a transfer flag on a deed, the other a comparison on a date. Neither is a finding of the same party. |
| `open-violation-rate` | `violation` | input-to | The count of the building's open violations is the numerator; computed at answer time, not stored. |
| `open-violation-rate` | `violation-status` | input-to | Only violations with status Open at the snapshot count toward the rate. |
| `open-violation-rate` | `residential-units` | input-to | The lot's PLUTO unit count is the denominator; 0 or missing gives rate unavailable. |
| `retrieved-item` | `affiliation` | source-of | A retrieved report or filing is where a reported or documented affiliation lead comes from; the answer labels it reported and never a finding of control. |
| `reported-claim` | `reported` | same-subject-different-role | The claim is the quoted statement; `reported` is the evidence status the answer gives it. |
| `reported-claim` | `owner-portfolio` | contrasts-with | A publication's claim about ownership or a parent is kept apart from the derived Owner Portfolio; neither supports the other. |
| `extraction-method` | `match-basis` | input-to | A value read from a scan with low confidence makes the match basis lead only, never a link. |
| `conflicts` | `contested` | contrasts-with | Conflicts compares an item with a recorded fact; contested says two items disagree with each other. Reported apart; neither is resolved. |
| `item-unreviewed` | `unreviewed` | contrasts-with | Starting status of a retrieved item (Q16) versus the review status of a mail-drop list entry (Q6): different schemes, same word. |
| `missing-registration` | `hpd-registered` | input-to | The lot flag (no row in the registration data) is what the condition reads. |
| `missing-registration` | `no-usable-registration` | contrasts-with | No row at all versus rows with only a placeholder id or BIN; the second is registered in the data, so lapsed and older-than-deed are cannot-tell. |
| `no-usable-registration` | `hpd-registered` | input-to | The flag is true; the absence of a usable registration under it is what sets this one. |
| `lapsed-registration` | `registration-end-date` | input-to | Every registration's end date against the as-of date decides it. |
| `lapsed-registration` | `registration-in-force` | contrasts-with | Lapsed is lot-wide at the snapshot date; in force is one registration on a violation date (Q14). Different dates and scope. |
| `lapsed-registration` | `registration-older-than-deed` | contrasts-with | Look-alike stale conditions: one reads the end date, the other the last registration date against a deed. Reported apart, never merged. |
| `registration-older-than-deed` | `last-registered-date` | input-to | The lot's latest last-registered date is one side of the comparison. |
| `registration-older-than-deed` | `recorded-date` | input-to | The latest deed's recorded date is the other side. |
| `registration-older-than-deed` | `not-a-sale` | reported-with | A $0, correction or confirmatory deed is listed with its flag so the comparison is not read as a sale. |
| `unit-threshold` | `residential-units` | input-to | PLUTO's lot-wide unit count is compared with the threshold of 3. |
| `deed-classification` | `deed` | summary-of | The class reads a deed's type and amount. |
| `deed-classification` | `document-amount` | input-to | The recorded amount (0 or above) decides zero-transfer or priced. |
| `deed-classification` | `not-a-sale` | contrasts-with | Not-a-sale is the Q12 flag (amount 0 or a correction); the classification keeps correction, zero-transfer and priced apart. |
| `deed-classification` | `zero-transfer` | summary-of | Zero-transfer is one of the three classes. |
| `zero-transfer` | `not-a-sale` | summary-of | A zero-transfer deed carries the not-a-sale flag. |
| `zero-transfer` | `restructuring-signal` | input-to | Signals are looked for on zero-transfer deeds only. |
| `restructuring-signal` | `attributable-transfer` | contrasts-with | Attributable-transfer matches a deed party to the current registered owner; the signal that does so is one of four and never a finding. |
| `restructuring-signal` | `comparison-rule` | input-to | Every signal compares names by rule N3. |
| `restructuring-signal` | `owner-portfolio` | contrasts-with | The portfolio only chooses the lots; no signal reads its membership, so the grouping is never its own evidence. Reported apart. |
| `louvain-community` | `pre-subdivision-connectivity` | contrasts-with | A Louvain community is membership after the cut; connectivity before subdivision ignores the cut. A pair can be connected and still lie in different communities. |
| `ownership-signal` | `stage-precision` | summary-of | Precision is reported per linkage stage (each signal is a stage code); it summarizes the release's evaluation of that stage and is never a property of one link. |
| `pair-layer-state` | `representative-path` | input-to | A path is shown only when the pair state is same group. |
| `pair-layer-state` | `pre-subdivision-connectivity` | contrasts-with | Connectivity before the cut is not membership: a pair can be connected and still in different networks. |
| `representative-path` | `stage-precision` | contrasts-with | Each link names its stage; the stage's precision is a method property, never the probability that this link is right. |
| `dossier` | `stop-reason` | reported-with | A dossier always reports exactly one stop reason; the answer is incomplete without it. |
| `dossier` | `lead` | reported-with | A dossier lists each lead followed or logged, with the reason it was not followed. |
| `dossier` | `retrieved-item` | reported-with | Retrieved items are the dossier's fifth section; they stay session evidence, labeled and never merged into recorded facts. |
| `lead` | `stop-reason` | reported-with | A lead not followed or not resolved carries one value of the same scheme. |
| `lead` | `lead-only` | contrasts-with | A lead is a name or address that passes the lead rule; lead-only is a match basis of a retrieved item that never joins recorded facts. |
| `lead` | `hypothesized` | same-subject-different-role | A hypothesis is a lead, never a finding: the lead is the thing to follow, hypothesized is the evidence status it carries. |
| `reached-service-address` | `dos-process-address` | source-of | A DOS process address is one of the addresses at which a trail stops; it links nothing on its own. |
| `lot-violation-ranking` | `open-violation-rate` | reported-with | Each ranked row reports its rate beside the open count by class; a lot with no units shows rate unavailable and ranks last. |
| `lot-violation-ranking` | `operational-network` | input-to | The chosen layer decides which lots are ranked; the list is a lead within a derived group, not a finding about owners. |
| `lot-violation-ranking` | `owner-portfolio` | input-to | Same, for the portfolio's rental lots; the ranking changes with the layer. |
| `violation-concentration` | `lot-violation-ranking` | reported-with | The share is stated with the ranked list it summarizes, the member count and the number of top lots. |
| `violation-concentration` | `violation` | summary-of | A share of recorded open violations at the snapshot date, never a measure of conditions. |
| `source-absence` | `network-absence` | summary-of | The layer rows of a source absence carry the network reason; absence is not a finding that the lot has no common operator. |
| `source-absence` | `portfolio-absence` | summary-of | Same, for the portfolio; the two layers can give different reasons for one lot. |
| `source-absence` | `violation` | reported-with | No violation for a registered lot means none in the snapshot, never good conditions; an unregistered lot is not loaded, not none. |
| `agent-footprint` | `agent` | summary-of | The footprint summarizes the registrations, buildings and lots that disclose one agent name. The agent role is management, never ownership. |
| `agent-footprint` | `operational-network` | input-to | The reference building's network is compared with the footprint lots at answer time; the network is a derived lead, not a finding of common ownership. |
| `agent-footprint` | `owner-portfolio` | input-to | The reference building's portfolio is compared with the footprint lots at answer time; rental lots only, a derived lead. |
| `agent-footprint` | `network-masked-address` | reported-with | The agent's business addresses are reported with the Operational Network masks. A mask is a method's decision, not a finding about the address. |
| `agent-footprint` | `portfolio-masked-address` | reported-with | The same addresses are reported with the Owner Portfolio masks, whose degrees can differ from the network's. |
| `name-search` | `lead` | output-of | A name search returns person rows and near names as leads to verify; a lead here is a name found in the records, never a finding. |
| `name-search` | `name-agreement` | reported-with | Each match states its basis (exact or normalized) from the name comparison rules; the answer is incomplete without it. |
| `name-search` | `comparison-rule` | reported-with | The answer states the rule used (N3 for an entity, uppercase for a person) with the key. |
| `name-search` | `legal-suffix-only` | reported-with | A name search lists near names with their kind; this is the kind found when only a legal-form word differs. |
| `legal-suffix-only` | `different` | contrasts-with | Q3 and Q22 call such names different; a name search reports them as a lead because the core words agree. |
| `legal-suffix-only` | `normalization-match` | contrasts-with | A normalization match is the same name after a stated rule; a legal-form word added or removed is not one of those rules, so it is a lead only. |
| `registry-search` | `retrieved-item` | output-of | A registry search returns the retrieved item (record or status) that the answer lists. |
| `registry-search` | `jurisdiction` | input-to | The recorded jurisdiction decides which registry is searched. |
| `registry-search` | `registry-outcome` | reported-with | Every search is reported with its outcome. |
| `registry-status-only` | `needs-payment` | reported-with | A status-only result ends in the stop reason needs payment. |
| `registry-unreachable` | `service-unavailable` | contrasts-with | Both are outages that are never an answer about the data; one is a registry, the other the address service. |

| `complaint-problem` | `violation` | contrasts-with | A problem is what a tenant reported; a violation is what an inspector cited. Counted apart, never merged; a problem is not evidence of a violation or the reverse. |
| `pest-complaint` | `complaint-problem` | output-of | The pest complaints are the complaint problems whose minor category is PESTS; a filter over the other concept, computed at answer time. Reached by link, not by hierarchy (stage 3). |
| `pest-complaint` | `minor-category` | input-to | The minor category PESTS is the stored value that marks a problem as a pest complaint. |
| `pest-complaint` | `problem-code` | input-to | The problem code names the pest (MICE, ROACHES, BED BUGS and so on); OTHER is a catch-all and never means mice. |
| `pest-complaint` | `pest-violation` | contrasts-with | A pest complaint is what a tenant reported; a pest violation is what an inspector cited under a pest order. Counted apart, never merged; neither is evidence of the other. |
| `major-category` | `minor-category` | reported-with | HPD's minor category sits within a major category and is read with it: a minor category can sit under two majors (CABINET, RADIATOR). |
| `minor-category` | `problem-code` | reported-with | A problem code is read with its minor category: OTHER appears under many minor categories, so it means nothing alone. |
| `complaint-problem` | `pest-violation` | contrasts-with | A pest complaint problem is what a tenant reported; a pest violation is what an inspector cited under a pest order. Counted apart, never merged; a complaint is not evidence of a violation, and no violation is not evidence of no pests. |
| `complaint-problem` | `complaint-rate` | input-to | The period's problem count is the numerator; computed at answer time, not stored. |
| `complaint-rate` | `residential-units` | input-to | The lot's PLUTO unit count is the denominator; 0 or missing gives rate unavailable. |
| `complaint-rate` | `open-violation-rate` | contrasts-with | Look-alike per-unit rates with different numerators (reported problems over a period versus open citations at the snapshot); never compared as one measure. |
| `order-number` | `pest-violation` | input-to | The order number is the stored value filtered at answer time against the pest list to produce the pest violations and their kind. The kind is not stored. |
| `pest-violation` | `violation` | output-of | The pest violations are the violations whose order number is on the pest list; a filter over the other concept, computed at answer time. Reached by link, not by hierarchy (stage 3). |
| `litigation-case` | `violation` | contrasts-with | A case is an action HPD brought in Housing Court; a violation is what an inspector cited. Counted apart; a case is not evidence of a violation, nor the reverse. |
| `harassment-finding` | `case-type` | contrasts-with | A case type such as 'Tenant Action/Harrassment' names the kind of action, not its outcome. Only the finding says harassment was found; the answer never reads one from the other. |
| `harassment-finding` | `finding-date` | reported-with | The date exists only with a finding and is reported together with it; a finding with no date is reported with the date absent. |
| `respondent` | `respondent-owner-match` | input-to | The respondent's name keys are what is compared with the owner names to produce the match. |
| `respondent` | `contact` | contrasts-with | A respondent is a name HPD recorded in a case, role unrecorded; a contact is a party on a registration. The same string is a lead, not the same party. |
| `respondent-owner-match` | `contact` | input-to | The registered owner contacts' names are the other side of the comparison. |

## Labels

Reviewed 2026-11-12 across the whole vocabulary: no label (preferred, alternative or hidden) is shared by two concepts.

- `number of buildings` was removed as an alternative label of `pluto-building-count`. It would send "number of buildings" to PLUTO's count alone, but an answer must give both counts (PLUTO's and HPD's list).
- `assessed value` stays an alternative label of `assessed-total-value` because Q1.4 uses that wording. PLUTO also holds a land-only assessed value. If a question adds it, qualify this label.
- `lot` (of `tax-lot`) can also mean a vacant lot in everyday use. The definition and scope note settle it; kept.
- `parcel`, `structure`, `unit count`, `building class code`, `borough-block-lot` and `building identification number` are plain synonyms; kept.
- Hidden labels hold source column spellings, so a schema or query that says them finds the concept without displaying them: `numbldgs`, `unitsres`, `yearbuilt`, `bldgclass`, `assesstot`.

### Q2 label review (2026-11-12)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).

- `registered owner` and `owner of record` are alternative labels of `owner-contact`, the wording the question uses. The definition says it is a contact HPD records, not proof of title.
- Bare `owner` is deliberately not a label of any concept. It would send users to the HPD contact when they may mean the deed grantee or an Owner Portfolio.
- `registration` is an alternative label of `registration` (HPD registration). It can also mean a rent registration or a business registration; the preferred label carries "HPD".
- Hidden labels hold the source spellings: `registrationid`, `lastregistrationdate`, `registrationenddate`, and the stored contact types `CorporateOwner`, `IndividualOwner`, `JointOwner`.

### Q3 label review (2026-11-12)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).

- `buyer` moved from alternative to hidden label of `grantee`. Users say it, but a $0 deed is not a sale; it should find the concept without being displayed.
- `price` and `sale price` are deliberately not labels of `document-amount`; the amount is not a price. `deed date` is not a label of `document-date` or `recorded-date`; users may mean either.
- `unit` (of `address-line-two`) is near `unit count` (of `residential-units`). The definitions settle it; kept.
- `name` is a hidden label of `grantee-name` only (the source column). Bare `owner` stays unassigned, as in Q2.
- The definition of `document-type` listed the codes with commas, which read as extra codes ("DEED, TS"). Rewritten with semicolons.
- Hidden labels hold source spellings: `documentid`, `doctype`, `docdate`, `recordedfiled`, `docamount`, `address1`, `address2`, `businessstreetname`, `businessapartment`, `businesszip`.

### Q4 label review (2026-11-12)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).

- `managing agent` is the preferred label of `agent`; the bare HPD spelling `Agent` is hidden. Bare `agent` is not a preferred label, since it also means the software agent.
- `title` is a hidden label of `contact-title` only. It is not a label of the role concepts; a title never sets the role.
- `officer` (concept) and `head officer` stay separate. The definitions and scope notes settle it; kept.
- `lessee` is not a tenant of an apartment (scope note); `tenant` is deliberately not a label.
- `manager` and `property manager` are deliberately not labels: they would send users to `agent` or `site-manager` by guess. The two are different HPD roles.
- Hidden labels hold the stored types (`Agent`, `HeadOfficer`, `Officer`, `Shareholder`, `SiteManager`, `Lessee`) and `corporationname`.

### Q5 label review (2026-11-13)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).
- `registered agent name` is not given the alternative label `agent`: bare `agent` already means the HPD managing agent. The link to `agent` (contrasts-with) carries the connection.
- `process agent` and `service address` are not labels: the first suggests the registered agent and the second the managing agent's or owner's mailing address. `DOS process name` and `DOS process address` stay distinct.
- No hidden labels added: the DOS source column names are not wording users or other sources use.

### Q8 label review (2026-11-13)

No label (preferred, alternative or hidden) is shared by two concepts (`make thesaurus` checks this).

- `network` is an alternative label of `operational-network`, with `Operational Network`, the wording the question uses. The definition says what it groups and that it is a lead.
- `ownership network`, `portfolio` and `owner group` are deliberately not labels of `operational-network`: they suggest common ownership, which the network does not show, and `portfolio` is the Owner Portfolio layer (Q9).
- `landlord record` is an alternative label of `landlord`. `owner` and `beneficial owner` are deliberately not labels: a landlord record is not proof of ownership. Revisit when the user's idea of using Beneficial Owner for the shared meaning is taken up.
- Hidden labels hold source spellings, so a schema or query that says them finds the concept without displaying them: `group_id`, `split`, `node_id`, `edge_id`, `name_weight`, `address_weight`, `identity_weight`, `crosses_networks`, `top_level_reason`, `reason_code`, and the graph property names (`groupId`, `nodeId`, `edgeId`, `nameWeight`, `addressWeight`, `identityWeight`, `crossesNetworks`, `networkAbsence`, `networkAbsenceDetail`). The bare source column `weight` is not a label: too generic.
- BOR's reason and split codes (`wcc`, `louvain`, `no_linkage` and the rest) are hidden labels of their concepts, which is how `check_profiles.py` matches the stored value to the scheme.
- `no linkage` (detail) and `no qualifying linkage` (top level) are close; the definitions and the hierarchy settle it.

### Q9 label review (2026-11-13)

No label is shared by two concepts (`make thesaurus` checks this).

- `owner portfolio` keeps `Owner Portfolio` and `apparent owner footprint` as alternative labels. Plain `portfolio` is still not a label of `operational-network`, and it is not added here either: a bare "portfolio" is wording a user may use for either layer, so the agent must ask or name both.
- `owner`, `owns` and `beneficial owner` are deliberately not labels of `owner-portfolio` or `landlord`: a portfolio is an attribution from signals, not proof of ownership.
- Hidden labels hold source spellings and graph names: `composition`, `signal`, `portfolioGroupId`, `portfolioAbsence`, `portfolioAbsenceDetail`, and BOR's codes for compositions, signals (with their dots, for example `identity.splink_base`) and the new absence reasons.
- `identity` (BOR's composition code) is a hidden label of `identity-based`, not an alternative label: the word is too generic.

### Q6 label review (2026-11-13)

No label is shared by two concepts (`make thesaurus` checks this).

- `network masked address` keeps `aggregator address` and `masked address` as alternative labels: the wording the question uses. They name the method's decision, never a finding about the address. `aggregator address masked` (the lot-level absence reason) stays a separate concept with its own label.
- `mail-drop address` keeps `mail drop address`, `registered-agent address` and `service address` as alternative labels. `service address` is also the wording the project guidance uses for masked leads, so the definitions say the two classifications are reported apart.
- `business address` is already an alternative label of `mailing-address`; it is not added to the Q6 concepts, so a user's "business address" finds the contact's address and not a classification.
- Hidden labels hold source spellings and graph names: `address_id`, `addressId`, `degree`, `address_key`, `zip5`, `kind`, `basis`, `review_status`, `reviewStatus`, and the list's four kind codes and `unreviewed`. The bare word `address` is not a hidden label of `masked-address-text`: it is the preferred label of the Q1 concept `address`.

### Q11 label review (2026-11-16)

`ownership`, `management` and `financing` are the preferred labels of the three affiliation types; no other concept carries them as a label, so none is shared. `parent company` and `other affiliation` are qualified so they are not confused with `parent` or `other` used loosely. `mortgage` carries the alternative label `MTGE` (the ACRIS code); no other concept uses it. `documented`, `hypothesized` and `reported` are plain words used as evidence statuses only; none is an alternative label elsewhere. Hidden labels were not needed: the HPD role words are already hidden labels on the contact types. `make thesaurus` checks that no label is shared.

### Q12 label review (2026-11-17)

`grantor` (alt `party giving title`; hidden `partytype 1`, `seller`) and the Q3 `grantee` (hidden `partytype 2`, `buyer`) are a matched pair; no label is shared with another concept. `seller` and `buyer` are hidden so user wording finds the role but is not displayed, since a not-a-sale deed has no seller or buyer in the usual sense. `not a sale` carries `deed without consideration` as an alternative label; no other concept uses it.

### Q13 label review (2026-11-17)

Preferred labels `assignment`, `satisfaction`, `termination` and `agreement` are plain words used for these five document kinds only; no other concept carries them as a label (`make thesaurus` checks). Document codes are alternative labels (`MTGE`, `ASST`, `AL&R`, `SAT`, `TL&R`, `AGMT`, `SAGE`). Hidden labels carry user and ACRIS wording so it finds the concept without displaying: `loan` (mortgage), `loan document` (financing document), `assignment of mortgage`, `assignment of leases and rents`, `satisfaction of mortgage`, `termination of assignment of leases and rents`. "Paid off", "release" and "discharge" were left out on purpose: they state an outcome the records do not prove.

Links dropped in stage 4: `financing-document` to `document` and to `has-financing-document` (the schema declares both: a Document node reached by `HAS_FINANCING_DOCUMENT`), and `assignment` to `satisfaction` (siblings with no move a reader needs).

### Q15 label review (2026-11-18)

Hidden labels carry source and user wording without displaying it: `hazard class` (violation class), `violationstatus` (violation status), `inspectiondate` (inspection date), `violations per residential unit` (open violation rate). Each is used once; no shared labels. `class` was already an alternative label of `violation-class` only.

Links dropped in stage 4 (the schema declares them): `violation` to `building` and to `has-violation`, `has-violation` to `has-building`, and `violation-class`, `violation-status`, `inspection-date` to `violation` (properties of the Violation node).

### Q16 label review (2026-11-18)

The hidden label `unreviewed` on `item-unreviewed` was shared with the Q6 list status `unreviewed`; replaced by `not yet reviewed`. Hidden labels added so user and source wording finds the concept without displaying: `news claim`, `article claim` (reported claim); `OCR`, `scanned text` (extraction method); `similar name` (lead only). `confirmed`, `refuted`, `inconclusive`, `contested`, `agrees`, `adds`, `conflicts`, `unrelated` are plain words used as values of one scheme each; no other concept carries them.

Links dropped in stage 4 (the answer contract in `profiles/q16.yaml` declares them): `retrieved-item` to `reported-claim`, `extraction-method`, `source-category`, `review-status`, `fact-relation` and `match-basis` (each is a field of the item).

### Q17 label review (2026-11-18)

Hidden labels for user wording, each checked against the whole vocabulary and used once: `not registered` (missing registration), `expired registration` (lapsed registration), `outdated registration` (registration older than the latest deed), `3+ units` and `three or more units` (unit threshold). `stale registration` stays an alternative label of `registration-older-than-deed` only. No shared labels.

### Q18 label review (2026-11-18)

Hidden labels for user wording, each checked against the whole vocabulary and used once: `nominal deed` (zero-transfer deed, beside `no-money deed` and `zero-dollar deed`), `LLC shuffle` and `re-deed into an LLC` (restructuring signal; the wording is a hint, the concept reports leads, not a verdict). `$0 deed` stays an alternative label of `zero-transfer`. No shared labels.

### Q19 label review (2026-11-19)

No hidden labels added. `connecting path` is an alternative label of `representative-path` and `connected in the original component` of `connectivity before subdivision`; neither is used elsewhere. No shared labels.

### Q20 label review (2026-11-19)

Hidden labels added: `investigation summary` (dossier), `where the trail stops` (stop-reason), `qualified lead` (lead). `landlord dossier` stays an alternative label of `dossier`. `lead` is not an alternative label of `lead-only` or `hypothesized`: a lead is not a match basis or an evidence status. `finding` and `hypothesis` are deliberately not labels of `lead`: a hypothesis is a lead, never a finding. `report` is not a label of `dossier` (it also means a published report, `retrieved-item`).

Q21 label review (2026-11-19): `worst lots in a layer` and `share held by the top lots` are alternative labels used by no other concept. "Hazardous" is deliberately not a label: it would suggest one combined class. Hidden labels not added.

Q22 label review (2026-11-19): `abbreviation-match` and `differs-by-numeral-or-word` carry one hidden label each ("abbreviation expansion", "numeral difference"); no shared labels with other concepts.

Q23 label review (2026-11-19): hidden labels `buildings managed by this agent` and `management company footprint` added to `agent-footprint`; no other concept carries them. `agent` gained the alternative label `property manager`, used by no other concept. "Operator" and "commercial service" are deliberately not labels: the answer never states that verdict.
Q26 label review (2026-11-19): `what an absence means` is an alternative label of `source-absence`, used by no other concept. Hidden labels `nothing found` and `no record` added (user wording; found by search, not displayed), used by no other concept. "Missing" is deliberately not a label: it suggests an error in the source. The five reasons keep their existing labels.

Q25 label review (2026-11-19): `registry-search` (alternative `other-state registry search`), `registry-outcome` and the four outcome values share no label with another concept. `registry-unreachable` is kept apart from `service-unavailable` by scheme and scope. Hidden label `foreign registry` added to `registry-search`.

Q24 label review (2026-11-19): `name-search` (alternative `starting from a name`, hidden `search by name`) and `legal-suffix-only` (hidden `differs by LLC or INC`) share no label with another concept. "Match" is deliberately not a label of `name-search`: its rows are leads.

### Q27 label review (2026-11-19)

Hidden labels carry source wording: `problemid`, `complaintid`, `majorcategory`, `problemstatus`, `receiveddate`, `problemduplicateflag`. Alternative labels: `HPD complaint problem` and `complaint` (complaint problem), `complaint type` (problem type), `open or closed problem` (problem status), `problems per unit` (complaint rate). Each is used once; no label is shared. The bare word `complaint` is kept on `complaint-problem` because users say it, and its scope note says the counting unit is the problem, not the complaint. `complaint-id` keeps the exact distinction.

### Q15 pest extension label review (2026-11-21)

`order number` has alternative label `order code` and hidden label `ordernumber` (the source column); `pest violation` has alternative label `infestation violation` and hidden label `mice violation`, so a reader who asks about mice finds it. The hidden label does not claim the concept is only mice: the definition and scope note say that only orders 569 and 869 name mice and that 566 and 866 are unspecified vermin. "Pest", "vermin", "mice" and "order" are not preferred or alternative labels of any other concept (`make thesaurus` checks shared labels). "Complaint about mice" belongs to `complaint-problem`, which has no pest field until the Q27 extension; it is not a label of `pest-violation`.

### Q27 pest extension label review (2026-11-21)

`minor category` has hidden label `minorcategory` and `problem code` has hidden label `problemcode` (the source columns); neither has an alternative label, because HPD's words are the ones users meet. `pest complaint` has alternative label `pest complaint problem` and hidden label `mice complaint`, so a reader who asks about mice finds it; the definition and scope note say only the code MICE names mice and OTHER never does. The wording "complaint about mice" is not a label of `pest-violation`, and "mice violation" stays with `pest-violation`; the two never share a label (`make thesaurus` checks shared labels). "Category", "code" and "pest" are not preferred or alternative labels of any other concept.

### Q28 label review (2026-11-20)

Alternative labels: `Housing Court case` and `HPD litigation` (litigation case), `litigation type` (case type), `date opened` (case open date), `litigation status` (case status), `open judgment` (open judgement), `finding of harassment` (harassment finding), `date of finding` (finding date), `penalty` (case penalty), `named respondent` (respondent). Hidden labels carry source spellings (`litigationid`, `casetype`, `caseopendate`, `casestatus`, `openjudgement`, `findingofharassment`, `findingdate`) and `litigation`. Each is used once; no label is shared with another concept. "Defendant" and "owner" are deliberately not labels of `respondent`: the source records neither role.

## Navigation pilot

Reviewed 2026-11-12 against Q1's worked examples. No gaps.

| Example | Route |
| --- | --- |
| Lot with three buildings (anchor D) | `tax-lot` to `building` through the schema's `has-building`; `building` to `bin` |
| PLUTO counts more buildings than HPD lists | `building` to `pluto-building-count` (contrasts-with) |
| Ambiguous address | `address` to `address-resolution-outcome` to `candidate-street-name` |
| Condominium or shared BIN | `bin` to `related-lot` to `tax-lot` |
| A lot outside the rental scope | `in-graph` to `tax-lot` |
| "What is the year built?" | `tax-lot` property `yearBuilt`, through the schema; no thesaurus link needed |

### Q2 navigation pilot (2026-11-12)

| Example | Route |
| --- | --- |
| Single registration (anchor A) | `building` to `registration` through `has-registration`; `registration` to `contact` through `has-contact` (both schema) |
| Co-op owner (anchor C) | `owner-contact` to `owner-name`, schema; spelling differs from PLUTO's, reported as recorded |
| Multi-building lot (anchor D) | `tax-lot` to `building` (Q1) to `registration`; the lot flag `hpd-registered` to `registration` (summary-of) |
| Registration ended before the snapshot | `last-registered-date` to `registration-end-date` (contrasts-with) |
| Quoted registration number | `registration-id` to `registration` (identifier-of) |
| No registration found | `hpd-registered` false; no route to a registration, by design |

No gaps.

### Q3 navigation pilot (2026-11-12)

| Example | Route |
| --- | --- |
| Exact agreement (anchor A) | `tax-lot` to `deed` through `has-deed` (schema); `deed` to `grantee` through `has-grantee` (schema); `grantee-name` and `owner-name` to `name-agreement` (input-to); `name-agreement` to `comparison-rule` (reported-with) |
| Latest deed is not a sale | `recorded-date` to `document-date` (contrasts-with); `document-amount` and `document-type` are properties of `deed` (schema) |
| Spelling difference (anchor G) | `grantee-name` to `name-agreement` to `different` (scheme); the rule is reached through `comparison-rule` |
| Two deeds the same day (anchor D) | `recorded-date` is a property of `deed` (schema); the tie rule is in its scope note |
| Deed party against HPD owner | `grantee` to `owner-contact` (contrasts-with) |
| Same address on both sides | `mailing-address` and `zip-code` to `address-agreement`; `address-line-two` reported with it |
| Quoted ACRIS document number | `document-id` to `deed` (identifier-of) |
| Property address against party address | `mailing-address` to `address` (contrasts-with) |

No gaps.

### Q4 navigation pilot (2026-11-12)

| Example | Route |
| --- | --- |
| Five contacts (anchor A) | `registration` to `contact` through `has-contact` (schema); `contact` to each type in `contact-types` and to `contact-title`, `corporation-name`, `person-name`, `mailing-address` (schema properties) |
| Agent is the owner (anchor C) | `corporation-name` to `owner-name` (same-subject-different-role); `agent` to `owner-contact` (contrasts-with) |
| Title read as role | `head-officer` to `contact-title` (contrasts-with) |
| Owner or agent? | `role-contact` to `owner-contact` (contrasts-with) |
| Shared business address | `mailing-address` to `address-agreement` (Q3); caveat in the scope note of `role-contact` |

No gaps.

### Q5 navigation pilot (2026-11-13)

| Example | Route |
| --- | --- |
| Entity is its own process agent (anchor A) | `dos-entity` to `dos-process-name` and `registered-agent-name` (schema properties); `dos-process-name` to `registered-agent-name` (contrasts-with) |
| Statutory default (`THE COMPANY`) | `dos-process-name` scope note; `dos-process-address` through `dos-process-name` (reported-with) |
| Person as process name (anchor G) | `dos-process-name` scope note: where service goes, not who runs it |
| Spelling (anchor C) | `owner-name` to `dos-entity-name` (found-through); `dos-entity-name` to `comparison-rule` and `name-agreement` |
| Abbreviation (anchor D) | `dos-entity-name` to `comparison-rule`; no match under N3, candidate only |
| Quoted DOS id | `dos-id` to `dos-entity` (identifier-of) |
| "Who is the agent?" | `registered-agent-name` to `agent` (contrasts-with) |

No gaps.

### Q8 navigation pilot (2026-11-13)

| Example | Route |
| --- | --- |
| Anchor C: the network of a lot (ON-98617) | `tax-lot` to `operational-network` (`in-network`, schema); `network-group-id` and `network-split` are its properties (schema) |
| Who is in the network | `landlord` to `operational-network` (found-through); `landlord` to `covers` to `tax-lot` (schema) |
| "Is a landlord the owner?" | `landlord` to `owner-contact` (contrasts-with) |
| "Are these lots related?" | `operational-network` to `related-lot` (contrasts-with): shared BIN is not network membership |
| Strength of a link (anchor C) | `connected-by-name`, `connected-by-address` or `connected-by-identity` to `link-weight` (schema) |
| ON-675, a Louvain community | `network-split` to `louvain-community` (scheme); `network-group-id` to `network-split` (schema; absent where a link crosses a boundary) |
| Anchors A and F: why in no network | `in-network` to `network-absence` (contrasts-with) to `network-absence-detail`; the values nest by hierarchy |

No gaps.

### Q9 navigation pilot (2026-11-13)

| Example | Route |
| --- | --- |
| Anchor: the portfolio of a lot (OP-98617) | `tax-lot` to `owner-portfolio` (`in-portfolio`, schema); `portfolio-group-id` and `portfolio-composition` are its properties (schema) |
| Who is in the portfolio | `landlord` to `owner-portfolio` (found-through); `landlord` to `covers` to `tax-lot` (schema) |
| "Are these lots related?" | `owner-portfolio` to `related-lot` (contrasts-with): shared BIN is not portfolio membership |
| Why two landlords are linked | `connected-by-identity` or `connected-by-deed` to `ownership-signal` (found-through) to the six signal values (scheme); the four link kinds contrast with one another |
| Portfolio versus network (Q9.4) | `owner-portfolio` to `operational-network` (contrasts-with) |
| Why a lot is in no portfolio | `in-portfolio` to `portfolio-absence` (contrasts-with) to `portfolio-absence-detail`; the values nest by hierarchy; `portfolio-absence` to `network-absence` for the other layer |
| A co-op lot in a published group | `coop-condo-excluded` under `excluded-by-policy` (hierarchy) |

No gaps.

### Q6 navigation pilot (2026-11-13)

| Example | Route |
| --- | --- |
| Anchors A and B: `746 61ST STREET` 11220 | `mailing-address` to `network-masked-address` (found-through; no mask) and to `mail-drop-address` (found-through; not listed); counts from `owner-contact`, `role-contact`, `registration`, `building` (schema) |
| `418 BROADWAY` 12207 | `mailing-address` to `mail-drop-address` (found-through) to `mail-drop-kind` (schema) to `listed-registered-agent` (scheme) |
| A masked address (`455 PARK AVENUE`) | `network-masked-address` to `masked-address-degree` and `masked-address-text` (schema); to `mailing-address` and `zip-five` for the HPD ZIPs |
| "Is it masked or listed?" | `network-masked-address` to `mail-drop-address` (contrasts-with): never merged |
| Why a lot's evidence was masked | `aggregator-address-masked` to `network-masked-address` (source-of) |
| Owner Portfolio mask | Not recorded per address; no concept (answer contract) |

No gaps.

### Q15 navigation pilot (2026-11-18)

| Example | Route |
| --- | --- |
| Anchor C: 0.125 open per unit | `open-violation-rate` to `violation`, `violation-status` (numerator, Open only) and `residential-units` (denominator, 32) |
| Anchor C: open B 2, C 2, oldest 2023-03-25 | `violation` to `violation-class` and `inspection-date` (schema); `building` to `has-violation` (schema) |
| A lot with 0 units | `residential-units` to `open-violation-rate`: rate unavailable, never 0 |

No gaps.

### Q13 navigation pilot (2026-11-17)

| Example | Route |
| --- | --- |
| Anchor C: no satisfaction for the 2002, 2005 or 2015 mortgages | `mortgage` to `satisfaction` (acts-on); the answer lists the documents and does not say which loan is outstanding |
| Anchor C: agreement and assignment of leases and rents recorded the same day as the mortgage | `mortgage` to `agreement` (acts-on); `financing-document` to `assignment` (hierarchy) |
| Anchor A: termination of assignment of leases and rents, no satisfaction | `assignment` to `termination` (acts-on); `termination` to `satisfaction` (contrasts-with); `satisfaction` to `mortgage` |
| Anchor A: the lot's deeds and its financing documents | `has-deed` to `has-financing-document` (contrasts-with); both reach `document` through the schema |
| Borrower and lender on a mortgage | `mortgage` to `borrower` and `lender` (Q11) |

No gaps.

### Q12 navigation pilot (2026-11-17)

| Example | Route |
| --- | --- |
| Anchor A: the 2025 deed names one party on both sides | `grantee` to `grantor` (contrasts-with) and `grantee-name` to `grantor-name` (contrasts-with): both listed as recorded |
| Anchor A: two deeds since 2015, one with amount 0 | `deed` to `not-a-sale` (summary-of) to `document-amount` (input-to) |
| Anchor C: the portfolio's deeds | `deed` to `in-portfolio` and `owner-portfolio` (schema, Q9) |
| Anchor C: is the deed the registered owner's? | `deed` to `attributable-transfer` (summary-of) to `corporate-owner` (input-to); an owner spelled differently in the two sources is missed (recorded gap) |

No gaps.

Q14 (2026-11-17): hidden labels `title holder on a date` (supporting deed) and `registered owner on a date` (registration in force) catch user wording; each checked against the vocabulary and used once. No shared labels.

### Q16 navigation pilot (2026-11-18)

| Example | Route |
| --- | --- |
| Article says a fund controls the parent company | `retrieved-item` to `affiliation`; `reported-claim` to `reported` and, kept apart, to `owner-portfolio` |
| Two articles contradict each other | `conflicts` to `contested`: item against record versus item against item |
| Scanned attachment with an uncertain name | `extraction-method` to `match-basis` (lead only) |
| Item starts unreviewed | `item-unreviewed` to `unreviewed` (the Q6 list status, kept apart) |
| Similar but not identical LLC name | `lead-only` and `unrelated`, by the answer contract; no link needed |
| Nothing found, dated after as-of, unreadable | answer-contract fields in `profiles/q16.yaml`; no thesaurus link needed |

### Q17 navigation pilot (2026-11-18)

| Example | Route |
| --- | --- |
| Lapsed and older than the deed (anchor E) | `lapsed-registration` to `registration-end-date`; `registration-older-than-deed` to `last-registered-date` and `recorded-date`, and to `not-a-sale` for the $0 case |
| Missing (anchor F) | `missing-registration` to `hpd-registered`; kept apart from `no-usable-registration` |
| Period not yet ended (anchor A) | `lapsed-registration` to `registration-end-date`; the as-of date is an input stated in the answer |
| 6 units against the threshold | `unit-threshold` to `residential-units` |

### Q18 navigation pilot (2026-11-18)

| Example | Route |
| --- | --- |
| Anchor B: a $0 deed to an LLC, then a $6,800,000 deed from it | `zero-transfer` to `deed-classification` (priced is the other value) and to `restructuring-signal`; `deed` to `deed-classification` |
| Same name on both sides (anchor A, 2025) | `restructuring-signal` to `comparison-rule`; `grantor` and `grantee` by the schema |
| Grantee is the registered owner | `restructuring-signal` to `attributable-transfer` (contrasts-with) |
| Portfolio lots chosen, grouping not used as evidence | `restructuring-signal` to `owner-portfolio` (contrasts-with) |
| Amount 0 versus not a sale | `zero-transfer` to `not-a-sale` |

No gaps.

### Q19 navigation pilot (2026-11-19)

| Example | Route |
| --- | --- |
| 438 52 Street and 1704 East 15 Street: same portfolio and network | `pair-layer-state` to `representative-path` (a path only when the state is same); `ownership-signal` and `connected-by-identity` name the stage; `ownership-signal` to `stage-precision` |
| Anchors A and B: no path | `pair-layer-state` (ungrouped) and the reason through `network-absence-reasons`; `representative-path` is not shown |
| A Louvain-split pair connected through a third network | `pair-layer-state` to `pre-subdivision-connectivity` (contrasts-with) and `louvain-community` to `pre-subdivision-connectivity` |
| Stage precision stated for a link | `representative-path` to `stage-precision` (contrasts-with); `ownership-signal` to `stage-precision` |

No gaps.

### Q20 navigation pilot (2026-11-19)

| Example | Route |
| --- | --- |
| Anchor A trail ends at the entity's own process address | `dossier` to `stop-reason` (`reached-service-address`), then `dos-process-address` (source-of) |
| The shared HPD business address and `702 PLAZA LLC` stay open | `dossier` to `lead`; `lead` to `stop-reason` for any not followed |
| A news claim about a parent company | `dossier` to `retrieved-item`; `lead` to `hypothesized` and `reported`; `lead` to `lead-only` for a loose match |

No gaps.

### Q22 navigation pilot (2026-11-19)

| Example | Route |
| --- | --- |
| Anchor G, `KS` and `K S` | `name-agreement` to `normalization-match` (rule S1 via `comparison-rule`) |
| Anchor D, `HDFC` and the long form | `name-agreement` to `abbreviation-match`; `abbreviation-match` to `comparison-rule` (AB1) |
| `Holdings` and `Holdings II` | `normalization-match` to `differs-by-numeral-or-word` |
| Anchor B, no joining record | `name-agreement` to `different`; joining records are read from the schema (lot, registration, document, DOS id) |

No gaps.

### Q23 navigation pilot (2026-11-19)

| Example | Route |
| --- | --- |
| `BRIGHTON MANAGEMENT`, spelling variants | `agent` to `agent-footprint`; the rule is `comparison-rule` N3, read through `corporation-name` in the schema |
| Footprint against the building's layers | `agent-footprint` to `operational-network` and `owner-portfolio` |
| The agent's address on the mask lists | `agent-footprint` to `network-masked-address` and `portfolio-masked-address` |
| "Operator or commercial service?" | No concept: the answer reports size and caveats, never a verdict |

No gaps.

### Q25 navigation pilot (2026-11-19)

From `jurisdiction` a reader reaches `registry-search`, then `registry-outcome` and its four values, and `retrieved-item`. From `registry-status-only` they reach `needs-payment`; from `registry-unreachable` they reach `service-unavailable`. The match basis and review status are in the Q16 scheme and reached through `retrieved-item`'s fields. No gap.

### Q24 navigation pilot (2026-11-19)

| Example | Route |
| --- | --- |
| `5413 PLAZA LLC` in three sources | `name-search` to `name-agreement` (basis) and `comparison-rule` (N3); roles from `contact-type`, `grantee`, `grantor` and `dos-entity` through the schema |
| A common personal name | `name-search` to `lead`: every person row is a lead with a count |
| `BRIGHTON MANAGEMENT` and `BRIGHTON MANAGEMENT LLC` | `name-search` to `legal-suffix-only`; `legal-suffix-only` to `different` and `normalization-match` (kept apart) |
| A name that matches nothing | `name-search`: "no match in these sources" with the rule |

No gaps.

### Q27 navigation pilot (2026-11-19)

| Example | Route |
| --- | --- |
| Anchor C: 0.84375 problems per unit, 2023 to 2025 | `complaint-rate` to `complaint-problem` (numerator, 27) and `residential-units` (denominator, 32) |
| Anchor C: 12 emergency, 2 immediate emergency, 13 non-emergency | `complaint-problem` to `problem-type`, `problem-status`, `major-category`, `received-date` (schema); `building` to `has-problem` (schema) |
| "Is this a violation?" | `complaint-problem` to `violation` (contrasts-with): reported versus cited |
| A lot with 0 units | `residential-units` to `complaint-rate`: rate unavailable, never 0 |

No gaps.

### Q15 pest extension navigation pilot (2026-11-21)

| Example | Route |
| --- | --- |
| "Do other people have mice?" for anchor C's building | `pest-violation` to `violation` (output-of) and `order-number` (input-to): the count is a filter on the order number; anchor C has one open roach violation (568), no mice |
| "Is a complaint about mice a violation?" | `pest-violation` to `complaint-problem` (contrasts-with): reported versus cited |
| A building with only vermin orders (566, 866) | `pest-violation` scope note and the code list: reported as unspecified vermin, never mice |
| Open pest violations | `pest-violation` to `violation-status` through `violation` (schema) |

No gaps.

### Q27 pest extension navigation pilot (2026-11-21)

| Example | Route |
| --- | --- |
| "Do other people have mice?" for anchor C's building | `pest-complaint` to `complaint-problem` (output-of), `minor-category` (PESTS) and `problem-code` (MICE): anchor C has 1 closed MICE problem since 2021, plus roaches 3, other 2, flies 1 |
| "Is a complaint about mice a violation?" | `pest-complaint` to `pest-violation` (contrasts-with): reported versus cited; anchor C has a roach violation, no mice violation |
| A building with only OTHER pest problems | `problem-code` to `minor-category` (reported-with) and the `pest-complaint` scope note: OTHER is never mice |
| A minor category such as RADIATOR | `minor-category` to `major-category` (reported-with): read with its major category |

No gaps.

### Q28 navigation pilot (2026-11-20)

| Example | Route |
| --- | --- |
| Anchor C: one closed Tenant Action, no finding | `litigation-case` to `case-type`, `case-status`, `case-open-date` (schema); `harassment-finding` to `case-type` (contrasts-with): the type is not the outcome |
| A finding After Trial with a date and penalty | `harassment-finding` to `finding-date` (reported-with); `litigation-case` to `case-penalty` (schema) |
| "Did the city also cite violations?" | `litigation-case` to `violation` (contrasts-with): action brought versus cited |
| Anchor A: respondent `5413 PLAZA LLC` equals the registered owner | `respondent` to `respondent-owner-match` (input-to) to `contact` (input-to) and `name-agreement` (rule N3) |
| Anchor C: STREET versus ST | `respondent-owner-match`: not matched, reported, not reconciled |

No gaps.

## External mappings

None sought for Q1 (decided 2026-11-12). Nothing in Q1's answers needs an external scheme. Revisit when party, organization or provenance questions arrive (W3C ORG, PROV-O). Q3 (2026-11-12): none sought. A deed, a grantee and an agreement result have no true equivalent the agent needs; a W3C ORG or schema.org party class would blur the grantee with the registered owner, which the project keeps apart. Q2 (2026-11-12): none sought either. HPD registration, owner contact and owner name have no true equivalent in W3C ORG, PROV-O or schema.org that the agent needs; a mapping would be a guess. No SSSOM file exists yet; it is created with the first mapping.

Q4 (2026-11-12): none sought. HPD roles have no true equivalent in W3C ORG or schema.org; a `Role` or `Person` mapping would blur the agent with the owner, which the project keeps apart.

Q5 (2026-11-13): none sought. A DOS entity is a state filing; the W3C ORG `Organization` and schema.org `Organization` are broader than a filed entity and would invite merging it with an HPD owner, which the project keeps apart. A registered agent has no true equivalent that does not blur it with the managing agent.

Q8 (2026-11-13): none sought. The BOR release publishes codes, not IRIs, so there is nothing to map to; its codes are kept as hidden labels. W3C ORG and schema.org have no true equivalent of an operational network or a landlord record, and a mapping would suggest group ownership.

Q9 (2026-11-13): none sought. The BOR release publishes codes, not IRIs; its codes are hidden labels. W3C ORG and schema.org have no true equivalent of an owner portfolio, and a mapping would suggest common ownership. PROV-O would fit the signals as derivation only by guesswork, so none is asserted.

Q6 (2026-11-13): none sought. The BOR release publishes codes, not IRIs, and the list is a project file. Schema.org and W3C ORG have postal-address terms, but none says "masked by a method" or "mail drop", and a mapping would suggest the address is a finding about its users.

Q11 (2026-11-16): none sought. An ACRIS mortgage has no true equivalent that is not broader or narrower in schema.org (`MortgageLoan` is a financial product, not a recorded document), and W3C ORG has no financing or service-of-process relation. Mapping an affiliation type to an ORG membership or reporting-line term would suggest control, which the project does not assert.

Q13 (2026-11-17): none sought. ACRIS document types have no true equivalent in schema.org (`MortgageLoan` is a product, not a recorded document) or W3C ORG; a mapping would suggest an outcome (paid, ended) the project does not assert.

Q12 (2026-11-17): none sought. A grantor and a grantee have no true equivalent in schema.org or W3C ORG that does not suggest a seller or a buyer in a sale; the project reports recorded roles and says nothing about intent. The attribution and not-a-sale flags are project-derived states.

Q14 (2026-11-17): none sought. A supporting deed and a registration in force are computed answer states with no true equivalent in schema.org, W3C ORG or PROV-O; a mapping would suggest ownership or responsibility on the date.

Q15 (2026-11-18): none sought. An HPD violation is an inspector's citation of the housing maintenance code; schema.org and W3C ORG have no equivalent, and a mapping to a complaint or incident term would suggest a measure of conditions or of conduct. The class and status are HPD values.

Q16 (2026-11-18): none sought. A retrieved item, claim and review status are answer-contract terms. PROV-O (`prov:Entity`, `prov:wasDerivedFrom`) is broader and would suggest provenance of a fact, while the project keeps a published claim apart from the recorded facts; schema.org `Claim` and `NewsArticle` do not carry the review status or match basis. None asserted.

Q17 (2026-11-18): none sought. Missing, lapsed and older-than-deed are computed answer states over HPD and ACRIS dates; schema.org and W3C ORG have no equivalent, and a mapping would suggest a legal violation or a change of owner, which the answer does not assert.

Q19 (2026-11-19): none sought. The pair state, path, connectivity and precision are answer-contract terms over BOR output; PROV-O and schema.org have no equivalent, and a mapping would suggest a finding of common ownership.
Q18 (2026-11-18): none sought. Classification and signals are computed answer states over ACRIS names and amounts; PROV-O, schema.org and W3C ORG have no equivalent, and a mapping would suggest a finding of restructuring or common control, which the answer does not assert.

Q20 (2026-11-19): none sought. A dossier, a lead and a stop reason are answer-contract terms of this project. PROV-O and schema.org have no equivalent, and a mapping would suggest a finding of ownership or completeness.

Q21 (2026-11-19): none sought. A lot ranking and a concentration share are answer-contract terms; no external scheme defines them, and a mapping would suggest a finding about conditions or ownership.

Q22 (2026-11-19): none sought. Entity name outcomes are answer-contract terms of this project; no external scheme defines them, and a mapping would suggest a finding of identity.

Q23 (2026-11-19): none sought. A footprint is an answer-contract term of this project; no external scheme defines it, and a mapping would suggest a finding of common ownership or a commercial service.
Q26 (2026-11-19): none sought. A source absence is an answer-contract term; the five reasons come from the BOR release and no external scheme defines them.

Q25 (2026-11-19): none sought. A registry search and its outcomes are answer-contract terms of this project; PROV-O activities and schema.org have no matching concept, and a mapping would suggest a finding of identity.

Q24 (2026-11-19): none sought. A name search and its lead kinds are answer-contract terms of this project; no external scheme defines them, and a mapping would suggest a finding of identity.

Q27 (2026-11-19): none sought. A complaint problem is HPD's record of a reported condition; schema.org and W3C ORG have no equivalent, and a mapping to a complaint or incident term would suggest a finding about conditions or conduct. The type and status are HPD values.

Q15 pest extension (2026-11-21): none sought. A pest violation is an inspector's citation under an HPD order code; schema.org, W3C ORG and PROV-O have no equivalent, and an infestation or pest-control term would suggest a measure of conditions or of conduct. The order codes are HPD values read from descriptions.
Q27 pest extension (2026-11-21): none sought. A pest complaint is a tenant's report to HPD; schema.org, W3C ORG and PROV-O have no equivalent, and a pest-control or infestation term would suggest a finding. The minor category and the problem code are HPD's values.
Q28 (2026-11-20): none sought. A litigation case is HPD's record of an action brought; schema.org and W3C ORG have no equivalent, and a legal-case mapping would suggest a finding of fault. The respondent match is an answer-contract term.

## Exceptions

Concepts with no related link, left unlinked on purpose:

- `has-building`, `year-built`, `building-class`, `assessed-total-value`: the schema already declares the node, property or relationship they belong to, and the check enforces it.
- `matched-exactly`, `matched-by-variant`, `ambiguous`, `not-found`: a flat value set in `address-resolution-outcomes`; they relate to the outcome by scheme membership, not by an association.
- Q23: none. The new concept carries related links.
- Q24: none. Both concepts carry related links.
- Q25: `registry-record-found` and `registry-no-record`: flat values in `registry-outcomes`, related to their field by scheme membership, not by association.
- Q2: `has-registration`, `has-contact`, `contact-type`: the schema declares the node, property or relationship they belong to. `individual-owner`, `joint-owner`: a flat value set in `owner-contact-types` and `contact-types`; they relate to `contact-type` by scheme membership.
- Q3: `has-grantee`, `document-type`: the schema declares the node, property or relationship they belong to. `exact-normalized`, `not-comparable`, `same`, `differs`, `address-absent`: flat value sets in `name-agreement-outcomes` and `address-agreement-outcomes`; they relate to their agreement concept by scheme membership.
- Q4: `person-name`: the schema declares the property. `officer`, `lessee`: a flat value set in `role-contact-types` and `contact-types`; they relate to `contact-type` by scheme membership.
- Q5: `entity-type`, `initial-filing-date`: properties of the DOS entity node that the schema declares; no cross-branch reader needs a link.
- Q8: `network-group-id`, `covers`, `based-on-contact`, `network-split`, `link-weight`, `edge-id`: the schema declares the node, property or relationship they belong to. `whole-component`: a flat value set in `network-splits` (its sibling value is linked in Q19). The five top-level and ten of the eleven detail values of `network-absence-reasons` (the eleventh is linked in Q6) (`no-qualifying-linkage`, `excluded-by-policy`, `below-eligibility-rule`, `outside-source-coverage`, `outside-method-input`, `no-linkage`, `no-registration`, `no-owner-contact`, `address-evidence-masked`, `first-name-veto`, `common-name-veto`, `shared-company-degree-unknown`, `shared-company-name-not-rare`, `shared-company-first-name-conflict`, `shared-company-degree-cap`): related by hierarchy and scheme membership, not by association.
- Q9: `portfolio-group-id`, `portfolio-composition`: the schema declares the node, property or relationship they belong to. `identity-based`, `deed-only`, `deed-bridged`: a flat value set in `portfolio-compositions`. `identity-splink-base`, `identity-splink-feedback`, `identity-curated`, `identity-registered-llc`, `deed-held-since`, `deed-linked-successor`: a flat value set in `ownership-signals`. The eight new detail values of `network-absence-reasons` (`unmatched-node`, `coop-condo-excluded`, `coop-condo-dominated`, `institutional-screen`, `deed-not-latest`, `deed-parcels-out-of-range`, `successor-not-shell`, `successor-transfer-not-nominal`): related by hierarchy and scheme membership, not by association.
- Links: `identity-cluster-evidence`, `link-set-evidence`, `deed-evidence-item`: a flat value set in `link-evidence-types`; they relate to the link property that names the kind by scheme membership.
- Q6: `portfolio-masked-address-text`, `portfolio-masked-address-degree`, `masked-identities`, `masked-address-id`, `masked-address-text`, `masked-address-degree`, `mail-drop-address-key`, `zip-five`, `mail-drop-basis`, `list-review-status`: the schema declares the node and property they belong to. `mail-drop-kind`: likewise; its four values (`listed-registered-agent`, `listed-law-firm`, `listed-management-office`, `listed-unknown`) are a flat value set in `mail-drop-kinds`, and the one value of `list-review-statuses` is related by scheme membership, not by association.
- Q12: `has-grantor`: the schema declares the relationship it belongs to. A grantor to its name association is left out for the same reason.
- Q13: `financing-document`: connected through its five narrower concepts; the schema declares the Document node and its link from the lot, so a related link would repeat both.
- Q15: `violation-class`, `inspection-date`, `violation-id`, `has-violation`: the schema declares the node, property or relationship they belong to.
- Q16: `source-category`, `review-status`, `fact-relation` (their only association was to the item, which the answer contract declares); `public-record`, `published-reporting`, `web-content`, `project-derived`, `confirmed`, `refuted`, `inconclusive`, `agrees`, `adds`, `unrelated`, `exact-match`: flat value sets (lead-only is linked in Q20) in `source-categories`, `review-statuses`, `fact-relations`, `match-bases`; related to their field by scheme membership.
- Q17: none. All five concepts carry at least one related link.
- Q18: none. All three concepts carry related links.
- Q19: none. All four concepts carry related links.
- Q20: `no-further-link`, `budget-reached`, `unresolved-conflict`: a flat value set in `stop-reasons`; related to their field by scheme membership, not by association.
- Q21: none. Both concepts carry related links.
- Q22: none. Both concepts carry related links.

- Q26: none. The new concept is linked.
- Q27: `problem-id`, `complaint-id`, `has-problem`, `problem-type`, `problem-status`, `received-date`, `duplicate-flag`: the schema declares the node, property or relationship they belong to.
- Q28: `litigation-id`, `has-litigation-case`, `case-open-date`, `case-status`, `open-judgement`, `case-penalty`: the schema declares the node, property or relationship they belong to.
- Q27 pest extension: none. All three concepts carry related links.
- Q15 pest extension: none. Both concepts carry related links; the order number is not linked straight to the violation node because the schema declares the property of the node.
