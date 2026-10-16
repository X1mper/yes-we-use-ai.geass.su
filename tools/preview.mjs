import { spawn } from 'node:child_process';
import { mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const output = path.join(root, 'output', 'pr-preview');
let browser;
let server;

async function startServer() {
  server = spawn('python3', ['-m', 'http.server', '0', '--bind', '127.0.0.1', '--directory', path.join(root, 'build')], {
    cwd: root, env: { ...process.env, PYTHONUNBUFFERED: '1' }, stdio: ['ignore', 'pipe', 'pipe'],
  });
  server.stderr.on('data', chunk => process.stderr.write(chunk));
  return new Promise((resolve, reject) => {
    let buffer = '';
    const timer = setTimeout(() => reject(new Error('Preview server did not start')), 10_000);
    server.once('error', error => { clearTimeout(timer); reject(error); });
    server.once('exit', code => { clearTimeout(timer); reject(new Error(`Preview server exited: ${code}`)); });
    server.stdout.on('data', chunk => {
      buffer += chunk.toString();
      const match = buffer.match(/Serving HTTP on 127\.0\.0\.1 port (\d+)/);
      if (match) {
        clearTimeout(timer);
        resolve(`http://127.0.0.1:${match[1]}`);
      }
    });
  });
}

async function main() {
  await rm(output, { recursive: true, force: true });
  await mkdir(output, { recursive: true });
  const origin = await startServer();
  browser = await chromium.launch({
    ...(process.env.PREVIEW_CHROMIUM_PATH ? { executablePath: process.env.PREVIEW_CHROMIUM_PATH } : {}),
  });
  for (const [language, route] of [['ru', '/'], ['en', '/en/']]) {
    for (const [size, width] of [['desktop', 1440], ['narrow', 375]]) {
      const context = await browser.newContext({
        viewport: { width, height: 1000 }, deviceScaleFactor: 1,
        colorScheme: 'light', reducedMotion: 'reduce', locale: language === 'ru' ? 'ru-RU' : 'en-US',
        serviceWorkers: 'block',
      });
      try {
        // Preview only the local build; never load external fonts/images/scripts.
        await context.route('**/*', async request => {
          const url = new URL(request.request().url());
          if (url.origin === origin) {
            const response = await request.fetch({ maxRedirects: 0 });
            // Match the public site's policy: inline code must not look valid
            // in a preview if production would block it.
            await request.fulfill({ response, headers: {
              ...response.headers(),
              'content-security-policy': "default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
              'x-content-type-options': 'nosniff',
              'referrer-policy': 'strict-origin-when-cross-origin',
            } });
          } else if (url.protocol === 'data:' || url.protocol === 'blob:') {
            await request.continue();
          } else {
            await request.abort();
          }
        });
        const page = await context.newPage();
        page.setDefaultTimeout(15_000);
        const response = await page.goto(origin + route, { waitUntil: 'networkidle', timeout: 30_000 });
        if (!response?.ok()) throw new Error(`Preview page failed: ${route}`);
        await page.evaluate(async () => {
          await document.fonts.ready;
          const images = [...document.images];
          for (const image of images) image.loading = 'eager';
          await Promise.all(images.map(image => image.decode()));
        });
        const filename = `${language}-${size}.png`;
        await page.screenshot({ path: path.join(output, filename), fullPage: true, animations: 'disabled', caret: 'hide', timeout: 30_000 });
        console.log(`Saved ${filename} (${width}px wide)`);
      } finally {
        await context.close();
      }
    }
  }
}

try {
  await main();
} finally {
  try {
    if (browser) await browser.close();
  } finally {
    if (server && server.exitCode === null && server.signalCode === null) {
      const stopped = new Promise(resolve => server.once('exit', resolve));
      server.kill('SIGTERM');
      await stopped;
    }
  }
}
