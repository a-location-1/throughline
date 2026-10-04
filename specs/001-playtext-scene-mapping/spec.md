# Feature Specification: Playtext Scene Mapping

**Feature Branch**: `001-playtext-scene-mapping`

**Created**: 2026-09-20

**Status**: Draft

**Input**: User description: "Build a standalone web application that accepts a theater playtext by URL or PDF upload and generates a character-by-scene table plus a visualization of character reappearances across scenes."

## Clarifications

### Session 2026-09-20

- Q: What maximum playtext size should the first release support for both PDF uploads and URL-based sources? → A: 200 pages or 10 MB.
- Q: What format should the download action produce for the completed table and visualization? → A: CSV for the completed table.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a character-by-scene overview (Priority: P1)

As a student, researcher, or analyst, I want to submit a playtext and receive a reliable overview of its scenes and characters so that I can understand the play's structure without manually annotating the text.

**Why this priority**: The scene and character mapping is the core value of the product and is useful even without the visualization.

**Independent Test**: Submit a representative playtext through either supported input method and verify that the result identifies the play's acts/scenes, characters, scene appearances, and line counts where speaking text is available.

**Acceptance Scenarios**:

1. **Given** a readable playtext submitted by URL, **When** processing completes, **Then** the application displays the detected acts and scenes and a table mapping each identified character to the scenes in which they appear.
2. **Given** a readable playtext submitted as a PDF, **When** processing completes, **Then** the application displays the same types of structured results as for a URL submission.
3. **Given** a one-act play with no explicit scene breaks, **When** processing completes, **Then** the result represents one act and the correct number of scenes rather than inventing additional breaks.
4. **Given** a play with one character or speaker, **When** processing completes, **Then** the result includes that single character and its actual scene participation without requiring multiple characters.
5. **Given** a speaker who is unnamed in the source text, **When** processing completes, **Then** the result includes a clearly labeled unnamed-speaker entry rather than dropping the speech or assigning an unsupported name.
6. **Given** a play uses consistent but non-canonical formatting for structural markers, such as `Scene`, `SCENE`, `Scene:`, `Chapter`, or `---`, **When** processing completes, **Then** the parser evaluates the marker in its text context and recognizes the corresponding scene boundaries without requiring one exact spelling or punctuation pattern.
7. **Given** a play contains the word "scene" inside dialogue or stage directions without a structural boundary, **When** processing completes, **Then** the parser does not create a scene solely from that word.
8. **Given** a source contains multiple plays, **When** processing completes, **Then** the application warns that multiple plays were found and analyzes only the first play.

### User Story 2 - Explore character reappearances (Priority: P2)

As a director or stage manager, I want a visual representation of when characters enter and reappear across scenes so that I can use the output while planning rehearsals and understanding continuity.

**Why this priority**: The visualization turns the extracted structure into a practical rehearsal and planning aid after the underlying mapping is available.

**Independent Test**: Process a playtext containing characters who appear in multiple scenes and verify that the visualization shows scene order, character identity, first appearance, and subsequent reappearances consistently with the table.

**Acceptance Scenarios**:

1. **Given** a completed character-by-scene table, **When** the visualization is displayed, **Then** it shows the scenes in play order and represents each character's appearances and reappearances in those scenes.
2. **Given** characters with different first-appearance positions, **When** the visualization is displayed, **Then** character ordering reflects their order of first appearance.
3. **Given** the same playtext is processed again with the same application version and parsing rules, **When** the results are compared, **Then** the table ordering, appearance data, and visualization are identical.
4. **Given** a character who is present but does not speak in a scene, **When** the visualization and table are displayed, **Then** that non-speaking presence is represented distinctly from speaking participation.

### User Story 3 - Review, share, and recover from processing outcomes (Priority: P3)

As any tool user, I want clear progress, error, and export controls so that I know what the application is doing and can reuse the result in notes, analysis, or rehearsal materials.

**Why this priority**: Feedback and sharing make the core analysis usable in real workflows and prevent users from mistaking an incomplete or invalid result for a finished one.

**Independent Test**: Submit valid, invalid, and unsupported playtexts; observe progress and errors; then copy and download a completed result.

**Acceptance Scenarios**:

