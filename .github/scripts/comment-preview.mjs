import { pathToFileURL } from 'node:url';
import { appendFile } from 'node:fs/promises';

const MARKER = '<!-- pr-browser-preview -->';
const SHA = /^[0-9a-f]{40}$/;
const WORKFLOW = 'pr-preview.yml';
const MAX_ARTIFACT = 32 * 1024 * 1024;

function positiveInteger(value) {
  return Number.isSafeInteger(value) && value > 0;
}

function matchesPull(pr, run, repo) {
  return pr.state === 'open' && pr.base?.ref === 'main'
    && pr.base?.repo?.id === repo.id
    && pr.head?.repo?.id === run.head_repository?.id
    && pr.head?.sha === run.head_sha;
}

export async function resolvePreview({ request, repository, runId, log = console.log }) {
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository) || !positiveInteger(runId)) {
    throw new Error('Invalid repository or run ID');
  }
  const root = `/repos/${repository}`;
  const [repo, workflow, run] = await Promise.all([
    request(root), request(`${root}/actions/workflows/${WORKFLOW}`), request(`${root}/actions/runs/${runId}`),
  ]);
  // Only GitHub API metadata is trusted. No artifact contents or PR-provided IDs.
  if (repo.full_name?.toLowerCase() !== repository.toLowerCase()
      || !positiveInteger(repo.id) || !positiveInteger(workflow.id) || workflow.state !== 'active'
      || workflow.path !== `.github/workflows/${WORKFLOW}`
      || run.id !== runId || run.repository?.id !== repo.id || run.workflow_id !== workflow.id
      || run.event !== 'pull_request' || run.status !== 'completed'
      || typeof run.head_sha !== 'string' || !SHA.test(run.head_sha)
      || !positiveInteger(run.head_repository?.id)
      || !['success', 'failure', 'timed_out', 'cancelled', 'skipped'].includes(run.conclusion)) {
    log('Not an eligible completed PR preview run; skipped.');
    return { skipped: true };
  }
  let numbers = [...new Set((run.pull_requests || []).map(pr => pr.number).filter(positiveInteger))];
  if (numbers.length === 0) {
    // Fork runs can omit pull_requests. Query current PRs in the BASE repo;
    // never rely on an ID or URL supplied in the screenshot artifact.
    for (let page = 1; page <= 10; page++) {
      const open = await request(`${root}/pulls?state=open&base=main&per_page=100&page=${page}`);
      numbers.push(...open.filter(pr => matchesPull(pr, run, repo)).map(pr => pr.number).filter(positiveInteger));
      if (open.length < 100) break;
      if (page === 10) throw new Error('Open PR pagination limit reached');
    }
    numbers = [...new Set(numbers)];
  }
  if (numbers.length > 20) throw new Error('Too many PR candidates');
  const candidates = [];
  for (const number of numbers) {
    const pr = await request(`${root}/pulls/${number}`);
    if (pr.number === number && matchesPull(pr, run, repo)) candidates.push(pr);
  }
  if (candidates.length !== 1) {
    log('No unique current PR with matching head SHA and repository; skipped.');
    return { skipped: true };
  }
  return { repo, run, pr: candidates[0] };
}

