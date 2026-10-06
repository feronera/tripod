---
name: intent
description: Draft intent.md for a new change with the PO, one question at a time, including Risk tier. Use when the user wants to start a change, write an intent, or says "ร่าง intent", "เริ่มงานใหม่", "เขียน intent.md", "draft intent", "new change".
---

# ร่าง intent.md (SuperBiz: PO)

เป้าหมาย: ได้ `docs/changes/NNN-slug/intent.md` ที่พร้อมให้มนุษย์ลงชื่อ gate 1

## ขั้นตอน
1. ถามว่าจะทำ change ใด หากยังไม่มีโฟลเดอร์ ให้ขอให้มนุษย์รัน `scripts/new-change.sh <slug>`
   และรอ path ที่คำสั่งพิมพ์ออกมา (คำสั่งจะปฏิเสธหากถึง WIP limit ให้แจ้งมนุษย์ตามข้อความนั้น)
2. อ่าน `docs/templates/intent.md`, `docs/risk-tiers.md` และ intent.md ในโฟลเดอร์ change
3. สัมภาษณ์ PO ทีละคำถาม รอคำตอบก่อนถามข้อถัดไป ตามลำดับนี้
   1. ปัญหาคืออะไร เกิดกับใคร มีหลักฐานอะไร
   2. ผู้ใช้หรือผู้ได้รับผลกระทบคือใคร
   3. Success measure เป็นตัวเลขใด ค่าปัจจุบันเท่าไร เป้าหมายเท่าไร ภายในเมื่อใด
   4. คำถาม 4 ข้อใน `docs/risk-tiers.md` ทีละข้อ
   5. มีข้อจำกัดใดบ้าง
4. กำหนด Risk ตามเกณฑ์ใน `docs/risk-tiers.md` หากไม่แน่ใจ ให้เลือกระดับที่สูงกว่า
   และเขียนบรรทัด `Risk: low`, `Risk: medium` หรือ `Risk: high` เพียงบรรทัดเดียว
5. เขียน intent.md ตาม template คง `Status: draft` ไว้
6. ห้ามแต่งตัวเลขหรือข้อเท็จจริง สิ่งที่ PO ไม่ทราบให้ใส่ใน Open questions
7. ตรวจด้วยคำถามของ Gate 1 ใน `docs/gates.md` แล้วรายงานข้อที่ยังไม่ผ่าน

## สิ่งที่ห้ามทำ
- ห้ามรัน `scripts/gate.sh` และห้ามแก้ `gates.log`
- ห้ามแก้ไฟล์นอก `docs/`

## จบงาน
แจ้งมนุษย์ว่า
1. SuperBiz ตรวจ intent.md แล้วรัน `scripts/gate.sh docs/changes/NNN-slug 1`
2. ขอให้ SuperDev ตรวจทาน (ทำได้จริงและวัดผลได้หรือไม่) แล้วรันคำสั่งเดียวกัน
3. ตรวจผลด้วย `scripts/gate-check.sh docs/changes/NNN-slug`
