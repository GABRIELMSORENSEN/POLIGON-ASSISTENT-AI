# Polygon Shared Memory and Knowledge Layer

## Goal

Polygon should become more useful across conversations without requiring the user to repeat their identity, preferences, workflows, project context, or previously learned facts. Memory is shared by the Polygon application, not owned by an individual model or chat session.

## Memory layers

1. **User profile** — stable preferences and working style: language, tone, formatting, preferred tools, accessibility choices, recurring constraints. Examples must be editable and deletable by the user.
2. **Project memory** — facts, architecture, conventions, decisions, file locations, test commands, known issues, and current milestones scoped to a project such as Polygon, Unity/VRChat, or video editing.
3. **Conversation memory** — concise summaries and unresolved tasks from previous chats, with links to their originating conversation where available.
4. **Shared knowledge base** — reusable technical notes, verified procedures, documentation extracts, and lessons learned. Store source, date, confidence, scope, and version.
5. **Session context** — temporary information for the active chat; it must not silently become permanent memory.

## Cross-model behavior

- Every model adapter receives a permission-filtered context packet from the same Polygon memory service.
- The packet is assembled for the current task: global profile + relevant project memory + selected knowledge snippets + current session.
- Models do not automatically see every private conversation or every stored fact. Retrieval is relevance-based and respects project boundaries and privacy settings.
- Model-specific context adapters may summarize or format the packet for each provider, but must not create incompatible copies of the user's profile.
- New insights produced by any model can be proposed to the shared memory service. They are not accepted as facts merely because a model asserted them.

## Learning and quality controls

- After a conversation or meaningful task, Polygon may propose concise memory updates: preference, confirmed fact, project decision, reusable procedure, or unresolved task.
- Record provenance (source conversation/task, model/provider, timestamp), confidence, and whether the user confirmed it.
- Resolve conflicts by preserving both claims with dates/sources until the user or stronger evidence resolves them. Never silently overwrite a confirmed fact.
- Knowledge learned from one provider can be shared with others only as a sourced note or validated procedure, not as a claim that the other model's neural weights were trained or improved.
- External documentation and web research must retain citations/URLs, retrieval date, version, and license/usage restrictions where applicable.
- Code and operational lessons should be tested where practical before being promoted from a draft note to verified knowledge.

## User controls

- Inspect, search, edit, pin, export, and delete memories.
- Toggle memory globally, per project, and per provider.
- Mark content as temporary / do not remember.
- Exclude sensitive categories and private projects from cloud context.
- Set retention limits and clear a conversation's derived memory.
- Show which memories were used in a response and allow correction ("that's wrong", "use this instead").
- Local-first storage by default; encrypted sync between desktop and Android when the user enables pairing. Cloud providers receive only the context required for the selected task.

## Suggested data model

- `memory_items`: id, type, scope, subject, content, tags, confidence, status, source_ref, source_provider, created_at, updated_at, expires_at, user_confirmed, sensitivity.
- `memory_links`: from_id, to_id, relation, created_at.
- `knowledge_sources`: id, title, url_or_file_ref, publisher, version, retrieved_at, license, checksum.
- `memory_audit`: event_id, item_id, action, actor, timestamp, reason.
- `project_spaces`: id, name, root_paths, privacy_mode, memory_policy.

## Retrieval and context assembly

1. Identify active project and task.
2. Retrieve relevant profile preferences and project facts.
3. Retrieve a small ranked set of knowledge items using keyword and semantic search.
4. Filter by sensitivity, user settings, provider permissions, and cloud/offline mode.
5. Deduplicate, resolve known conflicts, and attach source references.
6. Enforce a context budget; prioritize confirmed preferences and current project decisions.
7. Record which memory IDs were actually used.

## Important distinction

Shared memory makes different models behave consistently and lets them reuse verified knowledge. It does **not** merge their model weights, make one provider's neural network learn another's training, or guarantee that every model has identical reasoning ability. The improvement comes from better persistent context, retrieval, tools, and validated knowledge.

## Implementation order

1. Define storage schema and memory service API.
2. Add local SQLite storage and migration/versioning.
3. Add context assembler to desktop agent and provider adapters.
4. Add memory review UI and per-project controls.
5. Sync approved memory to paired Android clients.
6. Add retrieval evaluation tests: relevance, leakage between projects, conflict handling, deletion, offline behavior, and provider context filtering.