export async function publishPreview({ request, repository, runId, expectedNumber, log = console.log }) {
  if (!positiveInteger(expectedNumber)) throw new Error('A trusted expected PR number is required');
  const resolved = await resolvePreview({ request, repository, runId, log });
  if (resolved.skipped) return resolved;
  const { repo, run, pr } = resolved;
  if (pr.number !== expectedNumber) {
    log('PR association changed since queue selection; skipped.');
    return { skipped: true };
  }
  const root = `/repos/${repository}`;
  const runURL = `https://github.com/${repository}/actions/runs/${runId}`;
  const attempt = positiveInteger(run.run_attempt) ? run.run_attempt : 1;
  let details;
  if (run.conclusion === 'success') {
    const result = await request(`${root}/actions/runs/${runId}/artifacts?per_page=100`);
    const artifacts = result.artifacts.filter(a => a.name === 'browser-preview' && a.expired === false
      && positiveInteger(a.id) && positiveInteger(a.size_in_bytes) && a.size_in_bytes <= MAX_ARTIFACT);
    if (artifacts.length === 1) {
      const artifactURL = `${runURL}/artifacts/${artifacts[0].id}`;
      details = `[Download RU/EN screenshots](${artifactURL})\n\nDesktop **1440 px** · narrow **375 px**.\n\nGitHub sign-in is required to download. Screenshots are retained for 14 days.`;
    } else {
      details = 'No screenshot artifact is available for this run.';
    }
  } else {
    const outcomes = { failure: 'failed', timed_out: 'timed out', cancelled: 'was cancelled', skipped: 'was skipped' };
    details = `The browser preview ${outcomes[run.conclusion]}. See the run for details.`;
  }
  const body = `${MARKER}\n<!-- run:${runId} attempt:${attempt} -->\n### Browser preview\n\n${details}\n\nCommit \`${run.head_sha.slice(0, 7)}\` · [View run](${runURL})`;
  let previous;
  for (let page = 1; page <= 10; page++) {
    const comments = await request(`${root}/issues/${pr.number}/comments?per_page=100&page=${page}`);
    previous = comments.find(comment => comment.user?.login === 'github-actions[bot]'
      && comment.user?.type === 'Bot' && comment.body?.startsWith(MARKER));
    if (previous || comments.length < 100) break;
    if (page === 10) throw new Error('Comment pagination limit reached');
  }
  if (previous) {
    if (!positiveInteger(previous.id)) throw new Error('Invalid bot comment ID');
    const prior = previous.body.match(/<!-- run:(\d+) attempt:(\d+) -->/);
    if (prior && (Number(prior[1]) > runId || (Number(prior[1]) === runId && Number(prior[2]) > attempt))) {
      log('A newer preview comment already exists; skipped.');
      return { skipped: true };
    }
  }
  // Recheck after all reads so a new PR revision cannot receive a stale preview.
  const fresh = await request(`${root}/pulls/${pr.number}`);
  if (fresh.number !== pr.number || !matchesPull(fresh, run, repo)) {
    log('PR was closed or advanced while preparing the comment; skipped.');
    return { skipped: true };
  }
  if (previous) {
    await request(`${root}/issues/comments/${previous.id}`, { method: 'PATCH', body: { body } });
  } else {
    await request(`${root}/issues/${pr.number}/comments`, { method: 'POST', body: { body } });
  }
  log(`Browser preview comment updated for PR #${pr.number}.`);
  return { commented: true, number: pr.number };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error('GitHub Actions token is missing');
  const repository = process.env.GITHUB_REPOSITORY;
  const runId = Number(process.env.PREVIEW_RUN_ID);
  const request = async (endpoint, { method = 'GET', body } = {}) => {
    const response = await fetch('https://api.github.com' + endpoint, {
      method, headers: {
        Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json',
      },
      ...(body ? { body: JSON.stringify(body) } : {}), signal: AbortSignal.timeout(20_000),
      redirect: 'error',
    });
    if (!response.ok) throw new Error(`GitHub API ${method} ${endpoint}: HTTP ${response.status}`);
    return response.json();
  };
  if (process.argv.slice(2).length === 1 && process.argv[2] === '--resolve') {
    if (!process.env.GITHUB_OUTPUT) throw new Error('GitHub Actions output file is missing');
    const resolved = await resolvePreview({ request, repository, runId });
    if (resolved.pr) await appendFile(process.env.GITHUB_OUTPUT, `number=${resolved.pr.number}\n`);
  } else if (process.argv.length === 2) {
    await publishPreview({ request, repository, runId, expectedNumber: Number(process.env.EXPECTED_PR_NUMBER) });
  } else {
    throw new Error('Unknown arguments');
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
