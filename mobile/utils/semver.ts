// Version comparison — must use real semver, not string comparison.
// "1.10.0" > "1.9.0" must be true. See root CLAUDE.md §12.

import semver from 'semver'

export function isVersionBelow(currentVersion: string, minVersion: string): boolean {
  return semver.lt(currentVersion, minVersion)
}
