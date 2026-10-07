---
name: bug-fix
description: Fix a bug at its root cause. Reproduce first and show the failing behavior, ask why until the cause is in code, write a failing test that reproduces it, lock tests, fix, and prove the fix with the same reproduction. Uses the normal change flow. Use when the user says "แก้ bug", "มี bug", "ระบบทำงานผิด", "bug fix", "fix this bug".
---

# แก้ bug ที่ต้นเหตุ (SuperDev: Dev และ QA)

เป้าหมาย: แก้ที่สาเหตุจริง และพิสูจน์ด้วยการทำซ้ำแบบเดียวกับที่พบ bug

## 1. ทำซ้ำให้เห็นก่อน
- หาคำสั่งหรือขั้นตอนที่ทำให้ bug เกิด แล้วรันให้เห็นผลผิดจริง
- บันทึกคำสั่งและผลลัพธ์ที่ได้ (ตัดข้อมูลส่วนบุคคลออก) เช่น
  ```
  $ <คำสั่งที่ทำให้เกิด bug>
  <ผลที่ผิด>
  คาดหวัง: <ผลที่ถูกต้อง>
  ```
- หากทำซ้ำไม่ได้ ห้ามแก้ ให้รายงานสิ่งที่ลองแล้วและขอข้อมูลเพิ่มจากมนุษย์

## 2. หาต้นเหตุ
- ถาม "ทำไม" ต่อไปเรื่อย ๆ จนได้คำตอบที่ชี้ไปที่บรรทัดโค้ด (`path:line`) หรือข้อมูลที่ผิด
- ห้ามเดา เมื่อไม่แน่ใจ ให้เพิ่มการพิมพ์ค่าชั่วคราวหรืออ่าน error จริง แล้วลบออกก่อน commit
- ค้นหารูปแบบเดียวกันในโค้ดส่วนอื่น (`grep`) และแก้ทุกจุดที่มีสาเหตุเดียวกัน
- การเพิ่ม `if x is None: return` เพื่อปิด error เป็นการแก้อาการ ไม่ใช่ต้นเหตุ

## 3. เข้า change flow ตามปกติ
1. ขอให้มนุษย์รัน `scripts/new-change.sh <slug>`
2. ร่าง intent.md: Problem คือ bug พร้อมคำสั่งทำซ้ำและผลที่ได้, Success measure คือ
   คำสั่งเดิมให้ผลที่ถูกต้อง, Risk ตาม `docs/risk-tiers.md`
3. ผ่าน gate 1 ถึง 3 ตามปกติ plan.md ระบุต้นเหตุใน Data shape หรือ Risks

## 4. test ที่ทำซ้ำ bug แล้วล็อก
- เขียน test ที่ fail เพราะ bug นี้ และผ่านเมื่อแก้ถูก (assert ค่าที่ถูกต้องที่ระบุชัด)
- รัน `make test` เพื่อยืนยันว่า test fail ด้วยอาการเดียวกับที่ทำซ้ำได้
- commit test แล้วขอให้มนุษย์ `touch .pod/lock-tests`

## 5. แก้และพิสูจน์
- แก้โค้ดที่ต้นเหตุตาม `/superdev:build`
- รันคำสั่งทำซ้ำจากข้อ 1 อีกครั้ง และแสดงผลลัพธ์ที่ถูกต้องเทียบกับผลเดิม
- รัน `make check`

## สิ่งที่ห้ามทำ
- ห้ามแก้อาการโดยไม่รู้ต้นเหตุ
- ห้ามแก้ test ที่ล็อกให้ผ่าน
- ห้ามรัน `scripts/gate.sh`

## จบงาน
ส่งต่อ `/superdev:review` และแนบคำสั่งทำซ้ำกับผลก่อนและหลังแก้ใน review.md
