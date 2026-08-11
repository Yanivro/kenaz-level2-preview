#!/usr/bin/env python3
"""Build personalised KENAZ Level 2 application-confirmation emails.

Reads a Formspree CSV export of the application form (endpoint mrevwwje) and
writes one .html + one .txt per applicant into emails/out/, plus an index.html
contact sheet so you can eyeball every message before anything is sent.

    python3 emails/build.py path/to/formspree-export.csv

Nothing is sent from here. The output is what you paste (or feed to a sender).
emails/out/ holds real personal answers - it is gitignored.
"""

import csv
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# Form field -> label shown back to the applicant, in the order they were asked.
FIELDS = [
    ("room_preference", "Room preference"),
    ("session_reports", "Level 1 session reports"),
    ("certification", "Level 1 certification"),
    ("journey_status", "Where you are in your journey"),
    ("main_drive", "What's drawing you to Level 2"),
    ("expectations", "What you hope to walk away with"),
    ("facilitation_challenges", "Your biggest challenges in facilitation right now"),
    ("anything_else", "Anything else you wanted us to know"),
    ("location_timezone", "Where you are"),
    ("call_availability", "When you're usually free to talk"),
]

SUBJECT = "We have your Level 2 application, {first}"
PREHEADER = "Your application is in. We'll be in touch to book a discovery call."


def norm(key):
    """Formspree exports headers as-is, but casing/spacing can drift."""
    return re.sub(r"[^a-z0-9]", "", (key or "").lower())


def pick(row, *names):
    keys = {norm(k): k for k in row}
    for n in names:
        k = keys.get(norm(n))
        if k and (row.get(k) or "").strip():
            return row[k].strip()
    return ""


def first_name(name):
    """Name is optional on the form. Never guess one from the email address -
    a wrong name in the greeting is worse than no name."""
    name = (name or "").strip()
    if not name:
        return ""
    part = name.split()[0]
    return part[:1].upper() + part[1:]


def answers_html(row):
    blocks = []
    for key, label in FIELDS:
        val = pick(row, key)
        if not val:
            continue
        body = "<br>".join(html.escape(line) for line in val.splitlines() if line.strip())
        blocks.append(
            '<div style="padding:14px 0;border-top:1px solid #ececec;">'
            '<div style="font-family:Raleway,Helvetica,Arial,sans-serif;font-size:11px;'
            'font-weight:400;letter-spacing:.12em;text-transform:uppercase;color:#737373;'
            'padding-bottom:5px;">' + html.escape(label) + "</div>"
            '<div style="font-family:Raleway,Helvetica,Arial,sans-serif;font-weight:300;'
            'font-size:15px;line-height:1.7;color:#212121;">' + body + "</div></div>"
        )
    return "\n".join(blocks)


def answers_text(row):
    out = []
    for key, label in FIELDS:
        val = pick(row, key)
        if not val:
            continue
        out.append("\n" + label.upper())
        for line in val.splitlines():
            if line.strip():
                out.append("  " + line.strip())
    return "\n".join(out)


def slug(email, i):
    return "%02d-%s" % (i, re.sub(r"[^a-z0-9]+", "-", (email or "unknown").lower()).strip("-"))


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 emails/build.py <formspree-export.csv>")

    with open(sys.argv[1], newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    html_tmpl = open(os.path.join(HERE, "confirmation.html.tmpl"), encoding="utf-8").read()
    txt_tmpl = open(os.path.join(HERE, "confirmation.txt.tmpl"), encoding="utf-8").read()
    os.makedirs(OUT, exist_ok=True)

    sheet, built = [], 0
    for i, row in enumerate(rows, 1):
        email = pick(row, "email", "_replyto")
        if not email:
            print("  skip row %d - no email" % i)
            continue
        first = first_name(pick(row, "name"))
        greeting = ("Hi %s," % first) if first else "Hi there,"
        subject = SUBJECT.format(first=first) if first else "We have your Level 2 application"

        body_html = (html_tmpl
                     .replace("{{GREETING}}", html.escape(greeting))
                     .replace("{{PREHEADER}}", html.escape(PREHEADER))
                     .replace("{{ANSWERS}}", answers_html(row)))
        body_txt = (txt_tmpl
                    .replace("{{GREETING}}", greeting)
                    .replace("{{ANSWERS}}", answers_text(row)))

        base = slug(email, i)
        with open(os.path.join(OUT, base + ".html"), "w", encoding="utf-8") as f:
            f.write("<!doctype html><meta charset=utf-8><title>%s</title>\n"
                    "<!-- To: %s | Subject: %s -->\n%s" %
                    (html.escape(email), html.escape(email), html.escape(subject), body_html))
        # .body.html is the bare markup to paste into a Gmail draft's htmlBody -
        # no doctype, no wrapper, nothing an email client would choke on.
        with open(os.path.join(OUT, base + ".body.html"), "w", encoding="utf-8") as f:
            f.write(body_html)
        with open(os.path.join(OUT, base + ".txt"), "w", encoding="utf-8") as f:
            f.write("To: %s\nSubject: %s\n\n%s" % (email, subject, body_txt))

        sheet.append((email, subject, base, body_html))
        built += 1

    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write("<!doctype html><meta charset=utf-8><title>KENAZ confirmations "
                "(%d)</title><body style='margin:0;background:#efefef;"
                "font-family:Raleway,Helvetica,Arial,sans-serif'>" % built)
        for email, subject, base, body in sheet:
            f.write("<div style='max-width:640px;margin:26px auto 0;font-size:12px;"
                    "color:#555'><b>To:</b> %s &nbsp;|&nbsp; <b>Subject:</b> %s "
                    "&nbsp;|&nbsp; <a href='%s.txt'>plain text</a></div>%s" %
                    (html.escape(email), html.escape(subject), base, body))
        f.write("</body>")

    print("built %d email(s) -> %s" % (built, OUT))
    print("preview: open %s" % os.path.join(OUT, "index.html"))


if __name__ == "__main__":
    main()
