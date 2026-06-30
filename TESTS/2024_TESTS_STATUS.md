# 2024 Bluebook Tests — Ingestion Status

Generated: 2026-06-26  
DB: `dsat_dev` | `content_origin = 'official'` | `source_release_year = 2024`

---

## Summary

All 10 Bluebook practice tests are nominally present, but **data integrity is poor** across most tests. Common issues: duplicate rows under inconsistent exam codes (`'01'` vs `'1'`), mixed module naming (`mod02` vs `mod02A` vs `mod02B`), and inflated question counts suggesting re-ingestion without deduplication.

| Test | Expected q | Actual rows | Verdict |
|------|-----------|-------------|---------|
| 1 | 81 (3×27) | mod01 27 + mod02A 27 + mod02B 27 = 81, but split across `'01'`/`'1'` codes | ⚠️ duplicate codes |
| 2 | 81 | mod01 25 + mod02 27 + mod02A 27 = split across `'02'`/`'2'`/`'SAT'` | ⚠️ chaotic naming |
| 3 | 81 | mod01 27 + mod02A 27 + mod02B 27 | ✅ cleanest |
| 4 | 81 | mod01 25+2=27 + mod02 27 + mod02B 27 = duplicate mod01 rows; both mod02/mod02B present | ⚠️ dup mod01 + module naming |
| 5 | 81 | mod01 25+2=27 + mod02 27 + mod02B 25 = mod02B only 25/27 q | ⚠️ missing 2 q in mod02B |
| 6 | 81 | mod01 27 + mod02A 27 + mod02B 27 | ✅ clean |
| 7 | 81 | mod01 27 + mod02A 27 + mod02B 27 | ✅ clean (no test names) |
| 8 | 81 | mod01 27 + mod02A 27 + mod02B 27 | ✅ clean |
| 9 | 81 | 6 rows — overlapping module codes, some duplicate counts | ❌ worst integrity |
| 10 | 81 | mod01 27 + mod02A 27 + mod02B 27 | ✅ clean |

**Stray row:** `verbal / mod02B / "05"` — 27 questions, appears to be a mis-tagged Test 5 mod02B.

---

## Raw DB Rows

```
exam_code | module | test_name                    | q_count
----------+--------+------------------------------+---------
01        | 01     | Test01_ENG_Sec01_Mod01       | 27
01        | 02A    | Bluebook Practice Test 1     | 26      ← split w/ below
01        | 02A    | Test01_ENG_Sec01_Mod02A      |  1      ← dup
02        | 01     | Bluebook Practice Test 2     | 25      ← only 25
02        | 02     | Test02_ENG_Sec01_Mod02B      | 27
03        | 01     | Bluebook Practice Test 3     | 27
03        | 02A    | Test03_ENG_Sec01_Mod02A      | 27
03        | 02B    | Test03_ENG_Sec01_Mod02B      | 27
04        | 01     | Bluebook Practice Test 4     | 25      ← split w/ below
04        | 01     | Test04_ENG_Sec01_Mod01       |  2      ← dup
04        | 02     | Bluebook Practice Test 4     | 27
04        | 02B    | Test04_ENG_Sec01_Mod02B      | 27
05        | 01     | Bluebook Practice Test 5     | 25      ← split w/ below
05        | 01     | Test05_ENG_Sec01_Mod01       |  2      ← dup
05        | 02     | (blank)                      | 27
05        | 02B    | (blank)                      | 25      ← missing 2 q
06        | 01     | Test06_ENG_Sec01_Mod01       | 27
06        | 02A    | Test06_ENG_Sec01_Mod02A      | 27
06        | 02B    | Test06_ENG_Sec01_Mod02B      | 27
07        | 01     | (blank)                      | 27
07        | 02A    | (blank)                      | 27
07        | 02B    | (blank)                      | 27
08        | 01     | Bluebook Practice Test 8     | 27
08        | 02A    | (blank)                      | 27
08        | 02B    | Test08_ENG_Sec01_Mod02B      | 27
09        | 01     | (blank)                      | 26      ← dup mod01
09        | 01     | Bluebook Practice Test 9     | 27      ← dup mod01
09        | 02     | Bluebook Practice Test 9     | 27
09        | 02A    | (blank)                      | 26
09        | 02B    | (blank)                      | 26      ← dup mod02B
09        | 02B    | Bluebook Practice Test 9     | 27      ← dup mod02B
1         | 02B    | Test01_ENG_Sec01_Mod02B      | 27      ← orphan (bare '1')
10        | 01     | (blank)                      | 27
10        | 02A    | Bluebook Practice Test 10    | 27
10        | 02B    | Test10_ENG_Sec01_Mod02B      | 27
2         | 02A    | Test02_ENG_Sec01_Mod02A      | 27      ← orphan (bare '2')
SAT       | 01     | Test02_ENG_Sec01_Mod01       | 27      ← mis-tagged exam_code
verbal    | 02B    | 05                           | 27      ← stray / mis-tagged
```

---

## Issues Requiring Cleanup

1. **Duplicate exam codes** — Tests 1 and 2 have rows under both zero-padded (`'01'`, `'02'`) and bare (`'1'`, `'2'`) codes. Orphan rows under `'1'` and `'2'` should be merged or deleted.
2. **`'SAT'` exam code** — 27 questions tagged `source_exam_code='SAT'` that belong to Test 2 mod01.
3. **`'verbal'` exam code** — 27 questions with no proper exam code; likely Test 5 mod02B.
4. **Duplicate module rows** — Tests 4 and 5 have split mod01 entries (25+2). Test 9 has duplicate mod01 and mod02B rows.
5. **Mixed module naming** — Some tests use `mod02` (no suffix), others use `mod02A`/`mod02B`. Needs standardisation.
6. **Blank test names** — Tests 5 (mod02/02B), 7 (all), 8 (mod02A), 9 (most), 10 (mod01) have no `source_test_name`.
7. **Test 5 mod02B shortfall** — Only 25/27 questions ingested.
8. **Test 2 mod01 shortfall** — Only 25/27 questions ingested under `'02'`.
