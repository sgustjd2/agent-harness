# Upgrade guide

**M1 placeholder.** Written in M8.

Will cover version-to-version upgrades, state schema migration, and rollback.

Two rules already fixed: state files carry `schema_version`, and a state file newer than
the plugin understands causes a stop rather than a write. Migration is never automatic
without approval, and the original is always preserved first.
