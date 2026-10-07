# ให้ agent หลายตัวทำงานพร้อมกัน

หลักการ: ทำพร้อมกันเฉพาะงานที่แบ่งได้ ทุกสายส่งผลกลับมาที่ session หลักของแต่ละคน แล้วคนตัดสินที่ gate
ภาพรวมอยู่ในสไลด์ "Multi-agent ใน pod" ของ `deck/adlc-pod-deck.html`

## กติกา 3 ข้อ

| งาน | ทำอย่างไร | เหตุผล |
|---|---|---|
| agent ที่อ่านอย่างเดียว (ba-researcher, ux-critic, reviewer) | สั่งพร้อมกันได้ทุกครั้ง | ไม่แก้ไฟล์ จึงไม่ชนกัน |
| agent ที่เขียนโค้ด | หนึ่ง agent หนึ่ง worktree และไฟล์ไม่ทับกัน | ถ้า plan.md แบ่งไฟล์ไม่ได้ ให้ทำทีละส่วน |
| การวางแผน การเขียน spec และการอนุมัติ gate | session หลักตัวเดียว | งานที่ต้องทำต่อกันจะแย่ลงเมื่อใช้ agent หลายตัว |

## เริ่มจาก plan.md

การแบ่งงานต้องเขียนไว้ใน plan.md ก่อน gate 3 และ gate 3 ตรวจรูปแบบนี้

```
## Throughput checkpoint
- Blocking first steps: test ที่ fail และโครงข้อมูลใน Data shape
- Independent workstreams: หน้ารายการ (A) และหน้ารายละเอียด (B)
- Shared mutable state: n/a: แต่ละส่วนแก้ไฟล์ของตัวเอง
- Smallest safe decomposition: หนึ่ง requirement ต่อหนึ่ง commit

## Parallel parts
### A
files: app/history.py
### B
files: app/detail.py
```

- ถ้าไม่แบ่ง ให้เขียน `none: <เหตุผล>` ใต้ `## Parallel parts`
- ไฟล์ของแต่ละส่วนต้องไม่ซ้ำกัน ถ้าซ้ำ gate 3 จะไม่ผ่านและแจ้งชื่อไฟล์ที่ซ้ำ
- ถ้ามี Shared mutable state ให้แยกออกเป็นไฟล์ของแต่ละส่วนก่อน ถ้าแยกไม่ได้ ให้ทำส่วนนั้นทีละส่วน
- แต่ละส่วนทำด้วย `/superdev:build` ทีละ unit และ commit ทุก unit ที่ test ผ่าน

## SuperBiz: fan-out ใน session เดียว

ใน Claude Code ที่โหลด `plugins/superbiz`

```
/superbiz:spec docs/changes/002-[ชื่องาน]
ให้ ba-researcher และ ux-critic ทำงานพร้อมกัน แล้วรวมผลลง spec.md
```

## SuperDev: build สองส่วนพร้อมกัน แล้ว review สามมุม

ก่อนเริ่ม plan.md ต้องแบ่งงานเป็นส่วน A และ B ที่แก้ไฟล์ไม่ทับกัน และ test ของ change ต้อง commit บน `change/001` แล้ว

```
git worktree add ../pod-a -b change/001-a change/001
git worktree add ../pod-b -b change/001-b change/001
mkdir -p ../pod-a/.pod ../pod-b/.pod
touch ../pod-a/.pod/lock-tests ../pod-b/.pod/lock-tests

# terminal 1
cd ../pod-a && claude --plugin-dir ~/my-pod/plugins/superdev
# terminal 2
cd ../pod-b && claude --plugin-dir ~/my-pod/plugins/superdev

# รวม แล้วให้ test ที่ล็อกไว้ตัดสิน
git switch change/001
git merge change/001-a change/001-b
make check

# review สามมุมพร้อมกัน แล้วตามด้วย reviewer-second (model อื่น) เป็นความเห็นที่สอง
/superdev:review

# เก็บกวาด
git worktree remove ../pod-a && git worktree remove ../pod-b
```

## Arena: เมื่อยังเลือกแนวทางออกแบบไม่ได้

ใช้ worktree สองชุดแบบเดียวกัน แต่ทั้งสองทำงานเดียวกันคนละแนวทาง แล้วเทียบด้วย test ที่ล็อกไว้
test-strength, ขนาด diff และผล reviewer มนุษย์ SuperDev เลือก แล้วบันทึกใน plan.md ใต้ `## Decision log`
ขั้นตอนอยู่ใน skill `/superdev:arena`

## ข้อควรระวัง

- `.pod/` ไม่อยู่ใน git worktree ใหม่จึงยังไม่ล็อก test ต้อง `touch .pod/lock-tests` ในทุก worktree
- kill switch ทำงานรายโฟลเดอร์ เมื่อต้องหยุดทุก agent ให้ `touch .pod/kill-switch` ในทุก worktree
- ถ้า merge ชนกัน แปลว่าการแบ่งไฟล์ใน plan.md ไม่จริง ให้แก้ plan.md แล้วทำส่วนที่ชนทีละส่วน
- จำนวน agent ที่เขียนโค้ดพร้อมกันไม่ควรเกินจำนวนที่ SuperDev review ทัน ส่วนใหญ่สองส่วนก็พอ
