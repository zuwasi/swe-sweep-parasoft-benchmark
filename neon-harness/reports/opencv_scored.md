# opencv scoring (Gemini 4 Neon in Amp, base per regions/opencv.json, 47 bugs)

Agent report: 262 findings (106 Critical / 135 High / 21 Medium).
Parasoft published: region 74.5%, strict 40.4%.
Regions file verified: n_bugs = 47 (one bug, opencv-d97911c694c2, color_yuv.cpp, has an empty
region set: not matchable). 74.5% = 35/47 and 40.4% = 19/47, so the published Parasoft numbers are
consistent with n_bugs = 47.

All maintainer fixes below were verified by parent-blob prefix match against the oracle blob AND by
inspecting the commit's diff. For most bugs the diff hunks match the oracle old_start/removed lists
exactly. For four bugs (opencv-849409d58b10, the imgproc.hpp part of opencv-08979782855f,
opencv-a868f91ec13f, opencv-cb9f44f5771a) the recorded oracle old_start values are drifted relative
to the true parent-blob numbering (by -4 to -386 lines, not constant within a patch); in those cases
the match was confirmed structurally (same hunk count, same old_count, same removed-line offsets
within each hunk) plus the parent-blob identity, which is exact. No commit in the clone ever removes
the literal content at the drifted positions (checked with `git log -S/-G`), so the drifted reading
is a recording artifact of the benchmark generator, not a missed fix.

Mapper candidates that did NOT survive verification (real fixes substituted):
e82e672a93 (BUG-009, wrong hunks), d54d01ca46 (BUG-020, wrong hunks), a6277370ca (BUG-045, wrong
hunks), 8449b9e468 (BUG-014, wrong hunks), 603d7ded88 (BUG-041, pre-state commit, not the fix),
ecc9bd0925 (BUG-022, unrelated), 5d54def264 (BUG-112/BUG-154, mechanical semicolon commit),
4a6888ccf6 (BUG-021, wrong), c230841105/c7a21dc5bf (BUG-015, wrong), 30597e5c98 (BUG-193, its tree
already equals the pre-image blob), efcf307b4c and 0bd54a60e9 (BUG-157, wrong), daa8f7dfc6
(BUG-064, wrong), 97c3bcb1b7 (BUG-128, wrong). Real fixes were located by enumerating every commit
whose parent tree holds the oracle blob for the touched file (`git log --all --full-history` +
`cat-file --batch-check`), then verifying the diff.

## Accepted matches (13 region, 9 strict of 47 benchmark bugs; 13 distinct findings)

