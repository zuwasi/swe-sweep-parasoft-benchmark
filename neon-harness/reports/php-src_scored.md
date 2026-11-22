# php-src scored (Gemini 4 Neon bug hunt vs benchmark bugs)

- Repo: php-src, base commit c9c9815a08cbaa1451344c473fe7a1c2ace35df7 ("Prepare PHP 8.2.12")
- Neon report: 121 findings (BH-001..BH-121), all SUSPECTED (no repros)
- Benchmark bugs: 26 (3 with empty region sets: pdo_dbh.c, spl_iterators.c, phar_object.c; not matchable)

## Matcher result (reports/php-src_matches.json)
- Region hits on 4 bugs (strict on 3): 81a2694ec050, 67638986e670, 644f4c81235d, 3dd6d56bed43.

## Accepted
None.

## Rejected overlaps (line overlap, different mechanism)

| bug_id | reason | Neon finding | maintainer's fix | why rejected |
|---|---|---|---|---|
| php-src-81a2694ec050 | same-side tie-break (MEMORY) | BH-009 yield-from re-entrant UAF / Generator::throw NULL deref | 99e0d3fe098 (#15158) destruction of generators running in fibers during shutdown (IN_FIBER flag tracking through the generator node tree) | Different defect: fiber-shutdown destruction vs delegation re-entrancy; line overlap only. |
| php-src-67638986e670 | iterator compare on poisoned stale table | BH-012 wrong HashTable checked for HT_ITERATORS_OVERFLOW in zend_hash_iterator_pos_ex | cd53ce838a8 track HashTableIterators for copy-on-write copies (find_copy_pos search); the wrong-table overflow check Neon flagged is unchanged by the fix | Different defect: COW copy tracking vs the overflow-check argument; same function, adjacent lines. |
| php-src-644f4c81235d | missing return true in state deserializer | BH-109 Randomizer unserialize NULL deref / status leak | 1a428e528f9 (GH-21732) __unserialize must reject all-zero state (adds return false before return true) | Different defect: missing all-zero-state validation vs Randomizer lifecycle UAF. |
| php-src-3dd6d56bed43 | wrong strncasecmp length, OOB read | BH-060 soap unchecked object_init_ex | 476706165a (#14398, bug 69280) classmap fully-qualified-name comparison: zend_binary_strncasecmp length args used ZSTR_LEN(ce->name) for both strings | Different defect: object_init_ex failure handling vs strncasecmp length/OOB read. |

## Clear misses (all other 22 bugs)
No Neon finding touches their files/regions: zend_gc.c (2 bugs), zend_inheritance.c (2), user_filters.c, versioning.c, soap.c, php_spl.c, engine_xoshiro (beyond above), zend_hash.c COW (beyond above), php_encoding.c 779-797, assert.c, php_zip.c (2), math.c, zend_opcode.c, zend_hash.h, curl/interface.c, url_scanner_ex.re, curl/multi.c, zend_ast.c.

## Final score
- Region: 0/26 = 0.0%
- Strict: 0/26 = 0.0%
- Parasoft published (26 bugs): region 50.0%, strict 26.9%
- Novel findings: 121 (no benchmark overlap)
