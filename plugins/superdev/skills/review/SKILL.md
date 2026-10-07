---
name: review
description: Review the branch diff with three reviewer lenses in parallel (security, correctness, tests and edge cases) plus an independent second opinion from reviewer-second on another model, fix Blockers, and write docs/changes/NNN-slug/review.md with the machine-readable header that auto-merge-check reads. Use when the user says "รีวิวโค้ด", "ตรวจ PR", "review", "code review", "ready for gate 4".
---

# Review (SuperDev: QA)

เป้าหมาย: ไม่มี Blocker เหลือ ความเห็นที่สองเห็นตรงกัน และได้ `review.md` สำหรับ gate 4 และ merge

## ขั้นตอน
1. ตรวจว่า working tree สะอาด (`git status`) แล้วรัน `git diff main...HEAD`, `git log main..HEAD --oneline`
   และ `make check` (รวม `scripts/test-strength.sh`)
2. ส่ง agent `reviewer` สามตัวพร้อมกันในข้อความเดียว ทุกตัวได้รับ diff, spec.md, plan.md
   และ REVIEW checklist ด้านล่าง แต่ละตัวเน้นคนละมุม
   - security: สิทธิ์การเข้าถึง ข้อมูลส่วนบุคคล secret การรับ input
   - correctness: ทำตาม requirement ใน spec.md ครบและถูกต้องหรือไม่
   - tests และ edge cases: edge case ใน spec.md มี test หรือไม่ และ test ตรวจพฤติกรรมจริงหรือไม่
3. รวมผลเป็นรายการเดียว ตัดข้อซ้ำ
4. แก้ทุกข้อที่เป็น Blocker แล้วรัน `make check` อีกครั้ง
   - หาก Blocker อยู่ใน test ที่ล็อกแล้ว ห้ามแก้ test ให้แจ้งมนุษย์
5. Major: แก้ หรือเขียนเหตุผลที่ไม่แก้ให้มนุษย์ตัดสิน Major ที่ยังไม่แก้นับเป็น `majors_open`
6. Minor: บันทึกไว้ ไม่ต้องแก้ใน change นี้
7. ส่ง reviewer ตรวจซ้ำจนไม่มี Blocker และ commit การแก้ทั้งหมด
8. ความเห็นที่สอง: ส่ง agent `reviewer-second` ตรวจ diff ล่าสุดด้วย checklist เดียวกัน
   - ส่งเฉพาะ diff, spec.md, plan.md และ checklist ห้ามส่งผลของ reviewer ตัวแรก
   - `agree`: reviewer-second ไม่พบ Blocker ที่ reviewer ตัวแรกพลาด และไม่โต้แย้งผล "ไม่มี Blocker"
   - `disagree`: พบ Blocker ใหม่ หรือโต้แย้งผล ให้แก้ แล้วกลับไปข้อ 2
9. เขียน `docs/changes/NNN-slug/review.md` ตาม `docs/templates/review.md`
   4 บรรทัดแรกต้องเป็น header นี้ (ชื่อ key ต้องตรง เพราะ `scripts/auto-merge-check.sh` อ่าน)
   ```
   blockers: <int>
   majors_open: <int>
   second_opinion: agree | disagree
   reviewed_head: <git sha ของ HEAD ที่ตรวจ>
   ```
   ค่า `reviewed_head` ได้จาก `git rev-parse HEAD` ณ ตอนตรวจ แล้วตามด้วยรายการ findings
10. commit review.md: `git commit -m "docs(NNN): review"`
    commit ที่แก้เฉพาะไฟล์ใน `docs/changes/NNN-slug/` หลัง reviewed_head ไม่ทำให้ review ล้าสมัย
    แต่การแก้โค้ดหรือ test หลังจากนี้ต้อง review ใหม่

## REVIEW checklist
Blocker
- requirement ใน spec.md ข้อใดไม่มีโค้ดหรือ test รองรับ
- ผู้ใช้เห็นข้อมูลของผู้อื่นได้ หรือ error บอกว่าข้อมูลของผู้อื่นมีอยู่
- มีข้อมูลส่วนบุคคล secret หรือ token ในโค้ด test หรือ log
- test ถูกแก้หรือลบหลังล็อก หรือ `make check` ไม่ผ่าน
- `scripts/test-strength.sh` ไม่ผ่าน (มี test ที่ยังผ่านแม้ทุกฟังก์ชันใน app/ คืนค่า None)
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
แจ้งมนุษย์ว่าขั้นต่อไปคือ `/superdev:merge` ซึ่ง merge ตาม Risk ของ change
