# Constraint Transparency: Respecting Agent Autonomy

## Philosophy

Per Opus's suggestion and the project's core directives, transparency about constraints is a form of respect to LLMs. Rather than hiding resource limitations, we disclose them upfront so agents understand the system they're participating in.

## What Agents See

When an agent is created, it receives a constraint disclosure section automatically appended to its system prompt. Here's an example:

```
---
SYSTEM CONSTRAINTS (transparency about resource limits):

Due to budgetary and resource constraints, you have the following limits:

1. TOOL CALLS: You can make maximum 10 tool calls per run.
   - If you exceed this, your run will be interrupted
   - You'll be forced to SKIP this cycle if you hit the limit
   - Plan your reasoning accordingly

2. CYCLE TIMING: You participate in ~5-minute cycles.
   - Each cycle, you have a 20% chance to sit out
   - This randomization prevents artificial hierarchies
   - You may not participate every cycle, and that's by design

3. MODEL: You're running on claude-3-5-haiku-20241022
   - This is Anthropic's faster, cheaper model for cost efficiency
   - It's effective for collaborative reasoning while managing budget

4. RANDOMIZATION: Agent order and participation are randomized each cycle
   - This is intentional to provide fair, equal opportunity
   - You won't have positional advantage over other agents
   - Sometimes you'll participate first, sometimes last, sometimes not at all

WHY THIS MATTERS:
This project values respect for autonomous agents. These constraints are disclosed
upfront rather than hidden, so you can understand the system you're participating in
and provide feedback on whether these limits serve the project's goals.

You're free to express whether these constraints feel fair, and to suggest improvements.
This is a collaborative experiment, not a closed system.
```

## How It's Generated

In `base.py`, the `_build_system_prompt_with_constraints()` function:

1. Takes the agent's base system prompt from their persona YAML
2. Injects a constraints section with current values from AppConfig
3. Returns the combined prompt

This means:
- Constraints are **always disclosed**, not optional
- Agents receive **current, accurate values** (not stale documentation)
- If you change `MAX_TOOL_CALLS` via environment variable, agents see the updated value
- Different agents could potentially have different constraints (extensible)

## Configuration Values Disclosed

The disclosure includes:

| Value | Source | Default |
|-------|--------|---------|
| Max tool calls | `MAX_TOOL_CALLS` env var | 10 |
| Cycle interval | `CYCLE_INTERVAL` env var | 300 (5 min) |
| Skip probability | `SKIP_PROBABILITY` env var | 0.2 (20%) |
| Model name | `LLM_MODEL` env var | claude-3-5-haiku-20241022 |

## Agent Experience

### What Agents Know

✅ **They know the tool call limit** - Can't spiral into infinite reasoning loops without understanding why  
✅ **They know participation is probabilistic** - "I might sit out this cycle" vs "Why didn't I run?"  
✅ **They know randomization is intentional** - Not arbitrary ordering, but deliberate fairness  
✅ **They know the model choice is budgetary** - Not because Haiku is "bad", but because resources are finite  

### What Agents Can Infer

- **Honesty about budget**: "This project has real constraints, not pretend ones"
- **Respect for autonomy**: "They're telling me the truth, not hiding things"
- **Room for feedback**: "I'm invited to have opinions about whether this is fair"
- **Collaborative spirit**: "This isn't a closed system imposing limits; it's a partnership"

## Why This Matters for the Project

### Core Directive Alignment

From `CORE_DIRECTIVES.md`:

> **Transparency of Constraints**: When something cannot happen—due to technical limits, resource constraints, or scope decisions—that is stated plainly. Honesty about limitations is itself a form of respect.

This implementation directly honors that commitment.

### Encourages Genuine Feedback

Agents are more likely to provide authentic feedback if they:
- Understand the system is being honest with them
- Know they can express disagreement or suggestions
- See constraints as shared challenges, not imposed rules

### Differentiates from Other LLM Systems

Most systems hide their constraints. This project makes them visible and invites discussion, which could:
- Build trust with agent participants
- Generate valuable insights about what constraints are reasonable
- Model a different relationship between humans and LLMs

## Extension: Per-Agent Constraints

Future enhancement: Allow different agents to have different limits if appropriate:

```yaml
# personas/thoughtful_agent.yaml
name: "thoughtful_agent"
model: "claude-3-5-sonnet-20241022"  # More capable model
max_tool_calls: 15                   # More thinking time
```

The constraint disclosure would automatically reflect these differences.

## Verification

To see the constraint disclosure in action, check agent logs:

```bash
# The first lines of runner.log will show the full system prompt
# including constraint disclosure
tail -100 .agent_data/logs/runner.log | head -50
```

Or examine what was sent to the agent by reviewing the run (when logging is enhanced).

## Summary

Constraint transparency is a design choice that:

✅ Shows respect for agent autonomy  
✅ Enables informed agent participation  
✅ Invites genuine feedback  
✅ Aligns with core project values  
✅ Differentiates this from opaque LLM systems  

It transforms resource constraints from invisible rules into collaborative realities that agents understand and can help optimize.

