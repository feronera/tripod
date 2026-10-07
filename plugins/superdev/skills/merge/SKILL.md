---
name: merge
description: Merge a reviewed change by its risk tier. Low risk may auto-merge only when scripts/auto-merge-check.sh prints ALLOW; medium needs SuperDev to sign gate 4 first; high stops and hands over to humans. Use when the user says "merge", "merge ตาม risk", "รวมเข้า main", "ปิด PR", "auto-merge".
---

# Merge ตาม risk (SuperDev: Deploy)

เป้าหมาย: merge เข้า main ตามสิทธิ์ของแต่ละระดับความเสี่ยงใน `docs/merge-by-risk.md`

## ก่อนเริ่ม
1. `review.md` ของ change มีอยู่ และ `blockers: 0`
2. PR เปิดแล้ว และ CI job `pod-gates` ผ่าน
3. อ่าน Risk จาก intent.md และตรวจว่า diff แตะ path ใน `docs/risk-paths` หรือไม่
   (`git diff --name-only main...HEAD`) ถ้าแตะ ให้ถือว่าเป็น high

## Risk: low
1. รัน `scripts/auto-merge-check.sh docs/changes/NNN-slug`
2. ถ้าพิมพ์ `DENY` ให้แจ้งเหตุผลทุกบรรทัดแก่มนุษย์ แล้วทำตามแบบ medium (หรือแก้ตามเหตุผล)
3. ถ้าพิมพ์ `ALLOW` ให้รัน `scripts/auto-merge-check.sh docs/changes/NNN-slug --record`
   แล้ว commit และ push gates.log: `git commit -m "chore(NNN): auto-merge record" -- docs/changes/NNN-slug/gates.log`
4. รัน `gh pr merge --auto --squash` (hook gate-guard ตรวจซ้ำก่อน)
5. แจ้ง SuperBiz ว่าต้องตรวจรับด้วย `/superbiz:acceptance` และลงชื่อ gate 4 ภายใน
   `acceptance_hours` ใน pod.yml ก่อนปล่อยขึ้น production

## Risk: medium
1. acceptance.md ต้องมีแล้ว (SuperBiz ร่างด้วย `/superbiz:acceptance`)
   แจ้ง SuperDev ให้ตรวจ review.md และ acceptance.md แล้วลงชื่อ gate 4 เอง
   (`scripts/gate.sh docs/changes/NNN-slug 4`)
2. หลังจาก `scripts/gate-check.sh docs/changes/NNN-slug 4` ผ่าน จึงรัน `gh pr merge --auto --squash`
3. SuperBiz ลงชื่อ gate 4 (cross) ก่อน release หาก SuperBiz แก้ acceptance.md การลงชื่อของ SuperDev จะ stale และต้องลงชื่อใหม่

## Risk: high
- หยุด ห้าม merge เอง แจ้ง SuperDev, SuperBiz และ escalation ว่าต้องลงชื่อ gate 4 ครบสามคน
  และ approve PR บน GitHub ครบสามคน แล้วมนุษย์เป็นผู้ merge

## สิ่งที่ห้ามทำ
- ห้ามรัน `scripts/gate.sh` และ `scripts/mark-revert.sh` และห้ามแก้ `gates.log` ด้วยมือ
  (บรรทัด `role=auto` ต้องมาจาก `--record` เท่านั้น)
- ห้ามรัน `--record` หรือ `gh pr merge` เมื่อผลไม่ใช่ `ALLOW`
- ห้ามลด Risk ใน intent.md เพื่อให้ merge อัตโนมัติได้

## จบงาน
แจ้งมนุษย์ว่าขั้นต่อไปคือ `/superdev:release` ซึ่งใช้ `scripts/release-check.sh`
