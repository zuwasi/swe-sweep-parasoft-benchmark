# proj scoring (Gemini 4 Neon in Amp, base 3e49a80b8114b948fe5524fea8ba7ef8d2f4fe2c)

Agent report: 128 findings (15 Critical / 62 High / 44 Medium / 7 Low), 97 CONFIRMED via ASan/UBSan/LSan build, 31 SUSPECTED.
Parasoft published: region 13/21 (61.9%), strict 7/21 (33.3%).

## Accepted matches (3 region, 3 strict of 21 benchmark bugs)

| bug_id | defect | Neon finding | verdict | region | strict |
|---|---|---|---|---|---|
| proj-5ea62cb8daa4 | compares ellipsoid with itself | BUG-022 Ellipsoid::_isEquivalentTo compares otherEllipsoid against itself (datum.cpp 1047-1052, strict 1048) | exact same defect | yes | yes |
| proj-a2dc13a77ea7 | wrong error code ENOMEM returned (stere/ups/tmerc/utm) | BUG-118 explicitly says "ups/utm return ENOMEM", cites stere.cpp 314-317 and tmerc.cpp 543-546 (strict 315,316 / 544,545) | exact same defect | yes | yes |
| proj-782c2a51cca6 | transformation match confidence wrong (crs.cpp 4663-4675) | BUG-023 BoundCRS::_identify NULL TransformationNNPtr / FormattingException at 4660-4673 | borderline: same function and strict lines, but stated mechanism (NULL cast) differs from the fixed confidence logic | yes | yes (borderline) |

## Rejected line-overlaps

- proj-210490c1df4f / a289af9c5fe7 / d1e39e45b0a6 (nadgrids transformation source CRS wrong) vs BUG-025 PROJJSON recursion: io.cpp 5220-5268 overlap is coordinate coincidence in a different subsystem.

## Clear misses (18 bugs)

missing include x2 (factory.cpp), axis json export context, null cartesianCS deref x3 (io.cpp 3755-3760),
no snippet extractable, unit conversion z params, identifier creation from code key, UPS south axis condition,
geodetic CRS PROJ export x2, identifiers reference wrong, MAX_ITER macro (moll.cpp), CRS matching conditions,
nadgrids source CRS x3.

## Score

- Neon: region 3/21 (14.3%), strict 3/21 (14.3%, one borderline)
- Parasoft: region 13/21 (61.9%), strict 7/21 (33.3%)
- Novel findings: 125 of 128 not matched to any benchmark bug region
