---
name: test-first
description: Write failing tests from the spec edge cases that observe real behavior, check them with scripts/test-strength.sh, commit them and lock tests with .pod/lock-tests, then hand over to the build skill. Use when the user says "เริ่มเขียนโค้ด", "เขียน test ก่อน", "test first", "TDD", "implement the plan".
---

# Test-first (SuperDev: Dev และ QA)

เป้าหมาย: test ที่ fail ด้วยเหตุผลที่ถูกต้อง ตรวจพฤติกรรมจริง และถูกล็อกก่อนเขียนโค้ด

## ขั้นตอน
1. ตรวจว่า gate 3 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 3`
   หากไม่ผ่าน ให้แจ้งมนุษย์และหยุด
2. อ่าน spec.md (Requirements และ Edge cases) และ plan.md (Data shape และ Order of work)
3. เขียน test ใน `tests/` ด้วย unittest ให้ครบทุก requirement และทุก edge case
   ตั้งชื่อ test ให้อ้างอิง R หรือ E เช่น `test_r1_...`, `test_e2_...`
4. แต่ละ test ต้องเรียกโค้ดแบบที่ผู้ใช้เรียก และ assert ผลลัพธ์ด้วยค่าที่ระบุชัด
   หลีกเลี่ยง test อ่อน 5 แบบ ซึ่งยังผ่านได้แม้ทุกฟังก์ชันใน `app/` คืนค่า None
   - assert อ่อนหรือไม่มี assert: เช่น มีเพียง `assertTrue(x)` หรือ `assertIsNotNone(x)`
   - ตรวจเฉพาะ mock หรือการไม่มีข้อมูล: เช่น มีเพียง `assertIsNone(...)` หรือ `assertEqual(..., [])`
     ให้จับคู่กับกรณีที่มีข้อมูลใน test เดียวกัน
   - อ้างอิงตัวเอง: ค่าที่คาดหวังมาจากโค้ดที่กำลังทดสอบ เช่น `assertEqual(f(a), f(a))`
   - ตรึงค่าคงที่: assert ค่าคงที่หรือ config ที่เขียนไว้ในโค้ดซ้ำ แทนการทดสอบกลไกที่ใช้ค่านั้น
   - fixture ตรวจ fixture: assert ข้อมูลที่ test สร้างเอง โดยไม่ได้เรียกโค้ดที่ทดสอบ
5. รัน `make test` และยืนยันว่า test ใหม่ fail ด้วยเหตุผลที่ถูกต้อง (ไม่ใช่ import error หรือพิมพ์ผิด)
6. รัน `scripts/test-strength.sh` ก่อนล็อก
   - `WEAK <test id>`: แก้ test ตามคำแนะนำ แล้วรันใหม่จนไม่มี WEAK
   - `FAIL (ปกติ) <test id>`: test ที่ยังแดงอยู่ ยังวัดความแข็งไม่ได้ ให้ตรวจเองตาม 5 แบบข้างต้น
     `make check` จะตรวจซ้ำเมื่อโค้ดเสร็จ หากพบ test อ่อนหลังล็อก ต้องหยุดและแจ้งมนุษย์
7. แสดงรายการ test ให้มนุษย์ตรวจ เมื่อมนุษย์ยืนยันแล้วให้ commit:
   `git add tests && git commit -m "test(NNN): failing tests from spec"`
8. ขอให้มนุษย์ล็อก tests: `touch .pod/lock-tests`
   หลังจากนี้ hook protect-tests จะปฏิเสธการแก้ไฟล์ใน `tests/`

## สิ่งที่ห้ามทำ
- ห้ามเขียนโค้ดใน `app/` ใน skill นี้
- ห้ามเพิ่ม dependency นอก Python standard library
- ห้ามลบไฟล์ `.pod/lock-tests` เอง

## จบงาน
แจ้งมนุษย์ว่าขั้นต่อไปคือ `/superdev:build` และหลังจบ change ให้ปลดล็อกด้วย `rm .pod/lock-tests`
