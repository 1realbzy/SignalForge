# Temporary Twikit 2.2.2 compatibility patches

These files are **upstream dependency patches**, not SignalForge application code.

They exist because `twikit==2.2.2` cannot search X after X changed:

1. homepage `ondemand.s` webpack layout (transaction-id generation)
2. the SearchTimeline GraphQL document (`flaR-PUMshxFWZWPNpq4zA` now 404s)
3. the User object shape in SearchTimeline results (identity fields moved off `legacy`)

SignalForge still depends on `twikit==2.2.2`. The pin is unchanged. Do not compensate inside `src/job_board_tool`.

## Patches

All three patches apply to a **clean** install of `twikit==2.2.2` only, in this order.

| Order | File | Origin | Affected installed files |
| --- | --- | --- | --- |
| 1 | `patches/twikit/2.2.2/0001-4a62e28-transaction-ondemand-regex.patch` | PR #411 commit `4a62e2895676398e5c2dcce697597abbddb07a2c` | `twikit/x_client_transaction/transaction.py` |
| 2 | `patches/twikit/2.2.2/0002-de9c6f3-search-timeline.patch` | PR #419 SearchTimeline-only commit `de9c6f314f40a3c547ea4dea7cc87ed769b205bb` | `twikit/client/gql.py`, `twikit/constants.py` |
| 3 | `patches/twikit/2.2.2/0003-user-relocated-fields.patch` | Local SearchTimeline investigation: HTTP 200 with tweet entries, `User.__init__` `KeyError` on relocated fields | `twikit/user.py` |

No other Twikit files should change.

Patch #0003 prefers the relocated current X fields when those keys are present (`core`, `avatar`, `location`, `verification`, `dm_permissions`, `media_permissions`), falls back to `legacy` when they are not, and uses `[]` only for the observed missing `pinned_tweet_ids_str`, `withheld_in_countries`, and `entities.description.urls` fields. Legacy payloads keep working.

## Apply

```text
pip install twikit==2.2.2
python -m scripts.apply_twikit_compat_patches
```

`pip install` does not apply the patches. The script:

- refuses any Twikit version other than `2.2.2`
- applies the three patches in the order above
- converts the four target files to LF if needed, then runs `git apply` with `core.autocrlf=false` (the published 2.2.2 wheel uses CRLF)
- is a no-op if all three patches are already present
- does not read cookies, `.env`, or credentials

## Secrets

`cookies.json`, `.env`, and login credentials stay outside this mechanism. They are not inputs to the apply script.

## Removal

When a released Twikit version includes all three fixes, delete this directory, the three patch files, the apply script, and the related tests, then install that release. Do not keep these patches after they are unnecessary.
