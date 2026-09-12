'use strict';

async function verifyReadOnlyServer(base, fetchImpl = globalThis.fetch) {
  const failure = () => new Error('Reward browser QA requires the marked read-only verification server.');
  if (typeof fetchImpl !== 'function') throw failure();
  const statusUrl = `${String(base).replace(/\/+$/, '')}/api/status`;
  let response;
  try {
    response = await fetchImpl(statusUrl, {method: 'GET', redirect: 'manual'});
  } catch {
    throw failure();
  }
  if (response.status !== 200 || response.headers.get('X-BET36FLY-Verification') !== 'read-only') {
    throw failure();
  }
  let payload;
  try {
    payload = await response.json();
  } catch {
    throw failure();
  }
  if (!payload || payload.verification_mode !== true) throw failure();
  return {verification_mode: true, marker: 'read-only'};
}

module.exports = {verifyReadOnlyServer};
