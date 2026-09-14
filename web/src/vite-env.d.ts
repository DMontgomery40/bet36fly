/** Minimal declaration for the one Node built-in the CSS regression tests need.
 *  `@types/node` is not a dependency of this package, and vitest stubs `?raw`
 *  stylesheet imports to an empty string, so the tests read the files directly. */
declare module 'node:fs' {
  export function readFileSync(path: string | URL, encoding: 'utf8'): string;
}
