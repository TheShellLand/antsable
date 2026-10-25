# AGENTS.md

# Git Tasks when commiting changes

- create a descriptive git commit using git diff 
- use the following specific format for all commits:

  [name of the ansible role] [Descriptive primary action/sentence]

  [A detailed description or paragraph explaining exactly what was changed and why.]

# Shared Agent Instructions

Before performing any task, select the shared skills directory:

1. If `/SKILLS` exists, use `/SKILLS`.
2. Otherwise, use `/tmp/SKILLS`. If it does not exist, run:

   ```sh
   git clone https://github.com/TheShellLand/SKILLS.git /tmp/SKILLS
   ```

Both paths are absolute and separate from this project. Reuse an existing directory; do not overwrite it or check
for a `.git` folder before running Git commands against it.

Run `git -C <skills-directory> pull --rebase` against the selected directory before searching for or reading skills.
Then read and follow its `AGENTS.md` in addition to this project's instructions. When using `/tmp/SKILLS`, treat
references to `/SKILLS` in the shared instructions as references to `/tmp/SKILLS`, including update and discovery steps.

Update the selected directory and discover and use relevant skills on every task, even if the instructions or skills
were read during an earlier task. If an update changes `AGENTS.md`, read the updated file before continuing.

If cloning or updating fails, report the failure and continue with available local skills unless the failure prevents
completing the task correctly. If the selected directory's `AGENTS.md` is missing, report that and continue using this
project's instructions and available tools.
