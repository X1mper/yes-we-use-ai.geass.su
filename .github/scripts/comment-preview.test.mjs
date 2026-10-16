import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { publishPreview, resolvePreview } from './comment-preview.mjs';

const repository = 'X1mper/yes-we-use-ai.geass.su';
const root = `/repos/${repository}`;
const sha = 'a'.repeat(40);
const marker = '<!-- pr-browser-preview -->';
const bot = { login: 'github-actions[bot]', type: 'Bot' };

function fixture(change = () => {}) {
  const pr = { number: 7, state: 'open', base: { ref: 'main', repo: { id: 100 } }, head: { sha, repo: { id: 101 } } };
  const state = {
    repo: { id: 100, full_name: repository },
    workflow: { id: 200, path: '.github/workflows/pr-preview.yml', state: 'active' },
    run: { id: 300, repository: { id: 100 }, workflow_id: 200, event: 'pull_request', status: 'completed',
      head_sha: sha, head_repository: { id: 101 }, conclusion: 'success', run_attempt: 1, pull_requests: [{ number: 7 }] },
    pulls: { 7: pr }, associated: [pr],
    artifacts: [{ id: 400, name: 'browser-preview', expired: false, size_in_bytes: 4096 }],
    pages: [[]],
  };
  change(state);
  const calls = [], writes = [], pullReads = {};
  const request = async (endpoint, options = {}) => {
    const method = options.method || 'GET';
    calls.push({ endpoint, method });
    if (method !== 'GET') {
      assert.ok((method === 'POST' && endpoint === `${root}/issues/7/comments`)
        || (method === 'PATCH' && endpoint === `${root}/issues/comments/500`), 'unexpected write target');
      writes.push({ endpoint, method, body: options.body.body });
      return { id: 500 };
    }
    let result;
    if (endpoint === root) result = state.repo;
    else if (endpoint === `${root}/actions/workflows/pr-preview.yml`) result = state.workflow;
    else if (endpoint === `${root}/actions/runs/300`) result = state.run;
    else if (endpoint.startsWith(`${root}/pulls?state=open&base=main&per_page=100&page=`)) {
      const page = Number(new URL('https://api.github.com' + endpoint).searchParams.get('page'));
      result = state.associatedPages ? state.associatedPages[page - 1] || [] : state.associated;
    }
    else if (endpoint === `${root}/actions/runs/300/artifacts?per_page=100`) result = { artifacts: state.artifacts };
    else if (endpoint.startsWith(`${root}/pulls/`)) {
      const number = Number(endpoint.slice(`${root}/pulls/`.length));
      pullReads[number] = (pullReads[number] || 0) + 1;
      result = number === 7 && pullReads[number] > 1 && state.fresh ? state.fresh : state.pulls[number];
    } else if (endpoint.startsWith(`${root}/issues/7/comments?`)) {
      const page = Number(new URL('https://api.github.com' + endpoint).searchParams.get('page'));
      result = state.pages[page - 1] || [];
    } else assert.fail('Unexpected API request: ' + endpoint);
    assert.notEqual(result, undefined, 'missing fixture');
    return structuredClone(result);
  };
  return { state, calls, writes,
    resolve: () => resolvePreview({ request, repository, runId: 300, log: () => {} }),
    run: (expectedNumber = 7) => publishPreview({ request, repository, runId: 300, expectedNumber, log: () => {} }) };
}

function oldComment(run = 299, attempt = 1) {
  return { id: 500, user: bot, body: `${marker}\n<!-- run:${run} attempt:${attempt} -->\nold preview` };
}

async function skipped(change) {
  const f = fixture(change);
  assert.equal((await f.run()).skipped, true);
  assert.equal(f.writes.length, 0);
  return f;
}

test('fork PR gets a metadata-only artifact link with commit ID', async () => {
  const f = fixture(s => {
    s.artifacts[0].archive_download_url = 'https://evil.invalid/not-used';
    s.artifacts[0].pr_number = 999;
    s.pulls[7].title = 'malicious markdown ](https://evil.invalid)';
  });
  assert.equal((await f.run()).commented, true);
  assert.equal(f.writes[0].method, 'POST');
  assert.match(f.writes[0].body, /actions\/runs\/300\/artifacts\/400/);
  assert.match(f.writes[0].body, /aaaaaaa/);
  assert.doesNotMatch(f.writes[0].body, /evil|999/);
  assert.ok(f.calls.every(c => c.endpoint.startsWith(root) && !c.endpoint.includes('/zip')));
});

test('same-repository PR is supported too', async () => {
  const f = fixture(s => { s.run.head_repository.id = 100; s.pulls[7].head.repo.id = 100; });
  assert.equal((await f.run()).commented, true);
});

test('empty fork association uses current PR metadata, not artifact data', async () => {
  const f = fixture(s => { s.run.pull_requests = []; });
  await f.run();
  assert.ok(f.calls.some(c => c.endpoint.includes('/pulls?state=open&base=main')));
  assert.equal(f.writes.length, 1);
});

test('fork association fallback handles PR pagination', async () => {
  const f = fixture(s => {
    s.run.pull_requests = [];
    s.associatedPages = [Array.from({ length: 100 }, (_, i) => ({ ...structuredClone(s.pulls[7]), number: i + 100, head: { sha: 'b'.repeat(40), repo: { id: 101 } } })), [s.pulls[7]]];
  });
  await f.run();
  assert.ok(f.calls.some(c => c.endpoint.endsWith('per_page=100&page=2')));
  assert.equal(f.writes.length, 1);
});

