--- a/goal-verification-lead/SKILL.md
+++ b/goal-verification-lead/SKILL.md
@@ -129,5 +129,14 @@
 credential-bearing, shared/production, payment, message, deployment,
 destructive, irreversible, or duplicate-sensitive effects without exact existing
 authority for the action, target, readback, cleanup, and non-duplication boundary.
+
+If product/source mutation begins after this final cycle starts, the cycle cannot
+return `GOAL VERIFIED`. Any still-safe Runner work is navigation only. Every
+overlapped Runner must return or be host-confirmed stopped, and every Runner-started
+product effect must reach its authored terminal/cleanup boundary or be established
+unable to mutate the target. Affected rows are `INCONCLUSIVE` because final
+attribution is unstable. A later Ralph attempt may start a wholly new Goal
+Verification Lead cycle with new fresh Runner invocations only after quiescence;
+this Lead does not dispatch remediation or rerun itself.
 
 ## Dispositions
