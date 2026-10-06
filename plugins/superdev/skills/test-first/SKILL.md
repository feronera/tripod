---
name: test-first
description: Implement an approved plan test-first. Write failing tests from spec edge cases, commit them, lock tests with .pod/lock-tests, then implement until make test passes without touching locked tests. Use when the user says "เริ่มเขียนโค้ด", "ทำตาม plan", "test first", "TDD", "implement the plan".
---

# Test-first (SuperDev: Dev และ QA)

เป้าหมาย: โค้ดที่ผ่าน `make test` โดย test ถูกเขียนและล็อกก่อนเขียนโค้ด

## ขั้นตอน
1. ตรวจว่า gate 3 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 3`
   หากไม่ผ่าน ให้แจ้งมนุษย์และหยุด
2. อ่าน spec.md (Requirements และ Edge cases) และ plan.md (Order of work)
3. เขียน test ใน `tests/` ด้วย unittest ให้ครบทุก requirement และทุก edge case
   ตั้งชื่อ test ให้อ้างอิง R หรือ E เช่น `test_r1_...`, `test_e2_...`
4. รัน `make test` และยืนยันว่า test ใหม่ fail ด้วยเหตุผลที่ถูกต้อง (ไม่ใช่ import error หรือพิมพ์ผิด)
5. แสดงรายการ test ให้มนุษย์ตรวจ เมื่อมนุษย์ยืนยันแล้วให้ commit:
   `git add tests && git commit -m "test(NNN): failing tests from spec"`
6. ขอให้มนุษย์ล็อก tests: `touch .pod/lock-tests`
   หลังจากนี้ hook protect-tests จะปฏิเสธการแก้ไฟล์ใน `tests/`
7. เขียนโค้ดใน `app/` ทีละ requirement ตามลำดับใน plan.md แล้วรัน `make test` ทุกครั้ง
8. ห้ามแก้ test ที่ล็อกแล้ว และห้ามหลบ hook ด้วยวิธีอื่น เช่น ใช้ Bash เขียนทับไฟล์
   หากเห็นว่า test ผิด ให้หยุดและอธิบายเหตุผลให้มนุษย์ตัดสิน
9. เมื่อ `make test` ผ่านครบ ให้รัน `make check` แล้ว commit โค้ด

## สิ่งที่ห้ามทำ
- ห้ามเพิ่ม dependency นอก Python standard library
- ห้ามลบไฟล์ `.pod/lock-tests` เอง

## จบงาน
แจ้งมนุษย์ว่าขั้นต่อไปคือ `/superdev:review` และหลังจบ change ให้ปลดล็อกด้วย `rm .pod/lock-tests`