1. **Given** a valid playtext is being processed, **When** analysis is underway, **Then** the application reports progress through meaningful stages and indicates when the result is ready.
2. **Given** a submission from which no characters or scenes can be identified, **When** processing completes, **Then** the application rejects it with a clear explanation and a useful next action.
3. **Given** a source contains recognizable playtext but does not use conventional act, scene, or speaker labels, **When** processing completes, **Then** the application produces the best-supported analysis it can, marks conventional play attributes as unidentified or uncertain, and communicates that limitation instead of rejecting the source solely for missing those labels.
4. **Given** a completed result, **When** the user selects copy, **Then** a usable representation of the table and visualization summary is placed on the clipboard and the action outcome is communicated.
5. **Given** a completed result, **When** the user selects download, **Then** the application downloads the completed character-by-scene table as a CSV file for later use.
6. **Given** the source cannot be retrieved or read, **When** processing fails, **Then** the application explains that the input could not be processed and allows the user to submit another source.

### Edge Cases

- A playtext contains explicit acts but no explicit scene breaks within an act; the output preserves the detected act and reports the available scene structure without fabricating scenes.
- A playtext has no act breaks but has scene breaks; the output reports a single act and the detected scenes.
- A playtext has no act or scene breaks; the output reports the source as one act and one scene only when the content can otherwise be recognized as a playtext.
- A scene contains only stage directions or silent characters; the output distinguishes non-speaking presence from speaking characters.
- A character name appears with formatting or spelling variations; the application uses a consistent identity only when the source provides sufficient evidence, and otherwise surfaces the ambiguity rather than silently merging distinct characters.
- A group of characters is introduced collectively and later referenced individually; the output associates an individual reference with the previously introduced group only when the source provides sufficient evidence, and otherwise surfaces the ambiguity rather than creating an unsupported character identity.
- A scene contains an unnamed speaker; the unnamed entry remains distinct and is not presented as a named character.
- A line is attributed to a collective speaker such as a crowd; the output preserves the line count and represents the collective attribution distinctly from a named individual character without inventing a character identity.
- A submission is empty, unreadable, malformed, inaccessible, or not a playtext; the application rejects it with a specific, user-understandable reason.
- A source is ordinary non-play content, such as a general website, and lacks sufficient evidence of dramatic text; the application rejects it rather than treating any occurrence of a word such as "scene" as a play marker.
- A source is a play that lacks conventional act, scene, or character labels; the application makes a best-effort analysis when possible and reports which conventional attributes could not be identified.
- A source contains multiple plays, such as an anthology page or document; the application identifies the first play, warns that additional plays were found, and does not combine them into one result.
- A source uses one consistent structural formatting convention throughout, even when that convention is unconventional; the parser applies that convention consistently and does not treat alternate casing or punctuation as a second convention within the same source.
- A play contains repeated or unusually formatted scene headings; the output remains deterministic and does not duplicate scenes solely because of formatting noise.
- A play contains a single speaker throughout; the output still includes a valid one-character result.
- A source uses Unicode characters, diacritics, punctuation, capitalization, or non-English names; the output preserves the source display form and does not silently strip meaningful characters.
- A source uses naming conventions, transliteration, or honorifics that cannot be resolved confidently; the output preserves the ambiguity rather than silently merging or rewriting identities.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST allow a user to submit a playtext by pasting a URL.
- **FR-002**: The application MUST allow a user to submit a playtext by uploading a PDF.
- **FR-003**: The application MUST report meaningful processing progress from submission through completed results or rejection.
- **FR-004**: The application MUST reject an input only when it cannot establish sufficient evidence that the source contains playtext or cannot identify any usable character or speaker after applying its supported best-effort rules, and MUST explain the reason for rejection.
- **FR-005**: The application MUST identify and report the number and order of acts and scenes supported by the source text.
- **FR-006**: The application MUST represent a play with no explicit act breaks as a single act when the source supports that interpretation.
- **FR-007**: The application MUST identify characters and speakers, including a single character or speaker when only one exists.
- **FR-008**: The application MUST preserve an unnamed speaker as an explicitly unnamed entry rather than omitting or inventing an identity.
- **FR-009**: The application MUST identify the characters present in each scene.
- **FR-010**: The application MUST identify speaking participation and, where supported by the source, distinguish it from non-speaking presence.
- **FR-011**: The application MUST record the order in which characters first appear and use that order as the default character order in results unless the user selects another supported order.
- **FR-012**: The application MUST provide a way to sort speaking characters within each scene by number of lines from most to fewest.
- **FR-013**: The application MUST generate a visualization showing scenes in order and character appearances/reappearances across those scenes.
- **FR-014**: The application MUST keep the table and visualization consistent with the same underlying scene, character, and appearance data.
- **FR-015**: The application MUST produce identical table data, ordering, and visualization for the same input, parsing rules, and application version.
- **FR-016**: The application MUST provide copy and CSV download actions for completed results, and MUST communicate whether each action succeeded or failed.
- **FR-017**: The application MUST not retain submitted playtexts or generated results after the user leaves or resets the standalone page, unless the user explicitly downloads or copies them.
- **FR-018**: The application MUST provide a useful next action for user-visible failures, such as correcting the source or submitting another playtext.
- **FR-019**: The application MUST resolve an individually referenced character to a previously introduced character group only when the source provides sufficient evidence, and MUST otherwise preserve the ambiguity rather than silently creating or merging an identity.
- **FR-020**: The application MUST preserve lines attributed to a collective or indeterminate speaker, such as a crowd, with their scene and line-count data, and MUST distinguish that attribution from a named individual character.
- **FR-021**: The application MUST preserve source-provided character and speaker display forms, including Unicode characters, diacritics, punctuation, capitalization, and honorifics, except where a documented normalization rule is supported by clear source evidence.
- **FR-022**: The application MUST NOT infer or display demographic, gender, racial, ethnic, disability, national, religious, or other personal identity attributes from names, pronouns, roles, or speech.
- **FR-023**: The first release MUST clearly state its supported source scope: primarily English-language, Latin-script playtexts following recognizable Western dramatic conventions, with tolerance for formatting variation within that scope. Unsupported language, script, or structural forms MUST be identified as unsupported or uncertain rather than presented as reliable results.
- **FR-024**: The application MUST preserve ambiguity caused by naming conventions, transliteration, honorifics, or formatting when the source does not provide sufficient evidence for identity resolution.
- **FR-025**: The fixture corpus MUST include variation within the supported scope, including Unicode and diacritics, naming and capitalization differences, non-speaking roles, collective speakers, unusual but recognizable formatting, and accessible and inaccessible source conditions.
- **FR-026**: The parser MUST recognize scene and act boundaries from multiple context-supported formatting conventions, including differences in capitalization, optional punctuation, alternate structural labels, and non-word separators, without treating an isolated occurrence of a structural word in dialogue or stage directions as a boundary.
- **FR-027**: The parser MUST assume one consistent structural formatting convention within a submission and MUST use contextual evidence, position, repetition, and surrounding playtext signals to distinguish structural markers from ordinary words or decorative formatting.
- **FR-028**: When a source contains multiple plays, the application MUST identify the first play as the analysis scope, emit a user-visible multiple-play warning, and exclude later plays from the primary result.
- **FR-029**: When a source contains sufficient evidence of playtext but lacks conventional act, scene, or character signals, the application MUST produce a best-effort result with explicit uncertainty or unidentified-attribute notices instead of rejecting the source solely for those missing conventions.
- **FR-030**: The application MUST reject ordinary non-play content when the source lacks sufficient combined evidence of dramatic text, even if it contains isolated words that can also occur in plays.
- **FR-031**: Scene-detection and character-identification evaluation MUST report results by fixture category, including formatting, source type, ambiguity, multiple-play, non-play, accessibility, and invalid-input categories, so systematic failures are not hidden by an aggregate percentage.
- **FR-032**: The application MUST remain usable on slow connections and modest mobile devices within the supported input limits, including visible progress, bounded client memory, responsive narrow-screen output, and no requirement for hover or high-bandwidth media.

