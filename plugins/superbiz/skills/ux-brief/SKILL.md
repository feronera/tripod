---
name: ux-brief
description: Act as the pod designer and write ux-brief.md (screens, empty/loading/error/success states, Thai copy, accessibility) from an approved intent. Use when the user says "ทำ ux brief", "ออกแบบหน้าจอ", "เขียนข้อความบนหน้าจอ", "ux brief", "design the screens".
---

# ร่าง ux-brief.md (SuperBiz: Designer)

เป้าหมาย: ได้ `docs/changes/NNN-slug/ux-brief.md` ที่ใช้ประกอบ spec.md ใน gate 2

## ขั้นตอน
1. อ่าน intent.md ของ change และ `docs/templates/ux-brief.md`
2. ตรวจว่า gate 1 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 1`
   หากไม่ผ่าน ให้แจ้งมนุษย์และหยุด
3. ระบุหน้าจอที่ต้องมี และจุดประสงค์ของแต่ละหน้าจอ ให้น้อยที่สุดที่ตอบ intent ได้
4. ทุกหน้าจอต้องมีครบ 4 states: empty, loading, error, success
   - error ต้องบอกผู้ใช้ว่าทำอะไรต่อได้
   - error ต้องไม่เปิดเผยข้อมูลของผู้อื่น หรือบอกว่าข้อมูลของผู้อื่นมีอยู่
5. เขียน copy ภาษาไทยที่ผู้ใช้เห็นจริง ใช้ภาษาสุภาพ สั้น และชัดเจน
6. เขียน accessibility notes: screen reader, ไม่สื่อความหมายด้วยสีอย่างเดียว, ใช้งานด้วยคีย์บอร์ดได้
7. ส่ง ux-brief.md ให้ agent `ux-critic` ตรวจ แล้วแก้ตามข้อที่เป็น Blocker หรือ Major
8. ข้อที่ยังตัดสินใจไม่ได้ ให้ระบุเป็นคำถามท้ายเอกสาร ไม่เดาแทน PO

## สิ่งที่ห้ามทำ
- ห้ามแก้ไฟล์นอก `docs/`
- ห้ามเพิ่ม feature ที่ไม่อยู่ใน intent.md

## จบงาน
แจ้งมนุษย์ว่าขั้นต่อไปคือ `/superbiz:spec` เพื่อรวม intent และ ux-brief เป็น spec.md
