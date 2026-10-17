<p align="center">
  <img src="assets/banner.png" alt="1v1: Builder vs Breaker for Claude Code" width="100%">
</p>

# 1v1: Builder vs Breaker

A Claude Code skill where one subagent builds the code and a separate subagent attacks the running result and can only return failing tests. Use it for hard or high-stakes tasks.

📄 **[Read the full report](1v1-report.pdf)**

## Install

**Claude Code:** copy the `1v1` folder into `~/.claude/skills/`.

**claude.ai:** zip the `1v1` folder, then go to Customize → Skills → Add → Upload a skill.

## Use

Type `/1v1`, or say things like "make sure it actually works" or "stress test this".

## License

MIT