### Key Entities *(include if feature involves data)*

- **Playtext Submission**: A URL or uploaded PDF provided for analysis, including its processing state and any retrieval or readability failure.
- **Act**: An optional structural grouping in the playtext containing one or more scenes; a play without act breaks is represented as one act when appropriate.
- **Scene**: An ordered portion of a playtext, identified by source structure or a supported default when no breaks are present.
- **Character or Speaker**: A named character, unnamed speaker, collective or indeterminate speaker, or silent/non-speaking role identified in the playtext, with a deterministic first-appearance position.
- **Scene Appearance**: The relationship between a character and a scene, including presence type and speaking line count when available.
- **Analysis Result**: The complete structured table, ordering metadata, and visualization data generated from one submission.
- **Parser Notice**: A user-visible warning or uncertainty statement attached to an analysis, including multiple-play detection, unidentified conventional attributes, or other limitations that do not prevent a best-effort result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a fixed set of representative playtexts, the application reports the correct number and order of acts and scenes, or explicitly marks the attribute as unidentified when the source does not support it, in at least 95% of evaluated inputs; every known failure case is reported rather than silently presented as valid.
- **SC-002**: For the same fixed input, parsing rules, and application version, 100% of repeated runs produce identical character order, scene order, scene appearances, line counts, and visualization layout inputs.
- **SC-003**: At least 90% of first-time users can submit a supported playtext and locate the completed table and visualization without assistance.
- **SC-004**: At least 95% of invalid or unreadable submissions receive a user-visible explanation and a next action instead of an apparently successful but empty result.
- **SC-005**: Users can copy or download a completed result within 30 seconds of the result becoming available.
- **SC-006**: For supported playtexts up to 200 pages or 10 MB, progress feedback begins within 2 seconds of submission and the interface remains responsive while analysis is in progress.
- **SC-007**: In reviewer evaluation, the visualization clearly distinguishes speaking participation, non-speaking presence, and absence for representative scenes and remains usable on current desktop and mobile browsers.
- **SC-008**: For each fixed fixture category, the application reports scene-detection and character-identification results separately; no category may be omitted from evaluation because the aggregate SC-001 percentage passes.
- **SC-009**: In a fixture set containing at least 20 ordinary non-play sources and 20 unconventional but recognizable play sources, at least 95% of non-plays are rejected and at least 90% of recognizable plays receive a best-effort analysis or an explicit uncertainty result rather than being rejected solely for missing conventional labels.
- **SC-010**: For every multi-play fixture, 100% of results identify the first play as the analysis scope, exclude later plays from the primary table, and display a multiple-play warning.
- **SC-011**: Representative keyboard-only, screen-reader-oriented, low-vision zoom/reflow, reduced-motion, mobile, slow-connection, and modest-device scenarios can complete submission, review a result, and recover from an error without relying on color, hover, or high-bandwidth media.

