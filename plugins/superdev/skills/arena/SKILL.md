---
name: arena
description: Settle a contested design by building two approaches side by side in separate git worktrees against the same locked tests, then compare them on tests, test strength, diff size and reviewer findings. SuperDev picks; the choice and reason go to plan.md under Decision log. Use when the user says "arena", "ลองสองแบบ", "เทียบสองแนวทาง", "ตัดสินใจไม่ได้ว่าจะออกแบบแบบไหน".
---

# Arena: เทียบสองแนวทางด้วยของจริง (SuperDev: SA)

ใช้เมื่อมีแนวทางออกแบบสองแบบที่โต้แย้งกันได้ทั้งคู่ และการลองทำจริงตัดสินได้ดีกว่าการถกเถียง
มนุษย์ SuperDev เป็นผู้เลือก agent มีหน้าที่เตรียมหลักฐาน

## ก่อนเริ่ม
1. gate 3 ผ่านแล้ว และ test ของ change ถูก commit บน `change/NNN` และล็อกแล้ว
2. เขียนแนวทาง A และ B อย่างละ 2-3 บรรทัด ให้มนุษย์ยืนยันว่าเป็นสองแนวทางที่ต่างกันจริง

## ขั้นตอน
1. ขอให้มนุษย์สร้าง worktree และล็อก tests ในทั้งสองที่
   ```
   git worktree add ../arena-a -b change/NNN-arena-a change/NNN
   git worktree add ../arena-b -b change/NNN-arena-b change/NNN
   mkdir -p ../arena-a/.pod ../arena-b/.pod
   touch ../arena-a/.pod/lock-tests ../arena-b/.pod/lock-tests
   ```
2. ให้ agent สองตัวทำพร้อมกัน ตัวละ worktree โดยใช้ `/superdev:build`
   ทั้งสองตัวได้รับ test ที่ล็อกชุดเดียวกัน และคำอธิบายแนวทางของตัวเองเท่านั้น
3. เมื่อทั้งสองเสร็จ เก็บผลในแต่ละ worktree
   - `make test` ผ่านหรือไม่
   - `scripts/test-strength.sh` ผ่านหรือไม่
   - ขนาด diff: `git diff --shortstat change/NNN...HEAD`
   - ผลของ agent `reviewer`: จำนวน Blocker, Major, Minor
4. ทำตารางเทียบให้มนุษย์

   | เกณฑ์ | A | B |
   |---|---|---|
   | make test | | |
   | test-strength | | |
   | diff (บรรทัด) | | |
   | Blocker / Major / Minor | | |

5. มนุษย์ SuperDev เลือก หากผลใกล้กัน ให้เสนอแบบที่ diff เล็กกว่าและอ่านง่ายกว่า
6. บันทึกใน plan.md
   ```
   ## Decision log
   - <วันที่> arena: เลือก A (<แนวทาง>) แทน B (<แนวทาง>) เพราะ <เหตุผลจากตาราง>
   ```
   การแก้ plan.md ทำให้การอนุมัติ gate 3 stale ต้องแจ้ง SuperDev และ SuperBiz ให้ลงชื่อใหม่
7. นำแบบที่ชนะเข้า `change/NNN` แล้วขอให้มนุษย์ลบแบบที่แพ้
   ```
   git switch change/NNN && git merge change/NNN-arena-a
   git worktree remove ../arena-a && git worktree remove ../arena-b
   git branch -D change/NNN-arena-b && git branch -d change/NNN-arena-a
   ```

## สิ่งที่ห้ามทำ
- ห้ามเลือกแทนมนุษย์ และห้ามรวมสองแบบเข้าด้วยกันโดยไม่มีการตัดสินใจ
- ห้ามแก้ test ที่ล็อกในแบบใดแบบหนึ่งเพื่อให้ผ่าน

## จบงาน
แจ้งมนุษย์ให้ลงชื่อ gate 3 ใหม่ แล้วต่อด้วย `/superdev:review`
