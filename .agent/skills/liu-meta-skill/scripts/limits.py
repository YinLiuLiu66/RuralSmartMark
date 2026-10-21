"""Single source of truth for skill budgets and DSH platform limits.

Budgets are estimated tokens using the English heuristic of ~4 characters per
token (inherited from yao-meta-skill; do not fork the math). Platform limits are
measured constants from the DSH runtime, not policy choices:

- ``dsh-compaction-tool-result-pruner`` (standard preset): thresholdChars 8192,
  headChars 4096, tailChars 1024.
- ``dsh-tool-skill``: DEFAULT_CATALOG_DESCRIPTION_MAX_LENGTH = 500.
"""

# Initial-load budgets, in estimated tokens. This local edition keeps the
# first two of yao's four tiers (library and governed are out of scope).
TIERS = {"scaffold": 700, "production": 1000}
INITIAL_LOAD_WARN = 2000

# The pruner counts the rendered ``skill`` tool result, not the file body.
# renderSkillContent wraps the body in <skill_content>/<skill_resources>/
# <skill_instructions>; measured 361 chars for a typical skill path, plus
# headroom for longer paths.
RENDERED_RESULT_LIMIT = 8192
RENDER_WRAPPER_RESERVE = 450
BODY_LIMIT = RENDERED_RESULT_LIMIT - RENDER_WRAPPER_RESERVE
BODY_WARN = BODY_LIMIT - 300

# Catalog descriptions are whitespace-collapsed, then cut to max - 3 + "...".
DESCRIPTION_MAX = 500
DESCRIPTION_WARN = 480
