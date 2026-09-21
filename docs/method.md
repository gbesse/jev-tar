# Defensibility method

This document explains the code-owned parts of the review workflow. Each document is judged once with responsiveness, potential privilege, and all issue questions in parallel. Oversized documents are chunked and each label uses the maximum chunk probability; this conservative aggregation can over-surface documents but avoids hiding one responsive passage.

Family propagation happens only after classification. A responsive member pulls its entire family into review, and the direct and propagated counts remain separate.

The cutoff is selected on a random tuning subset of human-coded control rows and measured on a disjoint holdout. The discard-pile sample estimates elusion using a Wilson interval; even zero observed misses has a positive upper bound. These calculations describe the supplied sample and coding—they do not establish legal sufficiency.
