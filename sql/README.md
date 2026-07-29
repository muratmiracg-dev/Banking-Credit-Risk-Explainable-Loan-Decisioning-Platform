# PostgreSQL layer

`schema.sql` separates the general decision-support schema from the restricted governance
schema. `views.sql` adds executive, risk-band, recommendation and fairness-disparity views.

The SQL is a deployment reference. A production implementation should additionally configure:

- role-based access and column-level controls;
- encrypted connections and managed secrets;
- retention, deletion and legal-hold policy;
- immutable decision and override events;
- approved data ingestion rather than local CSV artifacts;
- row-level security for business-unit or jurisdiction segmentation.
