require('ts-node/register');
const test = require('node:test');
const assert = require('node:assert/strict');
const { Security } = require('../src/security.ts');

test('blocks eval case-insensitively', () => {
  assert.throws(() => Security.validateInput('Eval("2+2")'));
});

test('blocks unicode full-width eval', () => {
  assert.throws(() => Security.validateInput('ｅｖａｌ("2+2")'));
});

test('blocks zero-width space bypass', () => {
  assert.throws(() => Security.validateInput('e\u200bval("2+2")'));
});

test('blocks prototype pollution attempts', () => {
  assert.throws(() => Security.validateInput('__proto__'));
  assert.throws(() => Security.validateInput('constructor'));
});

test('allows safe input', () => {
  assert.doesNotThrow(() => Security.validateInput('safe_input()'));
});

test('returns normalized string', () => {
  const result = Security.validateInput('ｆｏｏ');
  assert.equal(result, 'foo');
});

test('allows JSON punctuation', () => {
  assert.doesNotThrow(() => Security.validateInput('{"a": [1,2]}'));
});

test('sanitizePath blocks traversal', () => {
  assert.throws(() => Security.sanitizePath('../secret'));
});

test('safeEval executes harmless code', () => {
  assert.equal(Security.safeEval('1 + 1'), 2);
});

test('safeEval blocks dangerous code', () => {
  assert.throws(() => Security.safeEval('eval("2+2")'));
});
