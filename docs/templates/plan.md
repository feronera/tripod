# Plan: <ชื่องาน>

อ้างอิง: intent.md, spec.md

## Data shape
<โครงข้อมูลหลักและโครงสร้างที่ใช้จัด เช่น ตาราง, state machine, typed record ก่อนเขียน logic>

## Throughput checkpoint
- Blocking first steps: <งานที่ต้องเสร็จก่อนงานอื่นจึงเริ่มได้>
- Independent workstreams: <งานที่ทำแยกกันได้ หรือ n/a: <เหตุผล>>
- Shared mutable state: <ไฟล์หรือข้อมูลที่หลายส่วนต้องแก้ร่วมกัน หรือ n/a: <เหตุผล>>
- Smallest safe decomposition: <การแบ่งงานที่เล็กที่สุดที่แต่ละส่วนจบด้วยการตรวจได้>

## Parallel parts
<ไม่บังคับ ถ้าไม่แบ่งให้เขียน `none: <เหตุผล>`>
### A
files: app/a.py, app/b.py
### B
files: app/c.py

## Files to change
| ไฟล์ | เปลี่ยนอะไร | requirement |
|---|---|---|
| <path> | | R1 |

## Order of work
1. เขียน test ที่ fail จาก edge cases ใน spec.md แล้ว commit
2. ล็อก tests (`touch .pod/lock-tests`)
3. <unit ถัดไป: การเปลี่ยนที่เล็กที่สุดที่จบด้วย `make test` ผ่าน>

## Risks
- <ความเสี่ยงทางเทคนิค และวิธีลด>

## Proof
- `make test` และ `make strength` ผ่าน
- <วิธีพิสูจน์แต่ละ requirement>

## Rollback
- <วิธีย้อนกลับ เช่น git revert <commit> และสิ่งที่ต้องตรวจหลังย้อน>

## สรุปให้ SuperBiz
1. <ทำอะไร>
2. <กระทบผู้ใช้อย่างไร>
3. <ความเสี่ยงที่ SuperBiz ควรรู้>
