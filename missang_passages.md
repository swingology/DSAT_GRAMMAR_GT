# Official Questions Missing Passages

Live database audit: 2026-07-18.

- 54 official question records are missing passage content.
- Those records represent 51 distinct test/question locations.
- All listed records are marked `draft` for admin review.
- Three locations have duplicate database records; they are identified below.

## 2024

### Test01

- 2024 - Test01_Sec01_Mod02 Q26

### Test02

- 2024 - Test02_Sec01_Mod02A Q12
- 2024 - Test02_Sec01_Mod02A Q13
- 2024 - Test02_Sec01_Mod02B Q1
- 2024 - Test02_Sec01_Mod02B Q2
- 2024 - Test02_Sec01_Mod02B Q3
- 2024 - Test02_Sec01_Mod02B Q4
- 2024 - Test02_Sec01_Mod02B Q6
- 2024 - Test02_Sec01_Mod02B Q8
- 2024 - Test02_Sec01_Mod02B Q9
- 2024 - Test02_Sec01_Mod02B Q12
- 2024 - Test02_Sec01_Mod02B Q13
- 2024 - Test02_Sec01_Mod02B Q14
- 2024 - Test02_Sec01_Mod02B Q15
- 2024 - Test02_Sec01_Mod02B Q16
- 2024 - Test02_Sec01_Mod02B Q17
- 2024 - Test02_Sec01_Mod02B Q18
- 2024 - Test02_Sec01_Mod02B Q19
- 2024 - Test02_Sec01_Mod02B Q21

### Test03

- 2024 - Test03_Sec01_Mod02A Q14
- 2024 - Test03_Sec01_Mod02A Q15

### Test04

- 2024 - Test04_Sec01_Mod02 Q11
- 2024 - Test04_Sec01_Mod02 Q12
- 2024 - Test04_Sec01_Mod02 Q14

### Test05

- 2024 - Test05_Sec01_Mod01 Q8
- 2024 - Test05_Sec01_Mod01 Q9
- 2024 - Test05_Sec01_Mod02B Q16
- 2024 - Test05_Sec01_Mod02B Q17
- 2024 - Test05_Sec01_Mod02B Q18
- 2024 - Test05_Sec01_Mod02B Q19 (2 database records)
- 2024 - Test05_Sec01_Mod02B Q20 (2 database records)
- 2024 - Test05_Sec01_Mod02B Q21
- 2024 - Test05_Sec01_Mod02B Q22
- 2024 - Test05_Sec01_Mod02B Q23
- 2024 - Test05_Sec01_Mod02B Q24
- 2024 - Test05_Sec01_Mod02B Q25

### Test07

- 2024 - Test07_Sec01_Mod01 Q16

### Test08

- 2024 - Test08_Sec01_Mod01 Q9
- 2024 - Test08_Sec01_Mod01 Q12
- 2024 - Test08_Sec01_Mod01 Q14

### Test09

- 2024 - Test09_Sec01_Mod01 Q11 (2 database records)

### Test10

- 2024 - Test10_Sec01_Mod01 Q19

## 2025

### Test05

- 2025 - Test05_Sec01_Mod02 Q19
- 2025 - Test05_Sec01_Mod02 Q21
- 2025 - Test05_Sec01_Mod02 Q23
- 2025 - Test05_Sec01_Mod02 Q24
- 2025 - Test05_Sec01_Mod02 Q25
- 2025 - Test05_Sec01_Mod02 Q28

### Test06

- 2025 - Test06_Sec01_Mod01 Q20
- 2025 - Test06_Sec01_Mod01 Q24
- 2025 - Test06_Sec01_Mod01 Q25

## Duplicate Database Records

- 2024 - Test05_Sec01_Mod02B Q19:
  `468146fd-b14f-558e-9937-8bae131906c6`,
  `dba07e16-5237-5aa8-bea8-f5a431c04e1d`
- 2024 - Test05_Sec01_Mod02B Q20:
  `20b24d6b-b06b-5262-b529-cd0706c21cd5`,
  `63ed1062-e65f-571f-8875-9e5f35af7e54`
- 2024 - Test09_Sec01_Mod01 Q11:
  `08ce2bf4-7f23-5a49-9492-f9e2de8a78b7`,
  `26460ab4-17a5-5cda-90be-2e3badda7299`

## Audit Rule

A question is included when it is official, has no stored passage, and either:

- contains the explicit placeholder `The text for this question is missing.`; or
- uses a passage-bearing stimulus mode but contains only a short generic question stem rather
  than the referenced passage.
