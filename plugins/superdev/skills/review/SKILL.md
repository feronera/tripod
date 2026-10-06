---
name: review
description: Review the current branch diff with the reviewer agent using the Blocker/Major/Minor checklist, fix Blockers, and summarise for gate 4. Use when the user says "รีวิวโค้ด", "ตรวจ PR", "review", "code review", "ready for gate 4".
---

# Review (SuperDev: QA)

เป้าหมาย: ไม่มี Blocker เหลือ และได้สรุปสำหรับ gate 4

## ขั้นตอน
1. รัน `git diff main...HEAD` และ `git log main..HEAD --oneline`
2. ส่ง diff, spec.md และ plan.md ให้ agent `reviewer` พร้อม REVIEW checklist ด้านล่าง
3. แก้ทุกข้อที่เป็น Blocker แล้วรัน `make check` อีกครั้ง
   - หาก Blocker อยู่ใน test ที่ล็อกแล้ว ห้ามแก้ test ให้แจ้งมนุษย์
4. Major: แก้ หรือเขียนเหตุผลที่ไม่แก้ให้มนุษย์ตัดสิน
5. Minor: บันทึกไว้ในสรุป ไม่ต้องแก้ใน change นี้
6. ส่ง reviewer ตรวจซ้ำจนไม่มี Blocker

## REVIEW checklist
Blocker
- requirement ใน spec.md ข้อใดไม่มีโค้ดหรือ test รองรับ
- ผู้ใช้เห็นข้อมูลของผู้อื่นได้ หรือ error บอกว่าข้อมูลของผู้อื่นมีอยู่
- มีข้อมูลส่วนบุคคล secret หรือ token ในโค้ด test หรือ log
- test ถูกแก้หรือลบหลังล็อก หรือ `make check` ไม่ผ่าน
- มี dependency นอก Python standard library

Major
- edge case ใน spec.md ไม่มี test
- โค้ดเกินขอบเขตของ plan.md หรือแตะ Out of scope
- ไม่มีวิธี rollback ตามที่ plan.md ระบุ

Minor
- ชื่อไม่สื่อความหมาย โค้ดซ้ำ ข้อความภาษาไทยไม่ตรงกับ ux-brief.md

## จบงาน
เขียนสรุปสำหรับ gate 4 ใน PR description
1. สิ่งที่เปลี่ยน อ้างอิง R1, R2, ...
2. ผล `make check`
3. Major และ Minor ที่เหลือ พร้อมเหตุผล
4. demo steps สำหรับ SuperBiz ใช้ใน `/superbiz:acceptance`
แจ้งมนุษย์ว่า SuperDev รัน `scripts/gate.sh docs/changes/NNN-slug 4` หลังมี acceptance.md
