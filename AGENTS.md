# AGENTS.md

## Commit messages

When asked to create a commit, inspect `git diff` and write a descriptive message based on the actual changes.
Use the Ansible role name as the scope; otherwise, choose the best-fitting scope for the changes.

Use this format for every commit (angle brackets indicate placeholders and are not literal):

```text
[role name or best-fitting scope] Descriptive primary action/sentence

A detailed paragraph explaining exactly what changed and why
```

# Shared Agent Instructions

## Select the shared skills directory

At the start of every task, select one shared skills directory:

1. If `/SKILLS` exists, use `/SKILLS`.
2. Otherwise, use `/tmp/SKILLS`. If it does not exist, run:

   ```sh
   git clone https://github.com/TheShellLand/SKILLS.git /tmp/SKILLS
   ```

Both paths are absolute and separate from this project. Reuse an existing directory without overwriting it or
checking for a `.git` folder before running Git commands against it. In the steps below, `<skills-directory>` means
the selected path. Treat references to `/SKILLS` in shared instructions as references to that path, including update
and discovery steps.

## Prepare and execute each task

Perform this workflow once per task, even if instructions or skills were read during an earlier task:

1. Run `git -C <skills-directory> pull --rebase` before searching for or reading skills.
2. Read and follow the selected directory's updated `AGENTS.md` in addition to this project's instructions.
3. Recursively discover `SKILL.md` files in both the current project and the selected shared directory.
4. Inspect skill names and descriptions, then read each applicable skill and its required references before
   executing the task. Resolve relative references from the skill's directory.
5. Execute the task using the applicable preparation, execution, and verification requirements. If no skill applies,
   follow the project and shared instructions.
6. Before reporting completion, verify that actual tool calls and results support compliance with those requirements.

## Handle preparation failures

If cloning or updating fails, report the failure and continue with available local skills unless the failure prevents
completing the task correctly. If the selected directory's `AGENTS.md` is missing, report that and continue using
this project's instructions and available tools. Do not silently skip required steps or claim full compliance when
a requirement could not be completed.
