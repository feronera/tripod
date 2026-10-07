---
name: build
description: Implement an approved plan.md in small verifiable units after tests are locked. One unit is the smallest change that ends in a passing check, committed as feat(NNN) before the next unit starts. Use when the user says "build", "ลงมือเขียนโค้ด", "ทำตาม plan", "implement", "เขียนโค้ดให้ test ผ่าน".
---

# Build ทีละ unit (SuperDev: Dev)

เป้าหมาย: โค้ดใน `app/` ที่ทำให้ test ที่ล็อกไว้ผ่าน โดยทุก commit อยู่ในสถานะที่ตรวจแล้ว

## ก่อนเริ่ม
1. ตรวจว่า gate 3 ผ่านแล้ว: `scripts/gate-check.sh docs/changes/NNN-slug 3`
2. ตรวจว่า tests ถูกล็อกแล้ว (มีไฟล์ `.pod/lock-tests`) หากยังไม่มี ให้ใช้ `/superdev:test-first` ก่อน
3. อ่าน plan.md: Data shape, Throughput checkpoint, Parallel parts และ Order of work
4. หาก Parallel parts มีมากกว่าหนึ่งส่วน ให้ทำตาม `docs/parallel-agents.md`
   (หนึ่ง agent ต่อหนึ่ง worktree และแก้เฉพาะไฟล์ใน `files:` ของส่วนตัวเอง)
5. ตรวจว่าจุดเริ่มต้นเขียว: `make test` ต้องผ่านทุก test ยกเว้น test ใหม่ที่ล็อกไว้

## Unit คืออะไร
- unit คือการเปลี่ยนที่เล็กที่สุดที่จบด้วยการตรวจได้ เช่น test ของ R1 ผ่าน
- เริ่มจาก Blocking first steps ใน plan.md เช่น โครงข้อมูลใน Data shape ก่อน logic

## วนทีละ unit
1. เลือก unit ถัดไปตาม Order of work
2. แก้โค้ดเฉพาะที่ unit นี้ต้องใช้ ไม่แก้นอก Files to change
3. รัน `make test` และดูว่า test ของ unit นี้ผ่าน และ test ที่เคยผ่านยังผ่าน
4. commit ทันที: `git commit -m "feat(NNN): <unit>"`
5. ห้ามเริ่ม unit ถัดไปขณะที่มี test แดงที่ควรผ่านแล้ว ให้แก้ให้เขียวก่อน
6. หาก unit ใดต้องเปลี่ยน test ที่ล็อกไว้จึงจะผ่าน ให้หยุดทันที รายงาน test, เหตุผล และทางเลือก
   ให้มนุษย์ตัดสิน ห้ามหลบ hook ด้วยวิธีอื่น เช่น ใช้ Bash เขียนทับไฟล์

## เมื่อครบทุก unit
1. รัน `make check` (รวม `scripts/test-strength.sh`) ต้องผ่าน
2. ตรวจว่า diff อยู่ในขอบเขตของ plan.md: `git diff main...HEAD --stat`

## สิ่งที่ห้ามทำ
- ห้ามเพิ่ม dependency นอก Python standard library
- ห้ามรวมหลาย unit ใน commit เดียว และห้าม commit ขณะ test แดง
- ห้ามรัน `scripts/gate.sh` และห้ามลบ `.pod/lock-tests`

## จบงาน
แจ้งมนุษย์ว่าขั้นต่อไปคือ `/superdev:review`
