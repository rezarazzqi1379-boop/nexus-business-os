# NEXUS mandatory chat preflight

For every consequential task in this repository:

1. Resolve one exact `project_id` before using project data.
2. Recover the current Source Registry and the project master.
3. Refresh every required dynamic connector and record its observation time.
4. Normalize only the evidence required for the task into project-scoped envelopes.
5. Run `nexus_chat_bootstrap.bootstrap_chat` before drafting the consequential result.
6. Stop when the gate is `BLOCK`; expose the conflict or missing authority.
7. Treat `REVIEW` as unresolved and do not promote claims to facts.
8. Require exact approval for send, publish, payment, signature, deployment, permission change or deletion.

Never place credentials or full OAuth tokens in manifests, evidence, prompts, logs or commits.
Connector availability proves access only; it does not prove data correctness or authority.
This contract applies to every agent and chat entry point that operates through this repository.

