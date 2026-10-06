---
name: incident
description: Turn an application log into a draft change. Decide severity, never copy personal data, create a change with scripts/new-change.sh and fill intent.md citing log lines. Use when the user says "มี incident", "อ่าน log", "ระบบมีปัญหา", "incident", "triage this log".
---

# Incident เป็น change (SuperDev: MA)

เป้าหมาย: intent.md ฉบับร่างที่อ้างอิงหลักฐานจาก log โดยไม่มีข้อมูลส่วนบุคคล

## ขั้นตอน
1. ขอ path ของไฟล์ log จากมนุษย์ (เช่น `logs/sample-app.log`) ห้ามเดา path
2. ส่ง path ให้ agent `monitor` อ่านและสรุป หรืออ่านเองด้วยเครื่องมืออ่านอย่างเดียว
3. ตัดสิน severity
   - SEV1: ผู้ใช้จำนวนมากใช้งานไม่ได้ หรือข้อมูลรั่ว
   - SEV2: feature หลักผิดพลาดกับผู้ใช้บางส่วน
   - SEV3: ผิดพลาดเล็กน้อย มีทางเลี่ยง
4. ห้ามคัดลอกข้อมูลส่วนบุคคล เช่น ชื่อ เบอร์โทร อีเมล ที่อยู่ เลขบัตร
   ให้อ้างอิงเป็นหมายเลขบรรทัด และแทนค่าด้วย `[ตัดข้อมูลส่วนบุคคล]`
5. หากหลักฐานไม่พอ (น้อยกว่า 2 บรรทัดที่สอดคล้องกัน หรือสาเหตุเป็นเพียงการคาดเดา)
   ให้หยุดและถามมนุษย์ ห้ามสร้าง change
6. ขอให้มนุษย์รัน `scripts/new-change.sh <slug>` (คำสั่งปฏิเสธเมื่อถึง WIP limit ให้แจ้งมนุษย์)
7. เขียน intent.md ตาม template
   - Problem: อาการ จำนวนครั้ง ช่วงเวลา อ้างอิง `logs/...:<line>`
   - Success measure: เช่น จำนวน error ต่อชั่วโมงจาก X เป็น 0 ใช้ตัวเลขจาก log เท่านั้น
   - Risk: ตาม `docs/risk-tiers.md` หาก log มีข้อมูลส่วนบุคคล ให้พิจารณา `Risk: high`
   - Open questions: สิ่งที่ log ไม่ได้บอก
8. SEV1 ให้แจ้ง escalation จาก pod.yml ทันที และแนะนำให้มนุษย์พิจารณา kill switch

## สิ่งที่ห้ามทำ
- ห้ามรัน `scripts/gate.sh` และห้ามแก้ไฟล์ log

## จบงาน
แจ้งมนุษย์ว่า intent.md เป็นฉบับร่าง ให้ SuperBiz ตรวจและเป็น owner ของ gate 1
