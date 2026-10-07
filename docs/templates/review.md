blockers: 0
majors_open: 0
second_opinion: agree
reviewed_head: <git rev-parse HEAD ของ commit ที่ตรวจ>

# Review: <ชื่องาน>

4 บรรทัดแรกเป็น header ที่ `scripts/auto-merge-check.sh` อ่าน ห้ามเปลี่ยนชื่อ key
`second_opinion: agree` หมายถึง reviewer-second ไม่พบ Blocker ที่ reviewer หลักพลาด และไม่โต้แย้งผล "ไม่มี Blocker"

## Blocker
- <path:line ปัญหา (ข้อ checklist / R?) -> สิ่งที่ต้องแก้ หรือ "ไม่มี">

## Major
- <path:line ปัญหา -> แก้แล้ว หรือเหตุผลที่ไม่แก้>

## Minor
- <path:line ปัญหา>

## Second opinion (reviewer-second)
- <ผลของ reviewer-second และจุดที่เห็นต่าง>

## ผลการตรวจ
- `make check`: <ผ่าน หรือไม่ผ่าน>
- `scripts/test-strength.sh`: <ผ่าน หรือไม่ผ่าน>
