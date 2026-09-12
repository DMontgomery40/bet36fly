from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_browser_guard_requires_exact_read_only_marker_before_launch():
    program = r'''
const assert = require('assert/strict');
const { verifyReadOnlyServer } = require('./scripts/verification_server_guard.cjs');

function response(status, marker, body) {
  return {status, headers:{get:name => name.toLowerCase() === 'x-bet36fly-verification' ? marker : null}, json:async()=>body};
}

(async () => {
  const calls=[];
  const valid=await verifyReadOnlyServer('http://127.0.0.1:8765/', async (url, options) => {
    calls.push([url, options]);
    return response(200, 'read-only', {verification_mode:true});
  });
  assert.deepEqual(valid, {verification_mode:true, marker:'read-only'});
  assert.deepEqual(calls, [['http://127.0.0.1:8765/api/status', {method:'GET', redirect:'manual'}]]);
  for (const bad of [
    response(302, 'read-only', {verification_mode:true}),
    response(200, null, {verification_mode:true}),
    response(200, 'READ-ONLY', {verification_mode:true}),
    response(200, 'read-only', {verification_mode:false}),
    response(200, 'read-only', {}),
  ]) {
    await assert.rejects(() => verifyReadOnlyServer('http://example.test', async () => bad), /read-only verification server/i);
  }
})();
'''
    result = subprocess.run(['node', '-e', program], cwd=ROOT, text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr


def test_reward_browser_preflight_precedes_chromium_launch():
    source = (ROOT / 'scripts/verify_reward_browser.cjs').read_text()
    assert "verifyReadOnlyServer(base)" in source
    assert source.index('verifyReadOnlyServer(base)') < source.index('chromium.launch')


def test_verification_launcher_uses_explicit_factory_without_bytecode_writes():
    makefile = (ROOT / 'Makefile').read_text()
    assert 'serve-verify:' in makefile
    command = next(line for line in makefile.splitlines() if 'bet36fly.server:create_verification_app' in line)
    assert 'PYTHONDONTWRITEBYTECODE=1' in command
    assert '--factory' in command
