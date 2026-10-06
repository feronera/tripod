---
name: plan
description: Write plan.md for an approved spec (files to change, order of work, risks, proof, rollback) plus a 3-line Thai summary for SuperBiz. Always starts in plan mode. Use when the user says "วางแผน", "เขียน plan", "ทำ plan.md", "plan this change", "how do we build this".
---

# เขียน plan.md (SuperDev: SA)

เป้าหมาย: ได้ `docs/changes/NNN-slug/plan.md` ที่พร้อมให้มนุษย์ลงชื่อ gate 3

## ขั้นตอน
1. เริ่มใน plan mode เสมอ หากยังไม่อยู่ใน plan mode ให้ขอให้มนุษย์กด Shift+Tab จนเข้า plan mode
   ระหว่างนี้อ่านอย่างเดียว ห้ามแก้ไฟล์
2. ตรวจว่า gate 2 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 2`
   หากไม่ผ่าน ให้แจ้งมนุษย์และหยุด
3. อ่าน intent.md, spec.md, ux-brief.md (ถ้ามี), `docs/templates/plan.md` และ `AGENTS.md`
4. อ่านโค้ดใน `app/` และ test ใน `tests/` ที่เกี่ยวข้อง
5. ร่างแผนตาม template
   - Files to change: ทุกไฟล์ผูกกับ requirement (R1, R2, ...)
   - Order of work: เริ่มจาก test ที่ fail ก่อนเสมอ แล้วล็อก tests
   - Risks: ความเสี่ยงทางเทคนิคและวิธีลด
   - Proof: วิธีพิสูจน์แต่ละ requirement (test ใด หรือ demo ใด)
   - Rollback: ขั้นตอนย้อนกลับที่ทำได้จริง
6. Stack คือ Python 3 standard library เท่านั้น ห้ามวางแผนเพิ่ม dependency
7. เพิ่มหัวข้อ "สรุปให้ SuperBiz" 3 บรรทัด ภาษาไทยที่ไม่ใช้ศัพท์เทคนิค
   1. ทำอะไร
   2. ผู้ใช้จะเห็นอะไรเปลี่ยน
   3. ความเสี่ยงที่ SuperBiz ควรรู้
8. นำเสนอแผนให้มนุษย์อนุมัติ เมื่อออกจาก plan mode แล้วจึงเขียน plan.md

## สิ่งที่ห้ามทำ
- ห้ามแก้โค้ดหรือ test ใน skill นี้
- ห้ามรัน `scripts/gate.sh` และห้ามแก้ `gates.log`

## จบงาน
แจ้งมนุษย์ว่า
1. SuperDev รัน `scripts/gate.sh docs/changes/NNN-slug 3`
2. SuperBiz อ่าน "สรุปให้ SuperBiz" ตรวจว่ายังตรงกับ intent แล้วรันคำสั่งเดียวกัน
