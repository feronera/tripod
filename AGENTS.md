# AGENTS.md

กฎสำหรับ agent ทุกตัวใน repo นี้ (Claude Code อ่านผ่าน CLAUDE.md)

## Pod
- pod มีมนุษย์สองคน: **SuperBiz** (PO, PM, BA, Designer: อะไรและเพราะอะไร) และ **SuperDev** (SA, Dev, QA, Deploy, MA: อย่างไรและปลอดภัยหรือไม่)
- agent ร่างงานของทุกบทบาท มนุษย์เป็นผู้ตัดสินใจที่ gate
- ชื่อและอีเมลของสมาชิกอยู่ใน `pod.yml`

## Gates
| Gate | Artifact | Owner | Cross |
|---|---|---|---|
| 1 | intent.md | SuperBiz | SuperDev |
| 2 | spec.md (+ ux-brief.md) | SuperBiz | SuperDev |
| 3 | plan.md | SuperDev | SuperBiz |
| 4 | acceptance.md + PR | SuperDev | SuperBiz |

- `Risk: high` ใน intent.md ต้องมี escalation ลงชื่อเพิ่มที่ gate 2 และ 4
- รายละเอียดอยู่ใน `docs/gates.md` และ `docs/risk-tiers.md`

## กฎที่ห้ามละเมิด
1. agent ห้ามรัน `scripts/gate.sh` และห้ามแก้ `gates.log` เพราะการอนุมัติเป็นของมนุษย์เท่านั้น
2. เมื่อมีไฟล์ `.pod/lock-tests` ห้ามแก้ไฟล์ใน `tests/` หาก test ดูผิด ให้หยุดและแจ้งมนุษย์
3. เมื่อมีไฟล์ `.pod/kill-switch` ให้หยุดทำงานทันที และห้ามลบไฟล์นี้
4. ห้าม merge หรือ push เข้า main จนกว่า `scripts/gate-check.sh --all` ผ่าน และ change ล่าสุดผ่าน gate 4
5. ห้ามแต่งตัวเลข หากไม่ทราบ ให้ใส่ใน Open questions
6. ห้ามคัดลอกข้อมูลส่วนบุคคลจาก log ลงในเอกสารหรือโค้ด
7. ห้ามแก้ artifact ที่ผ่าน gate แล้วโดยไม่แจ้ง เพราะการอนุมัติจะ stale

## ที่อยู่ของงาน
- artifact ของแต่ละ change อยู่ใน `docs/changes/NNN-slug/`
  (intent.md, ux-brief.md, spec.md, plan.md, acceptance.md, runbook.md, gates.log)
- เริ่ม change ใหม่ด้วย `scripts/new-change.sh <slug>` เท่านั้น
- template อยู่ใน `docs/templates/`

## Stack
- Python 3 standard library เท่านั้น ห้ามเพิ่ม dependency
- โค้ดอยู่ใน `app/` test อยู่ใน `tests/` (unittest)

## Commands
- `make setup`: ตรวจเครื่องมือ และเตรียมโฟลเดอร์ `.pod/`
- `make test`: รัน unit test ทั้งหมด
- `make check`: test และ `scripts/gate-check.sh --all` (CI ใช้คำสั่งนี้)
- `make metrics CHANGE=docs/changes/NNN-slug`: เวลาจาก intent ถึงแต่ละ gate
