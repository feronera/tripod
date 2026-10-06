---
name: spec
description: Turn intent.md and ux-brief.md into spec.md with numbered requirements, edge cases, flagged concerns and out-of-scope, using the ba-researcher agent for code impact. Use when the user says "เขียน spec", "ทำ spec", "แปลง intent เป็น spec", "write the spec", "spec this change".
---

# ร่าง spec.md (SuperBiz: BA)

เป้าหมาย: ได้ `docs/changes/NNN-slug/spec.md` ที่พร้อมให้มนุษย์ลงชื่อ gate 2

## ขั้นตอน
1. อ่าน intent.md, ux-brief.md (ถ้ามี) และ `docs/templates/spec.md`
2. ตรวจว่า gate 1 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 1`
   หากไม่ผ่าน ให้แจ้งมนุษย์และหยุด
3. ส่งคำถามให้ agent `ba-researcher` เช่น
   "intent นี้แตะโค้ดหรือข้อมูลส่วนใด และมีพฤติกรรมเดิมใดที่ต้องคงไว้"
   ใช้คำตอบที่มีอ้างอิงไฟล์เท่านั้น
4. เขียน Requirements เป็น R1, R2, ... แต่ละข้อขึ้นต้นด้วย "ระบบต้อง" และระบุวิธีตรวจ (test หรือ demo)
5. เขียน Edge cases เป็น E1, E2, ... ให้ครอบคลุม
   - ข้อมูลว่างหรือไม่พบ
   - ข้อมูลผิดรูปแบบ
   - สิทธิ์: ผู้ใช้ต้องไม่เห็นข้อมูลของผู้อื่น
   - states จาก ux-brief.md
6. Flagged concerns: สิ่งที่ขัดกับโค้ดเดิม ความเสี่ยงที่พบ และคำถามที่ต้องให้มนุษย์ตัดสิน พร้อมอ้างอิงไฟล์
7. Out of scope: สิ่งที่ไม่ทำใน change นี้ เพื่อกันขอบเขตบานปลาย
8. หาก Risk ใน intent.md ดูต่ำเกินจริงจากผลของ ba-researcher ให้ระบุใน Flagged concerns
   ห้ามแก้ intent.md เอง เพราะ gate 1 จะ stale
9. ตรวจด้วยคำถามของ Gate 2 ใน `docs/gates.md`

## สิ่งที่ห้ามทำ
- ห้ามรัน `scripts/gate.sh` และห้ามแก้ `gates.log`
- ห้ามแก้ไฟล์นอก `docs/`

## จบงาน
แจ้งมนุษย์ว่า
1. SuperBiz รัน `scripts/gate.sh docs/changes/NNN-slug 2`
2. SuperDev ตรวจทานแล้วรันคำสั่งเดียวกัน
3. หาก `Risk: high` ผู้มีชื่อเป็น escalation ใน pod.yml ต้องรันคำสั่งเดียวกันด้วย
