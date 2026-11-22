# Frontdesk completion note

The portal supports ticket ownership, agent and customer replies, private notes, working-time deadlines, pausing, reopening and inactivity closure. PostgreSQL supplies the event time and protects the append-only ticket history.

The brief leaves mid-ticket priority changes open. I chose to give the owner the new priority’s working-time allowance from the change. This can extend an outstanding target. Each new priority-change entry shows both priorities and both sets of deadlines so reviewers can see that effect.

## What remains

The missed-deadline view explains first-reply and resolution misses against the ticket’s current targets. Reconstructing every previous breach after a priority change or reopening would require tracking each deadline cycle separately. This version focuses on the agent inbox. Older records retain their original audit detail.

The inactivity command runs when someone opens the inbox or a ticket. An independent five-minute production schedule is unverified. The Windows launcher was updated to use the project's virtual environment and still needs a Windows smoke test.

## Checks

Two calendar tests and nine Django tests passed against a disposable local PostgreSQL 16 database. Coverage includes simultaneous claims, note privacy, immutable history, pause/resume, priority history, inactivity closure, reopening and missed deadlines after resolution. The hosted login page responded successfully on 22 November 2026. That check covered the prior deployment. The revised release still needs a hosted sign-in check after deployment.

## Deployment record

Live URL: https://frontdesk-owvy.onrender.com

Platform: Render Web Service with Render PostgreSQL 17 in Oregon. First deployed 21 November 2026.

The revised source includes a public database health check at /healthz. Publishing this revision, configuring external uptime monitoring for the review window, and verifying the production holiday calendar remain pending.