## Assumptions

- Users have permission to submit the playtexts they analyze and are responsible for any copyright restrictions on source material.
- URL submissions point to publicly retrievable content that can be read as a playtext; authentication-protected or inaccessible sources may be rejected.
- PDF uploads contain selectable or extractable text in the first release; image-only PDFs may be rejected as unreadable.
- The first release supports playtexts up to 200 pages or 10 MB for both PDF uploads and URL-based sources; larger inputs may be rejected with a size-specific explanation.
- The first release's download action exports the completed character-by-scene table as CSV; the visualization remains available in the web page.
- The source text is authoritative. When formatting is ambiguous, the application reports uncertainty or rejection rather than inventing characters, scenes, or relationships.
- Structural detection is contextual rather than keyword-only: an isolated word such as "scene" is not a boundary, while a repeated, positionally plausible, consistently formatted marker may be a boundary even when its spelling, capitalization, punctuation, or separator is unconventional.
- A source is considered recognizable as playtext from combined evidence such as dramatic speech, speaker turns, stage directions, structural repetition, and play-like organization; no single conventional act, scene, or character label is required.
- Multiple-play detection is best-effort. When additional play boundaries are supported by the source, the first play is analyzed and the warning identifies that the source contained more than one play.
- A best-effort result may contain unidentified acts, scenes, speakers, or other conventional attributes, provided the limitation is visible to the user and the available analysis remains useful.
- The first release is intentionally optimized for English-language, Latin-script playtexts using recognizable Western dramatic conventions. This is a scope boundary, not a claim that other performance-text traditions are less valid; future iterations may expand the supported corpus and parsing rules.
- Source display names are preserved for reader visibility; internal identifiers may be deterministic and normalized without replacing the displayed source form.
- The application does not infer personal identity attributes and does not treat names, pronouns, or dramatic roles as reliable evidence of identity.
- Line counts mean identifiable spoken lines, using a consistent definition documented with the result; stage directions do not count as spoken lines.
- The default character ordering is first appearance, while scene-level line-count sorting is available as a user action.
- The standalone page supports current desktop and mobile versions of modern browsers.
- Results are session-only and are not stored in user profiles or a server-side history.
- Non-traditional or unusually formatted scripts may produce unusual results, as stated in the product scope.

## Out of Scope

- User profiles, sign-in, permissions management, or saved histories.
- Persistent storage of playtexts, analysis results, or user preferences.
- Manual editing or correction of parsed characters, scenes, or appearances.
- Collaborative annotations, rehearsal scheduling, or production-management workflows.
- General-purpose OCR for scanned image-only PDFs.