test('existing bot comment is updated rather than duplicated', async () => {
  const f = fixture(s => { s.pages = [[oldComment()]]; });
  await f.run();
  assert.equal(f.writes[0].method, 'PATCH');
  assert.equal(f.writes[0].endpoint, `${root}/issues/comments/500`);
});

test('human comment cannot impersonate the bot marker', async () => {
  const f = fixture(s => { s.pages = [{ ...oldComment(), user: { login: 'someone', type: 'User' } }].map(c => [c]); });
  await f.run();
  assert.equal(f.writes[0].method, 'POST');
});

for (const [label, change] of [
  ['wrong workflow', s => { s.run.workflow_id = 999; }],
  ['disabled workflow', s => { s.workflow.state = 'disabled_manually'; }],
  ['wrong run repository', s => { s.run.repository.id = 999; }],
  ['push rather than PR', s => { s.run.event = 'push'; }],
  ['incomplete run', s => { s.run.status = 'in_progress'; }],
  ['wrong head repository', s => { s.pulls[7].head.repo.id = 999; }],
  ['stale head commit', s => { s.pulls[7].head.sha = 'b'.repeat(40); }],
  ['synthetic merge SHA without head match', s => { s.run.head_sha = 'b'.repeat(40); }],
  ['closed PR', s => { s.pulls[7].state = 'closed'; }],
  ['wrong base branch', s => { s.pulls[7].base.ref = 'deploy'; }],
  ['wrong base repository', s => { s.pulls[7].base.repo.id = 999; }],
]) test(label + ' cannot receive a comment', async () => { await skipped(change); });

test('multiple matching PRs fail closed', async () => {
  await skipped(s => { s.run.pull_requests.push({ number: 8 }); s.pulls[8] = { ...structuredClone(s.pulls[7]), number: 8 }; });
});

test('head advancing during API reads prevents a stale write', async () => {
  await skipped(s => { s.fresh = structuredClone(s.pulls[7]); s.fresh.head.sha = 'b'.repeat(40); });
});

test('newer run comment cannot be overwritten by an old run', async () => {
  await skipped(s => { s.pages = [[oldComment(301)]]; });
});

test('newer attempt comment cannot be overwritten by an old attempt', async () => {
  await skipped(s => { s.pages = [[oldComment(300, 2)]]; });
});

test('failure replaces stale screenshots with a run link', async () => {
  const f = fixture(s => { s.run.conclusion = 'failure'; s.pages = [[oldComment()]]; });
  await f.run();
  assert.match(f.writes[0].body, /preview failed/);
  assert.doesNotMatch(f.writes[0].body, /Download/);
  assert.equal(f.calls.some(c => c.endpoint.includes('/artifacts?')), false);
});

for (const conclusion of ['cancelled', 'skipped']) test(conclusion + ' replacement removes old screenshot link', async () => {
  const f = fixture(s => { s.run.conclusion = conclusion; s.pages = [[oldComment()]]; });
  await f.run();
  assert.match(f.writes[0].body, new RegExp(conclusion));
  assert.doesNotMatch(f.writes[0].body, /Download/);
});

test('expired, oversized, or ambiguous artifacts are not linked', async () => {
  for (const change of [s => { s.artifacts[0].expired = true; },
    s => { s.artifacts[0].size_in_bytes = 100 * 1024 * 1024; },
    s => { s.artifacts.push({ ...s.artifacts[0], id: 401 }); }]) {
    const f = fixture(change); await f.run();
    assert.match(f.writes[0].body, /No screenshot artifact/);
    assert.doesNotMatch(f.writes[0].body, /Download/);
  }
});

test('comment pagination finds and updates the real bot comment', async () => {
  const f = fixture(s => { s.pages = [Array.from({ length: 100 }, (_, id) => ({ id, user: { login: 'person', type: 'User' }, body: 'Hi' })), [oldComment()]]; });
  await f.run(); assert.equal(f.writes[0].method, 'PATCH');
});

test('read-only resolution has no comment or artifact side effects', async () => {
  const f = fixture();
  assert.equal((await f.resolve()).pr.number, 7);
  assert.equal(f.writes.length, 0);
  assert.equal(f.calls.some(c => c.endpoint.includes('/comments') || c.endpoint.includes('/artifacts')), false);
});

test('target cannot change after the trusted PR queue was selected', async () => {
  const f = fixture();
  const target = (await f.resolve()).pr.number;
  f.state.run.pull_requests = [{ number: 8 }];
  f.state.pulls[8] = { ...structuredClone(f.state.pulls[7]), number: 8 };
  assert.equal((await f.run(target)).skipped, true);
  assert.equal(f.writes.length, 0);
});

test('workflow serializes different revisions by verified PR number', async () => {
  const yaml = await readFile(new URL('../workflows/pr-preview-comment.yml', import.meta.url), 'utf8');
  assert.ok(yaml.includes('group: pr-browser-preview-comment-${{ needs.resolve.outputs.number }}'));
  assert.ok(yaml.includes('EXPECTED_PR_NUMBER: ${{ needs.resolve.outputs.number }}'));
  assert.ok(yaml.includes('cancel-in-progress: false'));
  assert.equal(yaml.includes('group: pr-preview-comment-${{ github.event.workflow_run.head_sha }}'), false);
});

test('invalid IDs fail before any API access', async () => {
  await assert.rejects(publishPreview({ repository, runId: -1, request: () => assert.fail('must not call API') }));
});
