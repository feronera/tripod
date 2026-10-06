---
name: acceptance
description: Business-side gate 4 check. Compare the PR against the Success measure in intent.md, run or collect demo steps, and write acceptance.md with accept or reject plus reason. Use when the user says "ตรวจรับงาน", "acceptance", "รับมอบงาน", "UAT", "accept the PR".
---

# เขียน acceptance.md (SuperBiz: ตรวจรับ gate 4)

เป้าหมาย: ได้ `docs/changes/NNN-slug/acceptance.md` ที่ระบุ accept หรือ reject พร้อมเหตุผล

## ขั้นตอน
1. อ่าน intent.md (Success measure), spec.md (Requirements) และ `docs/templates/acceptance.md`
2. ตรวจว่า gate 3 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 3`
3. ขอสรุปการเปลี่ยนแปลงของ PR จากมนุษย์ หรืออ่านด้วย `git diff main...HEAD --stat`
   แล้วสรุปเป็นภาษาที่ผู้ไม่ใช่นักพัฒนาเข้าใจ
4. ใช้ demo steps ที่ SuperDev ให้ไว้ใน plan.md หรือ PR หากไม่มี ให้ถามมนุษย์ ห้ามคิดขั้นตอนเอง
5. ทำ demo ทีละขั้น บันทึกผลที่คาดหวังและผลจริง
6. เทียบผลกับ Success measure ทีละข้อ
   - หากวัดได้หลัง release เท่านั้น ให้ระบุวิธีวัดและวันที่จะวัด
7. เขียน Decision: `accept` หรือ `reject` พร้อมเหตุผลที่อ้างอิงผล demo
   หาก reject ให้ระบุสิ่งที่ต้องแก้เป็นข้อ ๆ
8. ห้ามตัดสินแทนมนุษย์ ให้เสนอคำตัดสินและให้ SuperBiz ยืนยัน

## สิ่งที่ห้ามทำ
- ห้ามรัน `scripts/gate.sh` และห้ามแก้ `gates.log`
- ห้ามแก้โค้ดหรือ test

## จบงาน
แจ้งมนุษย์ว่า
1. SuperDev (owner ของ gate 4) รัน `scripts/gate.sh docs/changes/NNN-slug 4` ก่อน
2. SuperBiz ยืนยันคำตัดสินแล้วรันคำสั่งเดียวกัน
3. หาก `Risk: high` escalation ต้องรันคำสั่งเดียวกันด้วย
