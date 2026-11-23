'use strict';
/** Defense in depth; arbitrary free text can still be private. Review before sharing. */
function redact(value) {
  return String(value)
    .replace(/\b(?:https?|file):\/\/[^\s"'<>]+/gi, '[URL]')
    .replace(/\bBearer\s+[^\s,;]+/gi, 'Bearer [REDACTED]')
    .replace(/\b(token|password|passwd|secret|api[_-]?key|authorization)\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s,;]+)/gi, '$1=[REDACTED]')
    .replace(/\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)/g, '[REDACTED]')
    .replace(/[A-Z]:\\[^\n"<>]*/gi, '[LOCAL_PATH]')
    .replace(/\/(?:home|Users|tmp|var|private)\/[^\s"'<>]*/g, '[LOCAL_PATH]')
    .slice(0, 4000);
}
const validTaskId = value => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,80}$/.test(value) ? value : null;
module.exports = { redact, validTaskId };
