---
name: kenaz-confirm
description: >
  Draft the KENAZ Level 2 application-confirmation email for whoever has newly
  applied, and put it in Gmail drafts ready to send. Pulls the new submission
  from the Formspree dashboard, renders the branded email with that person's own
  answers echoed back, creates the Gmail draft, and adds them to the MailerLite
  applicants group. Use when Yaniv says "someone applied", "new signup",
  "new application", "confirm the new applicant", "draft the confirmation",
  or runs /kenaz-confirm.
---

# KENAZ Level 2 — application confirmation

One applicant, one draft. Nothing is ever sent by this skill; Yaniv reviews and
sends every draft himself.

## The process this email sits inside

Applying is **not** acceptance and **not** a place held. Every applicant books a
discovery call with **Yaniv** to find out if it's the right fit, for them and for
us. Payment and registration details only follow a yes on both sides.

**Booking link** (goes in every confirmation, and it's the applicant's next
action — they don't wait for us to write):

    https://cal.com/yaniv-rose-m6ewam/level-2-discovery-call

This exists because someone applied impulsively while overwhelmed and already
booked onto other retreats — a fast yes she'd likely have regretted. The call is
there so the decision gets made consciously, and so each applicant feels seen
rather than processed. Rejections are expected to be rare; the value is in
hearing where each person actually is.

So the confirmation must never promise payment details next, never imply
acceptance, and never push for a quick decision. Receipt acknowledged → the
booking button → their own answers quoted back → what happens next (they book /
we read it personally before the call / we decide together, and only then
payment, Early Bird until 28 August 2026, 14 places). Signed **Patricia & Yaniv**. Templates live in
`emails/confirmation.html.tmpl` and `emails/confirmation.txt.tmpl` — edit those,
not the rendered output.

## Steps

### 1. Get the new submission from Formspree

Free plan: no API, no CSV automation — read it out of the dashboard with Chrome.

```
https://formspree.io/forms/mrevwwje/submissions
```

Applications have `_subject` = **New KENAZ Level 2 application**. Rows saying
"waitlist signup" are the old form — ignore them. Ignore `spike77707@gmail.com`
(Yaniv's own test). Anyone already in `emails/applicants.csv` is done already.

Click the row to open the detail panel, then extract it with JS rather than
transcribing from a screenshot — the answers get quoted back verbatim, so a
typo is a typo in front of the applicant:

```js
window.__grab=()=>{const ps=[...document.querySelectorAll('div')].filter(e=>e.innerText&&e.innerText.includes('journey_status')&&e.innerText.includes('room_preference'));if(!ps.length)return 'NO PANEL';const t=ps[ps.length-1].innerText;const keys=['_subject','anything_else','certification','email','expectations','facilitation_challenges','journey_status','main_drive','name','room_preference','session_reports','location_timezone','call_availability'];const idx=keys.map(k=>({k,i:t.indexOf('\n'+k+'\n')})).filter(o=>o.i>=0).sort((a,b)=>a.i-b.i);const out={};idx.forEach((o,n)=>{const start=o.i+o.k.length+2;const end=n+1<idx.length?idx[n+1].i:t.length;out[o.k]=t.slice(start,end).replace(/\n*_status[\s\S]*$/,'').trim();});return JSON.stringify(out);};window.__grab()
```

Long answers can exceed one tool result — fetch the rest with
`window.__grab().slice(1000)` rather than accepting a truncated quote.

> **Do not click the top-right of the Formspree page.** The sign-out icon sits
> at roughly (1458, 43), right where a panel close button looks like it should
> be. Clicking it ends the session and Yaniv has to sign in again by hand. Close
> the detail panel with its own ✕ inside the panel, or just navigate away.

If the session is signed out, ask Yaniv to sign in. Never enter credentials.

### 2. Render the email

```bash
echo '<the JSON from step 1>' | python3 emails/new_applicant.py
```

Appends to `emails/applicants.csv` (skips anyone already there), re-renders
everything into `emails/out/`, and prints the TO / SUBJECT / body paths.
Both files are gitignored — they hold real personal answers, never commit them.

### 3. Answer anything they actually asked

Read their `anything_else` and free-text answers before drafting. If they asked
a direct question, answer it in a short highlighted paragraph placed after the
greeting, before the standard body — a form confirmation that ignores a question
reads worse than no confirmation. Precedent: Seraphina asked whether she could
pay a deposit now to hold the private bungalow. Her email says yes, a deposit is
what holds a place — and that we'd like to talk first, framed as looking together
at whether the timing is right, not as a hurdle.

Never invent specifics. Deposit amounts, payment methods and call scheduling are
not settled — say the call comes first and details follow, or ask Yaniv. If they
ask to pay now, the honest answer is yes a deposit holds a place, and also that
we'd like to talk first — point them at the booking link.

### 4. Create the Gmail draft

`mcp__claude_ai_Gmail__create_draft` with:

- `to` — their email
- `subject` — `We have your Level 2 application, <First name>` (drop the name if
  the form's optional name field was left blank; never guess a name from an
  email address)
- `htmlBody` — contents of the `.body.html` file
- `body` — contents of the `.txt` file, minus its leading `To:`/`Subject:` lines

### 5. Add them to MailerLite

`mcp__mailerlite__add_subscriber` — group **`194793925566793242`**
(`KENAZ Level 2 – Applicants`), with email and name.

### 6. Tell Yaniv what's waiting

Report who the draft is for, anything personal you added, and remind him to
**switch the From address to `me@yanivrose.com`** before sending — drafts default
to the connected account (spike77707@gmail.com), and the API can't set the alias.

## Sender facts

`info@kenazportal.com` is what the site promises applicants, but Yaniv has no
access to that mailbox and `kenazportal.com` is not in his GoDaddy account, so it
can be neither the from-address nor an authenticated domain on his side.
`me@yanivrose.com` is the sender: SPF, DKIM and DMARC on `yanivrose.com` are all
in place. The email footer still gives `info@kenazportal.com` as the address for
questions, which is correct — that inbox is Patricia's.
