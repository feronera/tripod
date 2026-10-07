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
- gate 3: plan.md ต้องมี `## Data shape`, `## Throughput checkpoint` และ `## Parallel parts` (script ตรวจ)
- gate 4 แยกเป็น merge-ready (`scripts/gate-check.sh <dir> 4`) และ release-ready (`scripts/release-check.sh <dir>`)
  สิทธิ์ merge ตาม risk อยู่ใน `docs/merge-by-risk.md`
- รายละเอียดอยู่ใน `docs/gates.md` และ `docs/risk-tiers.md`

## กฎที่ห้ามละเมิด
1. agent ห้ามรัน `scripts/gate.sh` และ `scripts/mark-revert.sh` และห้ามแก้ `gates.log` ด้วยมือ
   เพราะการอนุมัติและการบันทึก revert เป็นของมนุษย์เท่านั้น
2. เมื่อมีไฟล์ `.pod/lock-tests` ห้ามแก้ไฟล์ใน `tests/` หาก test ดูผิด ให้หยุดและแจ้งมนุษย์
3. เมื่อมีไฟล์ `.pod/kill-switch` ให้หยุดทำงานทันที และห้ามลบไฟล์นี้
4. ห้าม merge หรือ push เข้า main จนกว่า `scripts/gate-check.sh --all` ผ่าน และ change ล่าสุด merge-ready ที่ gate 4
   ข้อยกเว้นเดียวของ agent: รัน `scripts/auto-merge-check.sh <dir> --record` แล้ว `gh pr merge --auto --squash`
   ได้เฉพาะเมื่อคำสั่งพิมพ์ `ALLOW` (งาน medium ให้ SuperDev ลงชื่อ gate 4 ก่อน งาน high ให้มนุษย์ merge)
5. ห้ามแต่งตัวเลข หากไม่ทราบ ให้ใส่ใน Open questions
6. ห้ามคัดลอกข้อมูลส่วนบุคคลจาก log ลงในเอกสารหรือโค้ด
7. ห้ามแก้ artifact ที่ผ่าน gate แล้วโดยไม่แจ้ง เพราะการอนุมัติจะ stale
8. test ต้องตรวจพฤติกรรมจริง `scripts/test-strength.sh` ต้องผ่าน (อยู่ใน `make check`)
9. แก้ bug ที่ต้นเหตุ: ทำซ้ำให้เห็นก่อน แล้วเขียน test ที่ fail ก่อนแก้ (`/superdev:bug-fix`)

## ที่อยู่ของงาน
- artifact ของแต่ละ change อยู่ใน `docs/changes/NNN-slug/`
  (intent.md, ux-brief.md, spec.md, plan.md, review.md, acceptance.md, runbook.md, gates.log)
- เริ่ม change ใหม่ด้วย `scripts/new-change.sh <slug>` เท่านั้น
- template อยู่ใน `docs/templates/`
- path อ่อนไหวอยู่ใน `docs/risk-paths` change ที่แตะ path เหล่านี้ถือเป็น high

## Stack
- Python 3 standard library เท่านั้น ห้ามเพิ่ม dependency
- โค้ดอยู่ใน `app/` test อยู่ใน `tests/` (unittest)

## Commands
- `make setup`: ตรวจเครื่องมือ และเตรียมโฟลเดอร์ `.pod/`
- `make test`: รัน unit test ทั้งหมด
- `make strength`: `scripts/test-strength.sh` หา test ที่ยังผ่านแม้ทุกฟังก์ชันใน app/ คืนค่า None
- `make check`: test, strength, ตรวจ CODEOWNERS และ `scripts/gate-check.sh --all` (CI ใช้คำสั่งนี้)
- `scripts/auto-merge-check.sh <dir> [--base main] [--record]`: ALLOW หรือ DENY สำหรับ merge อัตโนมัติ
- `scripts/release-check.sh <dir>`: พร้อมปล่อยขึ้น production หรือไม่
- `make metrics CHANGE=docs/changes/NNN-slug`: เวลาจาก intent ถึงแต่ละ gate
