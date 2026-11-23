'use strict';
const { parseEvent } = require('../src/core/task-events');
/** Bounded, UTF-8 safe stream framing; never JSON substring scraping. */
function createTaskStream({ taskId, onEvent, maxLine = 1024 * 1024 }) {
  let seq = 0, terminal = null, invalid = false;
  function attach(stream, kind) {
    let buffer = '', dropping = false;
    stream.setEncoding('utf8');
    const line = value => {
      const event = kind === 'stdout' && parseEvent(value);
      if (!event) {
        try { if (kind === 'stdout' && JSON.parse(value)?.schema === 'zsmm.task') invalid = true; } catch {}
        onEvent({ type: kind, line: value }); return;
      }
      if (event.task_id !== taskId || event.seq !== seq + 1 || terminal) {
        invalid = true;
        onEvent({ type: 'protocol-error', error: 'Task event identity/sequence mismatch' });
        return;
      }
      seq = event.seq;
      if (event.type === 'done') terminal = event;
      onEvent({ type: 'protocol', event });
    };
    stream.on('data', chunk => {
      for (const part of chunk.split(/(?<=\n)/)) {
        const ended = part.endsWith('\n');
        if (!dropping) buffer += part;
        if (buffer.length > maxLine) {
          buffer = ''; dropping = true; invalid = true;
          onEvent({ type: 'protocol-error', error: 'Task output line exceeds limit' });
        }
        if (ended) {
          if (!dropping) line(buffer.replace(/\r?\n$/, ''));
          buffer = ''; dropping = false;
        }
      }
    });
    stream.on('end', () => { if (buffer && !dropping) line(buffer); });
  }
  return { attach, result: () => ({ terminal, invalid }) };
}
module.exports = { createTaskStream };
