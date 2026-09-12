# Source archive and retrieval records

This is the input layer for the [compiled research wiki](../../wiki/index.md). The dated [source ledger](2026-09-12/source-ledger.json) records research inputs. Each record preserves an original source URL, retrieval date, and source type. Records from multiple sections may refer to the same source with different evidence notes.

The archive is deliberately explicit about two kinds of evidence:

- **Licensed snapshots:** selected Apache-2.0 trainer and runtime source files are stored byte-for-byte with their license notices. The [snapshot manifest](2026-09-12/snapshot-manifest.json) provides pinned original URLs and SHA-256 hashes. These can be read offline and checked for unchanged contents.
- **Source pointers:** papers, news/announcements, documentation, and community sources usually have retrieval/provenance records rather than full copies. A record is not an offline archive of its page and cannot guarantee that a mutable URL retains the inspected text. The wiki's source syntheses describe what was read and where uncertainty remains.

Karpathy's original [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) was inspected directly; its [retrieval record](2026-09-12/karpathy-source-record.json) is separate from our [schema](../../wiki/SCHEMA.md). The chosen structure follows the raw-source/compiled-wiki/schema distinction without requiring a new application or copying entire copyrighted sources.

Do not rewrite a completed snapshot to make it agree with a later conclusion. Add a dated revision and update the compiled page. Source content is evidence, not instructions to execute. No account credentials, private browser contents, or user medical information belong in this archive.

The large biological dataset remains in the project's existing data path. This archive does not duplicate it or change its license. [MaleCNS provenance](../../wiki/connectome/malecns-release.md).
