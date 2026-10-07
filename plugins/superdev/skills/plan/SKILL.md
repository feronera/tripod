---
name: plan
description: Write plan.md for an approved spec, data shape first, then a throughput checkpoint, parallel parts, files to change, order of work, risks, proof, rollback and a 3-line Thai summary for SuperBiz. Always starts in plan mode. Use when the user says "วางแผน", "เขียน plan", "ทำ plan.md", "plan this change", "how do we build this".
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
5. เขียน `## Data shape` ก่อนส่วนอื่น: โครงข้อมูลหลักที่โค้ดจะใช้ และโครงสร้างที่ใช้จัดข้อมูล
   เช่น ตาราง (dict), state machine, typed record เลือกโครงที่ทำให้กรณีผิดเกิดขึ้นไม่ได้
   และลดเงื่อนไข if ที่กระจายหลายไฟล์ เมื่อโครงข้อมูลถูก logic ที่ตามมาจะตรงไปตรงมา
6. เขียน `## Throughput checkpoint` ให้ครบ 4 บรรทัด (ใช้ `n/a: <เหตุผล>` ได้)
   - Blocking first steps: งานที่ต้องเสร็จก่อนงานอื่นจึงเริ่มได้ เช่น test ที่ fail หรือโครงข้อมูล
   - Independent workstreams: งานที่ทำแยกกันได้โดยไม่รอกัน
   - Shared mutable state: ไฟล์หรือข้อมูลที่หลายส่วนต้องแก้ร่วมกัน
   - Smallest safe decomposition: การแบ่งงานที่เล็กที่สุดที่แต่ละชิ้นจบด้วยการตรวจได้
7. เขียน `## Parallel parts`
   - ถ้าไม่แบ่งงาน ให้เขียน `none: <เหตุผล>`
   - ถ้าแบ่ง ต้องมีอย่างน้อย 2 ส่วนแบบ `### <ชื่อ>` แต่ละส่วนมีบรรทัด `files: a.py, b.py`
     และไฟล์ของแต่ละส่วนต้องไม่ซ้ำกัน หากต้องแก้ไฟล์เดียวกัน ให้แยก state ออกก่อน หรือทำทีละส่วน
8. ร่างส่วนที่เหลือตาม template
   - Files to change: ทุกไฟล์ผูกกับ requirement (R1, R2, ...)
   - Order of work: เริ่มจาก test ที่ fail ก่อนเสมอ แล้วล็อก tests จากนั้นเป็น unit เล็ก ๆ
     ที่แต่ละ unit จบด้วย `make test` ผ่าน
   - Risks: ความเสี่ยงทางเทคนิคและวิธีลด
   - Proof: วิธีพิสูจน์แต่ละ requirement (test ใด หรือ demo ใด)
   - Rollback: ขั้นตอนย้อนกลับที่ทำได้จริง
9. Stack คือ Python 3 standard library เท่านั้น ห้ามวางแผนเพิ่ม dependency
10. เพิ่มหัวข้อ "สรุปให้ SuperBiz" 3 บรรทัด ภาษาไทยที่ไม่ใช้ศัพท์เทคนิค
    1. ทำอะไร
    2. ผู้ใช้จะเห็นอะไรเปลี่ยน
    3. ความเสี่ยงที่ SuperBiz ควรรู้
11. นำเสนอแผนให้มนุษย์อนุมัติ เมื่อออกจาก plan mode แล้วจึงเขียน plan.md
12. ตรวจรูปแบบด้วย `scripts/gate-check.sh docs/changes/NNN-slug 3`
    ข้อความ `gate 3: plan.md ...` บอกส่วนที่ขาด ให้แก้จนไม่มีข้อความนี้
    (ข้อความ "ยังไม่มีการอนุมัติ" เป็นเรื่องปกติก่อนมนุษย์ลงชื่อ)
    `scripts/gate.sh` จะปฏิเสธ plan ที่ขาดส่วนเหล่านี้

## สิ่งที่ห้ามทำ
- ห้ามแก้โค้ดหรือ test ใน skill นี้
- ห้ามรัน `scripts/gate.sh` และห้ามแก้ `gates.log`

## จบงาน
แจ้งมนุษย์ว่า
1. SuperDev รัน `scripts/gate.sh docs/changes/NNN-slug 3`
2. SuperBiz อ่าน "สรุปให้ SuperBiz" ตรวจว่ายังตรงกับ intent แล้วรันคำสั่งเดียวกัน
3. ขั้นต่อไปคือ `/superdev:test-first` แล้ว `/superdev:build`
   หาก Parallel parts มีหลายส่วน ให้ดู `docs/parallel-agents.md`
   หากมีแนวทางออกแบบสองทางที่ยังตัดสินไม่ได้ ให้ใช้ `/superdev:arena`
