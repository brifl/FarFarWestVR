# Building and publishing a beta

Public packaging is separate from robot1-x’s Git/WSL development deployment.
The end-user installer refuses to replace Git checkouts. No native build is
required to package the profile.

1. Update `release.json` with the beta version and verified backend hash/game
   compatibility. Add `docs/releases/vVERSION.md` and update public download links.
2. Run `python3 tools/test_release.py`. These dependency-free tests check scrubbing,
   hashes, reproducibility, and isolation from loose local files.
3. Commit release inputs, then build and validate:

   ```bash
   python3 tools/package_release.py
   python3 tools/publish_release.py --tag v0.1.0-beta.1 --check
   ```

   The packager reads Git blobs from HEAD, never loose installed settings, and
   writes ignored `dist/` assets. `--revision` selects another committed snapshot.
   Functional settings/bindings, hooks, plugins, Lua, required artwork, and tuning
   are allowlisted. Logs, dumps, caches, experiments, overrides, unused art,
   symbols, and backend binaries are excluded. It adds version metadata and the
   exact controller-bridge marker. Public UI capture defaults to off; development
   tuning remains unchanged.
4. Test the generated Setup ZIP on Windows:

   ```powershell
   powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File tools\test_installer.ps1 -SetupZip dist\FarFarWestVR-0.1.0-beta.1-Setup.zip
   ```

   Tests use a temporary fake game/profile to check installation, updates,
   preservation, rollback, corrupt payloads, runtime mismatch, and Git/running-game
   guards. An administrator token tests real Windows log links;
   `-RequireRealLinks` makes that check mandatory instead of simulating link creation.
5. Push the version tag:

   ```bash
   git tag -a v0.1.0-beta.1 -m "Far Far West VR 0.1.0-beta.1"
   git push origin main
   git push origin v0.1.0-beta.1
   ```

   The release workflow fetches the exact tagged commit, runs packaging and
   Windows PowerShell 5.1 checks, builds assets, uploads a draft, and publishes a
   **prerelease** after verifying uploaded sizes. It uses the repository-scoped
   Actions token with contents:write, so no personal API token or connector is
   required. Verify Actions and public downloads afterward: a tag alone is not a release.

For local publishing, `tools/publish_release.py` accepts `GITHUB_TOKEN` or
`GH_TOKEN`, validates checksums and notes, and can resume a draft. It refuses to
overwrite public releases. Bump the beta version rather than reusing published tags.

**Runtime distribution is not enabled.** [Upstream UEVR's license](https://github.com/praydog/UEVR/blob/master/LICENSE) reserves all rights.
Until permission is obtained, publish the profile and installer only. Keep
UEVR backend/runtime binaries and private engine/UESDK sources out of public
Git and release assets. The installer verifies a separately provided runtime
and leaves it unchanged.
