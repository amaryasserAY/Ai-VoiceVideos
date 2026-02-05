# ⚠️ WARNING: Sync Required

This RULES.md file must always remain **fully synchronized** with `.cursorrules`.  
Any changes in `.cursorrules` must be reflected here immediately.  
Failure to sync may cause AI context inconsistencies or enforcement errors.

## ⚡ Project Rules (Global Standard)

## 📁 Required Files

Every project must include the following:

- README.md → Human-facing docs (setup, features, roadmap)
- AI_NOTES.md → AI-facing context (rules, goals, session logs)
- RULES.md → Human-readable global rules
- .cursorrules → Machine-readable enforcement rules

✅ These files are auto-created for every new project.  
✅ Quality checks are required before project activation.  
✅ Global standards are enforced in all projects.

## 🎯 Workflow Rules

- Start every session → Read AI_NOTES.md first (single source of truth).
- During session → Keep context short (use structured bullet points, avoid long paragraphs).
- End every session → Update:
  - AI_NOTES.md (always, AI memory + compression)
  - README.md (only if user-facing changes occurred)
  - Confirm RULES.md + .cursorrules are synced.
- File Completeness Check → Before ending, verify all required files are updated.

## 🔒 Security Rules

- Never commit .env files or secrets.
- Validate all inputs before processing.
- Sanitize database queries (prevent SQL injection).
- Enforce HTTPS in production.
- Use secure authentication (JWT with expiration).
- Rate limiting + error handling must be implemented.

## 📏 Code Quality Standards

- Max 20 lines per function (single responsibility).
- Max 300 lines per file (maintainability).
- Use meaningful variable names (no a, b, x).
- Follow DRY principle (Don’t Repeat Yourself).
- Use JSDoc for complex logic + APIs.
- Prefer TypeScript interfaces for type safety.

## 🧪 Testing Rules

- Use TDD when possible (write tests before features).
- Maintain 80%+ coverage on critical paths.
- Test both success and error scenarios.
- Mock external dependencies in unit tests.
- Always run tests before committing code.

## 📝 Documentation Rules

- Update README.md for human-facing changes.
- Update AI_NOTES.md for AI-facing memory.
- Keep RULES.md in sync with .cursorrules.
- Document API endpoints with examples.
- Add troubleshooting steps for setup issues.

## 🔄 Version Control Rules

- Use feature branches (feature/xyz).
- Never commit directly to main.
- Follow conventional commits (feat:, fix:, docs:, etc.).
- Tag releases with semantic versioning.
- Squash commits before merging.

## 📊 Logging & Error Handling

- Use structured logging with consistent format.
- Apply error codes for all error types.
- Log security events (failed logins, suspicious activity).
- Implement graceful degradation for failures.
- Use monitoring + alerts (no silent failures).

## 🚀 Performance & Monitoring

- Enforce API response time budgets.
- Use caching, pagination, indexing for performance.
- Optimize queries (avoid N+1 problems).
- Implement health checks for services.
- Enable lazy loading on frontend.

## ♿ Accessibility & UX

- Follow WCAG 2.1 guidelines.
- Use semantic HTML.
- Support keyboard navigation for all UI.
- Add alt text to all images/media.
- Ensure color contrast meets standards.
- Test with screen readers when possible.
