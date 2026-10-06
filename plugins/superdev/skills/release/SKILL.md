---
name: release
description: Prepare a release after gate 4. Run the release checklist, write rollback steps and a runbook entry in docs/changes/NNN-slug/runbook.md, and run a kill-switch drill. Use when the user says "ปล่อยงาน", "release", "deploy", "เตรียม release", "runbook".
---

# Release (SuperDev: Deploy และ MA)

เป้าหมาย: release ที่ย้อนกลับได้ และมี runbook ให้ผู้ดูแลระบบใช้ต่อ

## ขั้นตอน
1. ตรวจว่า gate 4 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 4`
   หากไม่ผ่าน ให้แจ้งมนุษย์และหยุด
2. Release checklist
   - [ ] `make check` ผ่านบน branch ล่าสุด
   - [ ] CI (pod-gates) ผ่าน
   - [ ] acceptance.md ระบุ `accept`
   - [ ] Rollback ใน plan.md ซ้อมแล้วอย่างน้อยหนึ่งครั้ง
   - [ ] ไม่มีข้อมูลส่วนบุคคลหรือ secret ใน diff
3. เขียน `docs/changes/NNN-slug/runbook.md`
   - สิ่งที่เปลี่ยน (หนึ่งย่อหน้า)
   - วิธีตรวจว่าระบบทำงานปกติหลัง release
   - อาการผิดปกติที่ควรเฝ้าดู และ log ที่ควรอ่าน
   - ขั้นตอน rollback ทีละคำสั่ง เช่น `git revert <commit>` แล้ว `make check`
   - ผู้ติดต่อ: SuperDev และ escalation จาก pod.yml
4. Kill-switch drill
   1. ขอให้มนุษย์รัน `touch .pod/kill-switch`
   2. ลองเรียกเครื่องมือหนึ่งครั้ง และยืนยันว่า hook ปฏิเสธพร้อมข้อความ "kill switch เปิดอยู่"
   3. หยุดทำงานทั้งหมด และรอให้มนุษย์รัน `rm .pod/kill-switch` เอง
   4. บันทึกผล drill ใน runbook.md
5. การ merge เข้า main ต้องผ่าน hook gate-guard ห้ามหลบ hook

## สิ่งที่ห้ามทำ
- ห้ามลบ `.pod/kill-switch` เอง
- ห้าม release เมื่อ acceptance.md ระบุ `reject`

## จบงาน
แจ้งมนุษย์ว่าขั้นต่อไปคือ SuperBiz ใช้ `/superbiz:release-notes`
