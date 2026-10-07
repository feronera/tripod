# ให้ agent หลายตัวทำงานพร้อมกัน

หลักการ: ทำพร้อมกันเฉพาะงานที่แบ่งได้ ทุกสายส่งผลกลับมาที่ session หลักของแต่ละคน แล้วคนตัดสินที่ gate
ภาพรวมอยู่ในสไลด์ "Multi-agent ใน pod" ของ `deck/adlc-pod-deck.html`

## กติกา 3 ข้อ

| งาน | ทำอย่างไร | เหตุผล |
|---|---|---|
| agent ที่อ่านอย่างเดียว (ba-researcher, ux-critic, reviewer) | สั่งพร้อมกันได้ทุกครั้ง | ไม่แก้ไฟล์ จึงไม่ชนกัน |
| agent ที่เขียนโค้ด | หนึ่ง agent หนึ่ง worktree และไฟล์ไม่ทับกัน | ถ้า plan.md แบ่งไฟล์ไม่ได้ ให้ทำทีละส่วน |
| การวางแผน การเขียน spec และการอนุมัติ gate | session หลักตัวเดียว | งานที่ต้องทำต่อกันจะแย่ลงเมื่อใช้ agent หลายตัว |

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

# review สามมุมพร้อมกัน
/superdev:review ให้ reviewer 3 ตัวทำพร้อมกัน: security, ความถูกต้อง, test และ edge case

# เก็บกวาด
git worktree remove ../pod-a && git worktree remove ../pod-b
```

## ข้อควรระวัง

- `.pod/` ไม่อยู่ใน git worktree ใหม่จึงยังไม่ล็อก test ต้อง `touch .pod/lock-tests` ในทุก worktree
- kill switch ทำงานรายโฟลเดอร์ เมื่อต้องหยุดทุก agent ให้ `touch .pod/kill-switch` ในทุก worktree
- ถ้า merge ชนกัน แปลว่าการแบ่งไฟล์ใน plan.md ไม่จริง ให้แก้ plan.md แล้วทำส่วนที่ชนทีละส่วน
- จำนวน agent ที่เขียนโค้ดพร้อมกันไม่ควรเกินจำนวนที่ SuperDev review ทัน ส่วนใหญ่สองส่วนก็พอ
