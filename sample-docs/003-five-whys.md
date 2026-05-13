# Five Whys

An iterative root-cause analysis technique that walks from an observed symptom back to a systemic cause by repeatedly asking "why?" — applied in software debugging, incident response, and AI agent failure analysis to prevent whole classes of failure rather than patching individual symptoms.

## Key Concepts

- Iterative questioning to root cause — start from an observed problem, ask "why did this happen?", take the answer, and ask "why?" again; repeat until the cause is actionable at the system level. Typically about five iterations, but the number is a heuristic, not a rule.
- Toyota Production System origin — developed by Sakichi Toyoda at Toyota in the 1930s and formalized by Taiichi Ohno; now standard in lean manufacturing, Six Sigma, Kaizen, incident response, and software/AI engineering.
- Symptoms live on the surface, causes live deeper — a failing test, a hallucinated answer, or a toppled production service are symptoms; the technique exists because bugs rarely live where they surface.
- Stop criterion: actionable and systemic — stop when fixing the cause would prevent the whole _class_ of failure, not just this instance. The chain has gone far enough when the fix is both within scope and eliminates a category of future failures.
- End with a concrete change — every chain must produce a test, alert, schema constraint, prompt guardrail, eval case, or runbook; a chain with no resulting change was an exercise, not an investigation.
- Precision at step zero — the problem statement determines the quality of the chain. "The agent gave a wrong answer" is too vague; "The agent answered X when the correct answer per doc Y was Z, on input I" is workable.
- Evidence over speculation — each "why" must be anchored in logs, traces, evals, git history, or a reproducible test. A chain of plausible-sounding deductions produces a confident but wrong root cause. Especially dangerous in AI debugging, where every "why" has a confident-sounding answer available from the model itself.
- System facts, not blame — never name a person as the root cause (Toyota's foundational rule). Restate "because the engineer forgot to..." as "because there is no check that catches this before merge."
- Branch when causes are multiple — if two independent causes contribute, split the chain. Agent failures often have 2–3 contributing causes (bad retrieval _and_ weak prompt _and_ missing eval); force-fitting them into one chain loses two of the fixes.

## Application to AI Agent Development

5-Why is especially valuable in AI agent systems because agent failures are compositional — a wrong answer can come from prompt design, retrieval, tool selection, tool execution, model behavior, or evaluation gaps. Stopping at "the model got it wrong" routinely misdiagnoses issues that actually live in retrieval, data freshness, or tool contracts.

Candidate "why" axes for agent chains:

- _Data_ — freshness, chunking, indexing.
- _Retrieval_ — recall, ranking.
- _Context assembly_ — what was actually in the prompt.
- _Model_ — behavior on this prompt family.
- _Tools_ — contracts, error signaling.
- _Evaluation_ — did an eval exist that would have caught this?

A chain that never touches any of these axes often stops too early.

Worked example (retrieval failure):

- Symptom: the LLM returned a wrong answer.
- Why 1: the relevant document was missing from context.
- Why 2: the retrieval index did not contain it.
- Why 3: the nightly reindex job failed.
- Why 4: the job silently timed out on a large document batch.
- Why 5: there is no alerting on job duration or failure.

The first "why" points to a missing document (patch by hand); the fifth points to a missing observability layer (fixing it prevents an entire class of silent failures).

Other agent-specific patterns:

- Wrong tool selected → because tool descriptions overlap → because the tool schema was never reviewed against the agent's prompt.
- Hallucinated fact → because context did not include the source → because chunking strategy lost the heading → because ingestion pipeline stripped markdown.
- Agent loops → because it cannot tell success from failure → because the tool returns `200 OK` on invalid input.

In each case, the first-level "fix" (re-prompt, tweak, retry) leaves the underlying defect intact. This connects directly to [[harness-engineering]] — sensors that fail visibly rather than gracefully, and evaluators with real observation tools, are the structural fixes that 5-Why chains tend to surface.

## How to Apply

1. State the problem concretely, with inputs, observed output, and expected output.
2. Anchor each "why" in evidence. Ask _how do we know?_ before accepting an answer.
3. Follow the causal thread, not the blame thread. Restate person-centric answers as system facts.
4. Continue until the cause is both actionable and systemic. Three may be enough; seven may be required.
5. Branch when causes are genuinely multiple.
6. Close the loop with a concrete change (test, alert, schema constraint, prompt guardrail, eval, runbook).

## Common Mistakes

- Blaming people instead of systems — individual mistakes are symptoms of missing guardrails.
- Stopping too early — the first cause that feels satisfying is usually still a symptom. Gut-check: _if we fix only this, will the same class of problem recur?_
- Going too far — chains that reach "our company has the wrong culture" are technically true and practically useless; stop at the deepest cause your team can actually change.
- Reasoning without evidence — whiteboard 5-Why devolves into plausible-sounding deductions; every link needs a log line, trace, reproducible test, or direct observation.
- Biased or leading questions — "Why didn't the prompt include anti-hallucination instructions?" presupposes the fix. Prefer "Why did the model produce this specific output?"
- Single-perspective analysis — an engineer alone finds engineering causes; a PM alone finds requirements causes. For AI failures, run the chain with data, ML, product, and infra concerns represented.
- Forcing a single chain when causes are multiple.
- Treating 5-Why as paperwork — a chain with no resulting change is an exercise, not an investigation.

## Sources

- Applying the 5-Why Technique in Software and AI Agent Development — `digested-original/five-whys/5-why-in-software-and-ai-agent-development.md` (internal note, synthesizing Wikipedia's "Five whys"; Atlassian Incident Management "The power of 5 Whys"; Orcalean "How Toyota Utilizes the 5 Whys Method"; EasyRCA "5 Whys Analysis Pitfalls"; Lean Enterprise Institute "5 Whys"; FlowFuse "Five Whys Root Cause Analysis", 2025)

## Related Topics

- [[harness-engineering]]
