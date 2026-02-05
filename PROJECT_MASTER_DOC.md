# 📂 Project Master Documentation: AI Voice Video Editor

## 1. Project Overview & Philosophy

**Project Name:** AI Voice Video Editor (The Smart Editor)
**Core Concept:** A multimodal video editing tool that eliminates the complexity of timeline manipulation. It translates natural language (voice/text) into executable video editing actions using GenAI.
**Current State:** Advanced Prototype (Streamlit + MoviePy + Gemini 2.5 Flash).
**Target Audience:** Content creators (Shorts/Reels) seeking speed over granular control.

## 2. Technical Architecture (Current Stack)

- **Frontend:** Streamlit (Web-based UI).
- **Backend Logic:** Python 3.10+ (Compatible with 3.13 via `audioop_lts`).
- **Video Engine:** MoviePy & FFmpeg (Local processing).
- **AI Engine:** Google Gemini 2.5 Flash (Multimodal: Audio/Text -> JSON).
- **Audio:** `audiorecorder` component + Pydub.
- **Styling:** Custom CSS (`style.css`) for visual timeline and dark mode.

## 3. Workflow Logic

1.  **Input:** User uploads video -> System generates visual thumbnails (Timeline).
2.  **Command:** User speaks or types -> System captures input.
3.  **Processing:** Gemini analyzes raw audio/text -> Returns strict JSON Array.
4.  **Execution:** System parses JSON -> Applies MoviePy effects sequentially.
5.  **Output:** Exports optimized video (`libx264`/`aac`) to local storage.

## 4. The Development Roadmap (Phased Execution)

### 🚩 Phase 1: Stability & Foundation (Next 2 Weeks)

_Goal: Zero crashes, strict validation, and clear error handling._

- **JSON Validation:** Implement strict Schema validation (Pydantic) for AI output.
- **Error Handling:** No silent failures. Display raw error logs in debug mode.
- **Caching Strategy:** Hash-based caching for inputs to prevent redundant API calls.
- **Refactoring:** Split monolithic `app.py` into modular architecture (`ai_handler`, `media_engine`, `ui_utils`).
- **Testing:** Unit tests for non-UI logic (80% coverage).

### 🚩 Phase 2: Creator Features (Weeks 3-6)

_Goal: Support real-world creation scenarios (Reels/Shorts)._

- **Action Dictionary:** Add `concat`, `remove_silence`, `fade_in/out`, `crop_9:16`.
- **Preview System:** Allow 5s preview before full render.
- **Session Management:** Save/Load project state (Video + JSON + Settings).
- **Performance:** Optimize timeline generation (async/caching).

### 🚩 Phase 3: Desktop Product (Months 2-4)

_Goal: Distributable, offline-capable desktop application._

- **Decoupling:** Separate Core Engine from UI completely.
- **Packaging:** PyInstaller or Electron/Tauri wrapper.
- **Privacy:** Local LLM options or strict data controls.
- **Pro Export:** Bitrate control, 4K support, Presets.

## 5. Coding Standards (Enforced by RULES.md)

- **Modularity:** Max 20 lines per function, Max 300 lines per file.
- **Security:** No API keys in code (.env only).
- **Documentation:** All modules must have docstrings.
- **Type Hinting:** Use Python type hints for all function arguments/returns.

---

**End of Master Documentation.**
