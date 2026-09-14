'use strict';
/**
 * Playwright is not vendored in this repository, so the browser suites resolve it
 * explicitly and fail with an actionable message rather than a bare MODULE_NOT_FOUND.
 *
 * Resolution order:
 *   1. normal require, which already covers a local install and NODE_PATH
 *   2. PLAYWRIGHT_PATH, either the package directory or a node_modules directory
 *      containing it, as a colon-separated list
 */
const path = require('path');

function candidates() {
  const roots = (process.env.PLAYWRIGHT_PATH || '').split(path.delimiter).filter(Boolean);
  return roots.flatMap(root => [root, path.join(root, 'node_modules')]);
}

function loadPlaywright() {
  try {
    return require('playwright');
  } catch (error) {
    if (error && error.code !== 'MODULE_NOT_FOUND') throw error;
  }
  for (const base of candidates()) {
    try {
      return require(require.resolve('playwright', { paths: [base] }));
    } catch (error) {
      if (error && error.code !== 'MODULE_NOT_FOUND') throw error;
    }
  }
  throw new Error(
    'Playwright is not resolvable and is not vendored in this repository.\n' +
    'Install it where node can find it, or point at an existing install, for example:\n' +
    '  PLAYWRIGHT_PATH=/path/to/a/project/node_modules node scripts/verify_circuit_browser.cjs\n' +
    '  NODE_PATH=/path/to/a/project/node_modules node scripts/verify_circuit_browser.cjs',
  );
}

module.exports = { loadPlaywright };
