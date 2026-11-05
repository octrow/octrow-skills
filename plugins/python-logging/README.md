# python-logging

**English** | [Русский](README.ru.md)

A skill that sets up, fixes or improves logging in a Python project.

## Install

```bash
claude plugin install python-logging@octrow-skills
npx skills add octrow/octrow-skills --skill python-logging -g
```

## What it does

- Sets one disk budget for all logs, with size rotation.
- Writes wide events: one JSON line per request, message or job.
- Masks secrets in log lines.
- Keeps records to one line, so journald does not split them.
- Adds tests that prove the cap.

## Ask

- "logs filled the disk, cap them at 1 GB"
- "I can't tell what happened to job 42 from the logs"
