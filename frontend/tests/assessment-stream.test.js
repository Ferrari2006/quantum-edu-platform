import test from 'node:test';
import assert from 'node:assert/strict';
import { scoreForm, comparison } from '../src/utils/assessment.js';
import { assessmentDemo } from '../src/data/assessmentDemo.js';
import { readRagStream } from '../src/utils/ragStream.js';

test('assessment rejects missing responses and reports decreases as percentage points', () => {
  assert.throws(() => scoreForm(assessmentDemo.forms.pre, {}), /全部/);
  const pre = scoreForm(assessmentDemo.forms.pre, {'pre-qubit': 0, 'pre-measure': 1});
  const post = scoreForm(assessmentDemo.forms.post, {'post-qubit': 0, 'post-measure': 0});
  assert.equal(comparison(pre, post).change_percentage_points, -50);
  assert.equal(post.responses[0].concept_id, 'classical-bit-and-qubit');
});

function response(text) {
  const bytes = new TextEncoder().encode(text);
  return new Response(new ReadableStream({ start(controller) {
    for (const byte of bytes) controller.enqueue(Uint8Array.of(byte));
    controller.close();
  }}));
}
test('stage stream handles UTF-8 and frame boundaries split at every byte', async () => {
  const events = [];
  await readRagStream(response('event: step\ndata: {"label":"检索"}\n\nevent: result\ndata: {"answer":"答案"}\n\n'), (...args) => events.push(args));
  assert.deepEqual(events, [['step', {label:'检索'}], ['result', {answer:'答案'}]]);
});
test('stage stream distinguishes server errors and incomplete answers', async () => {
  await assert.rejects(readRagStream(response('event: error\ndata: {"message":"未配置服务"}\n\n'), () => {}), /未配置/);
  await assert.rejects(readRagStream(response(': heartbeat\n\n'), () => {}), /Incomplete/);
});
