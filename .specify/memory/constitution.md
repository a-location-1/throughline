<!--
Sync Impact Report
- Version change: scaffold → 1.0.0
- Modified principles: template placeholders → Code Quality, Tested Behavior,
  Deterministic Visualization, Consistent User Experience, Performance
- Added sections: Domain Constraints; Delivery and Review
- Removed sections: none
-->

# Throughline Constitution

## Core Principles

### I. Code Quality
Production code MUST be cohesive, readable, and maintainable. Changes MUST use
existing project patterns where they fit, keep public interfaces intentional, and
avoid duplicated or speculative abstractions. A reviewer MUST be able to trace
uploaded play text through parsing, interaction data, and visualization without
relying on undocumented behavior. Prefer well-maintained libraries over custom 
implementations. Design library-first: every feature starts as a standalone library;
 libraries must be self-contained and independently testable.

### II. Tested Behavior (NON-NEGOTIABLE)
All production code MUST have unit tests, and the complete test suite MUST maintain
more than 80% code coverage. Tests MUST cover normal, boundary, invalid-input, and
regression behavior for parsing, scene and character relationships, and rendering
data transformations. A change MUST NOT be considered complete while required
tests are missing or coverage is at or below 80%.

### III. Deterministic Visualization
Given the same play text, parsing configuration, and application version, the
application MUST produce the same character and scene interaction data and the
same visual output. Ordering, identifiers, layout inputs, color assignments, and
any generated values MUST be deterministic and explicitly defined. Snapshot or
equivalent visual regression tests MUST protect representative plots from
unintended changes.

### IV. Consistent User Experience
The interface MUST use consistent terminology, controls, feedback, spacing, and
visual conventions across upload, parsing results, plot exploration, and error
states. User-visible failures MUST explain what happened and provide a useful
next action. The visual encoding MUST remain legible and usable across supported
screen sizes and input methods.

### V. Performance
The application MUST keep uploads, parsing, and plot interaction responsive for
the supported play size defined by the feature specification. Expensive work MUST
be measured and kept off the interaction path where practical. Performance
regressions MUST be detected with representative benchmarks or profiling before
release when a change affects parsing, data volume, rendering, or interaction.

## Domain Constraints

Play text is the source of truth. The system MUST preserve the distinction between
characters, scenes, appearances, and interactions, and MUST surface ambiguous or
unparsed text rather than silently inventing relationships. Any normalization or
interpretation that affects the plot MUST be documented and covered by tests.

## Delivery and Review

Every change MUST include updated unit tests and documentation when behavior,
configuration, or user-visible terminology changes. Before merge, automated tests
MUST pass, total coverage MUST exceed 80%, deterministic-output checks MUST pass
for affected visualizations, and reviewers MUST verify accessibility, usability,
and performance impact. Known limitations and unsupported input forms MUST be
recorded in project documentation.

## Governance

This constitution supersedes conflicting development conventions for Throughline.
Amendments MUST describe the affected principles, rationale, compatibility impact,
and required migration or test updates. Versioning follows semantic versioning:
MAJOR for incompatible governance changes or removed requirements, MINOR for new
principles or materially expanded requirements, and PATCH for clarifications that
do not change obligations. Each change MUST update the last-amended date and pass
the delivery gates above. Compliance is reviewed during code review and at each
release; exceptions MUST be documented with an owner, rationale, and expiration.

**Version**: 1.0.0 | **Ratified**: 2026-09-20 | **Last Amended**: 2026-09-20