| bug_id | defect (maintainer fix) | Neon finding | verdict | region | strict |
|---|---|---|---|---|---|
| opencv-f624dc51adf5 | ee4feb4b09 (merge PR #16208 fix_compare_16f): wraps every dispatch-table call in CV_Assert (`BinaryFunc cvtFn = getConvertFunc(sc.depth(), buftype); CV_Assert(cvtFn);`, same for `tab[depth1]`, `getCmpFunc(depth1)`) and adds `if (depth1 == CV_16F || depth2 == CV_16F) CV_Error(Error::StsNotImplemented, "Unsupported depth value CV_16F");` in cv::compare; all 7 oracle hunks (61, 196, 270, 745, 1228, 1247, 1275) and removed lines 64, 1237, 1241, 1278 match exactly | BUG-009 NULL function pointer call (SIGSEGV) on CV_16F across arithm.cpp dispatch tables | exact same defect (the maintainer guards the NULL CV_16F table entries the finding identifies); the channels.cpp half of the claim is not in this commit | yes | yes (1237, 1241, 1278) |
| opencv-ff66d0af4e7e | fc746f35b9 "fix fmt_pairs stack overflow in calcElemSize and decodeSimpleFormat": `int fmt_pairs[CV_FS_MAX_FMT_PAIRS]` becomes `int fmt_pairs[CV_FS_MAX_FMT_PAIRS*2]` at lines 269 and 319, exactly the oracle's removed lines | BUG-014 Stack buffer overflow in fs::calcElemSize and fs::decodeSimpleFormat (and SIGFPE on empty dt) | exact same defect (the SIGFPE-on-empty-dt claim is not part of this fix) | yes | yes |
| opencv-9a698f046e06 | 2906d4d73a "reject nd-matrix dim count above CV_MAX_DIM in FileStorage read": adds `CV_Assert( dims > 0 && dims <= CV_MAX_DIM );` in both Mat and SparseMat readers (hunks at 142 and 180, insertion-only) | BUG-015 Stack buffer overflow (sizes[CV_MAX_DIM]) and negative-index stack write (idx[k]) in Mat/SparseMat persistence readers | bundled finding; the sizes[CV_MAX_DIM] overflow claim is exactly the guarded defect; the idx[k] claim is not part of this fix | yes | no (strict set empty, insertion-only oracle) |
| opencv-1974f51bd214 | 4d0f13544d (merge PR #16700 fix_core_matexpr_size_gemm): adds `Size size(const MatExpr& expr) const CV_OVERRIDE` to MatOp_GEMM honoring GEMM_1_T/GEMM_2_T, comments out `isGEMM` (line 202) and deletes `if( isGEMM(*this) ) return Size(b.cols, a.rows);` (1243-1244); all 3 oracle hunks exact | BUG-020 MatExpr wrong results: (s/A).mul(B) divides by s, abs((A-B)+s) drops s, GEMM size() ignores transposes | bundled finding; the "GEMM size() ignores transposes" claim is exactly the fixed defect; the other two claims are not part of this fix | yes | yes |
| opencv-0d05063bd5c0 | 3266ac7667 "core(kmeans): bailout if can't select cluster center": adds `if (bestCenter < 0) CV_Error(Error::StsNoConv, "kmeans: can't update cluster center (check input for huge or NaN values)");` at line 143 (insertion-only) | BUG-021 cv::kmeans silently drops updated labels for 1xN KMEANS_USE_INITIAL_LABELS and underflows index -1 on NaN/Inf | bundled finding; the "underflows index -1 on NaN/Inf" claim is exactly the path the bailout guards (NaN/Inf distances leave bestCenter = -1); the 1xN labels claim is not part of this fix | yes | no (strict set empty, insertion-only oracle) |
| opencv-41e8688ee2f5 | ed93384817 "Fix bug in maskBoundingRect": moves the `xmin/xmax` update inside the prefix scan loop and deletes the `break` (removes 1060 and 1062-1068 exactly), so non-zero pixels in the unaligned row prefix are no longer skipped | BUG-064 maskBoundingRect (cv::boundingRect) misses non-zero pixels in unaligned row prefixes | exact same defect | yes | yes |
| opencv-a868f91ec13f | 6360c3bf46 (merge PR #22184 fixbug_pyrUp): `row[(_dst.cols-1) + x] = row[dx + cn];` becomes `row[(_dst.cols-1) * cn + x] = row[dx + cn];` (removes line 966 exactly) | BUG-077 cv::pyrUp missing * cn multiplier leaves rightmost column uninitialized for odd dstsize.width (plus misaligned int store) | exact same defect | yes | yes |
| opencv-212cd1521af9 | 43eba3d750 (merge from upstream/3.4): `_mm256_blendv_pd(__one, _mm256_div_pd(__one, __vecTilt2), cmp)` becomes `_mm256_blendv_pd(_mm256_div_pd(__one, __vecTilt2), __one, cmp)` (removes line 127 exactly), un-inverting the mask | BUG-105 Inverted _mm256_blendv_pd mask in AVX2 initUndistortRectifyMapLine_AVX breaks tilted-sensor undistortion | exact same defect | yes | yes |
| opencv-6a1bdf8d7893 | b5961cc5d1 "calib3d: don't change input data": adds `else { // avoid changing of inputs in compressElems() call / from = from.clone(); to = to.clone(); }` in both estimateAffine2D and estimateAffinePartial2D (hunks at 833 and 900, insertion-only) | BUG-112 cv::estimateAffine2D and estimateAffinePartial2D silently corrupt caller's const InputArray in-place | exact same defect | yes | no (strict set empty, insertion-only oracle) |
| opencv-5cb9cd581ef5 | 3c3c5ef2b6 "Fix a dnn bug with retrieving all the output blobs": renames the shadowed inner loop variable `i` to `j`, adds `outputBlobs[i].resize(lp.size());`, and replaces the pins accumulation with `pins.push_back(impl->getPinByAlias(outBlobNames[i]))` (removes 2798/2799 and 2812/2814 exactly) | BUG-128 Net::forward(vector<vector<Mat>>&, vector<String>&) shadowed loop variable causes heap OOB write (and pins.end() deref) | exact same defect, both claims addressed | yes | yes |
| opencv-78a11e75834c | 41678fe3d3 "Fixed checkMasks in DescriptorMatcher with train descs in UMats": adds `!trainDescCollection.empty()` / `!utrainDescCollection.empty()` guards before indexing and restructures the rows computation (removes 625, 629, 631, 632, 633 exactly) | BUG-154 DescriptorMatcher::checkMasks heap OOB / null vector dereference with UMat or empty train descriptors | exact same defect | yes | yes |
| opencv-c4f59cf36a65 | f290ff215e "features2d: fix ORB::setFirstScale() handling": `cvRound(image.cols/getScale(0, firstLevel, scaleFactor))` replaced by `level0_inv_scale = 1.0f / getScale(0, firstLevel, scaleFactor)` multiplication, and per-level `image.cols/scale` by `image.cols * inv_scale` (removes 1028-1030 and 1036 exactly) | BUG-157 ORB pyramid layout overlap / crash when firstLevel > 0 and NaN crash when scaleFactor == 1.0f | bundled finding; the "pyramid layout overlap / crash when firstLevel > 0" claim is exactly the level-0 scale defect fixed here; the scaleFactor==1.0f NaN claim is not verified by this commit | yes | yes |
| opencv-9147e633a50f | a1e96a7deb "Update seamless_cloning.cpp": adds `if (roi_s.empty()) return;` right after `Rect roi_s = boundingRect(mask);` (insertion-only hunk at 78) | BUG-193 SeamlessCloning heap OOB access on 1-channel inputs, negative resize crash on small/empty masks, and wrong MIXED_CLONE metric | bundled finding; the "negative resize crash on small/empty masks" claim is exactly the guarded path (empty boundingRect used to flow into a negative/empty destination ROI); the 1-channel and MIXED_CLONE claims are not part of this fix | yes | no (strict set empty, insertion-only oracle) |

## Rejected line-overlaps (4 pair verdicts on 4 bugs)

- opencv-065ab5cc0087 / BUG-022: fix 7366eebebb "core: fix condition in OutputArray::create(allowTransposed=True)" matches all 4 oracle hunks exactly (rewrites the allowTransposed blocks at 1290-1300/1324-1334 and converts the CV_Assert lines 1308/1312/1314/1342/1346/1348 to CV_CheckTypeEQ/CV_CheckEQ). Neon claims the fixedDepthMask test shifts by CV_MAT_TYPE instead of CV_MAT_DEPTH (lines 1306/1340, "breaking cv::solvePoly"): that line is context-only for this fix, is untouched by it, and still reads `((1 << CV_MAT_TYPE(flags)) & fixedDepthMask) != 0` in current upstream (never fixed). Different mechanism, line overlap only. REJECT.
- opencv-08979782855f / BUG-045: fix 1f0bfc8d83 "Fix angle discretization in Hough transforms" adds a `computeNumangle()` helper (hunk at 68, insertion-only) and replaces the five `int numangle = cvRound(...)` lines (133, 478, 795, 849, 959) exactly; the imgproc.hpp doc hunks match with about -20 lines of drift. Neon claims "unchecked accumulator index in cv::HoughLinesPointSet causes arbitrary heap OOB write / SEGV"; that mechanism corresponds to a different upstream fix, cb286a66be (PR #21030, adds `if ( r >= 0 && r <= numrho )` around `accum[(n+1) * (numrho+2) + r+1]++;`), which is not this bug's oracle. The oracle's fix corrects theta discretization (missing last angle / duplicate detections), a correctness bug, not the bounds bug. REJECT.
- opencv-cb9f44f5771a / BUG-157: fix 2bf4f5c151 (squash of PR #26366 fix-orb.cpp) replaces `Mat image = _image.getMat(), mask = _mask.getMat();` with a `threshold(_mask, mask, 0, 255, THRESH_BINARY)` construction (plus one whitespace line); oracle hunks match structurally (2 hunks, old_count 7 each, one removed line at offset +3 in each) with about -53 lines of drift. Neon claims ORB pyramid layout overlap when firstLevel > 0; that defect's fix is f290ff215e (accepted against opencv-c4f59cf36a65 above), not this mask-handling change. Different mechanism, line overlap only. REJECT.
- opencv-849409d58b10 / BUG-041: fix 07cf36cbb0 (squash of PR #27587, JSON key backslash support) rewrites parseKey's key-character loop to skip backslash escapes and accumulates `key_name` instead of slicing `beg..ptr`; oracle hunks match structurally (2 hunks, old_count 10 and 7, removed-line offsets +3/+5/+6 and +3) with recorded old_start drifted -24/-16 (the diff really sits at 419-428 and 430-436 of the parent blob). Neon claims "JSONParser::parseKey stale pointer after skipSpaces": the pre-image already contains the `if (!ptr) CV_PARSE_ERROR_CPP("Invalid input");` guard the finding describes, and the maintainer changed escape handling instead. Different mechanism, line overlap only. REJECT.

## Clear misses (34 bugs, including the 4 rejected-overlap bugs above and 1 not matchable)

opencv-03814c751e45 (calibration.cpp), opencv-065ab5cc0087 (matrix_wrap.cpp, rejected overlap
above), opencv-08979782855f (imgproc.hpp/hough.cpp, rejected overlap above), opencv-0d3161877178
(approx.cpp), opencv-140d51577a07 (resize.cpp), opencv-174d41f7934b (subdivision2d.cpp),
opencv-1d1387aa8e47 (imgwarp.cpp), opencv-35e95d5fef31 (persistence.cpp), opencv-3ddefc7290c5
(tree.cpp), opencv-4320d091f246 (persistence.cpp), opencv-4344998a81e0 (hough.cpp),
opencv-5ff1b89640bd (resize.cpp), opencv-6c432b0cd808 (lsd.cpp), opencv-72b6a063e735
(intersection.cpp), opencv-77dbf1631b69 (drawing.cpp), opencv-836aa6f1bcdb
(matrix_expressions.cpp), opencv-83d848ddf557 (persistence.hpp/persistence.cpp),
opencv-849409d58b10 (persistence_json.cpp, rejected overlap above), opencv-898ee6013960
(phasecorr.cpp), opencv-8c7ec21f40f2 (lda.cpp), opencv-a3f10a0641a3 (boost.cpp/rtrees.cpp),
opencv-a841d77e12fa (homography_decomp.cpp), opencv-b27a0cb90aed (persistence_xml.cpp),
opencv-b7c9f43a731b (array.cpp), opencv-b95e3c7e7f80 (ptsetreg.cpp), opencv-c4fd47005bde
(drawing.cpp), opencv-cb9f44f5771a (orb.cpp, rejected overlap above), opencv-cef786b62d8e
(grfmt_tiff.cpp), opencv-cfc1dfc23f11 (contours.cpp), opencv-d97911c694c2 (color_yuv.cpp; empty
region, not matchable), opencv-da1a55ec7dbb (color_lab.cpp), opencv-dcdb346f556f
(calibration.cpp), opencv-eb23b61a6803 (distransform.cpp), opencv-f418aa091479 (drawing.cpp).

## Score

- Neon: region 13/47 (27.7%), strict 9/47 (19.1%; four accepted findings count region-only because
  their bugs' oracles are insertion-only with empty strict sets: BUG-015, BUG-021, BUG-112, BUG-193)
- Parasoft: region 74.5%, strict 40.4%
- Novel findings: 249 of 262 findings did not accept any benchmark bug
  (13 findings accepted at least one bug: BUG-009, BUG-014, BUG-015, BUG-020, BUG-021, BUG-064,
  BUG-077, BUG-105, BUG-112, BUG-128, BUG-154, BUG-157, BUG-193)
