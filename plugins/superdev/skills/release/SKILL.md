---
name: release
description: Prepare a release once the change is release-ready (scripts/release-check.sh). Run the release checklist, write rollback steps and a runbook entry in docs/changes/NNN-slug/runbook.md, and run a kill-switch drill. Use when the user says "ปล่อยงาน", "release", "deploy", "เตรียม release", "runbook".
---

# Release (SuperDev: Deploy และ MA)

เป้าหมาย: release ที่ย้อนกลับได้ และมี runbook ให้ผู้ดูแลระบบใช้ต่อ

## ขั้นตอน
1. ตรวจว่าพร้อมปล่อย: `scripts/release-check.sh docs/changes/NNN-slug`
   - release-ready หมายถึง gate 4 มี SuperDev (owner) และ SuperBiz (ตรวจรับ) ครบและไม่ stale
     งาน high ต้องมี escalation ด้วย และ change ต้องไม่มีบันทึก revert
   - งาน low ที่ merge อัตโนมัติแล้ว ยังปล่อยขึ้น production ไม่ได้จนกว่า SuperBiz ตรวจรับ
   - หากไม่ผ่าน ให้แจ้งข้อความทุกบรรทัดแก่มนุษย์และหยุด
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
5. การ merge เข้า main ทำผ่าน `/superdev:merge` และต้องผ่าน hook gate-guard ห้ามหลบ hook
6. หากต้องย้อนกลับหลังปล่อย ให้มนุษย์รัน `scripts/mark-revert.sh docs/changes/NNN-slug "<เหตุผล>"`
   บันทึกนี้ทำให้ release-check ไม่ผ่าน และทำให้ pod ต้องสะสมผลงานใหม่ก่อน merge อัตโนมัติ

## สิ่งที่ห้ามทำ
- ห้ามลบ `.pod/kill-switch` เอง
- ห้ามรัน `scripts/mark-revert.sh` เอง เพราะเป็นการตัดสินใจของมนุษย์
- ห้าม release เมื่อ acceptance.md ระบุ `reject`

## จบงาน
แจ้งมนุษย์ว่าขั้นต่อไปคือ SuperBiz ใช้ `/superbiz:release-notes`
