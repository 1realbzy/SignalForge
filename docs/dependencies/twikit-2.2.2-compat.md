# Temporary Twikit 2.2.2 compatibility patches

These files are **upstream dependency patches**, not SignalForge application code.

They exist because `twikit==2.2.2` cannot search X after X changed:

1. homepage `ondemand.s` webpack layout (transaction-id generation)
2. the SearchTimeline GraphQL document (`flaR-PUMshxFWZWPNpq4zA` now 404s)

SignalForge still depends on `twikit==2.2.2`. The pin is unchanged. Do not compensate inside `src/job_board_tool`.

## Patches

Both patches apply to a **clean** install of `twikit==2.2.2` only.

| Order | File | Upstream | Affected installed files |
| --- | --- | --- | --- |
| 1 | `patches/twikit/2.2.2/0001-4a62e28-transaction-ondemand-regex.patch` | PR #411 commit `4a62e2895676398e5c2dcce697597abbddb07a2c` | `twikit/x_client_transaction/transaction.py` |
| 2 | `patches/twikit/2.2.2/0002-de9c6f3-search-timeline.patch` | PR #419 SearchTimeline-only commit `de9c6f314f40a3c547ea4dea7cc87ed769b205bb` | `twikit/client/gql.py`, `twikit/constants.py` |

No other Twikit files should change.

## Apply

```text
pip install twikit==2.2.2
python -m scripts.apply_twikit_compat_patches
```

`pip install` does not apply the patches. The script:

- refuses any Twikit version other than `2.2.2`
- applies the two patches in the order above
- converts the three target files to LF if needed, then runs `git apply` with `core.autocrlf=false` (the published 2.2.2 wheel uses CRLF)
- is a no-op if both patches are already present
- does not read cookies, `.env`, or credentials

## Secrets

`cookies.json`, `.env`, and login credentials stay outside this mechanism. They are not inputs to the apply script.

## Removal

When a released Twikit version includes both fixes, delete this directory, the two patch files, the apply script, and the related test, then install that release. Do not keep these patches after they are unnecessary.
