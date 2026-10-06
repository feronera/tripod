---
name: release-notes
description: Write Thai release notes for customers and for internal teams from a change folder. Use when the user says "เขียน release notes", "ประกาศการเปลี่ยนแปลง", "แจ้งลูกค้า", "release notes", "changelog for customers".
---

# เขียน release notes (SuperBiz: PM)

เป้าหมาย: ได้ `docs/changes/NNN-slug/release-notes.md` สองส่วน: สำหรับลูกค้า และสำหรับทีมภายใน

## ขั้นตอน
1. อ่าน intent.md, spec.md, acceptance.md และ runbook.md (ถ้ามี) ของ change
2. ตรวจว่า gate 4 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 4`
   หากไม่ผ่าน ให้เขียนเป็นฉบับร่าง และระบุบรรทัดแรกว่า "ฉบับร่าง ยังไม่ผ่าน gate 4"
3. ส่วนสำหรับลูกค้า
   - ไม่เกิน 5 บรรทัด ใช้ภาษาสุภาพและเข้าใจง่าย
   - บอกว่าผู้ใช้ได้อะไร และต้องทำอะไรหรือไม่
   - ไม่ใช้ศัพท์เทคนิค ไม่อ้างชื่อไฟล์ ไม่ระบุข้อมูลภายใน
4. ส่วนสำหรับทีมภายใน (ฝ่ายบริการลูกค้า ฝ่ายขาย ฝ่ายปฏิบัติการ)
   - สิ่งที่เปลี่ยน อ้างอิง R1, R2, ... จาก spec.md
   - สิ่งที่ไม่เปลี่ยน (Out of scope)
   - คำถามที่ลูกค้าอาจถาม พร้อมคำตอบ
   - ช่องทางแจ้งปัญหา และวิธีย้อนกลับโดยสรุปจาก runbook.md
5. ห้ามสัญญาสิ่งที่ไม่อยู่ใน spec.md และห้ามระบุตัวเลขที่ไม่มีใน acceptance.md

## สิ่งที่ห้ามทำ
- ห้ามแก้ไฟล์นอก `docs/`

## จบงาน
แจ้งมนุษย์ให้ตรวจถ้อยคำก่อนเผยแพร่ และส่งส่วนภายในให้ทีมที่เกี่ยวข้อง
